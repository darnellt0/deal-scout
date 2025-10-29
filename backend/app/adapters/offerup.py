from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, List

logger = logging.getLogger(__name__)


def fetch_listings(keywords: Iterable[str]) -> List[dict]:
    """OfferUp does not have an official API, provide a mock integration hook."""
    keyword_list = list(keywords)
    logger.debug("OfferUp fetch stub triggered with keywords=%s", keyword_list)
    now = datetime.now(timezone.utc)

    return [
        {
            "id": f"offerup-{idx}",
            "source": "offerup",
            "title": f"{keyword.title()} - Curbside Pickup",
            "description": f"Auto generated OfferUp listing for {keyword}",
            "price": 0,
            "condition": "good",
            "url": "https://offerup.com/item/sample",
            "thumbnail": None,
            "coords": (37.32 + idx * 0.01, -121.88),
            "posted_at": now,
        }
        for idx, keyword in enumerate(keyword_list[:2])
    ]
