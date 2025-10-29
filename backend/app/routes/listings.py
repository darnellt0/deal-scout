"""API routes for marketplace listings."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.models import Listing
from app.core.errors import NotFoundError, ConflictError
from app.schemas.listing import ListingOut, ListingCreate, ListingUpdate
from app.schemas.common import PageResponse, PageMeta

router = APIRouter(prefix="/listings", tags=["listings"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=PageResponse[ListingOut])
async def list_listings(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    source: Optional[str] = None,
    available: Optional[bool] = None,
) -> PageResponse[ListingOut]:
    """List marketplace listings with pagination and filtering."""
    query = db.query(Listing)

    # Apply filters
    if category:
        query = query.filter(Listing.category == category)
    if source:
        query = query.filter(Listing.source == source)
    if available is not None:
        query = query.filter(Listing.available == available)

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()

    return PageResponse[ListingOut](
        meta=PageMeta(page=page, size=size, total=total),
        items=[ListingOut.model_validate(item) for item in items],
    )


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(listing_id: int, db: Session = Depends(get_db)) -> ListingOut:
    """Get a specific listing by ID."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise NotFoundError(resource="Listing", resource_id=listing_id)
    return ListingOut.model_validate(listing)


@router.post("", response_model=ListingOut, status_code=201)
async def create_listing(
    payload: ListingCreate, db: Session = Depends(get_db)
) -> ListingOut:
    """Create a new marketplace listing."""
    # Check for duplicate source_id
    existing = db.query(Listing).filter(Listing.source_id == payload.source_id).first()
    if existing:
        raise ConflictError(
            message=f"Listing with source_id '{payload.source_id}' already exists"
        )

    listing = Listing(**payload.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return ListingOut.model_validate(listing)


@router.patch("/{listing_id}", response_model=ListingOut)
async def update_listing(
    listing_id: int, payload: ListingUpdate, db: Session = Depends(get_db)
) -> ListingOut:
    """Update a listing."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise NotFoundError(resource="Listing", resource_id=listing_id)

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return ListingOut.model_validate(listing)


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(listing_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a listing."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise NotFoundError(resource="Listing", resource_id=listing_id)

    db.delete(listing)
    db.commit()
