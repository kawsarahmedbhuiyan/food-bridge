from dataclasses import asdict
from typing import Any

from src.models import (
    AgentResult,
    Donor,
    EthicsReport,
    Match,
    NeedZone,
    PickupStop,
    Recipient,
    RedistributionPlan,
)


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
    }


def _stop(s: PickupStop) -> dict[str, Any]:
    return asdict(s)


def _ethics(e: EthicsReport) -> dict[str, Any]:
    return asdict(e)


def _agent_log(log: AgentResult) -> dict[str, Any]:
    return asdict(log)


def plan_to_dict(plan: RedistributionPlan) -> dict[str, Any]:
    route_stats = {}
    for log in plan.agent_logs:
        if log.agent_name == "Logistics Planner":
            route_stats = {
                "total_km": log.data.get("total_km"),
                "est_minutes": log.data.get("est_minutes"),
            }
            break

    return {
        "priority_zone": _need_zone(plan.priority_zone) if plan.priority_zone else None,
        "matches": [_match(m) for m in plan.matches],
        "route": [_stop(s) for s in plan.route],
        "route_stats": route_stats,
        "ethics_report": _ethics(plan.ethics_report),
        "agent_logs": [_agent_log(log) for log in plan.agent_logs],
    }
