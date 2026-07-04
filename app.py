"""FastAPI application for the Food Bridge PoC."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from food_bridge.orchestrator import FoodBridgeOrchestrator

app = FastAPI(
    title="Food Bridge",
    description="Multi-agent food waste redistribution proof of concept",
    version="0.1.0",
)

orchestrator = FoodBridgeOrchestrator()
STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "food-bridge"}


@app.get("/api/stats")
def dataset_stats():
    data = orchestrator.data
    return {
        "dinesafe_establishments": len(data.establishments),
        "biomass_grids": len(data.biomass_grids),
        "datasets": {
            "dinesafe": "Datasets/Dinesafe/Dinesafe.csv",
            "biomass": "Datasets/Biomass Canada/BIOMASS_MSW_INV.csv",
        },
    }


@app.post("/api/pipeline/run")
@app.get("/api/pipeline/run")
def run_pipeline(
    max_donors: int = Query(80, ge=10, le=500),
    max_recipients: int = Query(20, ge=5, le=100),
    max_allocations: int = Query(15, ge=1, le=50),
    max_distance_km: float = Query(12.0, ge=1.0, le=50.0),
    refresh: bool = Query(False),
):
    result = orchestrator.run(
        max_donors=max_donors,
        max_recipients=max_recipients,
        max_allocations=max_allocations,
        max_distance_km=max_distance_km,
        force_refresh=refresh,
    )
    return result.model_dump(mode="json")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
