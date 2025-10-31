"""Deal Alert Rules API endpoints for Phase 7."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal
from app.core.models import DealAlertRule, Listing, User
from app.core.auth import get_current_user

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/deal-alert-rules", tags=["deal-alerts"])


# ============================================================================
# SCHEMAS (Pydantic Models)
# ============================================================================


from pydantic import BaseModel


class DealAlertRuleCreate(BaseModel):
    """Schema for creating a deal alert rule."""
    name: str
    keywords: List[str] = []
    exclude_keywords: List[str] = []
    categories: List[str] = []
    condition: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    location: Optional[str] = None
    radius_mi: Optional[int] = None
    min_deal_score: Optional[float] = None
    notification_channels: List[str] = ["email"]
    enabled: bool = True


class DealAlertRuleUpdate(BaseModel):
    """Schema for updating a deal alert rule."""
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    condition: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    location: Optional[str] = None
    radius_mi: Optional[int] = None
    min_deal_score: Optional[float] = None
    notification_channels: Optional[List[str]] = None
    enabled: Optional[bool] = None


class DealAlertRuleResponse(BaseModel):
    """Schema for returning a deal alert rule."""
    id: int
    user_id: int
    name: str
    enabled: bool
    keywords: List[str]
    exclude_keywords: List[str]
    categories: List[str]
    condition: Optional[str]
    min_price: Optional[float]
    max_price: Optional[float]
    location: Optional[str]
    radius_mi: Optional[int]
    min_deal_score: Optional[float]
    notification_channels: List[str]
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DealAlertRuleResponse)
async def create_deal_alert_rule(
    rule_data: DealAlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new deal alert rule for the current user."""
    new_rule = DealAlertRule(
        user_id=current_user.id,
        name=rule_data.name,
        keywords=rule_data.keywords,
        exclude_keywords=rule_data.exclude_keywords,
        categories=rule_data.categories,
        condition=rule_data.condition,
        min_price=rule_data.min_price,
        max_price=rule_data.max_price,
        location=rule_data.location,
        radius_mi=rule_data.radius_mi,
        min_deal_score=rule_data.min_deal_score,
        notification_channels=rule_data.notification_channels,
        enabled=rule_data.enabled,
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule


@router.get("", response_model=List[DealAlertRuleResponse])
async def list_deal_alert_rules(
    enabled_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all deal alert rules for the current user."""
    query = select(DealAlertRule).where(
        DealAlertRule.user_id == current_user.id
    )

    if enabled_only:
        query = query.where(DealAlertRule.enabled == True)

    query = query.order_by(desc(DealAlertRule.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    rules = result.scalars().all()
    return rules


@router.get("/{rule_id}", response_model=DealAlertRuleResponse)
async def get_deal_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific deal alert rule."""
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.id == rule_id,
                DealAlertRule.user_id == current_user.id,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    return rule


@router.patch("/{rule_id}", response_model=DealAlertRuleResponse)
async def update_deal_alert_rule(
    rule_id: int,
    rule_data: DealAlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a deal alert rule."""
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.id == rule_id,
                DealAlertRule.user_id == current_user.id,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Update only provided fields
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a deal alert rule."""
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.id == rule_id,
                DealAlertRule.user_id == current_user.id,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    await db.delete(rule)
    await db.commit()


@router.post("/{rule_id}/test", response_model=dict)
async def test_deal_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test a deal alert rule and return matching listings."""
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.id == rule_id,
                DealAlertRule.user_id == current_user.id,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # Find matching listings
    matching_listings = await _find_matching_listings(db, rule)

    return {
        "rule_id": rule_id,
        "matching_count": len(matching_listings),
        "sample_matches": [
            {
                "id": listing.id,
                "title": listing.title,
                "price": listing.price,
                "category": listing.category,
                "condition": listing.condition.value if listing.condition else None,
            }
            for listing in matching_listings[:5]
        ],
    }


@router.post("/{rule_id}/pause", status_code=status.HTTP_200_OK)
async def pause_deal_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Temporarily disable a deal alert rule."""
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.id == rule_id,
                DealAlertRule.user_id == current_user.id,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    rule.enabled = False
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return {"status": "paused", "rule_id": rule_id}


@router.post("/{rule_id}/resume", status_code=status.HTTP_200_OK)
async def resume_deal_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-enable a paused deal alert rule."""
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.id == rule_id,
                DealAlertRule.user_id == current_user.id,
            )
        )
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    rule.enabled = True
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return {"status": "resumed", "rule_id": rule_id}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def _find_matching_listings(db: AsyncSession, rule: DealAlertRule) -> List[Listing]:
    """Find listings that match a deal alert rule."""
    query = select(Listing).where(Listing.available == True)

    # Price range filter
    if rule.min_price is not None:
        query = query.where(Listing.price >= rule.min_price)
    if rule.max_price is not None:
        query = query.where(Listing.price <= rule.max_price)

    # Category filter (OR logic)
    if rule.categories:
        query = query.where(Listing.category.in_(rule.categories))

    # Condition filter
    if rule.condition:
        query = query.where(Listing.condition == rule.condition)

    # Execute query
    result = await db.execute(query.limit(100))
    listings = result.scalars().all()

    # Filter by keywords (in-memory, after basic DB filters)
    filtered_listings = []
    for listing in listings:
        # Check keywords (OR logic - match any)
        if rule.keywords:
            title_lower = listing.title.lower()
            desc_lower = (listing.description or "").lower()
            keyword_match = any(
                keyword.lower() in title_lower or keyword.lower() in desc_lower
                for keyword in rule.keywords
            )
            if not keyword_match:
                continue

        # Check exclude keywords (NOT logic - exclude all)
        if rule.exclude_keywords:
            title_lower = listing.title.lower()
            desc_lower = (listing.description or "").lower()
            exclude_match = any(
                keyword.lower() in title_lower or keyword.lower() in desc_lower
                for keyword in rule.exclude_keywords
            )
            if exclude_match:
                continue

        filtered_listings.append(listing)

    return filtered_listings
