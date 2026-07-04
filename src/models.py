from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DecisionStep:
    step: int
    rule: str
    input_summary: str
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Donor:
    establishment_id: str
    name: str
    address: str
    establishment_type: str
    inspection_result: str
    latitude: float
    longitude: float
    region: str = ""
    surplus_score: float = 0.0
    predicted_surplus_kg: float = 0.0
    crucial_infractions: int = 0
    minor_infractions: int = 0
    inspection_date: str = ""


@dataclass
class NeedZone:
    region: str
    priority_score: float
    event_count: int
    top_signals: list[str] = field(default_factory=list)
    biomass_need_score: float = 0.0
    is_small_org_hub: bool = False


@dataclass
class Recipient:
    name: str
    region: str
    latitude: float
    longitude: float
    capacity_meals: int
    is_small_org: bool = False


@dataclass
class Match:
    donor: Donor
    recipient: Recipient
    match_score: float
    distance_km: float
    reasons: list[str] = field(default_factory=list)
    ethics_flags: list[str] = field(default_factory=list)
    approved: bool = False
    fairness_tier: str = "standard"
    allocated_kg: float = 0.0


@dataclass
class PickupStop:
    stop_type: str
    name: str
    address: str
    latitude: float
    longitude: float
    sequence: int
    notes: str = ""
    cumulative_km: float = 0.0
    window_start: str = ""
    window_end: str = ""


@dataclass
class EthicsReport:
    fairness_score: float
    safety_issues: list[str]
    transparency_log: list[str]
    recommendations: list[str]
    human_approval_required: bool = True
    small_org_allocations: int = 0
    environmental_note: str = ""


@dataclass
class AgentResult:
    agent_name: str
    summary: str
    dataset: str
    data: dict[str, Any] = field(default_factory=dict)
    decision_steps: list[DecisionStep] = field(default_factory=list)
    approved_count: Optional[int] = None
    rejected_count: Optional[int] = None


@dataclass
class RedistributionPlan:
    priority_zone: NeedZone | None
    matches: list[Match]
    route: list[PickupStop]
    ethics_report: EthicsReport
    agent_logs: list[AgentResult]
