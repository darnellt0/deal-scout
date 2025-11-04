"""Schemas for MediaAsset model."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
from app.schemas.base import ORMModel


class MediaAssetOut(ORMModel):
    """Output schema for media asset."""

    id: int
    user_id: int
    snap_job_id: Optional[int] = None
    listing_draft_id: Optional[int] = None

    # URLs
    original_url: str = Field(max_length=500)
    processed_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)

    # Media metadata
    media_type: str = Field(default="image", max_length=50)
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # Processing metadata
    processing_status: str = Field(default="pending", max_length=50)
    processing_steps: Dict = Field(default_factory=dict)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    ocr_text: Optional[str] = None

    # Vision metadata
    vision_labels: List[str] = Field(default_factory=list)
    vision_captions: List[str] = Field(default_factory=list)

    # Display order
    display_order: int = Field(default=0)

    created_at: datetime
    updated_at: Optional[datetime] = None


class MediaAssetCreate(ORMModel):
    """Schema for creating media asset."""

    snap_job_id: Optional[int] = None
    listing_draft_id: Optional[int] = None
    original_url: str
    media_type: str = "image"
    display_order: int = 0


class MediaAssetUpdate(ORMModel):
    """Schema for updating media asset."""

    processed_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    processing_status: Optional[str] = None
    processing_steps: Optional[Dict] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    ocr_text: Optional[str] = None
    vision_labels: Optional[List[str]] = None
    vision_captions: Optional[List[str]] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
