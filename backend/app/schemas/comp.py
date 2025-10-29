"""Schemas for Comp (comparable pricing) model."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import Field
from app.schemas.base import ORMModel
from app.core.models import Condition


class CompOut(ORMModel):
    """Output schema for comparable pricing."""

    id: int
    category: str = Field(..., max_length=120)
    title: str = Field(..., max_length=255)
    price: float = Field(default=0.0, ge=0)
    condition: Optional[Condition] = None
    source: str = Field(..., max_length=50)
    observed_at: datetime
    meta: Dict = Field(default_factory=dict, alias="metadata")


class CompCreate(ORMModel):
    """Schema for creating comp data."""

    category: str
    title: str
    price: float
    condition: Optional[Condition] = None
    source: str
    meta: Dict = Field(default_factory=dict, alias="metadata")
