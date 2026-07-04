# FoodBridge

**Agentic AI for food waste redistribution** — Toronto-focused proof of concept using Dinesafe health inspections, Canada Biomass municipal waste data, and optional GDELT food-security signals.

FoodBridge coordinates seven specialized agents to predict edible surplus, prioritize communities in need, screen donors for safety, match shelters fairly, plan pickup routes, negotiate timing, and produce an auditable ethics report before a human coordinator dispatches any pickup.

---

## Business need

### Problem

Restaurants, cafeterias, and grocery stores discard food that is still safe to eat while shelters and community kitchens face chronic shortages. The bottleneck is **coordination**, not supply:

- Donors lack a trusted way to identify eligible recipients nearby.
- Recipients cannot predict when surplus will be available.
- Routes and pickup windows are negotiated manually, wasting volunteer time.
- Allocation decisions can appear opaque, creating fairness and accountability risks.

### Stakeholders and outcomes

| Stakeholder | Need | FoodBridge response |
|-------------|------|---------------------|
| Food donors | Safe, low-friction way to redirect surplus | Pass-only Dinesafe screening; negotiated pickup windows |
| Shelters & community kitchens | Reliable, equitable access to surplus | Need-based matching; small-org priority queue |
| Coordinators & volunteers | Actionable daily plan | Matches, optimized route, schedule, and ethics summary |
| Public health | Inspection standards upheld in redistribution | Crucial-infraction exclusion; auditable donor eligibility |
| High-need communities | Food directed where urgency is greatest | GDELT + Biomass signals rank priority zones |

### Outcomes the system targets

- **Lower time-to-match** between donor and recipient.
- **Shorter delivery routes** via geographic optimization.
- **Explainable decisions** through per-agent audit trails.
- **Human oversight** before any pickup is dispatched.

---

## Architecture

### System overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Presentation layer                              │
│        Web dashboard (FastAPI + Leaflet)  │  CLI (main.py)              │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │  GET /api/plan
┌─────────────────────────────▼───────────────────────────────────────────┐
│                      FoodBridgeOrchestrator                               │
│              Sequential multi-agent pipeline (shared context)             │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   Seven agents         Data loader           Serializer
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    Dinesafe            Biomass MSW         GDELT / Supply chain
    (donors, safety)    (surplus, need)     (need, disruption signals)
                              │
                              ▼
                     RedistributionPlan
           (matches, route, schedule, ethics report, agent logs)
```

### Agent pipeline

Agents execute in a fixed order. Each reads from and writes to a shared planning context, producing a structured `AgentResult` with optional `decision_steps` for transparency.

```
Surplus Estimator → Need Prioritizer → Ethics & Donor Scout → Matcher
       → Logistics Planner → Timing Negotiator → Ethics Guardian
