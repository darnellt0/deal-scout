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


class UpdateQuietHours(BaseModel):
    """Update quiet hours settings."""
    enabled: bool
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None    # HH:MM format


class UpdateCategories(BaseModel):
    """Update category filters."""
    categories: List[str]


class UpdatePhone(BaseModel):
    """Update phone number for SMS."""
    phone_number: str


class VerifyPhone(BaseModel):
    """Verify phone number with OTP."""
    otp: str


class UpdateDiscord(BaseModel):
    """Update Discord webhook URL."""
    webhook_url: str


@router.patch("/quiet-hours", response_model=NotificationPreferencesResponse)
async def update_quiet_hours(
    data: UpdateQuietHours,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update quiet hours settings to prevent notifications during sleep."""
    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.quiet_hours_enabled = data.enabled

    if data.enabled:
        if not data.start_time or not data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time and end_time are required when enabling quiet hours",
            )
        prefs.quiet_hours_start = data.start_time
        prefs.quiet_hours_end = data.end_time

    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    return prefs


@router.patch("/categories", response_model=NotificationPreferencesResponse)
async def update_category_filters(
    data: UpdateCategories,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update category filters to only receive notifications for specific categories."""
    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.category_filters = data.categories
    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    return prefs


@router.post("/phone", response_model=NotificationPreferencesResponse)
async def add_phone_number(
    data: UpdatePhone,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add phone number for SMS notifications (requires verification)."""
    # TODO: Send OTP via SMS using Twilio
    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.phone_number = data.phone_number
    prefs.phone_verified = False  # Will be set to True after OTP verification
    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    return prefs


@router.post("/phone/verify", response_model=NotificationPreferencesResponse)
async def verify_phone_number(
    data: VerifyPhone,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify phone number with OTP code."""
    # TODO: Verify OTP code
    prefs = await _get_or_create_preferences(db, current_user.id)

    if not prefs.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No phone number to verify",
        )

    # For now, accept any OTP (TODO: implement actual verification)
    if data.otp and len(data.otp) == 6:
        prefs.phone_verified = True
        prefs.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(prefs)
        return prefs
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code",
        )


@router.delete("/phone", status_code=status.HTTP_204_NO_CONTENT)
async def remove_phone_number(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove phone number from SMS notifications."""
    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.phone_number = None
    prefs.phone_verified = False
    prefs.updated_at = datetime.utcnow()
    await db.commit()


@router.post("/discord-webhook", response_model=NotificationPreferencesResponse)
async def add_discord_webhook(
    data: UpdateDiscord,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add Discord webhook URL for notifications."""
    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.discord_webhook_url = data.webhook_url
    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    return prefs


@router.post("/discord-webhook/test", status_code=status.HTTP_200_OK)
async def test_discord_webhook(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a test message to Discord webhook."""
    prefs = await _get_or_create_preferences(db, current_user.id)

    if not prefs.discord_webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Discord webhook URL configured",
        )

    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            embed = {
                "title": "Test Notification",
                "description": "This is a test notification from Deal Scout",
                "color": 0x00FF00,
            }
            async with session.post(
                prefs.discord_webhook_url, json={"embeds": [embed]}
            ) as resp:
                if resp.status == 204:
                    return {"status": "success", "message": "Test notification sent"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Discord webhook returned status {resp.status}",
                    )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send test notification: {str(e)}",
        )


@router.delete("/discord-webhook", status_code=status.HTTP_204_NO_CONTENT)
async def remove_discord_webhook(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove Discord webhook URL."""
    prefs = await _get_or_create_preferences(db, current_user.id)
    prefs.discord_webhook_url = None
    prefs.updated_at = datetime.utcnow()
    await db.commit()
