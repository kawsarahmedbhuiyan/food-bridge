#!/usr/bin/env python3
"""FoodBridge CLI — multi-agent food waste redistribution prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.orchestrator import FoodBridgeOrchestrator

REGIONS = [
    "Scarborough",
    "Regent Park",
    "Downtown Toronto",
    "North York",
    "Etobicoke",
    "East York",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FoodBridge: agentic food rescue coordinator (Toronto POC)",
    )
    parser.add_argument(
        "--region",
        choices=REGIONS,
        help="Focus matching on a Toronto region (default: auto from GDELT need data)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top matches to show (default: 5)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use a smaller donor pool for quicker runs",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show per-agent dataset and detail output",
    )
    return parser


def print_plan(plan, verbose: bool = False) -> None:
    print("\n🌉 FoodBridge — Agentic Food Rescue CLI\n")
    print("=" * 60)
    print("Datasets: Dinesafe (#1) | Biomass (#3) | GDELT (#4) | Supply chain (#5)")
    print("=" * 60)

    if plan.priority_zone:
        z = plan.priority_zone
        print(f"\n🎯 Priority Zone: {z.region}")
        print(f"   Need score: {z.priority_score} | Events: {z.event_count}")
        for signal in z.top_signals:
            print(f"   • {signal}")

    print("\n🤖 Agent Workflow:")
    for i, log in enumerate(plan.agent_logs, 1):
        print(f"   {i}. [{log.agent_name}] {log.summary}")
        if verbose:
            print(f"      Dataset: {log.dataset}")
            for key, val in log.data.items():
                print(f"      {key}: {val}")

    print("\n✅ Top Matches:")
    if not plan.matches:
        print("   No matches generated.")
    for i, match in enumerate(plan.matches, 1):
        status = "APPROVED" if match.approved else "DEFERRED"
        print(f"\n   {i}. {match.donor.name} → {match.recipient.name} [{status}]")
        print(f"      Score: {match.match_score} | Distance: {match.distance_km} km")
        print(f"      Type: {match.donor.establishment_type} | {match.donor.address[:50]}")
        for reason in match.reasons:
            print(f"      • {reason}")
        for flag in match.ethics_flags:
            print(f"      ⚠️  {flag}")

    print("\n📋 Pickup Route:")
    if plan.route:
        for stop in plan.route:
            icon = "📦" if stop.stop_type == "pickup" else "🏠"
            print(f"   {stop.sequence}. {icon} {stop.name}")
            print(f"      {stop.notes}")
    else:
        print("   No route planned.")

    er = plan.ethics_report
    print(f"\n🛡️  Ethics Report (fairness: {er.fairness_score})")
    if er.safety_issues:
        for issue in er.safety_issues:
            print(f"   ⚠️  {issue}")
    for rec in er.recommendations[:4]:
        print(f"   • {rec}")
    print(f"\n   ⛔ Human approval required before dispatch: {er.human_approval_required}")
    print()


def main() -> int:
    args = build_parser().parse_args()
    donor_limit = 3000 if args.fast else None

    print("Loading Toronto Dinesafe + Canada Biomass data...")
    plan = FoodBridgeOrchestrator().run(
        focus_region=args.region,
        top_matches=args.top,
        donor_pool_limit=donor_limit,
    )
    print_plan(plan, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
