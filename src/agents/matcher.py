from src.agents.base import BaseAgent, haversine_km
from src.geo import is_chain_donor
from src.models import AgentResult, Match


class MatcherAgent(BaseAgent):
    name = "Matcher"
    dataset = "Combined outputs (Dinesafe + Biomass + GDELT)"

    def run(self, context: dict) -> AgentResult:
        donors = context.get("eligible_donors", context["donors"])
        recipients = context["recipients"]
        priority_zone = context.get("priority_zone")
        focus_region = context.get("focus_region")
        chain_pickup_counts = context.get("chain_pickup_counts", {})
        top_n = context.get("top_matches", 5)

        target_region = focus_region or (priority_zone.region if priority_zone else None)
        region_recipients = (
            [r for r in recipients if r.region == target_region] if target_region else recipients
        )
        if not region_recipients:
            region_recipients = recipients

        matches: list[Match] = []
        for donor in donors[: top_n * 3]:
            recipient = min(
                region_recipients,
                key=lambda r: haversine_km(donor.latitude, donor.longitude, r.latitude, r.longitude),
            )
            distance = haversine_km(
                donor.latitude, donor.longitude, recipient.latitude, recipient.longitude
            )

            score = donor.surplus_score * 0.45
            score += max(0, 1 - distance / 12) * 0.35
            if donor.inspection_result == "Pass":
                score += 0.2

            reasons = [
                f"Surplus estimate: {donor.surplus_score:.0%}",
                f"Distance: {distance:.1f} km",
                f"Dinesafe: {donor.inspection_result}",
                f"Region: {donor.region}",
            ]

            ethics_flags: list[str] = []
            if is_chain_donor(donor.name):
                pickups = chain_pickup_counts.get(donor.name, chain_pickup_counts.get("_default_chain", 0))
                if pickups >= 2:
                    ethics_flags.append("Chain donor cap reached — defer to small donors")
                    score *= 0.25

            if donor.inspection_result == "Conditional Pass":
                ethics_flags.append("Conditional inspection — extra safety review required")
                score *= 0.65

            matches.append(
                Match(
                    donor=donor,
                    recipient=recipient,
                    match_score=round(score, 2),
                    distance_km=round(distance, 1),
                    reasons=reasons,
                    ethics_flags=ethics_flags,
                    approved=len(ethics_flags) == 0,
                )
            )

        matches.sort(key=lambda m: m.match_score, reverse=True)
        matches = matches[:top_n]
        context["matches"] = matches

        approved = sum(1 for m in matches if m.approved)
        return AgentResult(
            agent_name=self.name,
            summary=f"Generated {len(matches)} donor→recipient matches ({approved} auto-approved).",
            dataset=self.dataset,
            data={
                "matches": [
                    {"donor": m.donor.name, "recipient": m.recipient.name, "score": m.match_score}
                    for m in matches
                ]
            },
        )
