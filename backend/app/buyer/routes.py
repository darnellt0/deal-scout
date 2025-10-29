from __future__ import annotations

from fastapi import APIRouter, Query

from app.buyer.templates import load_template
from app.core.db import get_session
from app.core.models import Listing, ListingScore, Notification

router = APIRouter()


@router.get("/deals")
async def list_deals(limit: int = Query(default=10, ge=1, le=50)):
    with get_session() as session:
        listings = (
            session.query(Listing, ListingScore)
            .join(ListingScore, Listing.id == ListingScore.listing_id)
            .filter(ListingScore.metric == "deal_score")
            .order_by(ListingScore.value.desc())
            .limit(limit)
            .all()
        )
        template = load_template()
        return [
            {
                "id": listing.id,
                "title": listing.title,
                "price": listing.price,
                "condition": listing.condition.value if listing.condition else "unknown",
                "url": listing.url,
                "thumbnail_url": listing.thumbnail_url,
                "deal_score": score.value,
                "auto_message": template,
                "price_cents": int(listing.price * 100),
            }
            for listing, score in listings
        ]


@router.get("/notifications")
async def list_notifications(limit: int = Query(default=10, ge=1, le=50)):
    with get_session() as session:
        notifications = (
            session.query(Notification)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": notification.id,
                "channel": notification.channel,
                "status": notification.status,
                "payload": notification.payload,
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                "created_at": notification.created_at.isoformat(),
            }
            for notification in notifications
        ]
