"""Base schema classes for ORM and API validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    """Base model for ORM object serialization.

    Uses from_attributes=True (Pydantic v2 equivalent of orm_mode=True)
    to automatically serialize SQLAlchemy ORM objects.
    """

    model_config = ConfigDict(from_attributes=True)


class TimestampedModel(BaseModel):
    """Base model with timestamp fields."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: Optional[datetime] = None


class BaseResponse(BaseModel):
    """Base response model with ID."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
