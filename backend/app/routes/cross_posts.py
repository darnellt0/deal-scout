"""Seller cross-post inventory endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require_seller
from app.core.db import SessionLocal
from app.core.models import CrossPost, MyItem, User
from app.schemas.cross_post import CrossPostItemSummary, CrossPostListing

router = APIRouter(prefix="/cross-posts", tags=["cross-posts"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[CrossPostListing])
async def list_cross_posts(
    status: Optional[str] = Query(default=None, description="Filter by cross-post status"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
) -> List[CrossPostListing]:
    """
    List cross-posted listings for the current seller.

    Admins can view all cross posts; sellers are scoped to their own items.
    """
    query = (
        db.query(CrossPost, MyItem)
        .join(MyItem, CrossPost.my_item_id == MyItem.id)
        .order_by(CrossPost.created_at.desc())
    )

    if status:
        query = query.filter(CrossPost.status == status)

    if current_user.role.value != "admin":
        query = query.filter(MyItem.user_id == current_user.id)

    rows = query.limit(limit).all()

    listings: List[CrossPostListing] = []
    for cross_post, item in rows:
        metadata = cross_post.meta or {}
        listing = CrossPostListing(
            id=cross_post.id,
            platform=cross_post.platform,
            status=cross_post.status,
            listing_url=cross_post.listing_url or None,
            created_at=cross_post.created_at,
            metadata=metadata,
            notes=metadata.get("notes"),
            snap_job_id=metadata.get("snap_job_id"),
            item=CrossPostItemSummary(
                id=item.id,
                title=item.title,
                price=float(item.price or 0),
                status=item.status,
            ),
        )
        listings.append(listing)

    return listings
