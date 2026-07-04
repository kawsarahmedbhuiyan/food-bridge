from src.agents.base import BaseAgent
from src.agents.decisions import DecisionLog
from src.models import AgentResult, NeedZone


class NeedPrioritizerAgent(BaseAgent):
    name = "Need Prioritizer"
    dataset = "GDELT Food Security (#4) + Biomass organic waste (#3)"

    def run(self, context: dict) -> AgentResult:
        log = DecisionLog()
        events_df = context["need_events_df"]
        biomass_df = context["biomass_df"]
        focus_region = context.get("focus_region")

        grouped = (
            events_df.groupby("region")
            .agg(event_count=("severity_score", "count"), priority_score=("severity_score", "mean"))
            .reset_index()
        )

        organic = biomass_df["MNCPL_SOLID_WASTE_ORGANIC_VOL"]
        bio_min, bio_max = float(organic.min()), float(organic.max())
        bio_span = bio_max - bio_min or 1.0

        log.add(
            "GDELT severity_score aggregated by Toronto region",
            f"{len(events_df)} food-security events in dataset",
            f"Identified need signals in {len(grouped)} regions",
            event_count=len(events_df),
        )

        log.add(
            "Boost need score with Biomass organic waste context",
            f"Organic volume range {bio_min:.0f}–{bio_max:.0f} m³",
            "Higher municipal organic waste proxies redistribution urgency",
        )

        zones: list[NeedZone] = []
        for row in grouped.itertuples(index=False):
            signals = (
                events_df[events_df["region"] == row.region]
                .sort_values("severity_score", ascending=False)
                .head(2)["headline_summary"]
                .tolist()
            )
            biomass_need = round((bio_max - bio_min) / bio_span * 0.3 + 0.1, 2)
            combined = round(float(row.priority_score) * 0.7 + biomass_need * 10 * 0.3, 2)
            zones.append(
                NeedZone(
                    region=row.region,
                    priority_score=combined,
                    event_count=int(row.event_count),
                    top_signals=signals,
                    biomass_need_score=biomass_need,
                    is_small_org_hub=row.region in {"Regent Park", "East York", "Scarborough"},
                )
            )

        zones.sort(key=lambda z: z.priority_score, reverse=True)

        if focus_region:
            focused = [z for z in zones if z.region == focus_region]
            priority_zone = focused[0] if focused else (zones[0] if zones else None)
            log.add(
                "User-selected focus region override",
                f"focus_region={focus_region}",
                f"Priority set to {priority_zone.region if priority_zone else 'none'}",
            )
        else:
            priority_zone = zones[0] if zones else None

        context["need_zones"] = zones
        context["priority_zone"] = priority_zone

        small_hubs = sum(1 for z in zones if z.is_small_org_hub)
        log.add(
            "Rank zones by combined GDELT + Biomass need score",
            f"{len(zones)} zones ranked",
            f"Top need: {priority_zone.region if priority_zone else 'N/A'}; "
            f"{small_hubs} small-community hub zones flagged",
            top_score=priority_zone.priority_score if priority_zone else 0,
        )

        summary = (
            f"Prioritized {len(zones)} zones from GDELT + Biomass. "
            f"Top need: {priority_zone.region} (score {priority_zone.priority_score})."
            if priority_zone
            else "No need zones identified."
        )
        return AgentResult(
            agent_name=self.name,
            summary=summary,
            dataset=self.dataset,
            data={"zones": [{"region": z.region, "score": z.priority_score} for z in zones]},
            decision_steps=log.steps,
        )
