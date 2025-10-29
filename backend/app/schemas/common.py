"""Common schemas for pagination and responses."""

from typing import Any, Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel):
    """Pagination request parameters."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PageMeta(BaseModel):
    """Pagination metadata."""

    page: int
    size: int
    total: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.size - 1) // self.size


class PageResponse(BaseModel, Generic[T]):
    """Generic paginated response container."""

    meta: PageMeta
    items: List[T]
