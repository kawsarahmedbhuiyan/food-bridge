from src.agents.base import BaseAgent, haversine_km
from src.agents.decisions import DecisionLog
from src.geo import is_chain_donor
from src.models import AgentResult, Match


class MatcherAgent(BaseAgent):
    name = "Matcher"
    dataset = "Combined outputs (Dinesafe + Biomass + GDELT)"

    def run(self, context: dict) -> AgentResult:
        log = DecisionLog()
        donors = context.get("eligible_donors", context["donors"])
        recipients = context["recipients"]
        priority_zone = context.get("priority_zone")
        focus_region = context.get("focus_region")
        chain_pickup_counts = context.get("chain_pickup_counts", {})
        top_n = context.get("top_matches", 5)
        max_distance_km = context.get("max_distance_km", 15.0)

        log.add(
            "Queue recipients: small organizations first, then by need",
            f"{len(recipients)} recipients, {len(donors)} ethics-approved donors",
            "Fairness: small orgs prioritized to prevent exclusion",
            max_distance_km=max_distance_km,
        )

        log.add(
            "priority_score = need_score × surplus × 100 / (1 + distance_km)",
            "Closer high-need matches score higher",
            "Balances geographic proximity with food insecurity priority",
        )

        target_region = focus_region or (priority_zone.region if priority_zone else None)
        need_score = priority_zone.priority_score if priority_zone else 5.0

        queue = sorted(
            recipients,
            key=lambda r: (not r.is_small_org, r.region != target_region if target_region else False),
        )

        matches: list[Match] = []
        used_donors: set[str] = set()

        for recipient in queue:
            if len(matches) >= top_n:
                break

            best_donor = None
            best_dist = float("inf")
            best_priority = 0.0

            for donor in donors:
                if donor.establishment_id in used_donors:
                    continue
                dist = haversine_km(
                    donor.latitude, donor.longitude,
                    recipient.latitude, recipient.longitude,
                )
                if dist > max_distance_km:
                    continue
                priority = need_score * donor.surplus_score * 100 / (1 + dist)
                if priority > best_priority:
                    best_priority = priority
                    best_donor = donor
                    best_dist = dist

            if best_donor is None:
                log.add(
                    "No donor within max_distance_km",
                    f"Recipient {recipient.name}",
                    "Skipped — logged transparently",
                    recipient=recipient.name,
                )
                continue

            if recipient.is_small_org:
                tier = "small-org-priority"
            elif target_region and recipient.region == target_region:
                tier = "critical-need"
            else:
                tier = "standard"

            reasons = [
                f"Surplus: {best_donor.predicted_surplus_kg:.1f} kg est.",
                f"Distance: {best_dist:.1f} km",
                f"Dinesafe: Pass ({best_donor.inspection_date})",
                f"Fairness tier: {tier}",
            ]

            ethics_flags: list[str] = []
            approved = True
            if is_chain_donor(best_donor.name):
                pickups = chain_pickup_counts.get(
                    best_donor.name, chain_pickup_counts.get("_default_chain", 0)
                )
                if pickups >= 2:
                    ethics_flags.append("Chain donor cap reached — defer to small donors")
                    approved = False

            allocated = min(best_donor.predicted_surplus_kg, 25.0)
            matches.append(
                Match(
                    donor=best_donor,
                    recipient=recipient,
                    match_score=round(best_priority, 2),
                    distance_km=round(best_dist, 1),
                    reasons=reasons,
                    ethics_flags=ethics_flags,
                    approved=approved,
                    fairness_tier=tier,
                    allocated_kg=allocated,
                )
            )
            used_donors.add(best_donor.establishment_id)

            log.add(
                "Greedy best priority within distance",
                f"{recipient.name} (small_org={recipient.is_small_org})",
                f"{best_donor.name} → {recipient.name}: {allocated:.1f} kg, {best_dist:.1f} km",
                tier=tier,
            )

        matches.sort(key=lambda m: m.match_score, reverse=True)
        context["matches"] = matches

        approved = sum(1 for m in matches if m.approved)
        small_allocs = sum(1 for m in matches if m.recipient.is_small_org)
        log.add(
            "Matching summary",
            f"{len(matches)} allocations",
            f"{approved} approved, {small_allocs} to small organizations",
            small_org_allocations=small_allocs,
        )

        return AgentResult(
            agent_name=self.name,
            summary=f"Created {len(matches)} matches ({approved} approved, {small_allocs} small-org).",
            dataset=self.dataset,
            data={
                "matches": [
                    {"donor": m.donor.name, "recipient": m.recipient.name, "score": m.match_score}
                    for m in matches
                ],
                "small_org_allocations": small_allocs,
            },
            decision_steps=log.steps,
        )
