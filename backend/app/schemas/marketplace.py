"""Schemas for MarketplaceAccount model."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import Field
from app.schemas.base import ORMModel, TimestampedModel


class MarketplaceAccountOut(TimestampedModel):
    """Output schema for marketplace account."""

    id: int
    platform: str = Field(..., max_length=50)
    connected: bool = False
    credentials: Dict = Field(default_factory=dict)


class MarketplaceAccountCreate(ORMModel):
    """Schema for creating marketplace account."""

    platform: str
    connected: bool = False
    credentials: Dict = Field(default_factory=dict)


class MarketplaceAccountUpdate(ORMModel):
    """Schema for updating marketplace account."""

    connected: Optional[bool] = None
    credentials: Optional[Dict] = None
