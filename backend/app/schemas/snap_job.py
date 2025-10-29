"""Schemas for SnapJob model."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
from app.schemas.base import ORMModel, TimestampedModel


class SnapJobOut(ORMModel, TimestampedModel):
    """Output schema for snap job."""

    id: int
    status: str = Field(default="pending", max_length=50)
    source: str = Field(default="upload", max_length=50)
    input_photos: List[str] = Field(default_factory=list)
    processed_images: List[str] = Field(default_factory=list)
    detected_category: Optional[str] = Field(None, max_length=120)
    detected_attributes: Dict = Field(default_factory=dict)
    condition_guess: Optional[str] = Field(None, max_length=50)
    price_suggestion_cents: Optional[int] = Field(None, ge=0)
    suggested_price: Optional[float] = Field(None, ge=0)
    suggested_title: Optional[str] = Field(None, max_length=255)
    suggested_description: Optional[str] = None
    title_suggestion: Optional[str] = Field(None, max_length=255)
    description_suggestion: Optional[str] = None


class SnapJobCreate(ORMModel):
    """Schema for creating snap job."""

    source: str = "upload"
    input_photos: List[str] = Field(default_factory=list)
    detected_category: Optional[str] = None
    detected_attributes: Dict = Field(default_factory=dict)


class SnapJobUpdate(ORMModel):
    """Schema for updating snap job."""

    status: Optional[str] = None
    processed_images: Optional[List[str]] = None
    condition_guess: Optional[str] = None
    price_suggestion_cents: Optional[int] = Field(None, ge=0)
    suggested_title: Optional[str] = None
    suggested_description: Optional[str] = None
