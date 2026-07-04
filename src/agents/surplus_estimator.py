from collections import defaultdict

from src.agents.base import BaseAgent
from src.models import AgentResult


class SurplusEstimatorAgent(BaseAgent):
    name = "Surplus Estimator"
    dataset = "Canada Biomass MSW (#3) + Supply Chain (#5, optional)"

    def run(self, context: dict) -> AgentResult:
        biomass_df = context["biomass_df"]
        donors = context["donors"]
        supply_chain = context.get("supply_chain_df")

        organic = biomass_df["MNCPL_SOLID_WASTE_ORGANIC_VOL"]
        p50 = float(organic.median())
        p75 = float(organic.quantile(0.75))
        national_pressure = min(1.0, p75 / (p50 * 2) if p50 else 0.5)

        region_stats: dict[str, list[str]] = defaultdict(list)
        for donor in donors:
            region_stats[donor.region].append(donor.establishment_type)

        region_scores: dict[str, float] = {}
        for region, types in region_stats.items():
            score = national_pressure * 0.4
            score += min(0.35, len(types) / 400)
            grocery_ratio = types.count("Grocery") / max(len(types), 1)
            cafeteria_ratio = types.count("Cafeteria") / max(len(types), 1)
            score += grocery_ratio * 0.15 + cafeteria_ratio * 0.1
            region_scores[region] = round(min(1.0, score), 2)

        supply_boost = 0.0
        if supply_chain is not None and not supply_chain.empty:
            supply_boost = float(supply_chain["severity"].mean()) * 0.1

        for donor in donors:
            base = region_scores.get(donor.region, 0.4)
            if donor.establishment_type == "Grocery":
                base = min(1.0, base + 0.12 + supply_boost)
            elif donor.establishment_type == "Cafeteria":
                base = min(1.0, base + 0.08 + supply_boost)
            donor.surplus_score = round(min(1.0, base), 2)

        top_regions = sorted(region_scores, key=region_scores.get, reverse=True)[:3]
        context["region_surplus_scores"] = region_scores

        return AgentResult(
            agent_name=self.name,
            summary=(
                f"Scored {len(donors)} donors using biomass baseline (organic p75={p75:.0f}). "
                f"Hotspots: {', '.join(top_regions)}."
            ),
            dataset=self.dataset,
            data={
                "national_organic_p50": round(p50, 1),
                "national_organic_p75": round(p75, 1),
                "top_surplus_regions": top_regions,
                "supply_chain_boost": round(supply_boost, 2),
            },
        )
