from src.agents.base import BaseAgent
from src.models import AgentResult, NeedZone


class NeedPrioritizerAgent(BaseAgent):
    name = "Need Prioritizer"
    dataset = "GDELT Food Security (#4)"

    def run(self, context: dict) -> AgentResult:
        events_df = context["need_events_df"]
        grouped = (
            events_df.groupby("region")
            .agg(event_count=("severity_score", "count"), priority_score=("severity_score", "mean"))
            .reset_index()
            .sort_values("priority_score", ascending=False)
        )

        zones: list[NeedZone] = []
        for row in grouped.itertuples(index=False):
            signals = (
                events_df[events_df["region"] == row.region]
                .sort_values("severity_score", ascending=False)
                .head(2)["headline_summary"]
                .tolist()
            )
            zones.append(
                NeedZone(
                    region=row.region,
                    priority_score=round(float(row.priority_score), 2),
                    event_count=int(row.event_count),
                    top_signals=signals,
                )
            )

        priority_zone = zones[0] if zones else None
        context["need_zones"] = zones
        context["priority_zone"] = priority_zone

        summary = (
            f"Prioritized {len(zones)} zones from GDELT signals. "
            f"Top need: {priority_zone.region} (score {priority_zone.priority_score})."
            if priority_zone
            else "No need zones identified."
        )
        return AgentResult(
            agent_name=self.name,
            summary=summary,
            dataset=self.dataset,
            data={"zones": [{"region": z.region, "score": z.priority_score} for z in zones]},
        )
