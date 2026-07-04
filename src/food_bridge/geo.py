"""Geographic utilities for linking Dinesafe and Biomass datasets."""

from __future__ import annotations

import hashlib
import math

# Toronto bounding box (Dinesafe coverage)
TORONTO_LAT_MIN = 43.58
TORONTO_LAT_MAX = 43.85
TORONTO_LON_MIN = -79.64
TORONTO_LON_MAX = -79.11


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def grid_id_to_coordinates(grid_id: int) -> tuple[float, float]:
    """
    Map Biomass grid IDs to deterministic coordinates within Toronto.

    The Biomass CSV lacks lat/lon; this PoC uses a stable hash so grid cells
    have fixed locations for distance-based matching with Dinesafe donors.
    """
    digest = hashlib.sha256(str(grid_id).encode()).hexdigest()
    lat_frac = int(digest[:8], 16) / 0xFFFFFFFF
    lon_frac = int(digest[8:16], 16) / 0xFFFFFFFF
    lat = TORONTO_LAT_MIN + lat_frac * (TORONTO_LAT_MAX - TORONTO_LAT_MIN)
    lon = TORONTO_LON_MIN + lon_frac * (TORONTO_LON_MAX - TORONTO_LON_MIN)
    return lat, lon


def nearest_grid_id(lat: float, lon: float, grid_coords: dict[int, tuple[float, float]]) -> int:
    """Find the biomass grid closest to a point."""
    best_id, best_dist = min(
        grid_coords.items(),
        key=lambda item: haversine_km(lat, lon, item[1][0], item[1][1]),
    )
    return best_id


def in_toronto_bounds(lat: float, lon: float) -> bool:
    return TORONTO_LAT_MIN <= lat <= TORONTO_LAT_MAX and TORONTO_LON_MIN <= lon <= TORONTO_LON_MAX