```

| Agent | Data sources | Responsibility |
|-------|--------------|----------------|
| **Surplus Estimator** | Biomass, supply chain (optional) | Estimates daily surplus per donor from regional organic-waste pressure and establishment type |
| **Need Prioritizer** | GDELT, Biomass | Ranks Toronto regions by food-security urgency |
| **Ethics & Donor Scout** | Dinesafe | Approves Pass-only donors; rejects crucial infraction history |
| **Matcher** | Agent outputs, recipient registry | Pairs donors to nearest high-need shelters; prioritizes small organizations |
| **Logistics Planner** | Coordinates | Builds nearest-neighbor pickup/delivery route from a central depot |
| **Timing Negotiator** | Route stops | Assigns evening pickup/delivery windows along the route |
| **Ethics Guardian** | Full plan | Final fairness and safety audit; requires human approval |

### Planning run (end to end)

1. Load Dinesafe establishments, Biomass grid volumes, GDELT events, and recipient hubs.
2. Score predicted surplus (kg) per donor.
3. Identify the highest-need region (optionally overridden by user-selected focus region).
4. Filter to ethics-approved donors.
5. Create donor–recipient matches within a configurable radius.
6. Optimize stop order for volunteer drivers.
7. Negotiate time windows (default evening run from 17:00).
8. Emit ethics report and full decision audit trail.

### Components

| Module | Role |
|--------|------|
| `src/orchestrator.py` | Runs the agent pipeline; returns `RedistributionPlan` |
| `src/agents/` | One agent per domain concern |
| `src/data_loader.py` | Ingests CSV and optional HuggingFace datasets |
| `src/models.py` | Domain types (`Donor`, `Match`, `PickupStop`, `DecisionStep`, …) |
| `src/serialize.py` | JSON serialization for API and dashboard |
| `web/` | Interactive map, agent log viewer, match and schedule panels |

---

## Design choices

### Multi-agent decomposition

Redistribution combines prediction, ethics, geography, scheduling, and governance. FoodBridge assigns each concern to a dedicated agent so that:

- Rules remain **modular** (routing can change without altering safety criteria).
- Outputs map to **stakeholder questions** (e.g. “Why was this donor excluded?”).
- Each stage produces an **independent audit trail**.

### Deterministic, explainable logic

Core decisions use **rules and heuristics on open data**, not opaque model outputs. Every agent records `DecisionStep` entries (rule, input, outcome, metadata) so coordinators can review reasoning in the dashboard or via `/api/plan`.

### Safety-first donor eligibility

| Rule | Rationale |
|------|-----------|
| Latest Dinesafe status = **Pass** | Only verified-safe premises participate |
| Zero **crucial (C)** infractions on record | Reduces liability from temperature or contamination issues |
| Conditional Pass / Closed excluded | Unresolved significant violations |

### Fairness for small organizations

Small community kitchens are prioritized in the matching queue. Allocations carry fairness tiers (`small-org-priority`, `critical-need`, `standard`). The Ethics Guardian reports how many matches served small-org recipients.

### Optimization strategy

| Function | Approach | Why |
|----------|----------|-----|
| Surplus | Biomass organic volume × establishment-type factor | Interpretable proxy where live inventory is unavailable |
| Need | GDELT severity blended with Biomass organic signal | Combines event-driven urgency with structural waste pressure |
| Matching | `need × surplus / distance` within max radius | Balances proximity and priority |
| Routing | Nearest-neighbor from depot | Efficient greedy heuristic for PoC-scale fleets |
| Timing | Sequential 17:00+ windows | Aligns with post-service surplus availability |

Machine learning is reserved for future production enhancements where labeled data exists; the PoC prioritizes **reproducibility and auditability**.

### Dual access paths

The **web dashboard** serves coordinators (map, audit trail, schedule). The **CLI** supports scripting and headless runs. Both invoke the same orchestrator, guaranteeing consistent behavior.

---

## Development process

FoodBridge follows a **data-first, agent-modular** engineering approach:

### 1. Data grounding

All agent logic is tied to real datasets with documented column specs (`data/dinesafe/`, `data/biomass/`). Optional HuggingFace datasets (GDELT, supply chain) degrade gracefully to bundled samples when not downloaded.

### 2. Agent isolation

Each agent lives in its own module, implements a single `run(context)` method, and returns an `AgentResult`. New capabilities (e.g. SMS negotiation) are added as agents or swapped implementations without rewriting the pipeline.

### 3. Shared orchestration contract

The orchestrator owns data loading, agent ordering, and plan assembly. Agents communicate only through the shared context dictionary, keeping interfaces stable while individual agents evolve.

### 4. API-first delivery

`GET /api/plan` exposes the full plan as JSON. The web UI is a client of that contract, enabling future mobile apps, partner integrations, or scheduled batch jobs without UI changes.

### 5. Transparency by construction

The `DecisionLog` utility is invoked inside every agent at rule boundaries—not added as an afterthought—so audit data is always co-generated with decisions.

---

## Testing approach

### Current validation (PoC)

The system is validated through repeatable integration checks:

```bash
# End-to-end pipeline
python -c "
from src.orchestrator import FoodBridgeOrchestrator
p = FoodBridgeOrchestrator().run(focus_region='Regent Park', top_matches=3)
assert p.matches and p.ethics_report
assert all(len(l.decision_steps) > 0 for l in p.agent_logs)
"

# CLI output
python main.py --region Scarborough --top 3 --verbose

