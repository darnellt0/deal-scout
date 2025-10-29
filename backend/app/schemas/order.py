"""Schemas for Order model."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import Field
from app.schemas.base import ORMModel, TimestampedModel


class OrderOut(ORMModel, TimestampedModel):
    """Output schema for order."""

    id: int
    cross_post_id: int
    platform_order_id: str = Field(..., max_length=120)
    status: str = Field(..., max_length=50)
    total: float = Field(default=0.0, ge=0)
    meta: Dict = Field(default_factory=dict, alias="metadata")


class OrderCreate(ORMModel):
    """Schema for creating order."""

    cross_post_id: int
    platform_order_id: str
    status: str
    total: float = 0.0
    meta: Dict = Field(default_factory=dict, alias="metadata")


class OrderUpdate(ORMModel):
    """Schema for updating order."""

    status: Optional[str] = None
    total: Optional[float] = Field(None, ge=0)
