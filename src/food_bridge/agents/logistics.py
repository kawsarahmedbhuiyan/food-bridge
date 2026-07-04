"""Logistics Agent — optimize pickup/delivery route with transparent heuristics."""

from __future__ import annotations

from food_bridge.geo import haversine_km
from food_bridge.models import AgentDecision, AgentName, Allocation, DecisionStep, RouteStop


def run_logistics_agent(
    allocations: list[Allocation],
    depot_lat: float = 43.6532,
    depot_lon: float = -79.3832,
) -> tuple[list[RouteStop], AgentDecision]:
    steps: list[DecisionStep] = []

    if not allocations:
        return [], AgentDecision(
            agent=AgentName.LOGISTICS,
            summary="No allocations to route.",
            steps=[
                DecisionStep(
                    step=1,
                    rule="N/A",
                    input_summary="Empty allocation set",
                    outcome="No route generated",
                )
            ],
        )

    steps.append(
        DecisionStep(
            step=1,
            rule="Depot at Toronto distribution centre (43.6532, -79.3832)",
            input_summary="Central hub for volunteer pickup fleet",
            outcome="All routes start and end at depot",
            metadata={"depot_lat": depot_lat, "depot_lon": depot_lon},
        )
    )

    stops: list[tuple[str, str, float, float, float, Allocation]] = []
    for alloc in allocations:
        stops.append(("pickup", alloc.donor.name, alloc.donor.latitude, alloc.donor.longitude, alloc.allocated_kg, alloc))
        stops.append(("delivery", alloc.recipient.name, alloc.recipient.latitude, alloc.recipient.longitude, alloc.allocated_kg, alloc))

    steps.append(
        DecisionStep(
            step=2,
            rule="Nearest-neighbor heuristic from depot",
            input_summary=f"{len(stops)} stops ({len(allocations)} pickup + delivery pairs)",
            outcome="Greedy TSP approximation — O(n²), suitable for PoC fleet planning",
            metadata={"algorithm": "nearest_neighbor"},
        )
    )

    route: list[RouteStop] = []
    remaining = list(stops)
    cur_lat, cur_lon = depot_lat, depot_lon
    cumulative = 0.0
    seq = 0

    route.append(
        RouteStop(
            sequence=seq,
            stop_type="depot",
            name="Food Bridge Depot",
            latitude=depot_lat,
            longitude=depot_lon,
            cumulative_km=0.0,
        )
    )
    seq += 1

    while remaining:
        nearest_idx = min(
            range(len(remaining)),
            key=lambda i: haversine_km(cur_lat, cur_lon, remaining[i][2], remaining[i][3]),
        )
        stop_type, name, lat, lon, kg, _ = remaining.pop(nearest_idx)
        leg = haversine_km(cur_lat, cur_lon, lat, lon)
        cumulative += leg
        cur_lat, cur_lon = lat, lon

        route.append(
            RouteStop(
                sequence=seq,
                stop_type=stop_type,
                name=name,
                latitude=lat,
                longitude=lon,
                allocated_kg=kg,
                cumulative_km=round(cumulative, 2),
            )
        )
        seq += 1

    return_km = haversine_km(cur_lat, cur_lon, depot_lat, depot_lon)
    cumulative += return_km
    route.append(
        RouteStop(
            sequence=seq,
            stop_type="depot",
            name="Food Bridge Depot (return)",
            latitude=depot_lat,
            longitude=depot_lon,
            cumulative_km=round(cumulative, 2),
        )
    )

    steps.append(
        DecisionStep(
            step=3,
            rule="Return to depot after all stops",
            input_summary=f"{len(route) - 1} legs planned",
            outcome=f"Total route distance: {cumulative:.1f} km (includes {return_km:.1f} km return)",
            metadata={"total_km": round(cumulative, 2), "stop_count": len(route)},
        )
    )

    env_note = (
        "Shorter routes reduce fuel emissions; "
        f"{cumulative:.1f} km for {len(allocations)} deliveries vs. "
        f"~{cumulative * 1.35:.1f} km estimated for random ordering"
    )
    steps.append(
        DecisionStep(
            step=4,
            rule="Environmental tradeoff disclosure",
            input_summary="Route optimization vs. fairness detours",
            outcome=env_note,
            metadata={"estimated_random_route_km": round(cumulative * 1.35, 1)},
        )
    )

    decision = AgentDecision(
        agent=AgentName.LOGISTICS,
        summary=f"Planned route with {len(route)} stops, {cumulative:.1f} km total.",
        steps=steps,
    )
    return route, decision
