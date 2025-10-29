"""API routes for marketplace listings."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.core.models import Listing, User
from app.core.auth import get_current_user, require_admin
from app.core.errors import NotFoundError, ConflictError
from app.core.search import ListingSearch
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
    payload: ListingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ListingOut:
    """Create a new marketplace listing (admin only)."""
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
    listing_id: int,
    payload: ListingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ListingOut:
    """Update a listing (admin only)."""
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
async def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    """Delete a listing (admin only)."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise NotFoundError(resource="Listing", resource_id=listing_id)

    db.delete(listing)
    db.commit()


@router.get("/search/listings", response_model=PageResponse[ListingOut])
async def search_listings(
    q: str = Query(..., description="Search query"),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_score: Optional[float] = None,
    condition: Optional[str] = None,
) -> PageResponse[ListingOut]:
    """
    Full-text search for listings.

    Search across title, description, and category.
    """
    offset = (page - 1) * size

    results, total = ListingSearch.search_listings(
        session=db,
        query=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_score=min_score,
        condition=condition,
        limit=size,
        offset=offset,
    )

    items = [ListingOut.model_validate(listing) for listing, score in results]

    return PageResponse[ListingOut](
        meta=PageMeta(page=page, size=size, total=total),
        items=items,
    )


@router.get("/search/advanced", response_model=PageResponse[ListingOut])
async def advanced_search(
    keywords: List[str] = Query(
        ...,
        description="Keywords that must be present (AND logic)"
    ),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    exclude: Optional[List[str]] = Query(
        None,
        description="Keywords to exclude (NOT logic)"
    ),
    category: Optional[List[str]] = Query(None, description="Categories to search in"),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_score: Optional[float] = None,
    condition: Optional[str] = None,
) -> PageResponse[ListingOut]:
    """
    Advanced search with multiple keywords and exclusions.

    - keywords: List of terms that MUST appear (AND)
    - exclude: List of terms to exclude (NOT)
    - category: Categories to search in
    """
    offset = (page - 1) * size

    results, total = ListingSearch.search_listings_advanced(
        session=db,
        keywords=keywords,
        exclude_keywords=exclude,
        min_price=min_price,
        max_price=max_price,
        min_score=min_score,
        categories=category,
        condition=condition,
        limit=size,
        offset=offset,
    )

    items = [ListingOut.model_validate(listing) for listing, score in results]

    return PageResponse[ListingOut](
        meta=PageMeta(page=page, size=size, total=total),
        items=items,
    )


@router.get("/search/suggestions")
async def search_suggestions(
    q: str = Query(..., min_length=2, description="Partial search query"),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    """
    Get autocomplete suggestions for search queries.

    Returns suggestions based on categories and titles.
    """
    suggestions = ListingSearch.get_suggestions(
        session=db,
        partial_query=q,
        limit=limit,
    )

    return {"query": q, "suggestions": suggestions}
