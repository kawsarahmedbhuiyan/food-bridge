from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import pandas as pd

from src.geo import infer_establishment_type, lat_lon_to_region
from src.models import Donor, Recipient

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
HF_DIR = DATA_DIR / "huggingface"
PROCESSED_DIR = DATA_DIR / "processed"

SUPPLY_CHAIN_RAW = HF_DIR / "supply_chain" / "food_supply_chain_data.csv"
GDELT_DIR = HF_DIR / "gdelt" / "data"
GDELT_NEED_CACHE = PROCESSED_DIR / "gdelt_need_events.csv"
SUPPLY_CHAIN_CACHE = PROCESSED_DIR / "supply_chain_signals.csv"

RECIPIENTS = [
    Recipient("East End Community Kitchen", "Scarborough", 43.7200, -79.2650, 120),
    Recipient("Regent Park Food Hub", "Regent Park", 43.6580, -79.3580, 80),
    Recipient("North York Shelter Meals", "North York", 43.7680, -79.4150, 100),
    Recipient("Etobicoke Community Pantry", "Etobicoke", 43.6400, -79.5250, 90),
    Recipient("Downtown Emergency Kitchen", "Downtown Toronto", 43.6520, -79.3840, 150),
    Recipient("East York Community Meals", "East York", 43.6900, -79.3300, 85),
]

SAFE_STATUSES = {"Pass", "Conditional Pass"}

FOOD_EVENT_TYPES = {
    "FOOD_SECURITY": "food_insecurity",
    "FOOD_BANK": "food_bank_shortage",
    "UNGP_AFFORDABLE_NUTRITIOUS_FOOD": "food_insecurity",
    "AGRICULTURE": "surplus_waste",
    "COMMUNITY_KITCHEN": "community_kitchen",
}


def _parse_gdelt_date(value: int | str) -> str:
    digits = re.sub(r"\D", "", str(value))
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return str(value)


def _parse_gdelt_tone(tone: str | float | None) -> float:
    if tone is None or (isinstance(tone, float) and pd.isna(tone)):
        return 5.0
    first = str(tone).split(",")[0].strip()
    try:
        return round(min(10.0, max(1.0, abs(float(first)) + 3.0)), 1)
    except ValueError:
        return 5.0


def _headline_from_url(url: str) -> str:
    if not url or pd.isna(url):
        return "Food security event"
    path = unquote(urlparse(str(url)).path)
    slug = path.rstrip("/").split("/")[-1]
    slug = re.sub(r"\.[a-z0-9]+$", "", slug, flags=re.I)
    slug = slug.replace("_", " ").replace("-", " ")
    return slug[:120] if slug else "Food security event"


def _event_type_from_themes(themes: str) -> str:
    upper = str(themes).upper()
    for key, label in FOOD_EVENT_TYPES.items():
        if key in upper:
            return label
    if "INSECURITY" in upper or "HUNGER" in upper:
        return "food_insecurity"
    if "WASTE" in upper or "SURPLUS" in upper:
        return "surplus_waste"
    return "food_insecurity"


def _first_location_segment(locations: str, v2_locations: str) -> str:
    for field in (v2_locations, locations):
        if field and not (isinstance(field, float) and pd.isna(field)):
            part = str(field).split(";")[0]
            if part:
                return part
    return ""


def _region_from_gdelt_row(locations: str, v2_locations: str) -> str | None:
    primary = _first_location_segment(locations, v2_locations)
    if not primary:
        return None

    matches = re.findall(r"#([\d.-]+)#([\d.-]+)#", primary)
    for lat_s, lon_s in matches:
        lat, lon = float(lat_s), float(lon_s)
        if 43.58 <= lat <= 43.85 and -79.65 <= lon <= -79.10:
            return lat_lon_to_region(lat, lon)

    if re.search(r"Toronto, Ontario|Toronto, Canada", primary):
        return "Downtown Toronto"
    return None


def _transform_gdelt(raw_dir: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("gdelt_*.csv"))
    if not files:
        raise FileNotFoundError(f"No GDELT CSV files in {raw_dir}")

    frames: list[pd.DataFrame] = []
    usecols = ["DATE", "DocumentIdentifier", "Themes", "Locations", "V2Locations", "V2Tone"]
    for path in files:
        frames.append(pd.read_csv(path, usecols=usecols, low_memory=False))

    raw = pd.concat(frames, ignore_index=True)
    rows: list[dict[str, object]] = []
    for row in raw.itertuples(index=False):
        region = _region_from_gdelt_row(row.Locations, row.V2Locations)
        if region is None:
            continue
        rows.append(
            {
                "date": _parse_gdelt_date(row.DATE),
                "region": region,
                "event_type": _event_type_from_themes(row.Themes),
                "severity_score": _parse_gdelt_tone(row.V2Tone),
                "headline_summary": _headline_from_url(row.DocumentIdentifier),
            }
        )

    if not rows:
        sample = DATA_DIR / "sample_gdelt_food_security.csv"
        if sample.exists():
            return pd.read_csv(sample)
        raise ValueError("No Toronto/Ontario GDELT rows matched")

    df = pd.DataFrame(rows)
    return df.sort_values(["date", "severity_score"], ascending=[False, False]).reset_index(drop=True)


