"""Surplus Agent — predict edible surplus from regional waste and donor signals."""

from __future__ import annotations

import hashlib

from food_bridge.data_loader import BiomassGrid
from food_bridge.geo import nearest_grid_id
from food_bridge.models import AgentDecision, AgentName, DecisionStep, DonorCandidate


def _donor_size_factor(est_id: str) -> float:
    """Deterministic 0.6–1.4 multiplier from establishment id (PoC proxy for kitchen size)."""
    h = int(hashlib.md5(est_id.encode()).hexdigest()[:8], 16)
    return 0.6 + (h % 80) / 100.0


def run_surplus_agent(
    donors: list[DonorCandidate],
    biomass_grids: list[BiomassGrid],
    grid_coords: dict[int, tuple[float, float]],
) -> tuple[list[DonorCandidate], AgentDecision]:
    steps: list[DecisionStep] = []
    organic_by_grid = {g.grid_id: g.organic_volume for g in biomass_grids}
    grid_median = sorted(organic_by_grid.values())[len(organic_by_grid) // 2]

    steps.append(
        DecisionStep(
            step=1,
            rule="Map each donor to nearest Biomass grid cell",
            input_summary=f"{len(biomass_grids)} municipal waste grids (BIOMASS_MSW_INV.csv)",
            outcome="Links Dinesafe donors to regional organic waste context",
            metadata={"median_organic_volume_m3": round(grid_median, 2)},
        )
    )

    steps.append(
        DecisionStep(
            step=2,
            rule="surplus_kg = regional_organic × size_factor × 0.015",
            input_summary="Organic volume (m³) scaled to estimated daily surplus kg",
            outcome="Higher-waste regions and larger-establishment proxies yield more surplus",
            metadata={"size_factor_range": "0.6–1.4", "conversion_factor": 0.015},
        )
    )

    steps.append(
        DecisionStep(
            step=3,
            rule="Confidence increases when inspection history is clean",
            input_summary="Fewer minor infractions → higher confidence in safe surplus handling",
            outcome="confidence = 0.5 + 0.05×(20 - minor_infractions), capped at 0.95",
            metadata={},
        )
    )

    enriched: list[DonorCandidate] = []
    for donor in donors:
        grid_id = nearest_grid_id(donor.latitude, donor.longitude, grid_coords)
        regional_organic = organic_by_grid.get(grid_id, grid_median)
        size_factor = _donor_size_factor(donor.est_id)
        surplus_kg = round(regional_organic * size_factor * 0.015, 1)
        confidence = min(0.95, 0.5 + 0.05 * (20 - donor.minor_infractions_recent))

        enriched.append(
            donor.model_copy(
                update={
                    "predicted_surplus_kg": surplus_kg,
                    "surplus_confidence": round(confidence, 2),
                    "regional_organic_waste": round(regional_organic, 2),
                }
            )
        )

    enriched.sort(key=lambda d: -d.predicted_surplus_kg)
    total_surplus = sum(d.predicted_surplus_kg for d in enriched)

    steps.append(
        DecisionStep(
            step=4,
            rule="Rank donors by predicted surplus (descending)",
            input_summary=f"{len(enriched)} ethics-approved donors",
            outcome=f"Total predicted surplus: {total_surplus:.1f} kg across selected donors",
            metadata={"total_surplus_kg": round(total_surplus, 1)},
        )
    )

    decision = AgentDecision(
        agent=AgentName.SURPLUS,
        summary=(
            f"Predicted {total_surplus:.1f} kg surplus from {len(enriched)} donors "
            f"using Biomass organic waste volumes and establishment proxies."
        ),
        steps=steps,
    )
    return enriched, decision
