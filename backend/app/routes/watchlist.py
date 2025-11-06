"""Watchlist API endpoints for price tracking (Phase 7)."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.db import SessionLocal
from app.core.models import Listing, User, WatchlistItem
from app.core.auth import get_current_user


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/watchlist", tags=["watchlist"])


# ============================================================================
# SCHEMAS (Pydantic Models)
# ============================================================================


class WatchlistItemCreate(BaseModel):
    """Schema for adding item to watchlist."""
    listing_id: int
    price_alert_threshold: Optional[float] = None


class WatchlistItemUpdate(BaseModel):
    """Schema for updating watchlist item."""
    price_alert_threshold: Optional[float] = None


class ListingDetails(BaseModel):
    """Nested listing details for watchlist response."""
    id: int
    title: str
    price: float
    category: Optional[str]
    condition: Optional[str]
    url: str
    thumbnail_url: Optional[str]

    class Config:
        from_attributes = True


class WatchlistItemResponse(BaseModel):
    """Schema for returning a watchlist item."""
    id: int
    user_id: int
    listing_id: int
    price_alert_threshold: Optional[float]
    alert_sent: bool
    last_price: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchlistItemWithListing(BaseModel):
    """Schema for watchlist item with listing details."""
    id: int
    user_id: int
    listing_id: int
    price_alert_threshold: Optional[float]
    alert_sent: bool
    last_price: Optional[float]
    created_at: datetime
    updated_at: datetime
    listing: Optional[ListingDetails]

    class Config:
        from_attributes = True


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WatchlistItemResponse)
async def add_to_watchlist(
    data: WatchlistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a listing to user's watchlist for price tracking."""
    # Check if listing exists
    result = await db.execute(select(Listing).where(Listing.id == data.listing_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    # Check if already in watchlist
    existing = await db.execute(
        select(WatchlistItem).where(
            and_(
                WatchlistItem.user_id == current_user.id,
                WatchlistItem.listing_id == data.listing_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing already in watchlist",
        )

    # Create watchlist item
    watchlist_item = WatchlistItem(
        user_id=current_user.id,
        listing_id=data.listing_id,
        price_alert_threshold=data.price_alert_threshold,
        last_price=listing.price,
    )
    db.add(watchlist_item)
    await db.commit()
    await db.refresh(watchlist_item)
    return watchlist_item


@router.get("", response_model=List[WatchlistItemWithListing])
async def list_watchlist(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all items in user's watchlist with listing details."""
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.user_id == current_user.id)
        .order_by(desc(WatchlistItem.created_at))
        .offset(skip)
        .limit(limit)
    )
    watchlist_items = result.scalars().all()

    # Fetch listing details for each watchlist item
    response = []
    for item in watchlist_items:
        listing_result = await db.execute(
            select(Listing).where(Listing.id == item.listing_id)
        )
        listing = listing_result.scalar_one_or_none()

        response.append(
            WatchlistItemWithListing(
                id=item.id,
                user_id=item.user_id,
                listing_id=item.listing_id,
                price_alert_threshold=item.price_alert_threshold,
                alert_sent=item.alert_sent,
                last_price=item.last_price,
                created_at=item.created_at,
                updated_at=item.updated_at,
                listing=ListingDetails(
                    id=listing.id,
                    title=listing.title,
                    price=listing.price,
                    category=listing.category,
                    condition=listing.condition.value if listing.condition else None,
                    url=listing.url,
                    thumbnail_url=listing.thumbnail_url,
                ) if listing else None,
            )
        )

    return response


@router.get("/{watchlist_item_id}", response_model=WatchlistItemWithListing)
async def get_watchlist_item(
    watchlist_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific watchlist item with listing details."""
    result = await db.execute(
        select(WatchlistItem).where(
            and_(
                WatchlistItem.id == watchlist_item_id,
                WatchlistItem.user_id == current_user.id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found",
        )

    # Fetch listing details
    listing_result = await db.execute(select(Listing).where(Listing.id == item.listing_id))
    listing = listing_result.scalar_one_or_none()

    return WatchlistItemWithListing(
        id=item.id,
        user_id=item.user_id,
        listing_id=item.listing_id,
        price_alert_threshold=item.price_alert_threshold,
        alert_sent=item.alert_sent,
        last_price=item.last_price,
        created_at=item.created_at,
        updated_at=item.updated_at,
        listing=ListingDetails(
            id=listing.id,
            title=listing.title,
            price=listing.price,
            category=listing.category,
            condition=listing.condition.value if listing.condition else None,
            url=listing.url,
            thumbnail_url=listing.thumbnail_url,
        ) if listing else None,
    )


@router.patch("/{watchlist_item_id}", response_model=WatchlistItemResponse)
async def update_watchlist_item(
    watchlist_item_id: int,
    data: WatchlistItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update price alert threshold for a watchlist item."""
    result = await db.execute(
        select(WatchlistItem).where(
            and_(
                WatchlistItem.id == watchlist_item_id,
                WatchlistItem.user_id == current_user.id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found",
        )

    if data.price_alert_threshold is not None:
        item.price_alert_threshold = data.price_alert_threshold
        item.alert_sent = False  # Reset alert flag when threshold changes

    item.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{watchlist_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    watchlist_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a listing from watchlist."""
    result = await db.execute(
        select(WatchlistItem).where(
            and_(
                WatchlistItem.id == watchlist_item_id,
                WatchlistItem.user_id == current_user.id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found",
        )

    await db.delete(item)
    await db.commit()


@router.post("/{watchlist_item_id}/reset-alert", response_model=WatchlistItemResponse)
async def reset_price_alert(
    watchlist_item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset the price alert flag to receive notifications again."""
    result = await db.execute(
        select(WatchlistItem).where(
            and_(
                WatchlistItem.id == watchlist_item_id,
                WatchlistItem.user_id == current_user.id,
            )
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found",
        )

    item.alert_sent = False
    item.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)
    return item
