"""Notification Preferences API endpoints for Phase 7."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.core.db import SessionLocal
from app.core.models import NotificationPreferences, User
from app.core.auth import get_current_user
from app.core.utils import utcnow

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/notification-preferences", tags=["notifications"])


# ============================================================================
# SCHEMAS (Pydantic Models)
# ============================================================================


class NotificationPreferencesResponse(BaseModel):
    """Schema for returning notification preferences."""
    id: int
    user_id: int
    channels: List[str]
    frequency: str
    digest_time: str
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    category_filters: List[str]
    max_per_day: int
    phone_number: Optional[str]
    phone_verified: bool
    discord_webhook_url: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UpdateChannels(BaseModel):
    """Update notification channels."""
    channels: List[str]


class UpdateFrequency(BaseModel):
    """Update notification frequency."""
    frequency: str  # immediate, daily, weekly
    digest_time: Optional[str] = "09:00"


class UpdateQuietHours(BaseModel):
    """Update quiet hours configuration."""
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class UpdateMaxPerDay(BaseModel):
    """Update maximum notifications per day."""
    max_per_day: int


class DiscordWebhookRequest(BaseModel):
    """Payload for adding a Discord webhook."""
    discord_webhook_url: str


def _get_or_create_preferences(db: Session, user_id: int) -> NotificationPreferences:
    """Get or create notification preferences for a user."""
    result = db.execute(
        select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = NotificationPreferences(user_id=user_id)
        db.add(prefs)
    db.commit()
    db.refresh(prefs)

    return prefs


@router.get("", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's notification preferences."""
    prefs = _get_or_create_preferences(db, current_user.id)
    return prefs


@router.patch("/channels", response_model=NotificationPreferencesResponse)
async def update_channels(
    data: UpdateChannels,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update notification channels (email, SMS, Discord, push)."""
    prefs = _get_or_create_preferences(db, current_user.id)
    prefs.channels = data.channels
    prefs.updated_at = utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


@router.patch("/quiet-hours", response_model=NotificationPreferencesResponse)
async def update_quiet_hours(
    data: UpdateQuietHours,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable or disable quiet hours (and their window)."""
    prefs = _get_or_create_preferences(db, current_user.id)
    prefs.quiet_hours_enabled = data.quiet_hours_enabled
    prefs.quiet_hours_start = data.quiet_hours_start if data.quiet_hours_enabled else None
    prefs.quiet_hours_end = data.quiet_hours_end if data.quiet_hours_enabled else None
    prefs.updated_at = utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


@router.patch("/max-per-day", response_model=NotificationPreferencesResponse)
async def update_max_per_day(
    data: UpdateMaxPerDay,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the maximum notifications delivered per day (rate limiting)."""
    if data.max_per_day <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_per_day must be greater than zero",
        )

    prefs = _get_or_create_preferences(db, current_user.id)
    prefs.max_per_day = data.max_per_day
    prefs.updated_at = utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


@router.post("/discord-webhook/add", response_model=NotificationPreferencesResponse)
async def add_discord_webhook(
    data: DiscordWebhookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Attach a Discord webhook URL for notifications."""
    url = data.discord_webhook_url.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discord webhook URL is required",
        )

    prefs = _get_or_create_preferences(db, current_user.id)
    prefs.discord_webhook_url = url
    if "discord" not in prefs.channels:
        prefs.channels.append("discord")
    prefs.updated_at = utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs


@router.delete("/discord-webhook", response_model=NotificationPreferencesResponse)
async def remove_discord_webhook(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove the configured Discord webhook."""
    prefs = _get_or_create_preferences(db, current_user.id)
    prefs.discord_webhook_url = None
    prefs.updated_at = utcnow()
    prefs.channels = [ch for ch in prefs.channels if ch != "discord"]
    db.commit()
    db.refresh(prefs)
    return prefs


@router.post("/discord-webhook/test", response_model=dict)
async def test_discord_webhook(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simulate a Discord webhook test (stubbed for local environments)."""
    prefs = _get_or_create_preferences(db, current_user.id)
    if not prefs.discord_webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discord webhook is not configured",
        )

    # In production this would POST to Discord; here we just acknowledge success.
    return {"status": "ok"}


@router.patch("/frequency", response_model=NotificationPreferencesResponse)
async def update_frequency(
    data: UpdateFrequency,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update notification frequency (immediate, daily, weekly)."""
    if data.frequency not in ["immediate", "daily", "weekly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frequency must be one of: immediate, daily, weekly",
        )

    prefs = _get_or_create_preferences(db, current_user.id)
    prefs.frequency = data.frequency
    if data.digest_time:
        prefs.digest_time = data.digest_time
    prefs.updated_at = utcnow()
    db.commit()
    db.refresh(prefs)
    return prefs
