"""Map Toronto coordinates to named regions for agent scoring."""

CHAIN_KEYWORDS = (
    "walmart", "costco", "loblaws", "metro", "sobeys", "no frills",
    "food basics", "freshco", "superstore", "longo's", "whole foods",
)


def lat_lon_to_region(lat: float, lon: float) -> str:
    if lat > 43.74 and lon > -79.42:
        return "North York"
    if lat < 43.68 and lon > -79.22:
        return "Scarborough"
    if lon < -79.50:
        return "Etobicoke"
    if 43.65 <= lat <= 43.68 and -79.37 <= lon <= -79.35:
        return "Regent Park"
    if lat > 43.68 and -79.35 <= lon <= -79.22:
        return "East York"
    if lat >= 43.64 and lon >= -79.40:
        return "Downtown Toronto"
    return "Toronto"


def infer_establishment_type(name: str) -> str:
    lower = name.lower()
    if any(k in lower for k in ("grocery", "market", "supermarket", "superstore", "freshco", "loblaws", "sobeys", "metro", "no frills")):
        return "Grocery"
    if any(k in lower for k in ("cafeteria", "cafe", "coffee")):
        return "Cafeteria"
    if any(k in lower for k in ("bakery", "pizza", "restaurant", "grill", "kitchen", "bistro")):
        return "Restaurant"
    return "Food Premise"


def is_chain_donor(name: str) -> bool:
    lower = name.lower()
    return any(k in lower for k in CHAIN_KEYWORDS)