# API contract
uvicorn web.app:app --port 8000
curl "http://127.0.0.1:8000/api/plan?fast=true&top=2"
```

| Validation area | Expected behavior |
|-----------------|-------------------|
| Data ingestion | ~18k Dinesafe establishments parsed; Biomass grid loaded |
| Ethics filter | Non-Pass and crucial-infraction donors excluded |
| Matching | Respects `max_distance_km`; small-org recipients matched |
| Transparency | All seven agents emit decision steps |
| API | Response includes matches, route, schedule, ethics report, agent logs |
| UI | Map, pipeline, audit trail, and schedule render from API response |

### Production testing roadmap

| Layer | Planned tests |
|-------|----------------|
| **Unit** | Ethics rules, distance calculations, infraction aggregation, decision log formatting |
| **Integration** | Orchestrator with fixture CSVs; snapshot comparison of plan JSON |
| **API** | Parameter validation, error handling, response schema |
| **Ethics regression** | Golden donor IDs with expected pass/fail outcomes |
| **Performance** | Full donor pool (~18k), routes with 50+ stops |
| **End-to-end** | Automated UI flow: region selection → plan generation → map verification |

---

## Scaling for production

### Data infrastructure

| PoC | Production |
|-----|------------|
| Static CSV files | Incremental ETL from Toronto Open Data, Statistics Canada, GDELT API |
| Fixed recipient list | CRM sync with food-bank networks (Feed Ontario, Second Harvest) |
| Estimated surplus (kg) | Donor-reported inventory via app/SMS; optional IoT temperature probes |
| Sample GDELT fallback | Real-time geo-fenced event stream for the GTA |

Spatial queries (donors within N km of a need zone) move to **PostgreSQL + PostGIS**.

### Orchestration

| PoC | Production |
|-----|------------|
| In-process sequential pipeline | Workflow engine (Temporal, Prefect) with persisted state |
| On-demand synchronous runs | Scheduled daily planning + event-triggered replanning on donor alerts |
| Single server | Horizontally scaled workers; idempotent, retryable agent steps |

Agent modules remain unchanged; only the runtime shell scales.

### Algorithm upgrades

| Agent | Production enhancement |
|-------|------------------------|
| Surplus Estimator | ML model trained on historical pickup weights |
| Matcher | OR-Tools assignment with capacity and fairness constraints |
| Logistics Planner | Full VRP with vehicle capacity, driver shifts, time windows |
| Timing Negotiator | Two-way donor/recipient confirmation via SMS or email |

### Platform

```
  Donors / Partner apps
           │
           ▼
    API Gateway (auth)
           │
           ▼
   FoodBridge service (K8s)
      │         │         │
      ▼         ▼         ▼
  PostgreSQL  Job queue  Audit storage
  (PostGIS)
```

**Operations:** metrics on match rate, route km saved, small-org share; structured agent-step logging; coordinator approval workflow before dispatch.

**Compliance:** long-retention audit logs; aggregate need data only (no individual tracking); PIPEDA-aligned data handling.

**Geographic expansion:** parameterized region boundaries, inspection schemas, and recipient registries per city; Biomass grids already cover Canada.

### Rollout path

1. **Pilot** — one Toronto borough, limited donor and shelter cohort, volunteer fleet.
2. **Municipal** — live Dinesafe sync via public-health partnership.
3. **Regional / national** — plug-in data adapters per province; shared agent core.

---

## Datasets

| Dataset | Location | Role |
|---------|----------|------|
| Toronto Dinesafe | `data/dinesafe/Dinesafe.csv` | Donor registry, inspection status, coordinates |
| Canada Biomass MSW | `data/biomass/BIOMASS_MSW_INV.csv` | Surplus and need pressure by grid |
| GDELT food security | `data/huggingface/gdelt/` or sample CSV | Regional urgency signals |
| Supply chain (optional) | `data/huggingface/supply_chain/` or sample CSV | Disruption-based surplus boost |

```bash
python scripts/download_datasets.py   # optional HuggingFace download (~1.1 GB)
```

---

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python main.py --region Scarborough --top 3 --verbose          # CLI
uvicorn web.app:app --reload --port 8000                       # Web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), select a region and radius, and click **Run planning**.

**API:** `GET /api/plan?region=Regent Park&top=5&max_distance_km=15&fast=false`

---

## Ethical safeguards

- **Safety** — Pass-only donors; zero tolerance for crucial Dinesafe infractions
- **Fairness** — Small-organization recipients prioritized in the matching queue
- **Transparency** — Step-level audit trail for every agent decision
- **Environment** — Route optimizer discloses distance saved vs. random ordering
- **Accountability** — Human coordinator approval required before dispatch

---

## Project structure

```
food-bridge/
├── main.py                 # CLI
├── web/                    # Dashboard + /api/plan
├── src/
│   ├── orchestrator.py
│   ├── agents/             # Seven specialized agents
│   ├── data_loader.py
│   ├── models.py
│   └── serialize.py
├── data/dinesafe/
├── data/biomass/
└── scripts/
```

---

## Attribution

CREATE-a-Thon — Group 1. Data: Toronto Open Data (Dinesafe), Natural Resources Canada (Biomass), HuggingFace (GDELT, supply chain).
