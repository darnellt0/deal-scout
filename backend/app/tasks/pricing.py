"""
Pricing task module for the Snap Job pipeline.

This module handles pulling comparable listings (comps) and suggesting prices
for items detected in snap jobs.
"""
from __future__ import annotations

from statistics import mean, median, stdev
from typing import Optional, List
from celery import shared_task

from app.core.db import get_session
from app.core.models import SnapJob, Comp, Condition
from app.seller.pricing import load_local_comps


def calculate_price_range(prices: List[float]) -> tuple[float, float, float]:
    """
    Calculate suggested price and price range from a list of comparable prices.

    Returns (price_low, price_suggested, price_high)
    """
    if not prices:
        return 0.0, 0.0, 0.0

    sorted_prices = sorted(prices)
    n = len(sorted_prices)

    # Use median as the suggested price
    suggested = median(sorted_prices)

    # Calculate range using 25th and 75th percentiles if we have enough data
    if n >= 4:
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        price_low = sorted_prices[q1_idx]
        price_high = sorted_prices[q3_idx]
    else:
        # For small datasets, use min and max
        price_low = sorted_prices[0]
        price_high = sorted_prices[-1]

    return round(price_low, 2), round(suggested, 2), round(price_high, 2)


def generate_pricing_rationale(
    category: str,
    condition: str,
    comp_count: int,
    price_low: float,
    price_suggested: float,
    price_high: float,
    locale: str,
) -> str:
    """Generate a human-readable rationale for the pricing suggestion."""
    condition_text = condition.replace("_", " ").title() if condition else "Good"

    rationale_parts = [
        f"Based on {comp_count} comparable {'sale' if comp_count == 1 else 'sales'} ",
        f"of {category.replace('>', ' > ')} items ",
        f"in {condition_text} condition near {locale}."
    ]

    if price_low != price_high:
        rationale_parts.append(
            f"\n\nPrice range: ${price_low:.2f} - ${price_high:.2f}"
        )
        rationale_parts.append(
            f"\nSuggested price of ${price_suggested:.2f} represents the median market value."
        )
    else:
        rationale_parts.append(
            f"\n\nLimited data available. Suggested price: ${price_suggested:.2f}"
        )

    return "".join(rationale_parts)


@shared_task(name="app.tasks.pricing.suggest_price")
def suggest_price(job_id: int, locale: str = "San Jose, CA") -> dict:
    """
    Pull comparable listings and suggest a price for the snap job item.

    This task:
    1. Retrieves the SnapJob and its detected category/attributes/condition
    2. Queries the Comp table for similar items
    3. Calculates price_low, price_suggested, price_high
    4. Generates a rationale explaining the pricing
    5. Stores results in SnapJob.meta.pricing

    Args:
        job_id: The SnapJob ID to price
        locale: Location string for geo-specific pricing (e.g., "San Jose, CA")

    Returns:
        dict with status and pricing data
    """
    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            return {"error": "job not found", "job_id": job_id}

        category = job.detected_category
        condition = job.condition_guess

        if not category:
            # Store empty pricing data if no category detected
            if not job.meta:
                job.meta = {}
            job.meta["pricing"] = {
                "error": "No category detected",
                "price_suggested": 0.0,
                "price_low": 0.0,
                "price_high": 0.0,
                "rationale": "Unable to suggest price without category information.",
                "locale": locale,
                "comp_count": 0,
            }
            session.commit()
            return {"status": "error", "message": "No category detected"}

        # Try to load comps from fixtures first (for demo data)
        fixture_data = load_local_comps(category)
        prices = []
        comp_count = 0

        if fixture_data:
            # Use fixture data if available
            bucket_map = {
                "excellent": "like_new",
                "great": "like_new",
                "good": "good",
                "fair": "fair",
                "poor": "fair",
            }
            bucket_key = bucket_map.get(condition, "good") if condition else "good"
            stats = fixture_data.get("condition_buckets", {}).get(bucket_key)

            if stats:
                # Get example prices from fixture
                examples = fixture_data.get("examples", [])
                prices = [ex["price_cents"] / 100.0 for ex in examples if "price_cents" in ex]
                comp_count = stats.get("n", len(prices))

        # If no fixture data or not enough prices, query database comps
        if not prices or len(prices) < 3:
            # Build condition filter
            condition_filters = [Condition.good, Condition.great, Condition.excellent]
            if condition:
                try:
                    cond_enum = Condition(condition)
                    if cond_enum not in condition_filters:
                        condition_filters.append(cond_enum)
                except (ValueError, KeyError):
                    pass

            # Query comps from database
            comps = (
                session.query(Comp)
                .filter(
                    Comp.category == category.lower(),
                    Comp.condition.in_(condition_filters)
                )
                .order_by(Comp.observed_at.desc())
                .limit(50)
                .all()
            )

            # Extract prices
            db_prices = [comp.price for comp in comps]
            if db_prices:
                prices = db_prices
                comp_count = len(comps)

        # Calculate price range
        if prices:
            price_low, price_suggested, price_high = calculate_price_range(prices)
        else:
            # No comps available - use fallback
            price_low = price_suggested = price_high = 50.0
            comp_count = 0

        # Generate rationale
        rationale = generate_pricing_rationale(
            category=category,
            condition=condition or "good",
            comp_count=comp_count,
            price_low=price_low,
            price_suggested=price_suggested,
            price_high=price_high,
            locale=locale,
        )

        # Store in job.meta.pricing
        if not job.meta:
            job.meta = {}

        job.meta["pricing"] = {
            "price_suggested": price_suggested,
            "price_low": price_low,
            "price_high": price_high,
            "rationale": rationale,
            "locale": locale,
            "comp_count": comp_count,
            "comps": [
                {"price": p, "source": "fixture" if fixture_data else "database"}
                for p in prices[:10]  # Store first 10 comps as reference
            ],
        }

        # Also update the legacy fields for backward compatibility
        job.suggested_price = price_suggested
        job.price_suggestion_cents = int(price_suggested * 100)

        session.commit()

        return {
            "status": "success",
            "job_id": job_id,
            "pricing": job.meta["pricing"],
        }
