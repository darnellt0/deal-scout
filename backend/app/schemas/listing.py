"""Schemas for Listing and ListingScore models."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
from app.schemas.base import ORMModel, TimestampedModel
from app.core.models import Condition


class ListingScoreOut(ORMModel):
    """Output schema for listing scores."""

    id: int
    listing_id: int
    metric: str
    value: float
    snapshot: Dict = Field(default_factory=dict)
    created_at: datetime


class ListingBase(ORMModel):
    """Base fields for listing schemas."""

    source: str = Field(..., max_length=50)
    source_id: str = Field(..., max_length=120)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    condition: Optional[Condition] = None
    category: Optional[str] = Field(None, max_length=120)
    url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    location: Dict = Field(default_factory=dict)
    available: bool = True


class ListingCreate(ListingBase):
    """Schema for creating a listing."""

    pass


class ListingUpdate(ORMModel):
    """Schema for updating a listing."""

    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    condition: Optional[Condition] = None
    category: Optional[str] = None
    available: Optional[bool] = None
    location: Optional[Dict] = None


class ListingOut(ORMModel):
    """Output schema for listing."""

    id: int
    source: str = Field(..., max_length=50)
    source_id: str = Field(..., max_length=120)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    condition: Optional[Condition] = None
    category: Optional[str] = Field(None, max_length=120)
    url: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    location: Dict = Field(default_factory=dict)
    available: bool = True
    last_seen_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    scores: Optional[List[ListingScoreOut]] = None
