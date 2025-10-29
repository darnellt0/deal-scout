"""Schemas for Notification model."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import Field
from app.schemas.base import ORMModel


class NotificationOut(ORMModel):
    """Output schema for notification."""

    id: int
    listing_id: Optional[int] = None
    channel: str = Field(..., max_length=50)
    payload: Dict = Field(default_factory=dict)
    sent_at: Optional[datetime] = None
    status: str = Field(default="pending", max_length=50)
    created_at: datetime


class NotificationCreate(ORMModel):
    """Schema for creating notification."""

    listing_id: Optional[int] = None
    channel: str
    payload: Dict = Field(default_factory=dict)
    status: str = "pending"
