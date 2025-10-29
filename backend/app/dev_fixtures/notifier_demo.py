from __future__ import annotations

from typing import List

from sqlalchemy import desc, select

from app.core.db import get_session
from app.core.models import Listing, ListingScore, Notification


def create_demo_notifications(sample_n: int = 5) -> int:
    """Create demo notifications using top scoring fixture deals."""
    created = 0
    with get_session() as session:
        session.query(Notification).filter(Notification.channel == "demo").delete()
        results = (
            session.execute(
                select(Listing, ListingScore)
                .join(ListingScore, Listing.id == ListingScore.listing_id)
                .where(ListingScore.metric == "deal_score")
                .order_by(desc(ListingScore.value))
                .limit(sample_n)
            )
            .all()
        )

        for listing, score in results:
            payload = {
                "title": listing.title,
                "price": listing.price,
                "deal_score": score.value,
                "distance_mi": score.snapshot.get("distance_mi"),
                "thumbnail_url": listing.thumbnail_url,
                "url": listing.url,
                "auto_message": "Hi! Is this still available? I can pick up today.",
                "source": listing.source,
                "fixture": True,
            }
            notification = Notification(
                listing_id=listing.id,
                channel="demo",
                payload=payload,
                status="pending",
            )
            session.add(notification)
            created += 1
    return created
