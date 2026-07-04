from src.agents.base import BaseAgent, haversine_km
from src.models import AgentResult, PickupStop


class LogisticsPlannerAgent(BaseAgent):
    name = "Logistics Planner"
    dataset = "Toronto Dinesafe (#1) coordinates"

    def run(self, context: dict) -> AgentResult:
        matches = [m for m in context.get("matches", []) if m.approved]
        if not matches:
            matches = context.get("matches", [])[:1]

        route: list[PickupStop] = []
        sequence = 1
        for match in matches[:3]:
            route.append(
                PickupStop(
                    stop_type="pickup",
                    name=match.donor.name,
                    address=match.donor.address,
                    latitude=match.donor.latitude,
                    longitude=match.donor.longitude,
                    sequence=sequence,
                    notes=f"Collect surplus → deliver to {match.recipient.name}",
                )
            )
            sequence += 1
            route.append(
                PickupStop(
                    stop_type="dropoff",
                    name=match.recipient.name,
                    address=match.recipient.region,
                    latitude=match.recipient.latitude,
                    longitude=match.recipient.longitude,
                    sequence=sequence,
                    notes="Verify temperature & receipt log",
                )
            )
            sequence += 1

        total_km = 0.0
        for i in range(len(route) - 1):
            total_km += haversine_km(
                route[i].latitude,
                route[i].longitude,
                route[i + 1].latitude,
                route[i + 1].longitude,
            )

        est_minutes = int(total_km * 3 + len(route) * 5)
        context["route"] = route
        context["route_stats"] = {"total_km": round(total_km, 1), "est_minutes": est_minutes}

        return AgentResult(
            agent_name=self.name,
            summary=f"Planned {len(route)} stops, ~{total_km:.1f} km, est. {est_minutes} min.",
            dataset=self.dataset,
            data={"stops": [s.name for s in route], "total_km": round(total_km, 1), "est_minutes": est_minutes},
        )
