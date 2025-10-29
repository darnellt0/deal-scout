"""Schemas for UserPref model."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
from app.schemas.base import ORMModel, TimestampedModel
from app.core.models import Condition


class UserPrefOut(ORMModel):
    """Output schema for user preferences."""

    id: int
    user_id: str = Field(..., max_length=64)
    radius_mi: int = Field(default=50, ge=1)
    city: str = Field(default="San Jose, CA", max_length=255)
    min_condition: Condition = Field(default=Condition.good)
    max_price_couch: float = Field(default=150.0, ge=0)
    max_price_kitchen_island: float = Field(default=300.0, ge=0)
    keywords_include: List[str] = Field(default_factory=list)
    notify_channels: List[str] = Field(default_factory=lambda: ["email"])
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserPrefCreate(ORMModel):
    """Schema for creating user preferences."""

    user_id: str
    radius_mi: int = Field(default=50, ge=1)
    city: str = "San Jose, CA"
    min_condition: Condition = Condition.good
    max_price_couch: float = 150.0
    max_price_kitchen_island: float = 300.0
    keywords_include: List[str] = Field(default_factory=list)
    notify_channels: List[str] = Field(default_factory=lambda: ["email"])


class UserPrefUpdate(ORMModel):
    """Schema for updating user preferences."""

    radius_mi: Optional[int] = Field(None, ge=1)
    city: Optional[str] = None
    min_condition: Optional[Condition] = None
    max_price_couch: Optional[float] = Field(None, ge=0)
    max_price_kitchen_island: Optional[float] = Field(None, ge=0)
    keywords_include: Optional[List[str]] = None
    notify_channels: Optional[List[str]] = None
