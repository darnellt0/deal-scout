from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from app.core.utils import haversine_distance


@dataclass
class DealScoreContext:
    price: float
    condition: str
    posted_at: datetime
    coords: Optional[Tuple[float, float]] = None
    user_coords: Optional[Tuple[float, float]] = None
    has_photos: bool = False
    is_free: bool = False
    keyword: Optional[str] = None
    distance_mi: Optional[float] = None


def condition_multiplier(condition: str) -> float:
    table = {
        "poor": 0.1,
        "fair": 0.3,
        "good": 0.6,
        "great": 0.8,
        "excellent": 1.0,
    }
    return table.get(condition.lower(), 0.5)


def _resolve_distance(ctx: DealScoreContext) -> float:
    if ctx.distance_mi is not None:
        return ctx.distance_mi
    if ctx.coords is None or ctx.user_coords is None:
        return 0.0
    return haversine_distance(*ctx.coords, *ctx.user_coords)


def _ensure_utc(dt: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def compute_deal_score(
    ctx: Optional[DealScoreContext] = None,
    *,
    price: Optional[float] = None,
    condition: Optional[str] = None,
    is_free: Optional[bool] = None,
    recency_hours: Optional[float] = None,
    has_photo: Optional[bool] = None,
    keyword_match: Optional[bool] = None,
    distance_mi: Optional[float] = None,
    posted_at: Optional[datetime] = None,
    coords: Optional[Tuple[float, float]] = None,
    user_coords: Optional[Tuple[float, float]] = None,
) -> float:
    if ctx is None:
        required = {
            "price": price,
            "condition": condition,
            "is_free": is_free,
            "recency_hours": recency_hours,
            "has_photo": has_photo,
        }
        missing = [key for key, value in required.items() if value is None]
        if missing:
            missing_args = ", ".join(missing)
            raise TypeError(
                f"compute_deal_score missing required keyword arguments: {missing_args}"
            )

        now_utc = datetime.now(timezone.utc)
        source_posted_at = (
            _ensure_utc(posted_at)
            if posted_at is not None
            else now_utc - timedelta(hours=float(recency_hours))
        )
        ctx = DealScoreContext(
            price=float(price),
            condition=str(condition),
            posted_at=source_posted_at,
            coords=coords,
            user_coords=user_coords,
            has_photos=bool(has_photo),
            is_free=bool(is_free),
            keyword="keyword_match" if keyword_match else None,
            distance_mi=distance_mi,
        )

    distance = _resolve_distance(ctx)
    distance_score = max(0.0, 1 - (distance / 50))
    condition_score = condition_multiplier(ctx.condition)
    posted_at = _ensure_utc(ctx.posted_at)
    recency_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
    recency_score = max(0.0, 1 - (recency_hours / 72))
    photo_score = 1.0 if ctx.has_photos else 0.5
    price_score = 1.0 if ctx.is_free else max(0.0, 1 - ctx.price / 300)
    keyword_bonus = 0.1 if ctx.keyword else 0.0

    raw = (
        (price_score * 3)
        + (condition_score * 2)
        + (recency_score * 2)
        + distance_score
        + photo_score
        + keyword_bonus
    )
    return round(min(raw / 9 * 100, 100), 2)
