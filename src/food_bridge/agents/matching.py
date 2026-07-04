"""Matching Agent — pair donors with high-need recipients fairly."""

from __future__ import annotations

from typing import Optional, Tuple

from food_bridge.geo import haversine_km
from food_bridge.models import (
    AgentDecision,
    AgentName,
    Allocation,
    DecisionStep,
    DonorCandidate,
    RecipientZone,
)


def _fairness_tier(recipient: RecipientZone) -> str:
    if recipient.is_small_org:
        return "small-org-priority"
    if recipient.need_rank <= 5:
        return "critical-need"
    return "standard"


def run_matching_agent(
    donors: list[DonorCandidate],
    recipients: list[RecipientZone],
    max_allocations: int = 20,
    max_distance_km: float = 15.0,
) -> tuple[list[Allocation], AgentDecision]:
    steps: list[DecisionStep] = []
    allocations: list[Allocation] = []
    donor_remaining = {d.est_id: d.predicted_surplus_kg for d in donors}
    donor_map = {d.est_id: d for d in donors}

    steps.append(
        DecisionStep(
            step=1,
            rule="Sort recipients: small orgs first, then by need_rank",
            input_summary=f"{len(recipients)} recipient zones, {len(donors)} donors",
            outcome="Fairness: small organizations receive priority in the matching queue",
            metadata={"max_distance_km": max_distance_km},
        )
    )

    steps.append(
        DecisionStep(
            step=2,
            rule="priority_score = need_score × 100 / (1 + distance_km)",
            input_summary="Closer high-need zones score higher",
            outcome="Balances geographic proximity with food insecurity priority",
            metadata={},
        )
    )

    queue = sorted(
        recipients,
        key=lambda r: (not r.is_small_org, r.need_rank),
    )

    step_num = 3
    for recipient in queue:
        if len(allocations) >= max_allocations:
            break

        best: Optional[Tuple[float, DonorCandidate, float]] = None
        for donor in donors:
            if donor_remaining[donor.est_id] <= 0:
                continue
            dist = haversine_km(
                donor.latitude, donor.longitude,
                recipient.latitude, recipient.longitude,
            )
            if dist > max_distance_km:
                continue
            priority = recipient.need_score * 100 / (1 + dist)
            if best is None or priority > best[0]:
                best = (priority, donor, dist)

        if best is None:
            steps.append(
                DecisionStep(
                    step=step_num,
                    rule="No donor within max_distance_km",
                    input_summary=f"Recipient {recipient.name} (need rank {recipient.need_rank})",
                    outcome="Skipped — no eligible donor in range (transparency: not hidden)",
                    metadata={"recipient_grid": recipient.grid_id},
                )
            )
            step_num += 1
            continue

        priority, donor, dist = best
        allocated = min(donor_remaining[donor.est_id], 25.0)
        donor_remaining[donor.est_id] -= allocated
        tier = _fairness_tier(recipient)

        reason = (
            f"Matched {donor.name} → {recipient.name}: "
            f"{allocated:.1f} kg, {dist:.1f} km, tier={tier}, priority={priority:.2f}"
        )

        allocations.append(
            Allocation(
                donor=donor,
                recipient=recipient,
                allocated_kg=round(allocated, 1),
                distance_km=round(dist, 2),
                priority_score=round(priority, 3),
                fairness_tier=tier,
                matching_reason=reason,
            )
        )

        steps.append(
            DecisionStep(
                step=step_num,
                rule="Greedy best priority_score within distance constraint",
                input_summary=f"Recipient need_rank={recipient.need_rank}, is_small={recipient.is_small_org}",
                outcome=reason,
                metadata={
                    "donor_id": donor.est_id,
                    "allocated_kg": allocated,
                    "distance_km": round(dist, 2),
                    "fairness_tier": tier,
                },
            )
        )
        step_num += 1

    total_kg = sum(a.allocated_kg for a in allocations)
    small_org_allocs = sum(1 for a in allocations if a.recipient.is_small_org)

    decision = AgentDecision(
        agent=AgentName.MATCHING,
        summary=(
            f"Created {len(allocations)} allocations totalling {total_kg:.1f} kg; "
            f"{small_org_allocs} to small-organization zones."
        ),
        steps=steps,
    )
    return allocations, decision
