from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Iterable

from app.config import get_settings


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in miles between two coordinates."""
    radius_mi = 3958.8
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_mi * c


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_keywords(keywords: Iterable[str]) -> list[str]:
    return sorted({kw.strip().lower() for kw in keywords if kw})


def load_default_preferences() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "radius_mi": settings.default_radius_mi,
        "city": settings.default_city,
        "min_condition": "good",
        "max_price_couch": 150,
        "max_price_kitchen_island": 300,
        "keywords_include": settings.default_keywords,
        "notify_channels": ["email"],
    }
