from __future__ import annotations

from typing import Dict, List, Optional
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.auth import get_current_user
from app.core.models import CrossPost, MyItem, Order, User, MarketplaceAccount
from app.market.ebay_client import (
    EbayApiError,
    EbayAuthError,
    create_offer,
    create_or_update_inventory,
    publish_offer,
)
from app.market.facebook_client import FacebookMarketplaceClient
from app.market.offerup_client import OfferupClient

logger = logging.getLogger(__name__)

router = APIRouter()


class MarketplacePostRequest(BaseModel):
    item_id: int
    marketplaces: List[str] = Field(default_factory=list)
    price: Optional[float] = None
    policies: Dict[str, object] = Field(default_factory=dict)


@router.post("/post")
async def post_item(
    payload: MarketplacePostRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Post item to multiple marketplaces (eBay, Facebook, Offerup).

    Supports posting to:
    - eBay: Uses existing eBay client
    - Facebook: Uses Facebook Marketplace via OAuth token
    - Offerup: Uses Offerup marketplace via OAuth token
    """
    with get_session() as session:
        item = session.get(MyItem, payload.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found.")

        # Get item images for marketplace posting
        item_images = item.attributes.get("images", []) if item.attributes else []

        item_data = {
            "sku": f"DEALSCOUT-{item.id}",
            "title": item.title,
            "description": payload.policies.get("listingDescription") or item.attributes.get("description") or item.title,
            "availableQuantity": int(payload.policies.get("availableQuantity", 1)),
        }
        price = payload.price or float(item.price)

    results: Dict[str, Dict[str, str]] = {}
    marketplaces_lower = [market.lower() for market in payload.marketplaces]

    # Process eBay posting
    if "ebay" in marketplaces_lower:
        try:
            inventory_response = create_or_update_inventory(item_data)
            offer_response = create_offer(item_data, price, payload.policies)
            offer_id = offer_response.get("offerId") or inventory_response.get("sku")
            if not offer_id:
                raise EbayApiError("Offer ID missing from response.")
            listing_url = publish_offer(offer_id)
        except (EbayApiError, EbayAuthError) as exc:
            logger.error(f"Failed to post to eBay: {exc}")
            results["ebay"] = {"status": "failed", "error": str(exc)}
        else:
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
                session.commit()
            results["ebay"] = {"offer_id": offer_id, "url": listing_url, "status": "success"}

    # Process Facebook Marketplace posting
    if "facebook" in marketplaces_lower:
        try:
            with get_session() as session:
                facebook_account = session.query(MarketplaceAccount).filter(
                    MarketplaceAccount.user_id == current_user.id,
                    MarketplaceAccount.marketplace == "facebook",
                    MarketplaceAccount.is_active == True,
                ).first()

                if not facebook_account or not facebook_account.access_token:
                    results["facebook"] = {
                        "status": "failed",
                        "error": "Facebook Marketplace account not connected. Please connect your account first."
                    }
                elif not facebook_account.marketplace_account_id:
                    results["facebook"] = {
                        "status": "failed",
                        "error": "Facebook page ID not stored. Please reconnect your account."
                    }
                else:
                    # FacebookMarketplaceClient requires page_id
                    page_id = facebook_account.marketplace_account_id
                    client = FacebookMarketplaceClient(facebook_account.access_token, page_id)
                    listing_id = await client.post_item(
                        title=item_data["title"],
                        description=item_data["description"],
                        price=price,
                        images=item_images,
                        category=item.category if hasattr(item, 'category') else None,
                        condition=item.condition.value if hasattr(item, 'condition') and item.condition else None,
                    )

                    if listing_id:
                        listing_url = client.get_listing_url(listing_id)
                        with get_session() as session_inner:
                            cross_post = (
                                session_inner.query(CrossPost)
                                .filter(
                                    CrossPost.my_item_id == payload.item_id,
                                    CrossPost.platform == "facebook",
                                )
                                .one_or_none()
                            )
                            metadata = {"listing_id": listing_id, "page_id": facebook_account.marketplace_account_id}
                            if cross_post:
                                cross_post.external_id = listing_id
                                cross_post.listing_url = listing_url
                                cross_post.status = "live"
                                cross_post.meta = metadata
                            else:
                                session_inner.add(
                                    CrossPost(
                                        my_item_id=payload.item_id,
                                        platform="facebook",
                                        external_id=listing_id,
                                        listing_url=listing_url,
                                        status="live",
                                        meta=metadata,
                                    )
                                )
                            session_inner.commit()
                        results["facebook"] = {"listing_id": listing_id, "url": listing_url, "status": "success"}
                    else:
                        results["facebook"] = {"status": "failed", "error": "Failed to post to Facebook Marketplace"}
        except Exception as exc:
            logger.error(f"Failed to post to Facebook: {exc}")
            results["facebook"] = {"status": "failed", "error": str(exc)}

    # Process Offerup posting
    if "offerup" in marketplaces_lower:
        try:
            with get_session() as session:
                offerup_account = session.query(MarketplaceAccount).filter(
                    MarketplaceAccount.user_id == current_user.id,
                    MarketplaceAccount.marketplace == "offerup",
                    MarketplaceAccount.is_active == True,
                ).first()

                if not offerup_account or not offerup_account.access_token:
                    results["offerup"] = {
                        "status": "failed",
                        "error": "Offerup account not connected. Please connect your account first."
                    }
                else:
                    # Get seller location from user profile or use default
                    user_location = current_user.profile.get("location", {}) if hasattr(current_user, 'profile') else {}
                    latitude = user_location.get("latitude", 37.3382)  # San Jose default
                    longitude = user_location.get("longitude", -121.8863)

                    client = OfferupClient(offerup_account.access_token)
                    listing_id = await client.post_item(
                        title=item_data["title"],
                        description=item_data["description"],
                        price=price,
                        images=item_images,
                        latitude=latitude,
                        longitude=longitude,
                        category=item.category if hasattr(item, 'category') else None,
                        condition=item.condition.value if hasattr(item, 'condition') and item.condition else None,
                    )

                    if listing_id:
                        listing_url = client.get_listing_url(listing_id)
                        with get_session() as session_inner:
                            cross_post = (
                                session_inner.query(CrossPost)
                                .filter(
                                    CrossPost.my_item_id == payload.item_id,
                                    CrossPost.platform == "offerup",
                                )
                                .one_or_none()
                            )
                            metadata = {"listing_id": listing_id, "user_id": offerup_account.marketplace_account_id}
                            if cross_post:
                                cross_post.external_id = listing_id
                                cross_post.listing_url = listing_url
                                cross_post.status = "live"
                                cross_post.meta = metadata
                            else:
                                session_inner.add(
                                    CrossPost(
                                        my_item_id=payload.item_id,
                                        platform="offerup",
                                        external_id=listing_id,
                                        listing_url=listing_url,
                                        status="live",
                                        meta=metadata,
                                    )
                                )
                            session_inner.commit()
                        results["offerup"] = {"listing_id": listing_id, "url": listing_url, "status": "success"}
                    else:
                        results["offerup"] = {"status": "failed", "error": "Failed to post to Offerup"}
        except Exception as exc:
            logger.error(f"Failed to post to Offerup: {exc}")
            results["offerup"] = {"status": "failed", "error": str(exc)}

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
