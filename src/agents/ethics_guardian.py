from src.agents.base import BaseAgent
from src.models import AgentResult, EthicsReport


class EthicsGuardianAgent(BaseAgent):
    name = "Ethics Guardian"
    dataset = "Dinesafe (#1) + match audit rules"

    def run(self, context: dict) -> AgentResult:
        matches = context.get("matches", [])
        priority_zone = context.get("priority_zone")
        route_stats = context.get("route_stats", {})

        safety_issues: list[str] = []
        transparency_log: list[str] = []
        recommendations: list[str] = []

        for match in matches:
            transparency_log.append(
                f"{match.donor.name} → {match.recipient.name}: score={match.match_score}, "
                f"flags={match.ethics_flags or 'none'}"
            )
            if match.donor.inspection_result == "Conditional Pass":
                safety_issues.append(f"{match.donor.name}: conditional Dinesafe status")
            for flag in match.ethics_flags:
                if "defer" in flag.lower():
                    recommendations.append(f"Prioritize small donor over {match.donor.name}")

        approved_matches = [m for m in matches if m.approved]
        fairness = 0.5
        if priority_zone:
            served = {m.recipient.region for m in approved_matches}
            if priority_zone.region in served:
                fairness += 0.3
        if len(matches) - len(approved_matches) > 0:
            fairness += 0.1
        fairness = min(1.0, round(fairness, 2))

        total_km = route_stats.get("total_km", 0)
        if total_km > 25:
            recommendations.append("Route exceeds 25 km — split runs to reduce environmental impact")

        recommendations.extend([
            "Human coordinator must approve all pickups before dispatch",
            "Use aggregate need data only — no individual tracking",
            "Log all agent decisions for accountability audit trail",
        ])

        report = EthicsReport(
            fairness_score=fairness,
            safety_issues=safety_issues,
            transparency_log=transparency_log,
            recommendations=recommendations,
            human_approval_required=True,
        )
        context["ethics_report"] = report

        return AgentResult(
            agent_name=self.name,
            summary=f"Fairness {fairness}. {len(safety_issues)} safety notes. Human approval required.",
            dataset=self.dataset,
            data={"fairness_score": fairness, "safety_issues": safety_issues},
        )
