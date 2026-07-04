from src.agents.base import BaseAgent
from src.agents.decisions import DecisionLog
from src.data_loader import PASS_STATUS
from src.models import AgentResult


class DonorScoutAgent(BaseAgent):
    """Ethics-aware donor screening using Dinesafe inspection records."""

    name = "Ethics & Donor Scout"
    dataset = "Toronto Dinesafe (#1)"

    BLOCKED_STATUSES = {"Conditional Pass", "Closed"}

    def run(self, context: dict) -> AgentResult:
        log = DecisionLog()
        donors = context["donors"]
        focus_region = context.get("focus_region")
        max_donors = context.get("max_donors", 500)

        log.add(
            "Latest inspection must be 'Pass' (inspectionStatus)",
            f"{len(donors)} establishments loaded from Dinesafe.csv",
            "Only Pass status eligible — Conditional Pass and Closed rejected",
            approved_status=PASS_STATUS,
        )

        log.add(
            "Exclude any establishment with crucial (C) infraction on record",
            "severity = 'C - Crucial' aggregated per estId",
            "Reduces liability from temperature control / contamination issues",
            max_crucial=0,
        )

        eligible = []
        rejected = 0
        for donor in donors:
            reasons = []
            ok = True
            if donor.inspection_result != PASS_STATUS:
                ok = False
                reasons.append(f"status={donor.inspection_result}")
            if donor.inspection_result in self.BLOCKED_STATUSES:
                ok = False
            if donor.crucial_infractions > 0:
                ok = False
                reasons.append(f"{donor.crucial_infractions} crucial infraction(s)")

            if ok:
                eligible.append(donor)
            else:
                rejected += 1

        log.add(
            "Ethics screening complete",
            f"{len(donors)} screened",
            f"{len(eligible)} approved, {rejected} rejected",
            approved=len(eligible),
            rejected=rejected,
        )

        if focus_region:
            regional = [d for d in eligible if d.region == focus_region]
            if regional:
                eligible = regional
                log.add(
                    "Filter to focus region",
                    f"region={focus_region}",
                    f"{len(eligible)} Pass-only donors in region",
                )

        eligible.sort(key=lambda d: d.surplus_score, reverse=True)
        eligible = eligible[:max_donors]
        context["eligible_donors"] = eligible

        log.add(
            f"Select top {max_donors} donors by surplus score",
            f"{len(eligible)} in final pool",
            f"Top: {', '.join(d.name for d in eligible[:3])}" if eligible else "No eligible donors",
        )

        return AgentResult(
            agent_name=self.name,
            summary=(
                f"Ethics-approved {len(eligible)} donors ({rejected} rejected). "
                f"Pass-only, zero crucial infractions."
            ),
            dataset=self.dataset,
            data={
                "eligible_count": len(eligible),
                "excluded_count": rejected,
                "focus_region": focus_region or "all Toronto",
                "top_donors": [d.name for d in eligible[:5]],
            },
            decision_steps=log.steps,
            approved_count=len(eligible),
            rejected_count=rejected,
        )