def _transform_supply_chain(raw_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(raw_path)
    rows: list[dict[str, object]] = []
    for row in raw.itertuples(index=False):
        signals: list[tuple[str, float, str]] = []
        if getattr(row, "supply_chain_disruption", 0):
            signals.append(
                (
                    "supply_chain_disruption",
                    max(float(row.disruption_risk), 0.6),
                    "Supply chain disruption flagged in HF model data",
                )
            )
        if getattr(row, "extreme_weather_event", 0):
            signals.append(
                (
                    "extreme_weather",
                    0.7,
                    f"Extreme weather event (temp {row.temperature_celsius:.1f}°C)",
                )
            )
        if getattr(row, "border_closure_days", 0) > 0:
            signals.append(
                (
                    "border_closure",
                    min(1.0, 0.5 + row.border_closure_days * 0.2),
                    f"Border closure lasting {int(row.border_closure_days)} day(s)",
                )
            )
        if getattr(row, "food_safety_incidents", 0) > 0:
            signals.append(
                (
                    "food_safety",
                    min(1.0, 0.4 + row.food_safety_incidents * 0.2),
                    f"{int(row.food_safety_incidents)} food safety incident(s) reported",
                )
            )
        if getattr(row, "disruption_risk", 0) >= 0.5 and not signals:
            signals.append(
                (
                    "transport_delay",
                    float(row.disruption_risk),
                    "Elevated disruption risk in supply chain indicators",
                )
            )

        for disruption_type, severity, description in signals:
            rows.append(
                {
                    "date": row.date,
                    "region_hint": "GTA",
                    "disruption_type": disruption_type,
                    "severity": round(severity, 2),
                    "description": description,
                }
            )

    if not rows:
        raise ValueError("No supply chain disruption signals found")

    df = pd.DataFrame(rows)
    return df.sort_values(["date", "severity"], ascending=[False, False]).reset_index(drop=True)


def _load_cached_or_build(
    cache_path: Path,
    source_mtime: float,
    builder,
) -> pd.DataFrame:
    if cache_path.exists() and cache_path.stat().st_mtime >= source_mtime:
        return pd.read_csv(cache_path)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = builder()
    df.to_csv(cache_path, index=False)
    return df


def load_donors(limit: int | None = None) -> list[Donor]:
    path = DATA_DIR / "dinesafe" / "Dinesafe.csv"
    df = pd.read_csv(path, low_memory=False)
    df["inspectionDate"] = pd.to_datetime(df["inspectionDate"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    latest = df.sort_values("inspectionDate").groupby("estId", as_index=False).tail(1)
    latest = latest[latest["inspectionStatus"].isin(SAFE_STATUSES)]

    donors: list[Donor] = []
    for row in latest.itertuples(index=False):
        region = lat_lon_to_region(float(row.latitude), float(row.longitude))
        donors.append(
            Donor(
                establishment_id=str(row.estId),
                name=str(row.estName).strip(),
                address=str(row.address),
                establishment_type=infer_establishment_type(str(row.estName)),
                inspection_result=str(row.inspectionStatus),
                latitude=float(row.latitude),
                longitude=float(row.longitude),
                region=region,
            )
        )

    if limit:
        donors.sort(key=lambda d: (d.establishment_type != "Grocery", d.name))
        return donors[:limit]
    return donors


def load_biomass() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "biomass" / "BIOMASS_MSW_INV.csv")


def load_need_events() -> pd.DataFrame:
    sample = DATA_DIR / "sample_gdelt_food_security.csv"
    if GDELT_DIR.exists() and any(GDELT_DIR.glob("gdelt_*.csv")):
        newest = max(p.stat().st_mtime for p in GDELT_DIR.glob("gdelt_*.csv"))
        return _load_cached_or_build(
            GDELT_NEED_CACHE,
            newest,
            lambda: _transform_gdelt(GDELT_DIR),
        )
    if sample.exists():
        return pd.read_csv(sample)
    raise FileNotFoundError(
        "GDELT data not found. Run: python scripts/download_datasets.py"
    )


def load_supply_chain_signals() -> pd.DataFrame:
    sample = DATA_DIR / "sample_supply_chain_signals.csv"
    if SUPPLY_CHAIN_RAW.exists():
        source_mtime = SUPPLY_CHAIN_RAW.stat().st_mtime
        return _load_cached_or_build(
            SUPPLY_CHAIN_CACHE,
            source_mtime,
            lambda: _transform_supply_chain(SUPPLY_CHAIN_RAW),
        )
    if sample.exists():
        return pd.read_csv(sample)
    return pd.DataFrame(columns=["disruption_type", "severity", "description"])


def load_recipients() -> list[Recipient]:
    return RECIPIENTS.copy()
