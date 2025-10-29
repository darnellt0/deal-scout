from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.models import CrossPost, MyItem, Order
from app.market.ebay_client import (
    EbayApiError,
    EbayAuthError,
    create_offer,
    create_or_update_inventory,
    publish_offer,
)

router = APIRouter()


class MarketplacePostRequest(BaseModel):
    item_id: int
    marketplaces: List[str] = Field(default_factory=list)
    price: Optional[float] = None
    policies: Dict[str, object] = Field(default_factory=dict)


@router.post("/post")
async def post_item(payload: MarketplacePostRequest):
    with get_session() as session:
        item = session.get(MyItem, payload.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found.")
        item_data = {
            "sku": f"DEALSCOUT-{item.id}",
            "title": item.title,
            "description": payload.policies.get("listingDescription") or item.attributes.get("description") or item.title,
            "availableQuantity": int(payload.policies.get("availableQuantity", 1)),
        }
        price = payload.price or float(item.price)

    results: Dict[str, Dict[str, str]] = {}

    if "ebay" in [market.lower() for market in payload.marketplaces]:
        try:
            inventory_response = create_or_update_inventory(item_data)
            offer_response = create_offer(item_data, price, payload.policies)
            offer_id = offer_response.get("offerId") or inventory_response.get("sku")
            if not offer_id:
                raise EbayApiError("Offer ID missing from response.")
            listing_url = publish_offer(offer_id)
        except (EbayApiError, EbayAuthError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        with get_session() as session:
            cross_post = (
                session.query(CrossPost)
                .filter(
                    CrossPost.my_item_id == payload.item_id,
                    CrossPost.platform == "ebay",
                )
                .one_or_none()
            )
            metadata = {
                "inventory": inventory_response,
                "offer": offer_response,
            }
            if cross_post:
                cross_post.external_id = offer_id
                cross_post.listing_url = listing_url
                cross_post.status = "live"
                cross_post.meta = metadata
            else:
                session.add(
                    CrossPost(
                        my_item_id=payload.item_id,
                        platform="ebay",
                        external_id=offer_id,
                        listing_url=listing_url,
                        status="live",
                        meta=metadata,
                    )
                )
            item = session.get(MyItem, payload.item_id)
            if item:
                item.status = "posted"
        results["ebay"] = {"offer_id": offer_id, "url": listing_url}

    return {"posted": results}


@router.post("/webhooks/ebay")
async def ebay_webhook(payload: Dict):
    order_data = payload.get("order") or payload
    offer_id = order_data.get("offerId") or payload.get("offer_id")
    status = (order_data.get("status") or payload.get("status") or "unknown").lower()
    platform_order_id = order_data.get("orderId") or payload.get("order_id") or offer_id
    total = float(order_data.get("total", 0) or payload.get("total", 0) or 0)

    if not offer_id:
        raise HTTPException(status_code=400, detail="Missing offer identifier.")

    with get_session() as session:
        cross_post = (
            session.query(CrossPost)
            .filter(
                CrossPost.platform == "ebay",
                CrossPost.external_id == offer_id,
            )
            .one_or_none()
        )
        if not cross_post:
            raise HTTPException(status_code=404, detail="Cross post not found.")

        order = Order(
            cross_post_id=cross_post.id,
            platform_order_id=platform_order_id,
            status=status,
            total=total,
            meta={"payload": payload},
        )
        session.add(order)

        if status in {"completed", "closed", "fulfilled"}:
            cross_post.status = "closed"
            session.query(CrossPost).filter(
                CrossPost.my_item_id == cross_post.my_item_id,
                CrossPost.id != cross_post.id,
            ).update({"status": "delisted"})

    return {"ok": True}
