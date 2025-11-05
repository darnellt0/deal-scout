"""Pricing Analytics API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import SessionLocal
from app.core.models import Listing, PriceAnalysis, User
from app.ml.pricing_analyzer import PriceAnalyzer

router = APIRouter(prefix="/pricing", tags=["pricing"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# SCHEMAS
# ============================================================================


class PriceAnalysisResponse(BaseModel):
    """Price analysis response schema."""

    listing_id: int
    analyzed_at: datetime
    market_avg: float
    market_median: float
    market_min: float
    market_max: float
    comparable_count: int
    recommended_price: float
    price_range_min: float
    price_range_max: float
    price_trend: str
    trend_pct_change: float
    confidence: str

    class Config:
        from_attributes = True


class ComparableListingResponse(BaseModel):
    """Comparable listing response schema."""

    id: int
    title: str
    price: float
    category: Optional[str]
    condition: Optional[str]
    created_at: datetime
    url: str


class MarketSummaryResponse(BaseModel):
    """Market summary response schema."""

    category: str
    listing_count: int
    avg_price: float
    median_price: float
    min_price: float
    max_price: float
    period_days: int


class BatchAnalysisRequest(BaseModel):
    """Batch analysis request schema."""

    listing_ids: List[int]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/analyze/{listing_id}", response_model=PriceAnalysisResponse)
async def analyze_listing_price(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger price analysis for a listing.

    This will analyze comparable listings and generate price recommendations.
    """
    # Verify listing exists
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )

    # Run analysis
    analyzer = PriceAnalyzer(db)
    analysis_data = await analyzer.analyze_listing_price(listing_id)

    if not analysis_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to analyze listing - insufficient comparable data",
        )

    # Save to database
    analysis = PriceAnalysis(**analysis_data)
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    return analysis


@router.get("/analysis/{listing_id}", response_model=PriceAnalysisResponse)
async def get_price_analysis(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get cached price analysis for a listing.

    Returns the most recent analysis if available.
    """
    # Get most recent analysis
    result = await db.execute(
        select(PriceAnalysis)
        .where(PriceAnalysis.listing_id == listing_id)
        .order_by(desc(PriceAnalysis.analyzed_at))
        .limit(1)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found for this listing. Run analysis first.",
        )

    return analysis


@router.get("/comparables/{listing_id}", response_model=List[ComparableListingResponse])
async def get_comparable_listings(
    listing_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comparable listings for price analysis.

    Useful for sellers to see competition and market pricing.
    """
    # Get listing
    result = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found"
        )

    # Find comparables
    analyzer = PriceAnalyzer(db)
    comparables = await analyzer.find_comparable_listings(listing, limit=limit)

    return [
        ComparableListingResponse(
            id=c.id,
            title=c.title,
            price=float(c.price),
            category=c.category,
            condition=(
                c.condition.value if hasattr(c, "condition") and c.condition else None
            ),
            created_at=c.created_at,
            url=c.url,
        )
        for c in comparables
    ]


@router.get("/market-summary/{category}", response_model=MarketSummaryResponse)
async def get_market_summary(
    category: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get market summary statistics for a category.

    Provides average prices, listing counts, and market trends.
    """
    analyzer = PriceAnalyzer(db)
    summary = await analyzer.get_market_summary(category)

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market data found for category '{category}'",
        )

    return MarketSummaryResponse(**summary)


@router.post("/batch-analyze", response_model=List[PriceAnalysisResponse])
async def batch_analyze_listings(
    request: BatchAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze multiple listings in batch.

    Useful for sellers to analyze all their items at once.
    """
    if len(request.listing_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 listings can be analyzed at once",
        )

    analyzer = PriceAnalyzer(db)
    results = []

    for listing_id in request.listing_ids:
        try:
            analysis_data = await analyzer.analyze_listing_price(listing_id)

            if analysis_data:
                # Save to database
                analysis = PriceAnalysis(**analysis_data)
                db.add(analysis)
                results.append(analysis)
        except Exception as e:
            # Log error but continue with other listings
            print(f"Error analyzing listing {listing_id}: {e}")
            continue

    if results:
        await db.commit()
        for analysis in results:
            await db.refresh(analysis)

    return results


@router.get("/seller/optimize", response_model=List[PriceAnalysisResponse])
async def optimize_seller_pricing(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze pricing for all of the current seller's active items.

    Returns price recommendations for optimization.
    """
    # Get seller's items (this would need to query MyItems table)
    # For now, we'll analyze listings associated with the user
    # This is a simplified version - you may need to adjust based on your data model

    analyzer = PriceAnalyzer(db)

    # Get listings (would typically be seller's listings)
    # For demo, let's analyze recent listings in general
    result = await db.execute(
        select(Listing)
        .where(Listing.available == True)
        .order_by(desc(Listing.created_at))
        .limit(20)
    )
    listings = result.scalars().all()

    results = []
    for listing in listings:
        try:
            # Check if analysis already exists and is recent
            analysis_result = await db.execute(
                select(PriceAnalysis)
                .where(
                    and_(
                        PriceAnalysis.listing_id == listing.id,
                        PriceAnalysis.analyzed_at
                        >= datetime.utcnow() - timedelta(days=1),
                    )
                )
                .order_by(desc(PriceAnalysis.analyzed_at))
                .limit(1)
            )
            existing_analysis = analysis_result.scalar_one_or_none()

            if existing_analysis:
                results.append(existing_analysis)
            else:
                # Run new analysis
                analysis_data = await analyzer.analyze_listing_price(listing.id)
                if analysis_data:
                    analysis = PriceAnalysis(**analysis_data)
                    db.add(analysis)
                    results.append(analysis)

        except Exception as e:
            print(f"Error analyzing listing {listing.id}: {e}")
            continue

    if results:
        await db.commit()
        for analysis in results:
            await db.refresh(analysis)

    return results


# Add missing import at top
from datetime import timedelta
