from src.agents.base import BaseAgent, haversine_km
from src.agents.decisions import DecisionLog
from src.models import AgentResult, PickupStop

DEPOT_LAT, DEPOT_LON = 43.6532, -79.3832


class LogisticsPlannerAgent(BaseAgent):
    name = "Logistics Planner"
    dataset = "Toronto Dinesafe (#1) coordinates"

    def run(self, context: dict) -> AgentResult:
        log = DecisionLog()
        matches = [m for m in context.get("matches", []) if m.approved]
        if not matches:
            matches = context.get("matches", [])[:3]

        log.add(
            "Depot at Toronto distribution centre",
            f"({DEPOT_LAT}, {DEPOT_LON})",
            "All routes start from central FoodBridge hub",
        )

        stops_data: list[tuple[str, str, str, float, float, str]] = []
        for match in matches:
            stops_data.append((
                "pickup", match.donor.name, match.donor.address,
                match.donor.latitude, match.donor.longitude,
                f"Collect {match.allocated_kg:.1f} kg → {match.recipient.name}",
            ))
            stops_data.append((
                "dropoff", match.recipient.name, match.recipient.region,
                match.recipient.latitude, match.recipient.longitude,
                "Verify temperature & receipt log",
            ))

        log.add(
            "Nearest-neighbor TSP heuristic from depot",
            f"{len(stops_data)} stops for {len(matches)} matches",
            "Greedy route optimization reduces fuel vs random ordering",
            algorithm="nearest_neighbor",
        )

        route: list[PickupStop] = []
        remaining = list(stops_data)
        cur_lat, cur_lon = DEPOT_LAT, DEPOT_LON
        cumulative = 0.0
        seq = 1

        while remaining:
            nearest_idx = min(
                range(len(remaining)),
                key=lambda i: haversine_km(cur_lat, cur_lon, remaining[i][3], remaining[i][4]),
            )
            stop_type, name, addr, lat, lon, notes = remaining.pop(nearest_idx)
            leg = haversine_km(cur_lat, cur_lon, lat, lon)
            cumulative += leg
            cur_lat, cur_lon = lat, lon

            route.append(
                PickupStop(
                    stop_type=stop_type,
                    name=name,
                    address=addr,
                    latitude=lat,
                    longitude=lon,
                    sequence=seq,
                    notes=notes,
                    cumulative_km=round(cumulative, 1),
                )
            )
            seq += 1

        return_km = haversine_km(cur_lat, cur_lon, DEPOT_LAT, DEPOT_LON)
        cumulative += return_km
        random_est = cumulative * 1.35

        log.add(
            "Environmental tradeoff disclosure",
            f"{cumulative:.1f} km optimized vs ~{random_est:.1f} km random",
            "Shorter routes reduce emissions; fairness may require minor detours",
            optimized_km=round(cumulative, 1),
            random_est_km=round(random_est, 1),
        )

        est_minutes = int(cumulative * 3 + len(route) * 5)
        context["route"] = route
        context["route_stats"] = {
            "total_km": round(cumulative, 1),
            "est_minutes": est_minutes,
            "random_route_km": round(random_est, 1),
        }

        return AgentResult(
            agent_name=self.name,
            summary=f"Planned {len(route)} stops, {cumulative:.1f} km, est. {est_minutes} min.",
            dataset=self.dataset,
            data={
                "stops": [s.name for s in route],
                "total_km": round(cumulative, 1),
                "est_minutes": est_minutes,
            },
            decision_steps=log.steps,
        )
