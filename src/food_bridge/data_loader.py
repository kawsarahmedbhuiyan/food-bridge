"""Load and preprocess Dinesafe and Biomass Canada datasets."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from food_bridge.geo import grid_id_to_coordinates, in_toronto_bounds
from food_bridge.models import Establishment

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DINESAFE_PATH = PROJECT_ROOT / "Datasets" / "Dinesafe" / "Dinesafe.csv"
BIOMASS_PATH = PROJECT_ROOT / "Datasets" / "Biomass Canada" / "BIOMASS_MSW_INV.csv"

CRUCIAL_SEVERITY = "C - Crucial"
RECENT_MONTHS = 12


@dataclass
class BiomassGrid:
    grid_id: int
    total_volume: float
    organic_volume: float
    paper_volume: float
    latitude: float
    longitude: float


@dataclass
class LoadedData:
    establishments: list[Establishment] = field(default_factory=list)
    biomass_grids: list[BiomassGrid] = field(default_factory=list)
    grid_coords: dict[int, tuple[float, float]] = field(default_factory=dict)


def load_biomass() -> list[BiomassGrid]:
    grids: list[BiomassGrid] = []
    with BIOMASS_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            grid_id = int(row["BIOMASS_GRID_ID"])
            lat, lon = grid_id_to_coordinates(grid_id)
            grids.append(
                BiomassGrid(
                    grid_id=grid_id,
                    total_volume=float(row["MNCPL_SOLID_WASTE_TOTAL_VOL"]),
                    organic_volume=float(row["MNCPL_SOLID_WASTE_ORGANIC_VOL"]),
                    paper_volume=float(row["MNCPL_SOLID_WASTE_PAPER_VOL"]),
                    latitude=lat,
                    longitude=lon,
                )
            )
    return grids


def load_establishments() -> list[Establishment]:
    """Aggregate Dinesafe rows to one record per establishment with infraction counts."""
    latest: dict[str, dict] = {}
    crucial_counts: dict[str, int] = defaultdict(int)
    minor_counts: dict[str, int] = defaultdict(int)

    with DINESAFE_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            eid = row["estId"]
            inspection_date = row["inspectionDate"]

            if row["severity"] == CRUCIAL_SEVERITY:
                crucial_counts[eid] += 1
            elif row["severity"] and "Minor" in row["severity"]:
                minor_counts[eid] += 1

            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
            except (TypeError, ValueError):
                continue

            if not in_toronto_bounds(lat, lon):
                continue

            if eid not in latest or inspection_date > latest[eid]["date"]:
                latest[eid] = {
                    "date": inspection_date,
                    "status": row["inspectionStatus"],
                    "name": row["estName"],
                    "address": row["address"],
                    "lat": lat,
                    "lon": lon,
                }

    establishments: list[Establishment] = []
    for eid, info in latest.items():
        establishments.append(
            Establishment(
                est_id=eid,
                name=info["name"],
                address=info["address"],
                latitude=info["lat"],
                longitude=info["lon"],
                latest_inspection_date=info["date"],
                latest_inspection_status=info["status"],
                crucial_infractions_recent=min(crucial_counts[eid], 5),
                minor_infractions_recent=min(minor_counts[eid], 20),
            )
        )
    return establishments


def load_all_data() -> LoadedData:
    biomass = load_biomass()
    grid_coords = {g.grid_id: (g.latitude, g.longitude) for g in biomass}
    establishments = load_establishments()
    return LoadedData(
        establishments=establishments,
        biomass_grids=biomass,
        grid_coords=grid_coords,
    )
