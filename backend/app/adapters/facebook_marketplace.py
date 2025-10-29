from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable, List

logger = logging.getLogger(__name__)


def fetch_listings(keywords: Iterable[str]) -> List[dict]:
    """Placeholder integration that could later be replaced with PostingKit or automation."""
    now = datetime.now(timezone.utc)
    keyword_list = list(keywords)
    if not keyword_list:
        return []

    synthetic: List[dict] = []
    for keyword in keyword_list[:2]:
        synthetic.append(
            {
                "id": f"fb-{keyword}",
                "source": "facebook",
                "title": f"{keyword.title()} - Facebook Marketplace Deal",
                "description": f"Facebook Marketplace synthetic listing for {keyword}",
                "price": 50 if "couch" in keyword else 0,
                "condition": "great",
                "url": "https://facebook.com/marketplace/sample",
                "thumbnail": None,
                "coords": (37.29, -121.85),
                "posted_at": now,
            }
        )
    logger.debug("Facebook Marketplace stub returning %d items", len(synthetic))
    return synthetic
