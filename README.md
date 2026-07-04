# FoodBridge

**Multi-agent food waste redistribution** for CREATE-a-Thon — Toronto Dinesafe + Canada Biomass datasets, with transparent AI decision-making.

## Problem

Restaurants discard edible food while communities face food insecurity. FoodBridge coordinates specialized agents to predict surplus, prioritize need, screen donors ethically, match shelters, optimize routes, and negotiate pickup timing.

## Datasets

| Dataset | Path | Used by |
|---------|------|---------|
| **Dinesafe** | `data/dinesafe/Dinesafe.csv` | Ethics screening, donor locations, logistics |
| **Biomass Canada** | `data/biomass/BIOMASS_MSW_INV.csv` | Surplus estimation, need scoring |
| **GDELT** (optional) | `data/huggingface/gdelt/` or sample CSV | Need prioritization |
| **Supply chain** (optional) | `data/huggingface/supply_chain/` or sample CSV | Surplus boost signals |

## Agent pipeline (transparent decisions)

Each agent emits auditable **decision steps** (rule → input → outcome → metadata):

| # | Agent | Role |
|---|-------|------|
| 1 | **Surplus Estimator** | Monitor inventory; predict kg surplus from Biomass + establishment type |
| 2 | **Need Prioritizer** | Rank regions by GDELT food-security signals + Biomass organic waste |
| 3 | **Ethics & Donor Scout** | Pass-only Dinesafe donors; exclude crucial infractions |
| 4 | **Matcher** | Pair closest high-need recipients; small-org priority queue |
| 5 | **Logistics Planner** | Nearest-neighbor route optimization; environmental tradeoff disclosure |
| 6 | **Timing Negotiator** | Auto-negotiate pickup/delivery windows (17:00+ evening run) |
| 7 | **Ethics Guardian** | Final fairness audit, safety review, human-approval gate |

## Quick start

```bash
cd food-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: download HuggingFace datasets (~1.1 GB)
python scripts/download_datasets.py

# CLI
python main.py --region Scarborough --top 3 --verbose

# Web app
uvicorn web.app:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) — pick a region, set radius/top matches, click **Run planning**. The UI shows map, agent pipeline, clickable audit trail, matches, route, pickup schedule, and ethics report.

## Ethical safeguards

- **Safety**: Latest `inspectionStatus = Pass` only; any crucial (`C - Crucial`) infraction disqualifies a donor
- **Fairness**: Small-organization recipients prioritized in matching queue
- **Transparency**: Full step-level audit trail per agent in API and dashboard
- **Environmental**: Logistics agent compares optimized vs estimated random route distance

## Cursor agent interaction log

Human ↔ AI chat is recorded in `logs/cursor-agent-interactions.log` via `.cursor/hooks.json`.

```bash
python3 scripts/backfill_cursor_log.py   # backfill from transcripts
```

## Project structure

```
food-bridge/
├── main.py              # CLI entry point
├── web/                 # FastAPI + map dashboard
├── src/agents/          # Specialized transparent agents
├── src/orchestrator.py  # Pipeline coordinator
├── data/dinesafe/       # Dinesafe CSV + specs
├── data/biomass/        # Biomass CSV + specs
└── scripts/
```
