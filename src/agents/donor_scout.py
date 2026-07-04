from src.agents.base import BaseAgent
from src.models import AgentResult


class DonorScoutAgent(BaseAgent):
    name = "Donor Scout"
    dataset = "Toronto Dinesafe (#1)"

    SAFE_RESULTS = {"Pass", "Conditional Pass"}

    def run(self, context: dict) -> AgentResult:
        donors = context["donors"]
        focus_region = context.get("focus_region")
        max_donors = context.get("max_donors", 500)

        eligible = [d for d in donors if d.inspection_result in self.SAFE_RESULTS]
        excluded = len(donors) - len(eligible)

        if focus_region:
            regional = [d for d in eligible if d.region == focus_region]
            if regional:
                eligible = regional

        eligible.sort(key=lambda d: d.surplus_score, reverse=True)
        eligible = eligible[:max_donors]
        context["eligible_donors"] = eligible

        return AgentResult(
            agent_name=self.name,
            summary=f"Found {len(eligible)} eligible Dinesafe donors ({excluded} excluded for safety).",
            dataset=self.dataset,
            data={
                "eligible_count": len(eligible),
                "excluded_count": excluded,
                "focus_region": focus_region or "all Toronto",
                "top_donors": [d.name for d in eligible[:5]],
            },
        )
