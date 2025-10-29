from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.buyer.templates import load_template
from app.core.db import SessionLocal
from app.core.models import Listing, ListingScore, Notification, User, UserPref, Condition
from app.core.auth import get_current_user
from app.core.utils import haversine_distance

router = APIRouter()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/deals")
async def list_deals(
    limit: int = Query(default=10, ge=1, le=50),
    category: Optional[str] = Query(default=None),
    min_score: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    condition: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """List top-scored deals with optional filtering."""
    listings = (
        db.query(Listing, ListingScore)
        .join(ListingScore, Listing.id == ListingScore.listing_id)
        .filter(ListingScore.metric == "deal_score")
    )

    # Apply filters
    if category:
        listings = listings.filter(Listing.category.ilike(f"%{category}%"))
    if min_score is not None:
        listings = listings.filter(ListingScore.value >= min_score)
    if max_price is not None:
        listings = listings.filter(Listing.price <= max_price)
    if condition:
        listings = listings.filter(Listing.condition == condition)

    # Order by deal score descending and limit
    listings = listings.order_by(desc(ListingScore.value)).limit(limit).all()

    template = load_template()
    return [
        {
            "id": listing.id,
            "title": listing.title,
            "price": listing.price,
            "condition": listing.condition.value if listing.condition else "unknown",
            "category": listing.category,
            "url": listing.url,
            "thumbnail_url": listing.thumbnail_url,
            "deal_score": score.value,
            "auto_message": template,
            "price_cents": int(listing.price * 100),
            "location": listing.location,
            "created_at": listing.created_at.isoformat() if listing.created_at else None,
        }
        for listing, score in listings
    ]


@router.get("/deals/saved")
async def get_saved_deals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get deals saved by the current user (via user preferences/watch list)."""
    # Get user preferences
    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()
    if not prefs or not prefs.saved_deals:
        return []

    saved_deal_ids = prefs.saved_deals
    if not saved_deal_ids:
        return []

    deals = (
        db.query(Listing, ListingScore)
        .join(ListingScore, Listing.id == ListingScore.listing_id)
        .filter(Listing.id.in_(saved_deal_ids))
        .order_by(desc(ListingScore.value))
        .all()
    )

    return [
        {
            "id": listing.id,
            "title": listing.title,
            "price": listing.price,
            "condition": listing.condition.value if listing.condition else "unknown",
            "url": listing.url,
            "deal_score": score.value,
        }
        for listing, score in deals
    ]


@router.post("/deals/{listing_id}/save")
async def save_deal(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a deal to current user's watch list."""
    # Verify listing exists
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Get or create user preferences
    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPref(
            user_id=current_user.id,
            max_price_couch=1000,
            max_price_island=2000,
            saved_deals=[],
        )
        db.add(prefs)

    # Add to saved deals if not already there
    if prefs.saved_deals is None:
        prefs.saved_deals = []

    if listing_id not in prefs.saved_deals:
        prefs.saved_deals.append(listing_id)

    db.commit()
    return {"message": "Deal saved successfully"}


@router.delete("/deals/{listing_id}/save")
async def unsave_deal(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a deal from current user's watch list."""
    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()
    if not prefs or not prefs.saved_deals:
        raise HTTPException(status_code=404, detail="Deal not in watch list")

    if listing_id in prefs.saved_deals:
        prefs.saved_deals.remove(listing_id)
        db.commit()
        return {"message": "Deal removed from watch list"}

    raise HTTPException(status_code=404, detail="Deal not in watch list")


@router.get("/notifications")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """List notifications for the current user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if status_filter:
        query = query.filter(Notification.status == status_filter)

    notifications = (
        query.order_by(desc(Notification.created_at)).limit(limit).all()
    )

    return [
        {
            "id": notification.id,
            "channel": notification.channel,
            "status": notification.status,
            "payload": notification.payload,
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
            "created_at": notification.created_at.isoformat(),
            "listing_id": notification.listing_id,
        }
        for notification in notifications
    ]


@router.get("/notifications/{notification_id}")
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific notification."""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "id": notification.id,
        "channel": notification.channel,
        "status": notification.status,
        "payload": notification.payload,
        "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
        "created_at": notification.created_at.isoformat(),
        "listing_id": notification.listing_id,
    }


@router.patch("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.status != "read":
        notification.status = "read"
        db.commit()

    return {"message": "Notification marked as read"}


@router.get("/preferences")
async def get_buyer_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get buyer's search and notification preferences."""
    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()

    if not prefs:
        return {
            "user_id": current_user.id,
            "max_price_couch": 1000,
            "max_price_island": 2000,
            "location": None,
            "search_radius_mi": 50,
            "notification_enabled": True,
            "notification_channels": ["email"],
        }

    return {
        "user_id": current_user.id,
        "max_price_couch": prefs.max_price_couch,
        "max_price_island": prefs.max_price_island,
        "location": prefs.location,
        "search_radius_mi": prefs.search_radius_mi,
        "notification_enabled": prefs.notification_enabled,
        "notification_channels": prefs.notification_channels or ["email"],
    }


@router.put("/preferences")
async def update_buyer_preferences(
    max_price_couch: Optional[int] = Query(default=None),
    max_price_island: Optional[int] = Query(default=None),
    search_radius_mi: Optional[int] = Query(default=None),
    notification_enabled: Optional[bool] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update buyer's search and notification preferences."""
    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()

    if not prefs:
        prefs = UserPref(user_id=current_user.id)
        db.add(prefs)

    if max_price_couch is not None:
        prefs.max_price_couch = max_price_couch
    if max_price_island is not None:
        prefs.max_price_island = max_price_island
    if search_radius_mi is not None:
        prefs.search_radius_mi = search_radius_mi
    if notification_enabled is not None:
        prefs.notification_enabled = notification_enabled

    db.commit()

    return {"message": "Preferences updated successfully"}
