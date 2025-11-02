from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from app.adapters.craigslist_rss import fetch_listings as fetch_craigslist
from app.adapters.ebay_api import fetch_listings as fetch_ebay
from app.adapters.facebook_marketplace import fetch_listings as fetch_facebook
from app.adapters.offerup import fetch_listings as fetch_offerup
from app.config import get_settings
from app.core.db import get_session
from app.core.models import Condition, Listing, ListingScore
from app.core.scoring import DealScoreContext, compute_deal_score
from app.core.utils import load_default_preferences

logger = logging.getLogger(__name__)

SAN_JOSE_COORDS = (37.3382, -121.8863)
CONDITION_ORDER = {
    "poor": 0,
    "fair": 1,
    "good": 2,
    "great": 3,
    "excellent": 4,
}


@dataclass
class ListingMatch:
    id: int
    title: str
    price: float
    condition: str
    category: str
    url: str
    thumbnail_url: Optional[str]
    distance_mi: float
    deal_score: float
    is_free: bool
    source: str
    auto_message: str


def _normalize_condition(raw: str | None) -> str:
    if not raw:
        return "good"
    raw_lower = raw.lower().replace("_", " ")
    mapping = {
        "like new": "excellent",
        "new": "excellent",
        "good": "good",
        "great": "great",
        "excellent": "excellent",
        "fair": "fair",
    }
    for key, value in mapping.items():
        if key in raw_lower:
            return value
    return "good"


def _within_keywords(title: str, keywords: Iterable[str]) -> bool:
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in keywords)


def _normalize_payload(payload: dict, keywords: Iterable[str]) -> Optional[dict]:
    title = payload.get("title", "")
    if not _within_keywords(title, keywords):
        return None

    condition = _normalize_condition(payload.get("condition"))
    if CONDITION_ORDER.get(condition, 0) < CONDITION_ORDER["good"]:
        return None

    price = float(payload.get("price", 0) or 0)
    if price > 0 and price < 5:  # treat suspicious low numbers as free
        price = 0

    coords = payload.get("coords") or SAN_JOSE_COORDS
    return {
        "source": payload.get("source", "unknown"),
        "source_id": payload.get("id") or payload.get("source_id"),
        "title": title,
        "description": payload.get("description"),
        "price": price,
        "condition": condition,
        "category": payload.get("category") or _infer_category(title),
        "url": payload.get("url"),
        "thumbnail_url": payload.get("thumbnail"),
        "coords": coords,
        "posted_at": payload.get("posted_at") or datetime.now(timezone.utc),
    }


def collect_candidates(use_live: bool = True) -> List[dict]:
    settings = get_settings()
    keywords = settings.default_keywords
    candidates: List[dict] = []

    if not use_live and settings.demo_mode:
        return _load_fixture_candidates()

    for fetcher in (
        fetch_craigslist,
        fetch_ebay,
        fetch_offerup,
        fetch_facebook,
    ):
        try:
            for payload in fetcher(keywords=keywords):
                normalized = _normalize_payload(payload, keywords)
                if normalized:
                    candidates.append(normalized)
        except Exception as exc:  # pragma: no cover - external fetchers may fail
            logger.exception("Fetcher %s failed: %s", fetcher.__name__, exc)
    return candidates


def _load_fixture_candidates(limit: int = 250) -> List[dict]:
    settings = get_settings()
    candidates: List[dict] = []
    fixture_names = ["listings.couches.json", "listings.kitchen_islands.json"]
    for name in fixture_names:
        path = settings.static_data_dir / "fixtures" / name
        if not path.exists():
            fallback = (
                Path(__file__).resolve().parents[3] / "data" / "fixtures" / name
            )
            if fallback.exists():
                path = fallback
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for entry in data[:limit]:
            posted_at = entry.get("posted_at")
            try:
                posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            except Exception:
                posted_dt = datetime.now(timezone.utc)
            coords = (entry.get("lat"), entry.get("lng"))
            candidates.append(
                {
                    "source": "craigslist",
                    "source_id": entry["source_id"],
                    "title": entry["title"],
                    "description": entry.get("description"),
                    "price": (entry.get("price_cents", 0) or 0) / 100.0,
                "condition": _normalize_condition(entry.get("condition", "good")),
                    "category": entry.get("category"),
                    "url": entry.get("url"),
                    "thumbnail_url": (entry.get("images") or [None])[0],
                    "coords": coords if all(coords) else SAN_JOSE_COORDS,
                    "posted_at": posted_dt,
                }
            )
    return candidates


