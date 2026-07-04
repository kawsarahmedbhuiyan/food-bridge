from dataclasses import dataclass, field
from typing import Any


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


@dataclass
class NeedZone:
    region: str
    priority_score: float
    event_count: int
    top_signals: list[str] = field(default_factory=list)


@dataclass
class Recipient:
    name: str
    region: str
    latitude: float
    longitude: float
    capacity_meals: int


@dataclass
class Match:
    donor: Donor
    recipient: Recipient
    match_score: float
    distance_km: float
    reasons: list[str] = field(default_factory=list)
    ethics_flags: list[str] = field(default_factory=list)
    approved: bool = False


@dataclass
class PickupStop:
    stop_type: str
    name: str
    address: str
    latitude: float
    longitude: float
    sequence: int
    notes: str = ""


@dataclass
class EthicsReport:
    fairness_score: float
    safety_issues: list[str]
    transparency_log: list[str]
    recommendations: list[str]
    human_approval_required: bool = True


@dataclass
class AgentResult:
    agent_name: str
    summary: str
    dataset: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RedistributionPlan:
    priority_zone: NeedZone | None
    matches: list[Match]
    route: list[PickupStop]
    ethics_report: EthicsReport
    agent_logs: list[AgentResult]
