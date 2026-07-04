"""Need Agent — identify priority recipient zones from waste and fairness signals."""

from __future__ import annotations

from food_bridge.data_loader import BiomassGrid
from food_bridge.models import AgentDecision, AgentName, DecisionStep, DonorCandidate, RecipientZone


def run_need_agent(
    biomass_grids: list[BiomassGrid],
    donors: list[DonorCandidate],
    max_recipients: int = 25,
    small_org_quota: float = 0.3,
) -> tuple[list[RecipientZone], AgentDecision]:
    steps: list[DecisionStep] = []

    organic_volumes = [g.organic_volume for g in biomass_grids]
    min_org, max_org = min(organic_volumes), max(organic_volumes)
    span = max_org - min_org or 1.0

    steps.append(
        DecisionStep(
            step=1,
            rule="Need score = normalized organic waste volume in grid cell",
            input_summary=f"{len(biomass_grids)} Biomass grid cells",
            outcome="Higher organic municipal waste proxies communities with greater redistribution need",
            metadata={"min_organic_m3": round(min_org, 2), "max_organic_m3": round(max_org, 2)},
        )
    )

    steps.append(
        DecisionStep(
            step=2,
            rule="Mark ~30% of zones as small organizations (fairness quota)",
            input_summary=f"small_org_quota = {small_org_quota}",
            outcome="Prevents large hubs from monopolizing allocations in matching phase",
            metadata={"fairness_rationale": "Small shelters often lack logistics capacity"},
        )
    )

    zones: list[RecipientZone] = []
    sorted_grids = sorted(biomass_grids, key=lambda g: -g.organic_volume)

    for i, grid in enumerate(sorted_grids[:max_recipients]):
        need_score = (grid.organic_volume - min_org) / span
        population_proxy = int(grid.organic_volume * 2.5)
        is_small = i >= int(max_recipients * (1 - small_org_quota))

        zones.append(
            RecipientZone(
                grid_id=grid.grid_id,
                name=f"Community Hub Grid {grid.grid_id}",
                latitude=grid.latitude,
                longitude=grid.longitude,
                organic_waste_volume=round(grid.organic_volume, 2),
                need_score=round(need_score, 3),
                need_rank=i + 1,
                population_proxy=population_proxy,
                is_small_org=is_small,
            )
        )

    for rank, zone in enumerate(sorted(zones, key=lambda z: -z.need_score), start=1):
        zone.need_rank = rank

    steps.append(
        DecisionStep(
            step=3,
            rule="Rank zones by need_score descending",
            input_summary=f"Top {len(zones)} high-need recipient zones selected",
            outcome=f"{sum(1 for z in zones if z.is_small_org)} small-org slots reserved",
            metadata={
                "small_org_count": sum(1 for z in zones if z.is_small_org),
                "top_need_score": zones[0].need_score if zones else 0,
            },
        )
    )

    decision = AgentDecision(
        agent=AgentName.NEED,
        summary=(
            f"Identified {len(zones)} priority recipient zones; "
            f"{sum(1 for z in zones if z.is_small_org)} flagged as small organizations "
            f"for equitable allocation."
        ),
        steps=steps,
    )
    return zones, decision
