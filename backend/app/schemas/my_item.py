"""Schemas for MyItem model."""

from datetime import datetime
from typing import Dict, Optional
from pydantic import Field
from app.schemas.base import ORMModel, TimestampedModel
from app.core.models import Condition


class MyItemBase(ORMModel):
    """Base fields for my item schemas."""

    title: str = Field(..., max_length=255)
    category: str = Field(..., max_length=120)
    attributes: Dict = Field(default_factory=dict)
    condition: Optional[Condition] = None
    price: float = Field(default=0.0, ge=0)
    status: str = Field(default="draft", max_length=50)


class MyItemCreate(MyItemBase):
    """Schema for creating my item."""

    pass


class MyItemUpdate(ORMModel):
    """Schema for updating my item."""

    title: Optional[str] = None
    category: Optional[str] = None
    attributes: Optional[Dict] = None
    condition: Optional[Condition] = None
    price: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None


class MyItemOut(TimestampedModel):
    """Output schema for my item."""

    id: int
    title: str = Field(..., max_length=255)
    category: str = Field(..., max_length=120)
    attributes: Dict = Field(default_factory=dict)
    condition: Optional[Condition] = None
    price: float = Field(default=0.0, ge=0)
    status: str = Field(default="draft", max_length=50)
