from __future__ import annotations

from src.agents import (
    DonorScoutAgent,
    EthicsGuardianAgent,
    LogisticsPlannerAgent,
    MatcherAgent,
    NeedPrioritizerAgent,
    SurplusEstimatorAgent,
    TimingNegotiatorAgent,
)
from src.data_loader import (
    load_biomass,
    load_donors,
    load_need_events,
    load_recipients,
    load_supply_chain_signals,
)
from src.models import RedistributionPlan


class FoodBridgeOrchestrator:
    def __init__(self):
        self.agents = [
            SurplusEstimatorAgent(),
            NeedPrioritizerAgent(),
            DonorScoutAgent(),
            MatcherAgent(),
            LogisticsPlannerAgent(),
            TimingNegotiatorAgent(),
            EthicsGuardianAgent(),
        ]

    def run(
        self,
        focus_region: str | None = None,
        top_matches: int = 5,
        donor_pool_limit: int | None = None,
        max_distance_km: float = 15.0,
    ) -> RedistributionPlan:
        context = {
            "donors": load_donors(limit=donor_pool_limit),
            "biomass_df": load_biomass(),
            "need_events_df": load_need_events(),
            "supply_chain_df": load_supply_chain_signals(),
            "recipients": load_recipients(),
            "focus_region": focus_region,
            "top_matches": top_matches,
            "max_donors": 800,
            "max_distance_km": max_distance_km,
            "chain_pickup_counts": {"_default_chain": 2},
        }

        agent_logs = []
        for agent in self.agents:
            agent_logs.append(agent.run(context))

        return RedistributionPlan(
            priority_zone=context.get("priority_zone"),
            matches=context.get("matches", []),
            route=context.get("route", []),
            ethics_report=context["ethics_report"],
            agent_logs=agent_logs,
        )
