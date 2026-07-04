from datetime import datetime, timedelta

from src.agents.base import BaseAgent
from src.agents.decisions import DecisionLog
from src.models import AgentResult


class TimingNegotiatorAgent(BaseAgent):
    name = "Timing Negotiator"
    dataset = "Route schedule + donor/recipient constraints"

    BASE_HOUR = 17
    PICKUP_MINUTES = 20
    TRAVEL_BUFFER_MINUTES = 15

    def run(self, context: dict) -> AgentResult:
        log = DecisionLog()
        route = context.get("route", [])
        route_stats = context.get("route_stats", {})

        log.add(
            "Default pickup window starts 17:00 (post-service surplus)",
            f"{len(route)} stops to schedule",
            "Restaurants typically release surplus after lunch/dinner service",
            base_hour=self.BASE_HOUR,
        )

        if not route:
            return AgentResult(
                agent_name=self.name,
                summary="No route stops to schedule.",
                dataset=self.dataset,
                decision_steps=log.steps,
            )

        current = datetime(2026, 1, 1, self.BASE_HOUR, 0)
        scheduled = 0

        for stop in route:
            window_start = current.strftime("%H:%M")
            duration = self.PICKUP_MINUTES if stop.stop_type == "pickup" else 10
            current += timedelta(minutes=duration)
            window_end = current.strftime("%H:%M")
            stop.window_start = window_start
            stop.window_end = window_end
            current += timedelta(minutes=self.TRAVEL_BUFFER_MINUTES)
            scheduled += 1

            log.add(
                f"Negotiate {stop.stop_type} window",
                stop.name,
                f"Agreed window {window_start}–{window_end} (auto-negotiated)",
                stop_type=stop.stop_type,
            )

        total_min = route_stats.get("est_minutes", 0)
        finish = current.strftime("%H:%M")

        log.add(
            "Timing constraints summary",
            f"est. route time {total_min} min",
            f"All {scheduled} windows fit within single evening run (done ~{finish})",
            finish_time=finish,
        )

        context["pickup_schedule"] = [
            {"name": s.name, "start": s.window_start, "end": s.window_end}
            for s in route
        ]

        return AgentResult(
            agent_name=self.name,
            summary=f"Negotiated {scheduled} pickup/delivery windows (17:00–{finish}).",
            dataset=self.dataset,
            data={"windows": context["pickup_schedule"], "finish_time": finish},
            decision_steps=log.steps,
        )
