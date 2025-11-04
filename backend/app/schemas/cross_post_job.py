"""Schemas for CrossPostJob model."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
from app.schemas.base import ORMModel


class CrossPostJobOut(ORMModel):
    """Output schema for cross-post job."""

    id: int
    user_id: int
    snap_job_id: Optional[int] = None
    listing_draft_id: Optional[int] = None
    my_item_id: Optional[int] = None

    # Target platforms
    platforms: List[str] = Field(default_factory=list)

    # Status
    status: str = Field(default="pending", max_length=50)
    progress: int = Field(default=0, ge=0, le=100)
    error_message: Optional[str] = None

    # Platform-specific metadata
    platform_metadata: Dict = Field(default_factory=dict)

    # Results
    cross_post_ids: List[int] = Field(default_factory=list)

    # Logs
    logs: List[str] = Field(default_factory=list)

    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CrossPostJobCreate(ORMModel):
    """Schema for creating cross-post job."""

    snap_job_id: Optional[int] = None
    listing_draft_id: Optional[int] = None
    my_item_id: Optional[int] = None
    platforms: List[str] = Field(default_factory=list)
    platform_metadata: Dict = Field(default_factory=dict)


class CrossPostJobUpdate(ORMModel):
    """Schema for updating cross-post job."""

    status: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None
    platform_metadata: Optional[Dict] = None
    cross_post_ids: Optional[List[int]] = None
    logs: Optional[List[str]] = None
    completed_at: Optional[datetime] = None
