from src.agents.base import BaseAgent
from src.agents.decisions import DecisionLog
from src.models import AgentResult, EthicsReport


class EthicsGuardianAgent(BaseAgent):
    name = "Ethics Guardian"
    dataset = "Dinesafe (#1) + match audit rules"

    def run(self, context: dict) -> AgentResult:
        log = DecisionLog()
        matches = context.get("matches", [])
        priority_zone = context.get("priority_zone")
        route_stats = context.get("route_stats", {})

        safety_issues: list[str] = []
        transparency_log: list[str] = []
        recommendations: list[str] = []

        log.add(
            "Audit all matches for safety and fairness",
            f"{len(matches)} matches to review",
            "Human coordinator must approve before dispatch",
        )

        for match in matches:
            transparency_log.append(
                f"{match.donor.name} → {match.recipient.name}: "
                f"score={match.match_score}, tier={match.fairness_tier}, "
                f"flags={match.ethics_flags or 'none'}"
            )
            if match.donor.inspection_result != "Pass":
                safety_issues.append(f"{match.donor.name}: non-Pass Dinesafe status")
            if match.donor.crucial_infractions > 0:
                safety_issues.append(f"{match.donor.name}: crucial infraction history")
            for flag in match.ethics_flags:
                if "defer" in flag.lower():
                    recommendations.append(f"Prioritize small donor over {match.donor.name}")

        approved_matches = [m for m in matches if m.approved]
        small_org_allocs = sum(1 for m in approved_matches if m.recipient.is_small_org)

        fairness = 0.5
        if priority_zone:
            served = {m.recipient.region for m in approved_matches}
            if priority_zone.region in served:
                fairness += 0.25
        if small_org_allocs > 0:
            fairness += 0.15
        if len(matches) - len(approved_matches) > 0:
            fairness += 0.05
        fairness = min(1.0, round(fairness, 2))

        total_km = route_stats.get("total_km", 0)
        random_km = route_stats.get("random_route_km", total_km * 1.35)
        env_note = (
            f"Optimized route {total_km} km saves ~{max(0, random_km - total_km):.1f} km "
            f"vs random ordering ({random_km:.1f} km est.)"
        )

        if total_km > 25:
            recommendations.append("Route exceeds 25 km — split runs to reduce environmental impact")

        recommendations.extend([
            "Human coordinator must approve all pickups before dispatch",
            "Use aggregate need data only — no individual tracking",
            "All agent decision steps retained for accountability audit",
        ])

        log.add(
            "Fairness and environmental assessment",
            f"{small_org_allocs} small-org allocations, fairness={fairness}",
            env_note,
            small_org_allocations=small_org_allocs,
        )

        report = EthicsReport(
            fairness_score=fairness,
            safety_issues=safety_issues,
            transparency_log=transparency_log,
            recommendations=recommendations,
            human_approval_required=True,
            small_org_allocations=small_org_allocs,
            environmental_note=env_note,
        )
        context["ethics_report"] = report

        return AgentResult(
            agent_name=self.name,
            summary=(
                f"Fairness {fairness}. {len(safety_issues)} safety notes. "
                f"{small_org_allocs} small-org allocations. Human approval required."
            ),
            dataset=self.dataset,
            data={
                "fairness_score": fairness,
                "safety_issues": safety_issues,
                "small_org_allocations": small_org_allocs,
            },
            decision_steps=log.steps,
        )
