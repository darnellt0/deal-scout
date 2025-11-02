from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from sqlalchemy import select

from app.buyer.search import SAN_JOSE_COORDS
from app.core.db import get_session
from app.core.models import Comp, Condition, Listing, ListingScore
from app.core.scoring import DealScoreContext, compute_deal_score
from app.core.utils import haversine_distance

FIXTURE_CONDITION_MAP = {
    "like_new": Condition.excellent,
    "excellent": Condition.excellent,
    "great": Condition.great,
    "good": Condition.good,
    "fair": Condition.fair,
    "poor": Condition.poor,
}


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _normalized_condition(value: str) -> Condition:
    return FIXTURE_CONDITION_MAP.get(value.lower(), Condition.good)


def load_listings_from_fixture(path: str | Path) -> Tuple[int, int]:
    file_path = Path(path)
    data = json.loads(file_path.read_text(encoding="utf-8"))
    inserted = 0
    updated = 0

    with get_session() as session:
        for entry in data:
            condition_enum = _normalized_condition(entry.get("condition", "good"))
            price_dollars = (entry.get("price_cents") or 0) / 100.0
            lat = entry.get("lat") or SAN_JOSE_COORDS[0]
            lng = entry.get("lng") or SAN_JOSE_COORDS[1]
            coords = (lat, lng)

            listing = (
                session.execute(
                    select(Listing).where(
                        Listing.source == entry["source"],
                        Listing.source_id == entry["source_id"],
                    )
                )
                .scalars()
                .one_or_none()
            )

            location_payload = {
                "coords": coords,
                "location_text": entry.get("location_text"),
                "raw": {"fixture": True},
            }

            thumbnail = entry.get("images", [None])[0]

            if listing:
                listing.title = entry.get("title", listing.title)
                listing.description = entry.get("description", listing.description)
                listing.price = price_dollars
                listing.condition = condition_enum
                listing.category = entry.get("category")
                listing.url = entry.get("url", listing.url)
                listing.thumbnail_url = thumbnail
                listing.location = location_payload
                listing.available = entry.get("availability", "active") == "active"
                updated += 1
            else:
                listing = Listing(
                    source=entry["source"],
                    source_id=entry["source_id"],
                    title=entry["title"],
                    description=entry.get("description"),
                    price=price_dollars,
                    condition=condition_enum,
                    category=entry.get("category"),
                    url=entry.get("url"),
                    thumbnail_url=thumbnail,
                    location=location_payload,
                    available=entry.get("availability", "active") == "active",
                )
                session.add(listing)
                session.flush()
                inserted += 1

            posted_at = _parse_datetime(
                entry.get("posted_at", datetime.now(timezone.utc).isoformat())
            )
            distance = haversine_distance(*coords, *SAN_JOSE_COORDS)
            deal_score = compute_deal_score(
                DealScoreContext(
                    price=price_dollars,
                    condition=condition_enum.value,
                    posted_at=posted_at,
                    coords=coords,
                    user_coords=SAN_JOSE_COORDS,
                    has_photos=bool(thumbnail),
                    is_free=price_dollars == 0,
                )
            )

            score_entry = (
                session.execute(
                    select(ListingScore).where(
                        ListingScore.listing_id == listing.id,
                        ListingScore.metric == "deal_score",
                    )
                )
                .scalars()
                .one_or_none()
            )

            snapshot = {
                "distance_mi": round(distance, 2),
                "price": price_dollars,
                "condition": condition_enum.value,
            }

            if score_entry:
                score_entry.value = deal_score
                score_entry.snapshot = snapshot
            else:
                session.add(
                    ListingScore(
                        listing_id=listing.id,
                        metric="deal_score",
                        value=deal_score,
                        snapshot=snapshot,
                    )
                )

    return inserted, updated


def load_comps_from_fixture(category: str, path: str | Path) -> int:
    file_path = Path(path)
    payload = json.loads(file_path.read_text(encoding="utf-8"))

    inserted = 0
    category_lower = category.lower()
    with get_session() as session:
        # remove existing fixture comps for category
        session.query(Comp).filter(
            Comp.category == category_lower, Comp.meta.contains({"fixture": True})
        ).delete(synchronize_session=False)

        for condition_name, stats in payload.get("condition_buckets", {}).items():
            comp = Comp(
                category=category_lower,
                title=f"{condition_name.title()} median snapshot",
                price=stats["median_price_cents"] / 100.0,
                condition=_normalized_condition(condition_name),
                source="fixture",
                meta={"fixture": True, "stats": stats},
            )
            session.add(comp)
            inserted += 1

        for example in payload.get("examples", []):
            comp = Comp(
                category=category_lower,
                title=example["title"],
                price=example["price_cents"] / 100.0,
                condition=_normalized_condition("good"),
                source="fixture",
                meta={
                    "fixture": True,
                    "url": example.get("url"),
                },
            )
            session.add(comp)
            inserted += 1

    return inserted
