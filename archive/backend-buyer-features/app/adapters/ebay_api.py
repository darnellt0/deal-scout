from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, List

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
EBAY_FINDING_API = "https://svcs.ebay.com/services/search/FindingService/v1"


def fetch_listings(keywords: Iterable[str]) -> List[dict]:
    """Fetch listings from the eBay Finding API (Best Match)."""
    settings = get_settings()
    keyword_query = " ".join(keywords)
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": settings.ebay_app_id or "sample",
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "true",
        "keywords": keyword_query,
        "buyerPostalCode": "95113",
        "itemFilter(0).name": "MaxDistance",
        "itemFilter(0).value": settings.default_radius_mi,
        "itemFilter(1).name": "LocatedIn",
        "itemFilter(1).value": "US",
    }

    items: List[dict] = []

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(EBAY_FINDING_API, params=params)
            response.raise_for_status()
            data = response.json()
            items = _extract_items(data)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.info("eBay API unavailable, using fallback data: %s", exc)
        items = _fallback_items()

    return items


def _extract_items(payload: dict) -> List[dict]:
    listings = []
    try:
        results = payload["findItemsByKeywordsResponse"][0]["searchResult"][0][
            "item"
        ]
    except (KeyError, IndexError):
        return listings

    for item in results:
        selling = item.get("sellingStatus", [{}])[0]
        price_info = selling.get("currentPrice", [{"__value__": "0"}])[0]
        title = item.get("title", ["Untitled"])[0]
        listings.append(
            {
                "id": item.get("itemId", ["0"])[0],
                "source": "ebay",
                "title": title,
                "description": item.get("subtitle", [""])[0],
                "price": float(price_info.get("__value__", 0)),
                "condition": item.get("condition", [{"conditionDisplayName": "Good"}])[0]
                .get("conditionDisplayName", "Good")
                .lower(),
                "url": item.get("viewItemURL", [""])[0],
                "thumbnail": item.get("galleryURL", [""])[0],
                "coords": (37.3382, -121.8863),
                "posted_at": datetime.now(timezone.utc),
            }
        )
    return listings


def _fallback_items() -> List[dict]:
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "ebay-couch-123",
            "source": "ebay",
            "title": "Modern Gray Sectional Couch",
            "description": "Gently used sectional in great condition.",
            "price": 120.0,
            "condition": "great",
            "url": "https://ebay.com/sample-couch",
            "thumbnail": None,
            "coords": (37.3882, -121.9449),
            "posted_at": now,
        },
        {
            "id": "ebay-island-456",
            "source": "ebay",
            "title": "Kitchen Island with Storage",
            "description": "Sturdy island with butcher block top.",
            "price": 250.0,
            "condition": "good",
            "url": "https://ebay.com/sample-island",
            "thumbnail": None,
            "coords": (37.3041, -121.8729),
            "posted_at": now,
        },
    ]
