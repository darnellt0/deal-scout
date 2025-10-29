from __future__ import annotations

from statistics import mean
from typing import List, Optional
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings
from app.core.db import get_session
from app.core.models import Comp, Condition, MyItem

router = APIRouter()
settings = get_settings()


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
async def list_my_items():
    with get_session() as session:
        items = session.query(MyItem).order_by(MyItem.created_at.desc()).all()
        return [
            {
                "id": item.id,
                "title": item.title,
                "category": item.category,
                "price": item.price,
                "status": item.status,
                "attributes": item.attributes,
            }
            for item in items
        ]
