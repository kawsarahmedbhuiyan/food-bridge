"""Coordinator — orchestrates the multi-agent redistribution pipeline."""

from __future__ import annotations

from typing import Optional

from food_bridge.agents.ethics import run_ethics_agent
from food_bridge.agents.logistics import run_logistics_agent
from food_bridge.agents.matching import run_matching_agent
from food_bridge.agents.need import run_need_agent
from food_bridge.agents.surplus import run_surplus_agent
from food_bridge.data_loader import LoadedData, load_all_data
from food_bridge.models import AgentDecision, AgentName, DecisionStep, PipelineResult


class FoodBridgeOrchestrator:
    def __init__(self, data: Optional[LoadedData] = None):
        self.data = data or load_all_data()
        self._cached_result: Optional[PipelineResult] = None

    def run(
        self,
        max_donors: int = 80,
        max_recipients: int = 20,
        max_allocations: int = 15,
        max_distance_km: float = 12.0,
        force_refresh: bool = False,
    ) -> PipelineResult:
        if self._cached_result and not force_refresh:
            return self._cached_result

        donors, ethics_decision = run_ethics_agent(
            self.data.establishments, max_donors=max_donors
        )
        donors, surplus_decision = run_surplus_agent(
            donors, self.data.biomass_grids, self.data.grid_coords
        )
        recipients, need_decision = run_need_agent(
            self.data.biomass_grids, donors, max_recipients=max_recipients
        )
        allocations, matching_decision = run_matching_agent(
            donors,
            recipients,
            max_allocations=max_allocations,
            max_distance_km=max_distance_km,
        )
        route, logistics_decision = run_logistics_agent(allocations)

        total_kg = sum(a.allocated_kg for a in allocations)
        route_km = route[-1].cumulative_km if route else 0

        coordinator = AgentDecision(
            agent=AgentName.COORDINATOR,
            summary=(
                f"Pipeline complete: {len(donors)} eligible donors, "
                f"{len(recipients)} need zones, {len(allocations)} matches, "
                f"{total_kg:.1f} kg allocated, {route_km:.1f} km route."
            ),
            steps=[
                DecisionStep(
                    step=1,
                    rule="Sequential agent pipeline",
                    input_summary="Ethics → Surplus → Need → Matching → Logistics",
                    outcome="Each agent emits auditable decision steps",
                    metadata={"agents": ["ethics", "surplus", "need", "matching", "logistics"]},
                ),
                DecisionStep(
                    step=2,
                    rule="Human oversight hook",
                    input_summary="All decisions exposed via /api/pipeline and dashboard",
                    outcome="Operators can review rules before dispatching pickups",
                    metadata={"transparency": "full step-level audit trail"},
                ),
                DecisionStep(
                    step=3,
                    rule="Ethical safeguards summary",
                    input_summary="Pass-only donors, crucial infraction exclusion, small-org priority",
                    outcome=(
                        f"Safety: {ethics_decision.approved_count} approved / "
                        f"{ethics_decision.rejected_count} rejected. "
                        f"Fairness: {sum(1 for a in allocations if a.recipient.is_small_org)} "
                        f"small-org allocations."
                    ),
                    metadata={
                        "total_allocated_kg": round(total_kg, 1),
                        "route_km": route_km,
                    },
                ),
            ],
        )

        result = PipelineResult(
            ethics_decision=ethics_decision,
            surplus_decision=surplus_decision,
            need_decision=need_decision,
            matching_decision=matching_decision,
            logistics_decision=logistics_decision,
            coordinator_summary=coordinator,
            approved_donors=donors[:20],
            recipient_zones=recipients,
            allocations=allocations,
            route=route,
            stats={
                "establishments_loaded": len(self.data.establishments),
                "biomass_grids": len(self.data.biomass_grids),
                "eligible_donors": len(donors),
                "recipient_zones": len(recipients),
                "allocations": len(allocations),
                "total_kg": round(total_kg, 1),
                "route_km": route_km,
                "small_org_allocations": sum(
                    1 for a in allocations if a.recipient.is_small_org
                ),
            },
        )
        self._cached_result = result
        return result
