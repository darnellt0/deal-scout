"""Notification preferences and management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.db import SessionLocal
from app.core.models import User, UserPref, Notification
from app.core.auth import get_current_user

router = APIRouter(prefix="/notification-preferences", tags=["notifications"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification preferences for the current user."""
    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()

    if not prefs:
        # Return defaults
        return {
            "user_id": current_user.id,
            "email_notifications": True,
            "notification_channels": ["email"],
            "notification_frequency": "instant",  # instant, daily_digest, weekly_digest
            "deal_alerts_enabled": True,
            "deal_alert_min_score": 7.0,
            "order_notifications_enabled": True,
            "marketplace_notifications_enabled": True,
            "promotional_emails": False,
        }

    return {
        "user_id": current_user.id,
        "email_notifications": prefs.notification_enabled,
        "notification_channels": prefs.notification_channels or ["email"],
        "notification_frequency": prefs.notification_frequency or "instant",
        "deal_alerts_enabled": prefs.notification_enabled,
        "deal_alert_min_score": prefs.deal_alert_min_score or 7.0,
        "order_notifications_enabled": True,
        "marketplace_notifications_enabled": True,
        "promotional_emails": prefs.promotional_emails or False,
    }


@router.put("")
async def update_notification_preferences(
    email_notifications: Optional[bool] = None,
    notification_frequency: Optional[str] = None,
    deal_alert_min_score: Optional[float] = None,
    promotional_emails: Optional[bool] = None,
    notification_channels: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences for the current user."""
    # Validate notification frequency
    valid_frequencies = ["instant", "daily_digest", "weekly_digest"]
    if notification_frequency and notification_frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"notification_frequency must be one of: {', '.join(valid_frequencies)}",
        )

    # Validate deal alert minimum score
    if deal_alert_min_score is not None:
        if deal_alert_min_score < 0 or deal_alert_min_score > 10:
            raise HTTPException(
                status_code=400,
                detail="deal_alert_min_score must be between 0 and 10",
            )

    # Validate notification channels
    valid_channels = ["email", "discord", "sms", "push"]
    if notification_channels:
        invalid_channels = [c for c in notification_channels if c not in valid_channels]
        if invalid_channels:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid channels: {', '.join(invalid_channels)}. Valid: {', '.join(valid_channels)}",
            )

    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPref(user_id=current_user.id)
        db.add(prefs)

    if email_notifications is not None:
        prefs.notification_enabled = email_notifications
    if notification_frequency is not None:
        prefs.notification_frequency = notification_frequency
    if deal_alert_min_score is not None:
        prefs.deal_alert_min_score = deal_alert_min_score
    if promotional_emails is not None:
        prefs.promotional_emails = promotional_emails
    if notification_channels is not None:
        prefs.notification_channels = notification_channels

    db.commit()

    return {
        "message": "Notification preferences updated successfully",
        "preferences": {
            "user_id": current_user.id,
            "email_notifications": prefs.notification_enabled,
            "notification_channels": prefs.notification_channels or ["email"],
            "notification_frequency": prefs.notification_frequency or "instant",
            "deal_alert_min_score": prefs.deal_alert_min_score or 7.0,
            "promotional_emails": prefs.promotional_emails or False,
        }
    }


@router.post("/reset")
async def reset_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset notification preferences to defaults."""
    prefs = db.query(UserPref).filter(UserPref.user_id == current_user.id).first()

    if prefs:
        prefs.notification_enabled = True
        prefs.notification_channels = ["email"]
        prefs.notification_frequency = "instant"
        prefs.deal_alert_min_score = 7.0
        prefs.promotional_emails = False
        db.commit()

    return {
        "message": "Notification preferences reset to defaults",
        "preferences": {
            "email_notifications": True,
            "notification_channels": ["email"],
            "notification_frequency": "instant",
            "deal_alert_min_score": 7.0,
            "promotional_emails": False,
        }
    }


@router.get("/history")
async def get_notification_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=500),
    status_filter: Optional[str] = Query(default=None),
    channel_filter: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get notification history for the current user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if status_filter:
        query = query.filter(Notification.status == status_filter)

    if channel_filter:
        query = query.filter(Notification.channel == channel_filter)

    notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()

    return {
        "total": len(notifications),
        "notifications": [
            {
                "id": notification.id,
                "channel": notification.channel,
                "status": notification.status,
                "payload": notification.payload,
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                "created_at": notification.created_at.isoformat(),
            }
            for notification in notifications
        ],
    }


@router.post("/clear")
async def clear_notifications(
    status_filter: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear notifications for the current user."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if status_filter:
        query = query.filter(Notification.status == status_filter)

    count = query.delete()
    db.commit()

    return {
        "message": f"Cleared {count} notifications",
        "cleared_count": count,
    }


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status != "read",
    ).all()

    count = 0
    for notification in notifications:
        notification.status = "read"
        count += 1

    db.commit()

    return {
        "message": f"Marked {count} notifications as read",
        "marked_count": count,
    }


@router.get("/channels-available")
async def get_available_notification_channels():
    """Get list of available notification channels."""
    return {
        "channels": [
            {
                "id": "email",
                "name": "Email",
                "description": "Receive notifications via email",
            },
            {
                "id": "discord",
                "name": "Discord",
                "description": "Receive notifications via Discord webhook",
            },
            {
                "id": "sms",
                "name": "SMS",
                "description": "Receive notifications via SMS (Twilio)",
            },
            {
                "id": "push",
                "name": "Push Notification",
                "description": "Receive web/mobile push notifications",
            },
        ]
    }


@router.get("/frequencies-available")
async def get_available_notification_frequencies():
    """Get list of available notification frequencies."""
    return {
        "frequencies": [
            {
                "id": "instant",
                "name": "Instant",
                "description": "Receive notifications immediately",
            },
            {
                "id": "daily_digest",
                "name": "Daily Digest",
                "description": "Receive a daily summary email",
            },
            {
                "id": "weekly_digest",
                "name": "Weekly Digest",
                "description": "Receive a weekly summary email",
            },
        ]
    }
