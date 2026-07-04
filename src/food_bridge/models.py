"""Shared data models for the Food Bridge multi-agent system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentName(str, Enum):
    ETHICS = "ethics"
    SURPLUS = "surplus"
    NEED = "need"
    MATCHING = "matching"
    LOGISTICS = "logistics"
    COORDINATOR = "coordinator"


class DecisionStep(BaseModel):
    """A single transparent reasoning step emitted by an agent."""

    step: int
    rule: str
    input_summary: str
    outcome: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentDecision(BaseModel):
    """Full decision record from one agent run."""

    agent: AgentName
    summary: str
    approved_count: Optional[int] = None
    rejected_count: Optional[int] = None
    steps: list[DecisionStep]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Establishment(BaseModel):
    est_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    latest_inspection_date: str
    latest_inspection_status: str
    crucial_infractions_recent: int = 0
    minor_infractions_recent: int = 0


class DonorCandidate(Establishment):
    ethics_approved: bool = False
    ethics_reason: str = ""
    predicted_surplus_kg: float = 0.0
    surplus_confidence: float = 0.0
    regional_organic_waste: float = 0.0


class RecipientZone(BaseModel):
    grid_id: int
    name: str
    latitude: float
    longitude: float
    organic_waste_volume: float
    need_score: float
    need_rank: int = 0
    population_proxy: int = 0
    is_small_org: bool = False


class Allocation(BaseModel):
    donor: DonorCandidate
    recipient: RecipientZone
    allocated_kg: float
    distance_km: float
    priority_score: float
    fairness_tier: str
    matching_reason: str


class RouteStop(BaseModel):
    sequence: int
    stop_type: str
    name: str
    latitude: float
    longitude: float
    allocated_kg: float = 0.0
    cumulative_km: float = 0.0


class PipelineResult(BaseModel):
    ethics_decision: AgentDecision
    surplus_decision: AgentDecision
    need_decision: AgentDecision
    matching_decision: AgentDecision
    logistics_decision: AgentDecision
    coordinator_summary: AgentDecision
    approved_donors: list[DonorCandidate]
    recipient_zones: list[RecipientZone]
    allocations: list[Allocation]
    route: list[RouteStop]
    stats: dict[str, Any]
