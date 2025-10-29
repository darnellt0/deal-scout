"""Schemas for CrossPost model."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import Field
from app.schemas.base import ORMModel, TimestampedModel


class CrossPostBase(ORMModel):
    """Base fields for cross post schemas."""

    my_item_id: int
    platform: str = Field(..., max_length=50)
    external_id: Optional[str] = Field(None, max_length=120)
    listing_url: str = Field(..., max_length=500)
    status: str = Field(default="pending", max_length=50)


class CrossPostCreate(CrossPostBase):
    """Schema for creating cross post."""

    meta: Dict = Field(default_factory=dict, alias="metadata")


class CrossPostUpdate(ORMModel):
    """Schema for updating cross post."""

    external_id: Optional[str] = None
    listing_url: Optional[str] = None
    status: Optional[str] = None


class CrossPostOut(ORMModel):
    """Output schema for cross post."""

    id: int
    my_item_id: int
    platform: str = Field(..., max_length=50)
    external_id: Optional[str] = Field(None, max_length=120)
    listing_url: str = Field(..., max_length=500)
    status: str = Field(default="pending", max_length=50)
    meta: Dict = Field(default_factory=dict, alias="metadata")
    created_at: datetime
    updated_at: Optional[datetime] = None
