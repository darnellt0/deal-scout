"""Schemas for ListingDraft model."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
from app.schemas.base import ORMModel


class ListingDraftOut(ORMModel):
    """Output schema for listing draft."""

    id: int
    user_id: int
    snap_job_id: Optional[int] = None

    # Status
    status: str = Field(default="draft", max_length=50)

    # Listing details
    title: str = Field(max_length=255)
    description: str
    category: str = Field(max_length=120)
    attributes: Dict = Field(default_factory=dict)
    condition: Optional[str] = None

    # Pricing
    price_suggested: Optional[float] = Field(None, ge=0)
    price_low: Optional[float] = Field(None, ge=0)
    price_high: Optional[float] = Field(None, ge=0)
    price_rationale: Optional[str] = None

    # Copywriting metadata
    bullet_highlights: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    seo_keywords: List[str] = Field(default_factory=list)

    # Vision metadata
    vision_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Pipeline metadata
    meta: Dict = Field(default_factory=dict)

    # Versioning
    version: int = Field(default=1)
    parent_draft_id: Optional[int] = None

    # Publication tracking
    published_item_id: Optional[int] = None
    published_at: Optional[datetime] = None

    created_at: datetime
    updated_at: Optional[datetime] = None


class ListingDraftCreate(ORMModel):
    """Schema for creating listing draft."""

    snap_job_id: Optional[int] = None
    title: str
    description: str
    category: str
    attributes: Dict = Field(default_factory=dict)
    condition: Optional[str] = None
    price_suggested: Optional[float] = None
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    price_rationale: Optional[str] = None
    bullet_highlights: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    seo_keywords: List[str] = Field(default_factory=list)
    vision_confidence: Optional[float] = None
    meta: Dict = Field(default_factory=dict)


class ListingDraftUpdate(ORMModel):
    """Schema for updating listing draft."""

    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    attributes: Optional[Dict] = None
    condition: Optional[str] = None
    price_suggested: Optional[float] = None
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    price_rationale: Optional[str] = None
    bullet_highlights: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    seo_keywords: Optional[List[str]] = None
    meta: Optional[Dict] = None
    published_item_id: Optional[int] = None
    published_at: Optional[datetime] = None