def store_candidates(candidates: List[dict]) -> List[ListingMatch]:
    from app.core.utils import haversine_distance
    from app.buyer.templates import load_template

    template_text = load_template()
    settings = get_settings()
    matches: List[ListingMatch] = []

    with get_session() as session:
        for candidate in candidates:
            condition_value = _normalize_condition(candidate.get("condition"))
            candidate["condition"] = condition_value
            existing = (
                session.query(Listing)
                .filter_by(source=candidate["source"], source_id=candidate["source_id"])
                .one_or_none()
            )

            if existing:
                listing = existing
                listing.last_seen_at = datetime.now(timezone.utc)
                listing.available = True
            else:
                listing = Listing(
                    source=candidate["source"],
                    source_id=candidate["source_id"],
                    title=candidate["title"],
                    description=candidate.get("description"),
                    price=candidate["price"],
                    condition=Condition(condition_value),
                    category=candidate.get("category"),
                    url=candidate["url"],
                    thumbnail_url=candidate.get("thumbnail_url"),
                    location={"coords": candidate["coords"]},
                )
                session.add(listing)
                session.flush()  # ensure id for relationships

            coords = candidate["coords"] or SAN_JOSE_COORDS
            if coords[0] is None or coords[1] is None:
                coords = SAN_JOSE_COORDS
            distance = haversine_distance(*coords, *SAN_JOSE_COORDS)
            deal_score = compute_deal_score(
                DealScoreContext(
                    price=candidate["price"],
                    condition=condition_value,
                    posted_at=candidate["posted_at"],
                    coords=coords,
                    user_coords=SAN_JOSE_COORDS,
                    has_photos=bool(candidate.get("thumbnail_url")),
                    is_free=candidate["price"] == 0,
                    keyword=_match_keyword(candidate["title"], settings.default_keywords),
                )
            )

            session.add(
                ListingScore(
                    listing_id=listing.id,
                    metric="deal_score",
                    value=deal_score,
                    snapshot={
                        "distance_mi": distance,
                        "price": candidate["price"],
                        "condition": candidate["condition"],
                    },
                )
            )

            matches.append(
                ListingMatch(
                    id=listing.id,
                    title=listing.title,
                    price=listing.price,
                    condition=listing.condition.value if listing.condition else "unknown",
                    category=listing.category or "misc",
                    url=listing.url,
                    thumbnail_url=listing.thumbnail_url,
                    distance_mi=round(distance, 2),
                    deal_score=deal_score,
                    is_free=listing.price == 0,
                    source=listing.source,
                    auto_message=template_text,
                )
            )
    return matches


def _match_keyword(title: str, keywords: Iterable[str]) -> Optional[str]:
    lower = title.lower()
    for keyword in keywords:
        if keyword in lower:
            return keyword
    return None


def _infer_category(title: str) -> str:
    title_lower = title.lower()
    if any(term in title_lower for term in ("couch", "sofa", "sectional")):
        return "furniture>sofas"
    if "island" in title_lower:
        return "kitchen>islands"
    return "misc"


def run_scan(use_live: bool = True) -> List[ListingMatch]:
    prefs = load_default_preferences()
    candidates = collect_candidates(use_live=use_live)
    matches = store_candidates(candidates)

    filtered: List[ListingMatch] = []
    for match in matches:
        if match.is_free:
            filtered.append(match)
            continue
        if match.deal_score >= 75:
            filtered.append(match)
        elif "couch" in match.title.lower() and match.price <= prefs["max_price_couch"]:
            filtered.append(match)
        elif (
            "kitchen island" in match.title.lower()
            and match.price <= prefs["max_price_kitchen_island"]
        ):
            filtered.append(match)
    return filtered
