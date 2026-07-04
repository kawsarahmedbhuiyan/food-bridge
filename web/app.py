"""FoodBridge web app — FastAPI UI over the multi-agent orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.orchestrator import FoodBridgeOrchestrator  # noqa: E402
from src.serialize import plan_to_dict  # noqa: E402

REGIONS = [
    "Scarborough",
    "Regent Park",
    "Downtown Toronto",
    "North York",
    "Etobicoke",
    "East York",
]

WEB_DIR = Path(__file__).resolve().parent
app = FastAPI(title="FoodBridge", description="Agentic food rescue coordinator")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"regions": REGIONS},
    )


@app.get("/api/plan")
async def get_plan(
    region: Optional[str] = Query(default=None),
    top: int = Query(default=5, ge=1, le=20),
    fast: bool = Query(default=False),
    max_distance_km: float = Query(default=15.0, ge=1.0, le=50.0),
) -> dict:
    if region and region not in REGIONS:
        region = None

    plan = FoodBridgeOrchestrator().run(
        focus_region=region,
        top_matches=top,
        donor_pool_limit=3000 if fast else None,
        max_distance_km=max_distance_km,
    )
    return plan_to_dict(plan)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)
