"""Notification Preferences API endpoints for Phase 7."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.db import SessionLocal
from app.core.models import NotificationPreferences, User
from app.core.auth import get_current_user

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

    class Config:
        from_attributes = True


class UpdateChannels(BaseModel):
    """Update notification channels."""
    channels: List[str]


class UpdateFrequency(BaseModel):
    """Update notification frequency."""
    frequency: str  # immediate, daily, weekly
    digest_time: Optional[str] = "09:00"


async def _get_or_create_preferences(db: AsyncSession, user_id: int) -> NotificationPreferences:
    """Get or create notification preferences for a user."""
    result = await db.execute(
        select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = NotificationPreferences(user_id=user_id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return prefs


@router.get("", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's notification preferences."""
    prefs = await _get_or_create_preferences(db, current_user.id)
    return prefs


@router.patch("/channels", response_model=NotificationPreferencesResponse)
async def update_channels(
    data: UpdateChannels,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update notification channels (email, SMS, Discord, push)."""
    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.channels = data.channels
    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    return prefs


@router.patch("/frequency", response_model=NotificationPreferencesResponse)
async def update_frequency(
    data: UpdateFrequency,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update notification frequency (immediate, daily, weekly)."""
    if data.frequency not in ["immediate", "daily", "weekly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frequency must be one of: immediate, daily, weekly",
        )

    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.frequency = data.frequency
    if data.digest_time:
        prefs.digest_time = data.digest_time
    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    return prefs
