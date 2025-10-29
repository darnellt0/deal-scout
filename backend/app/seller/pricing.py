from __future__ import annotations

from statistics import mean, stdev
from typing import List, Optional
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.config import get_settings
from app.core.db import SessionLocal, get_session
from app.core.models import Comp, Condition, MyItem, User
from app.core.auth import get_current_user, require_seller

router = APIRouter()
settings = get_settings()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class PriceSuggestionRequest(BaseModel):
    title: str
    category: str
    condition: Condition = Condition.good
    attributes: dict = {}


class PriceSuggestionResponse(BaseModel):
    suggested_price: float
    comparable_count: int
    comparables: List[dict]


class CompCreateRequest(BaseModel):
    category: str
    title: str
    price: float
    condition: Condition = Condition.good
    source: str
    metadata: dict = {}


FIXTURE_MAP = {
    "furniture>sofas": "sold_comps.couch.json",
    "kitchen>islands": "sold_comps.kitchen_island.json",
}


def load_local_comps(category: str) -> Optional[dict]:
    fixture_name = FIXTURE_MAP.get(category.lower())
    if not fixture_name:
        return None
    fixtures_dir = settings.static_data_dir / "fixtures"
    path = fixtures_dir / fixture_name
    if not path.exists():
        repo_fallback = Path(__file__).resolve().parents[3] / "data" / "fixtures"
        path = repo_fallback / fixture_name
        if not path.exists():
            return None
    return json.loads(path.read_text(encoding="utf-8"))


def response_from_fixture(category: str, condition: Condition) -> Optional[PriceSuggestionResponse]:
    payload = load_local_comps(category)
    if not payload:
        return None
    bucket_map = {
        "excellent": "like_new",
        "great": "like_new",
        "good": "good",
        "fair": "fair",
        "poor": "fair",
    }
    bucket_key = bucket_map.get(condition.value, "good")
    stats = payload["condition_buckets"].get(bucket_key)
    if not stats:
        return None
    examples = [
        {
            "title": example["title"],
            "price": example["price_cents"] / 100.0,
            "condition": bucket_key,
            "source": "fixture",
        }
        for example in payload.get("examples", [])
    ]
    return PriceSuggestionResponse(
        suggested_price=round(stats["median_price_cents"] / 100.0, 2),
        comparable_count=stats.get("n", len(examples)),
        comparables=examples,
    )


@router.post("/pricing/suggest", response_model=PriceSuggestionResponse)
async def suggest_price(payload: PriceSuggestionRequest):
    use_fixture = (
        settings.price_suggestion_mode != "ebay_only" or not settings.ebay_oauth_token
    )

    if use_fixture:
        fixture_response = response_from_fixture(payload.category, payload.condition)
        if fixture_response:
            return fixture_response

    with get_session() as session:
        comps = (
            session.query(Comp)
            .filter(
                Comp.category == payload.category.lower(),
                Comp.condition.in_(
                    [payload.condition, Condition.good, Condition.great, Condition.excellent]
                ),
            )
            .order_by(Comp.observed_at.desc())
            .limit(25)
            .all()
        )

        if not comps:
            raise HTTPException(status_code=404, detail="No comparables available.")

        prices = [comp.price for comp in comps]
        suggested = round(mean(prices), 2)

        return PriceSuggestionResponse(
            suggested_price=suggested,
            comparable_count=len(comps),
            comparables=[
                {
                    "title": comp.title,
                    "price": comp.price,
                    "condition": comp.condition.value if comp.condition else "unknown",
                    "source": comp.source,
                }
                for comp in comps
            ],
        )


@router.get("/pricing/comps", response_model=List[dict])
async def list_comps(category: Optional[str] = Query(default=None)):
    with get_session() as session:
        query = session.query(Comp).order_by(Comp.observed_at.desc()).limit(100)
        if category:
            query = query.filter(Comp.category == category.lower())
        comps = query.all()
        return [
            {
                "title": comp.title,
                "price": comp.price,
                "condition": comp.condition.value if comp.condition else None,
                "source": comp.source,
                "observed_at": comp.observed_at.isoformat(),
            }
            for comp in comps
        ]


