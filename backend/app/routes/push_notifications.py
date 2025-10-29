"""Push notification management endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import SessionLocal
from app.core.models import User
from app.notify.push import DeviceTokenManager, get_push_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/push-notifications", tags=["push-notifications"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DeviceTokenRequest(BaseModel):
    """Request to register a device token."""

    device_token: str = Field(..., description="FCM device token")
    device_type: str = Field(
        default="mobile",
        description="Device type (mobile, web, etc.)",
    )


class PushNotificationRequest(BaseModel):
    """Request to send a test push notification."""

    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message body")


class DeviceTokenResponse(BaseModel):
    """Response with device token."""

    token: str
    type: str
    created_at: str


class UserDeviceTokensResponse(BaseModel):
    """Response with list of user device tokens."""

    user_id: int
    device_tokens: List[DeviceTokenResponse]


@router.post("/devices/register")
async def register_device_token(
    payload: DeviceTokenRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Register a device token for push notifications.

    The device token is stored in the user's profile and used for sending
    push notifications.
    """
    success = DeviceTokenManager.add_device_token(
        user_id=current_user.id,
        device_token=payload.device_token,
        device_type=payload.device_type,
    )

    if success:
        return {
            "message": "Device token registered successfully",
            "device_token": payload.device_token,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register device token",
        )


@router.post("/devices/unregister")
async def unregister_device_token(
    payload: DeviceTokenRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Unregister a device token for push notifications.

    After unregistering, the device will no longer receive push notifications.
    """
    success = DeviceTokenManager.remove_device_token(
        user_id=current_user.id,
        device_token=payload.device_token,
    )

    if success:
        return {
            "message": "Device token unregistered successfully",
            "device_token": payload.device_token,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device token not found",
        )


@router.get("/devices")
async def get_user_device_tokens(
    current_user: User = Depends(get_current_user),
) -> UserDeviceTokensResponse:
    """
    Get all registered device tokens for the current user.

    Returns a list of device tokens that will receive push notifications.
    """
    tokens = DeviceTokenManager.get_user_device_tokens(current_user.id)

    # Return properly formatted response
    device_tokens = []
    if current_user.profile and "device_tokens" in current_user.profile:
        device_tokens = current_user.profile["device_tokens"]

    return UserDeviceTokensResponse(
        user_id=current_user.id,
        device_tokens=device_tokens,
    )


@router.post("/test")
async def send_test_notification(
    payload: PushNotificationRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Send a test push notification to all registered devices.

    Useful for testing push notification setup and connectivity.
    """
    device_tokens = DeviceTokenManager.get_user_device_tokens(current_user.id)

    if not device_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No device tokens registered for this user",
        )

    push_service = get_push_service()
    results = push_service.send_bulk_notifications(
        device_tokens=device_tokens,
        title=payload.title,
        message=payload.message,
        data={
            "type": "test",
            "user_id": str(current_user.id),
        },
    )

    return {
        "message": "Test notifications sent",
        "success": results["success"],
        "failed": results["failed"],
    }


@router.post("/devices/clear")
async def clear_all_device_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Clear all device tokens for the current user.

    After clearing, the user will no longer receive push notifications.
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.profile and "device_tokens" in user.profile:
        user.profile["device_tokens"] = []
        db.commit()
        logger.info(f"Cleared all device tokens for user {current_user.id}")

    return {"message": "All device tokens cleared"}
