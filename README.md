# FoodBridge CLI

Multi-agent food waste redistribution prototype for CREATE-a-Thon Group 1.

Uses **real Toronto Dinesafe** and **Canada Biomass** data from this folder, plus HuggingFace GDELT and supply-chain datasets.

## Quick start

```bash
cd /Users/kawsar/Desktop/food-bridge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_datasets.py   # ~1.1 GB GDELT + supply chain CSVs

python main.py
python main.py --region Scarborough
python main.py --top 3 --verbose
python main.py --fast
```

## Web app

```bash
pip install -r requirements.txt
uvicorn web.app:app --reload --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) — pick a region, set options, and click **Run planning**. The UI shows the priority zone, agent pipeline, matches, pickup route, ethics report, and an interactive map.

## Agents & datasets

| Agent | Dataset |
|-------|---------|
| Surplus Estimator | `data/biomass/BIOMASS_MSW_INV.csv` + [global-food-supply-chain-models-and-data](https://huggingface.co/datasets/IshaanPotle27/global-food-supply-chain-models-and-data) |
| Need Prioritizer | [gdelt-food-security-data](https://huggingface.co/datasets/Laurieqq/gdelt-food-security-data) |
| Donor Scout | `data/dinesafe/Dinesafe.csv` |
| Matcher | Combined agent outputs |
| Logistics Planner | `data/dinesafe/Dinesafe.csv` (coordinates) |
| Ethics Guardian | Dinesafe status + fairness rules |

## CLI options

| Flag | Description |
|------|-------------|
| `--region` | Focus on Scarborough, Regent Park, Downtown Toronto, etc. |
| `--top N` | Show top N matches (default 5) |
| `--fast` | Smaller donor pool for quicker demo |
| `--verbose` | Show dataset source per agent |

## Files

```
food-bridge/
├── main.py              # CLI entry point
├── web/
│   ├── app.py           # FastAPI web app
│   ├── templates/
│   └── static/
├── data/
│   ├── dinesafe/        # Toronto Dinesafe CSV + docs
│   ├── biomass/         # Canada biomass CSV + docs
│   ├── huggingface/     # Downloaded HF datasets (gitignored)
│   ├── processed/       # Cached transforms (gitignored)
│   ├── sample_gdelt_food_security.csv
│   └── sample_supply_chain_signals.csv
├── scripts/
│   └── download_datasets.py
└── src/                 # Agents + orchestrator
```

## HuggingFace datasets

Download once (~1.1 GB):

```bash
python scripts/download_datasets.py
```

| Dataset | HF repo | Local path |
|---------|---------|------------|
| GDELT food security | `Laurieqq/gdelt-food-security-data` | `data/huggingface/gdelt/data/` |
| Supply chain | `IshaanPotle27/global-food-supply-chain-models-and-data` | `data/huggingface/supply_chain/` |

Raw HF files are transformed on first run into `data/processed/` for the agents. Sample CSVs in `data/` are used only as fallback if downloads are missing.

## Note on Biomass

Biomass grid cells have no lat/long in the CSV. The Surplus Estimator uses the **national organic waste distribution** as a baseline, then scores Toronto regions by food-premise density and establishment type from Dinesafe.