@router.post("/pricing/comps")
async def create_comp(payload: CompCreateRequest):
    with get_session() as session:
        record = Comp(
            category=payload.category.lower(),
            title=payload.title,
            price=payload.price,
            condition=payload.condition,
            source=payload.source,
            meta=payload.metadata,
        )
        session.add(record)
        return {"id": record.id}


@router.get("/pricing/my-items")
async def list_my_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List seller's items with pricing (authenticated users only)."""
    items = (
        db.query(MyItem)
        .filter(MyItem.user_id == current_user.id)
        .order_by(MyItem.created_at.desc())
        .all()
    )
    return [
        {
            "id": item.id,
            "title": item.title,
            "category": item.category,
            "price": item.price,
            "status": item.status,
            "attributes": item.attributes,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]


@router.get("/pricing/market-trends")
async def get_market_trends(
    category: str = Query(...),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get market price trends for a category."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    comps = (
        db.query(Comp)
        .filter(
            Comp.category == category.lower(),
            Comp.observed_at >= cutoff_date,
        )
        .order_by(Comp.observed_at)
        .all()
    )

    if not comps:
        raise HTTPException(status_code=404, detail="No data for this category")

    prices = [comp.price for comp in comps]
    conditions_data = {}

    for condition in [Condition.excellent, Condition.great, Condition.good, Condition.fair, Condition.poor]:
        condition_comps = [c for c in comps if c.condition == condition]
        if condition_comps:
            condition_prices = [c.price for c in condition_comps]
            conditions_data[condition.value] = {
                "count": len(condition_prices),
                "min": min(condition_prices),
                "max": max(condition_prices),
                "avg": round(mean(condition_prices), 2),
                "median": round(sorted(condition_prices)[len(condition_prices) // 2], 2),
            }

    return {
        "category": category,
        "period_days": days,
        "total_comps": len(comps),
        "overall": {
            "min": min(prices),
            "max": max(prices),
            "avg": round(mean(prices), 2),
            "median": round(sorted(prices)[len(prices) // 2], 2),
            "stddev": round(stdev(prices), 2) if len(prices) > 1 else 0,
        },
        "by_condition": conditions_data,
    }


@router.get("/pricing/stats")
async def get_pricing_stats(
    category: str = Query(...),
    condition: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get pricing statistics for a category and condition."""
    query = db.query(Comp).filter(Comp.category == category.lower())

    if condition:
        query = query.filter(Comp.condition == condition)

    comps = query.all()

    if not comps:
        raise HTTPException(
            status_code=404,
            detail=f"No data for category: {category}" + (f" and condition: {condition}" if condition else ""),
        )

    prices = [comp.price for comp in comps]

    return {
        "category": category,
        "condition": condition,
        "count": len(comps),
        "min_price": min(prices),
        "max_price": max(prices),
        "avg_price": round(mean(prices), 2),
        "median_price": round(sorted(prices)[len(prices) // 2], 2),
        "stddev": round(stdev(prices), 2) if len(prices) > 1 else 0,
    }


@router.get("/pricing/categories")
async def get_available_categories(
    db: Session = Depends(get_db),
):
    """Get list of categories available for pricing analysis."""
    categories = (
        db.query(func.distinct(Comp.category))
        .filter(Comp.category.isnot(None))
        .order_by(Comp.category)
        .all()
    )

    return {
        "categories": [cat[0] for cat in categories if cat[0]],
    }


@router.post("/pricing/comps")
async def create_comp(
    payload: CompCreateRequest,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Create a new comparable listing (seller only)."""
    record = Comp(
        category=payload.category.lower(),
        title=payload.title,
        price=payload.price,
        condition=payload.condition,
        source=payload.source,
        meta=payload.metadata,
    )
    db.add(record)
    db.commit()

    return {
        "id": record.id,
        "message": "Comparable listing created successfully",
    }
