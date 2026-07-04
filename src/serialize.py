from dataclasses import asdict
from typing import Any

from src.models import (
    AgentResult,
    DecisionStep,
    Donor,
    EthicsReport,
    Match,
    NeedZone,
    PickupStop,
    Recipient,
    RedistributionPlan,
)


def _step(s: DecisionStep) -> dict[str, Any]:
    return asdict(s)


def _donor(d: Donor) -> dict[str, Any]:
    return asdict(d)


def _recipient(r: Recipient) -> dict[str, Any]:
    return asdict(r)


def _need_zone(z: NeedZone) -> dict[str, Any]:
    return asdict(z)


def _match(m: Match) -> dict[str, Any]:
    return {
        "donor": _donor(m.donor),
        "recipient": _recipient(m.recipient),
        "match_score": m.match_score,
        "distance_km": m.distance_km,
        "reasons": m.reasons,
        "ethics_flags": m.ethics_flags,
        "approved": m.approved,
        "fairness_tier": m.fairness_tier,
        "allocated_kg": m.allocated_kg,
    }


def _stop(s: PickupStop) -> dict[str, Any]:
    return asdict(s)


def _ethics(e: EthicsReport) -> dict[str, Any]:
    return asdict(e)


def _agent_log(log: AgentResult) -> dict[str, Any]:
    return {
        "agent_name": log.agent_name,
        "summary": log.summary,
        "dataset": log.dataset,
        "data": log.data,
        "approved_count": log.approved_count,
        "rejected_count": log.rejected_count,
        "decision_steps": [_step(s) for s in log.decision_steps],
    }


def plan_to_dict(plan: RedistributionPlan) -> dict[str, Any]:
    route_stats = {}
    pickup_schedule = []
    for log in plan.agent_logs:
        if log.agent_name == "Logistics Planner":
            route_stats = {
                "total_km": log.data.get("total_km"),
                "est_minutes": log.data.get("est_minutes"),
            }
        if log.agent_name == "Timing Negotiator":
            pickup_schedule = log.data.get("windows", [])

    return {
        "priority_zone": _need_zone(plan.priority_zone) if plan.priority_zone else None,
        "matches": [_match(m) for m in plan.matches],
        "route": [_stop(s) for s in plan.route],
        "route_stats": route_stats,
        "pickup_schedule": pickup_schedule,
        "ethics_report": _ethics(plan.ethics_report),
        "agent_logs": [_agent_log(log) for log in plan.agent_logs],
    }
