"""Price analysis engine for marketplace listings."""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Listing

logger = logging.getLogger("deal_scout.ml.pricing_analyzer")


class PriceAnalyzer:
    """Analyzes market prices and generates recommendations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_listing_price(
        self, listing_id: int
    ) -> Optional[Dict]:
        """
        Analyze market price for a listing and generate recommendations.

        Returns:
            Dict with market statistics and recommendations, or None if analysis fails.
        """
        try:
            # Get the listing
            result = await self.db.execute(
                select(Listing).where(Listing.id == listing_id)
            )
            listing = result.scalar_one_or_none()

            if not listing:
                logger.warning(f"Listing {listing_id} not found")
                return None

            # Find comparable listings
            comparables = await self.find_comparable_listings(listing)

            if len(comparables) < 3:
                logger.warning(
                    f"Not enough comparables for listing {listing_id} (found {len(comparables)})"
                )
                # Return basic analysis even with few comparables
                if comparables:
                    prices = [c.price for c in comparables]
                    return {
                        "listing_id": listing_id,
                        "analyzed_at": datetime.utcnow(),
                        "market_avg": float(statistics.mean(prices)),
                        "market_median": float(statistics.median(prices)),
                        "market_min": float(min(prices)),
                        "market_max": float(max(prices)),
                        "comparable_count": len(comparables),
                        "recommended_price": float(statistics.median(prices)),
                        "price_range_min": float(min(prices)),
                        "price_range_max": float(max(prices)),
                        "price_trend": "insufficient_data",
                        "trend_pct_change": 0.0,
                        "confidence": "low",
                    }
                return None

            # Calculate market statistics
            prices = [c.price for c in comparables]

            market_avg = statistics.mean(prices)
            market_median = statistics.median(prices)
            market_min = min(prices)
            market_max = max(prices)

            # Calculate percentiles for price range
            sorted_prices = sorted(prices)
            price_range_min = self._percentile(sorted_prices, 0.25)  # 25th percentile
            price_range_max = self._percentile(sorted_prices, 0.75)  # 75th percentile

            # Calculate recommended price based on listing features
            recommended_price = await self._calculate_optimal_price(
                listing, comparables, market_median
            )

            # Analyze price trend
            trend, trend_pct_change = await self._analyze_price_trend(listing)

            # Determine confidence level
            confidence = self._determine_confidence(len(comparables), prices)

            return {
                "listing_id": listing_id,
                "analyzed_at": datetime.utcnow(),
                "market_avg": float(market_avg),
                "market_median": float(market_median),
                "market_min": float(market_min),
                "market_max": float(market_max),
                "comparable_count": len(comparables),
                "recommended_price": float(recommended_price),
                "price_range_min": float(price_range_min),
                "price_range_max": float(price_range_max),
                "price_trend": trend,
                "trend_pct_change": float(trend_pct_change),
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error analyzing listing {listing_id}: {e}", exc_info=True)
            return None

    async def find_comparable_listings(
        self, listing: Listing, limit: int = 50
    ) -> List[Listing]:
        """
        Find comparable listings for price analysis.

        Criteria for comparables:
        - Same category
        - Similar condition (if available)
        - Created within last 90 days
        - Available or recently sold
        - Price within reasonable range (0.3x to 3x of target price)
        """
        try:
            # Build query
            query = select(Listing).where(
                and_(
                    Listing.id != listing.id,  # Exclude self
                    Listing.category == listing.category,
                    Listing.created_at
                    >= datetime.utcnow() - timedelta(days=90),  # Recent listings
                )
            )

            # Filter by price range (0.3x to 3x)
            if listing.price:
                min_price = listing.price * 0.3
                max_price = listing.price * 3.0
                query = query.where(
                    and_(
                        Listing.price >= min_price,
                        Listing.price <= max_price,
                    )
                )

            # Prefer same condition if available
            if hasattr(listing, "condition") and listing.condition:
                query = query.where(
                    or_(
                        Listing.condition == listing.condition,
                        Listing.condition.is_(None),
                    )
                )

            # Order by relevance (same condition first, then by recency)
            query = query.order_by(Listing.created_at.desc()).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            comparables = result.scalars().all()

            logger.info(
                f"Found {len(comparables)} comparable listings for listing {listing.id}"
            )
            return list(comparables)

        except Exception as e:
            logger.error(
                f"Error finding comparables for listing {listing.id}: {e}",
                exc_info=True,
            )
            return []

    async def _calculate_optimal_price(
        self, listing: Listing, comparables: List[Listing], base_price: float
    ) -> float:
        """
        Calculate optimal recommended price based on market data and listing features.

        Adjustments:
        - Condition: excellent (+5%), good (+2%), fair (-5%), poor (-10%)
        - Recency: listings < 7 days old (+3%)
        - Deal score: high scoring items get slight premium (+2%)
        """
        recommended_price = base_price
        adjustments = 0.0

        # Condition adjustment
        if hasattr(listing, "condition") and listing.condition:
            condition = listing.condition.value if hasattr(listing.condition, "value") else str(listing.condition)

            condition_adjustments = {
                "excellent": 0.05,  # +5%
                "good": 0.02,  # +2%
                "fair": -0.05,  # -5%
                "poor": -0.10,  # -10%
                "like new": 0.07,  # +7%
                "new": 0.10,  # +10%
            }

            adjustment = condition_adjustments.get(condition.lower(), 0.0)
            adjustments += adjustment
            logger.debug(f"Condition adjustment ({condition}): {adjustment*100:.1f}%")

        # Recency bonus (newer listings might command premium)
        if listing.created_at:
            days_old = (datetime.utcnow() - listing.created_at).days
            if days_old < 7:
                recency_bonus = 0.03
                adjustments += recency_bonus
                logger.debug(f"Recency bonus: {recency_bonus*100:.1f}%")

        # Deal score bonus (if listing has good deal score, might justify premium)
        if hasattr(listing, "deal_score") and listing.deal_score:
            score_value = listing.deal_score.value if hasattr(listing.deal_score, "value") else float(listing.deal_score)
            if score_value >= 0.8:
                score_bonus = 0.02
                adjustments += score_bonus
                logger.debug(f"Deal score bonus: {score_bonus*100:.1f}%")

        # Apply adjustments
        recommended_price = base_price * (1 + adjustments)

        # Ensure price is positive and reasonable
        recommended_price = max(0.01, recommended_price)

        logger.debug(
            f"Calculated optimal price: ${recommended_price:.2f} "
            f"(base: ${base_price:.2f}, adjustment: {adjustments*100:.1f}%)"
        )

        return recommended_price

    async def _analyze_price_trend(self, listing: Listing) -> Tuple[str, float]:
        """
        Analyze price trend for similar listings over past 30 days.

        Returns:
            Tuple of (trend_direction, trend_percentage)
            trend_direction: "increasing", "stable", "decreasing"
            trend_percentage: percentage change
        """
        try:
            # Get listings from 30 days ago vs recent (last 7 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)

            # Old period (30-7 days ago)
            old_query = select(Listing).where(
                and_(
                    Listing.category == listing.category,
                    Listing.created_at >= thirty_days_ago,
                    Listing.created_at < seven_days_ago,
                )
            )

            # Recent period (last 7 days)
            recent_query = select(Listing).where(
                and_(
                    Listing.category == listing.category,
                    Listing.created_at >= seven_days_ago,
                )
            )

            # Execute queries
            old_result = await self.db.execute(old_query)
            old_listings = old_result.scalars().all()

            recent_result = await self.db.execute(recent_query)
            recent_listings = recent_result.scalars().all()

            if len(old_listings) < 3 or len(recent_listings) < 3:
                return "insufficient_data", 0.0

            # Calculate average prices
            old_avg = statistics.mean([l.price for l in old_listings])
            recent_avg = statistics.mean([l.price for l in recent_listings])

            # Calculate percentage change
            pct_change = ((recent_avg - old_avg) / old_avg) * 100

            # Determine trend
            if pct_change > 5:
                trend = "increasing"
            elif pct_change < -5:
                trend = "decreasing"
            else:
                trend = "stable"

            logger.debug(
                f"Price trend for {listing.category}: {trend} ({pct_change:+.1f}%)"
            )

            return trend, pct_change

        except Exception as e:
            logger.error(f"Error analyzing price trend: {e}", exc_info=True)
            return "unknown", 0.0

    @staticmethod
    def _percentile(sorted_data: List[float], percentile: float) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0

        n = len(sorted_data)
        k = (n - 1) * percentile
        f = int(k)
        c = k - f

        if f + 1 < n:
            return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
        else:
            return sorted_data[f]

    @staticmethod
    def _determine_confidence(comparable_count: int, prices: List[float]) -> str:
        """
        Determine confidence level of price analysis.

        Factors:
        - Number of comparables
        - Price variance (standard deviation)
        """
        # Check sample size
        if comparable_count < 5:
            return "low"
        elif comparable_count < 10:
            confidence = "medium"
        else:
            confidence = "high"

        # Adjust for price variance
        if len(prices) > 1:
            std_dev = statistics.stdev(prices)
            mean_price = statistics.mean(prices)
            coefficient_of_variation = std_dev / mean_price

            # High variance reduces confidence
            if coefficient_of_variation > 0.5:
                if confidence == "high":
                    confidence = "medium"
                elif confidence == "medium":
                    confidence = "low"

        return confidence

    async def get_market_summary(self, category: str) -> Optional[Dict]:
        """Get market summary statistics for a category."""
        try:
            # Get listings from last 30 days
            cutoff = datetime.utcnow() - timedelta(days=30)

            query = select(Listing).where(
                and_(
                    Listing.category == category,
                    Listing.created_at >= cutoff,
                )
            )

            result = await self.db.execute(query)
            listings = result.scalars().all()

            if not listings:
                return None

            prices = [l.price for l in listings]

            return {
                "category": category,
                "listing_count": len(listings),
                "avg_price": float(statistics.mean(prices)),
                "median_price": float(statistics.median(prices)),
                "min_price": float(min(prices)),
                "max_price": float(max(prices)),
                "period_days": 30,
            }

        except Exception as e:
            logger.error(f"Error getting market summary for {category}: {e}")
            return None
