"""Ethics Agent — safety, liability, and eligibility screening."""

from __future__ import annotations

from food_bridge.models import AgentDecision, AgentName, DecisionStep, DonorCandidate, Establishment


APPROVED_STATUSES = {"Pass"}
BLOCKED_STATUSES = {"Conditional Pass", "Closed"}
MAX_CRUCIAL_INFRACTIONS = 0


def run_ethics_agent(
    establishments: list[Establishment],
    max_donors: int = 100,
) -> tuple[list[DonorCandidate], AgentDecision]:
    steps: list[DecisionStep] = []
    candidates: list[DonorCandidate] = []
    approved = 0
    rejected = 0

    steps.append(
        DecisionStep(
            step=1,
            rule="Latest inspection must be 'Pass' (Dinesafe inspectionStatus)",
            input_summary=f"{len(establishments)} establishments with Toronto coordinates",
            outcome="Only donors with verified pass status are eligible for redistribution",
            metadata={"approved_statuses": list(APPROVED_STATUSES), "source": "Dinesafe.csv"},
        )
    )

    steps.append(
        DecisionStep(
            step=2,
            rule="Exclude establishments with any crucial (C) infraction on record",
            input_summary="severity field = 'C - Crucial' aggregated per establishment",
            outcome="Reduces liability from temperature control / contamination issues",
            metadata={"max_crucial_allowed": MAX_CRUCIAL_INFRACTIONS},
        )
    )

    steps.append(
        DecisionStep(
            step=3,
            rule="Reject Conditional Pass and Closed premises",
            input_summary="Latest inspectionStatus per estId",
            outcome="Conditional Pass indicates significant unresolved infractions",
            metadata={"blocked_statuses": list(BLOCKED_STATUSES)},
        )
    )

    for est in establishments:
        reasons: list[str] = []
        approved_flag = True

        if est.latest_inspection_status not in APPROVED_STATUSES:
            approved_flag = False
            reasons.append(
                f"Latest status '{est.latest_inspection_status}' on {est.latest_inspection_date}"
            )

        if est.latest_inspection_status in BLOCKED_STATUSES:
            approved_flag = False
            if f"Latest status '{est.latest_inspection_status}'" not in " ".join(reasons):
                reasons.append(f"Blocked status: {est.latest_inspection_status}")

        if est.crucial_infractions_recent > MAX_CRUCIAL_INFRACTIONS:
            approved_flag = False
            reasons.append(
                f"{est.crucial_infractions_recent} crucial infraction(s) on record"
            )

        if approved_flag:
            approved += 1
            ethics_reason = (
                f"Approved: Pass on {est.latest_inspection_date}, "
                f"no crucial infractions ({est.minor_infractions_recent} minor noted)"
            )
        else:
            rejected += 1
            ethics_reason = "Rejected: " + "; ".join(reasons)

        candidate = DonorCandidate(
            **est.model_dump(),
            ethics_approved=approved_flag,
            ethics_reason=ethics_reason,
        )
        if approved_flag:
            candidates.append(candidate)

    candidates.sort(key=lambda d: (-d.minor_infractions_recent, d.name))
    candidates = candidates[:max_donors]

    steps.append(
        DecisionStep(
            step=4,
            rule=f"Cap eligible donors at {max_donors} for PoC pipeline",
            input_summary=f"{approved} passed ethics screening",
            outcome=f"Selected top {len(candidates)} donors for surplus analysis",
            metadata={"approved": approved, "rejected": rejected, "selected": len(candidates)},
        )
    )

    decision = AgentDecision(
        agent=AgentName.ETHICS,
        summary=(
            f"Screened {len(establishments)} establishments: "
            f"{approved} approved, {rejected} rejected. "
            f"Using {len(candidates)} donors for redistribution."
        ),
        approved_count=approved,
        rejected_count=rejected,
        steps=steps,
    )
    return candidates, decision
