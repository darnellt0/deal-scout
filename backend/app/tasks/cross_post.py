from __future__ import annotations

import logging
from typing import Dict, List, Optional

from celery import shared_task

from app.core.db import get_session
from app.core.models import CrossPost, MyItem, SnapJob, MarketplaceAccount, User
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


def generate_marketplace_metadata(
    item: MyItem,
    platform: str,
    user: User,
) -> Dict:
    """
    Generate platform-specific metadata for cross-posting.

    Args:
        item: The MyItem to generate metadata for
        platform: Target marketplace (ebay, facebook, offerup)
        user: The user who owns the item

    Returns:
        Dictionary with platform-specific fields and metadata
    """
    metadata = {
        "item_id": item.id,
        "platform": platform,
        "prepared_at": None,  # Will be set when actually prepared
    }

    if platform == "ebay":
        # eBay-specific metadata
        metadata.update({
            "sku": f"DEALSCOUT-{item.id}",
            "format": "FIXED_PRICE",
            "listing_duration": "GTC",  # Good 'Til Cancelled
            "quantity": 1,
            "category_id": _map_category_to_ebay(item.category),
            "item_specifics": _generate_ebay_item_specifics(item),
            "shipping_policy": "standard",
            "return_policy": "30_days",
            "payment_policy": "immediate",
        })

    elif platform == "facebook":
        # Facebook Marketplace-specific metadata
        metadata.update({
            "availability": "in_stock",
            "visibility": "PUBLIC",
            "category": _map_category_to_facebook(item.category),
            "condition": item.condition.value if item.condition else "used_good",
            "custom_label_0": f"DealScout-{item.id}",
        })

    elif platform == "offerup":
        # OfferUp-specific metadata
        user_location = user.profile.get("location", {}) if hasattr(user, 'profile') and user.profile else {}
        metadata.update({
            "latitude": user_location.get("latitude", 37.3382),  # San Jose default
            "longitude": user_location.get("longitude", -121.8863),
            "category": _map_category_to_offerup(item.category),
            "condition": item.condition.value if item.condition else "good",
            "shipping_enabled": False,  # Local pickup only by default
        })

    return metadata


def _map_category_to_ebay(category: str) -> str:
    """Map internal category to eBay category ID."""
    category_map = {
        "electronics": "293",
        "clothing": "11450",
        "shoes": "93427",
        "furniture": "3197",
        "books": "267",
        "toys": "220",
        "couch": "3197",
        "other": "1",
    }
    return category_map.get(category.lower(), "1")


def _map_category_to_facebook(category: str) -> str:
    """Map internal category to Facebook Marketplace category."""
    category_map = {
        "electronics": "electronics",
        "clothing": "apparel",
        "shoes": "shoes",
        "furniture": "furniture",
        "books": "entertainment",
        "toys": "toys_and_games",
        "couch": "furniture",
        "other": "other",
    }
    return category_map.get(category.lower(), "other")


def _map_category_to_offerup(category: str) -> str:
    """Map internal category to OfferUp category."""
    category_map = {
        "electronics": "electronics",
        "clothing": "clothing_and_shoes",
        "shoes": "clothing_and_shoes",
        "furniture": "home_and_garden",
        "books": "books_movies_and_music",
        "toys": "toys_and_games",
        "couch": "home_and_garden",
        "other": "everything_else",
    }
    return category_map.get(category.lower(), "everything_else")


def _generate_ebay_item_specifics(item: MyItem) -> Dict:
    """Generate eBay item specifics from item attributes."""
    specifics = {}

    if item.attributes:
        if "brand" in item.attributes:
            specifics["Brand"] = item.attributes["brand"]
        if "model" in item.attributes:
            specifics["Model"] = item.attributes["model"]
        if "color" in item.attributes:
            specifics["Color"] = item.attributes["color"]
        if "size" in item.attributes:
            specifics["Size"] = item.attributes["size"]

    if item.condition:
        specifics["Condition"] = item.condition.value

    return specifics


@shared_task(name="app.tasks.cross_post.prepare_crosspost")
def prepare_crosspost(job_id: int, platforms: Optional[List[str]] = None):
    """
    Prepare cross-post metadata for a completed snap job.

    This task:
    1. Finds the MyItem created from the SnapJob
    2. Generates marketplace-specific metadata for each platform
    3. Creates CrossPost records with status="pending"

    Args:
        job_id: The SnapJob ID
        platforms: List of platforms to prepare for (default: ["ebay", "facebook", "offerup"])
    """
    if platforms is None:
        platforms = ["ebay", "facebook", "offerup"]

    with get_session() as session:
        # Get the snap job
        snap_job = session.get(SnapJob, job_id)
        if not snap_job:
            logger.error(f"SnapJob {job_id} not found")
            return {"error": "snap_job_not_found", "job_id": job_id}

        # Find the associated MyItem (created by process_snap_job)
        # We'll look for the most recently created item by this user with matching category
        my_item = (
            session.query(MyItem)
            .filter(
                MyItem.user_id == snap_job.user_id,
                MyItem.category == snap_job.detected_category,
                MyItem.status == "draft",
            )
            .order_by(MyItem.id.desc())
            .first()
        )

        if not my_item:
            logger.error(f"No MyItem found for SnapJob {job_id}")
            return {"error": "my_item_not_found", "job_id": job_id}

        # Get user for location data
        user = session.get(User, snap_job.user_id)
        if not user:
            logger.error(f"User {snap_job.user_id} not found")
            return {"error": "user_not_found", "job_id": job_id}

        created_cross_posts = []

        # Create CrossPost records for each platform
        for platform in platforms:
            # Check if CrossPost already exists
            existing = (
                session.query(CrossPost)
                .filter(
                    CrossPost.my_item_id == my_item.id,
                    CrossPost.platform == platform.lower(),
                )
                .first()
            )

            if existing:
                logger.info(f"CrossPost already exists for item {my_item.id} on {platform}")
                continue

            # Generate platform-specific metadata
            metadata = generate_marketplace_metadata(my_item, platform.lower(), user)

            # Create CrossPost record
            cross_post = CrossPost(
                my_item_id=my_item.id,
                platform=platform.lower(),
                status="pending",
                meta=metadata,
            )
            session.add(cross_post)
            created_cross_posts.append({
                "platform": platform.lower(),
                "item_id": my_item.id,
            })

            logger.info(f"Created pending CrossPost for item {my_item.id} on {platform}")

        session.commit()

        return {
            "job_id": job_id,
            "item_id": my_item.id,
            "cross_posts_created": len(created_cross_posts),
            "platforms": created_cross_posts,
        }


@shared_task(name="app.tasks.cross_post.post_to_marketplaces")
def post_to_marketplaces(item_id: int, platforms: Optional[List[str]] = None):
    """
    Post a MyItem to multiple marketplaces asynchronously.

    This task reads CrossPost records with status="pending" and attempts to
    publish them to their respective marketplaces.

    Args:
        item_id: The MyItem ID to post
        platforms: Optional list of specific platforms to post to
    """
    with get_session() as session:
        # Get the item
        item = session.get(MyItem, item_id)
        if not item:
            logger.error(f"MyItem {item_id} not found")
            return {"error": "item_not_found", "item_id": item_id}

        # Get user
        user = session.get(User, item.user_id) if hasattr(item, 'user_id') else None

        # Get pending cross posts
        query = session.query(CrossPost).filter(
            CrossPost.my_item_id == item_id,
            CrossPost.status == "pending",
        )

        if platforms:
            query = query.filter(CrossPost.platform.in_([p.lower() for p in platforms]))

        pending_posts = query.all()

        if not pending_posts:
            logger.info(f"No pending cross posts found for item {item_id}")
            return {"item_id": item_id, "message": "no_pending_posts"}

        results = {}

        # Prepare item data
        item_images = item.attributes.get("images", []) if item.attributes else []

        for cross_post in pending_posts:
            platform = cross_post.platform

            try:
                if platform == "ebay":
                    results[platform] = _post_to_ebay(item, cross_post, session)

                elif platform == "facebook":
                    results[platform] = _post_to_facebook(item, cross_post, user, item_images, session)

                elif platform == "offerup":
                    results[platform] = _post_to_offerup(item, cross_post, user, item_images, session)

                else:
                    logger.warning(f"Unknown platform: {platform}")
                    results[platform] = {"status": "failed", "error": "unknown_platform"}

            except Exception as exc:
                logger.error(f"Failed to post to {platform}: {exc}", exc_info=True)
                cross_post.status = "failed"
                cross_post.meta = {**cross_post.meta, "error": str(exc)}
                results[platform] = {"status": "failed", "error": str(exc)}

        session.commit()

        return {
            "item_id": item_id,
            "results": results,
        }


def _post_to_ebay(item: MyItem, cross_post: CrossPost, session) -> Dict:
    """Post item to eBay."""
    try:
        item_data = {
            "sku": cross_post.meta.get("sku", f"DEALSCOUT-{item.id}"),
            "title": item.title,
            "description": item.attributes.get("description") or item.title if item.attributes else item.title,
            "availableQuantity": cross_post.meta.get("quantity", 1),
        }

        inventory_response = create_or_update_inventory(item_data)
        offer_response = create_offer(item_data, float(item.price), cross_post.meta)
        offer_id = offer_response.get("offerId") or inventory_response.get("sku")

        if not offer_id:
            raise EbayApiError("Offer ID missing from response")

        listing_url = publish_offer(offer_id)

        # Update cross post
        cross_post.external_id = offer_id
        cross_post.listing_url = listing_url
        cross_post.status = "live"
        cross_post.meta = {
            **cross_post.meta,
            "inventory": inventory_response,
            "offer": offer_response,
        }

        # Update item status
        item.status = "posted"

        return {"status": "success", "offer_id": offer_id, "url": listing_url}

    except (EbayApiError, EbayAuthError) as exc:
        cross_post.status = "failed"
        cross_post.meta = {**cross_post.meta, "error": str(exc)}
        raise


def _post_to_facebook(item: MyItem, cross_post: CrossPost, user: User, images: List[str], session) -> Dict:
    """Post item to Facebook Marketplace."""
    if not user:
        raise ValueError("User required for Facebook posting")

    # Get Facebook account
    facebook_account = session.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == user.id,
        MarketplaceAccount.marketplace == "facebook",
        MarketplaceAccount.is_active == True,
    ).first()

    if not facebook_account or not facebook_account.access_token:
        raise ValueError("Facebook Marketplace account not connected")

    if not facebook_account.marketplace_account_id:
        raise ValueError("Facebook page ID not stored")

    page_id = facebook_account.marketplace_account_id
    client = FacebookMarketplaceClient(facebook_account.access_token, page_id)

    # Note: This is a synchronous call in an async task - ideally this should be async
    import asyncio
    listing_id = asyncio.run(client.post_item(
        title=item.title,
        description=item.attributes.get("description") or item.title if item.attributes else item.title,
        price=float(item.price),
        images=images,
        category=item.category if hasattr(item, 'category') else None,
        condition=item.condition.value if hasattr(item, 'condition') and item.condition else None,
    ))

    if not listing_id:
        raise ValueError("Failed to get listing ID from Facebook")

    listing_url = client.get_listing_url(listing_id)

    # Update cross post
    cross_post.external_id = listing_id
    cross_post.listing_url = listing_url
    cross_post.status = "live"
    cross_post.meta = {
        **cross_post.meta,
        "listing_id": listing_id,
        "page_id": page_id,
    }

    return {"status": "success", "listing_id": listing_id, "url": listing_url}


def _post_to_offerup(item: MyItem, cross_post: CrossPost, user: User, images: List[str], session) -> Dict:
    """Post item to OfferUp."""
    if not user:
        raise ValueError("User required for OfferUp posting")

    # Get OfferUp account
    offerup_account = session.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == user.id,
        MarketplaceAccount.marketplace == "offerup",
        MarketplaceAccount.is_active == True,
    ).first()

    if not offerup_account or not offerup_account.access_token:
        raise ValueError("OfferUp account not connected")

    # Get location from metadata or user profile
    latitude = cross_post.meta.get("latitude", 37.3382)
    longitude = cross_post.meta.get("longitude", -121.8863)

    client = OfferupClient(offerup_account.access_token)

    # Note: This is a synchronous call in an async task - ideally this should be async
    import asyncio
    listing_id = asyncio.run(client.post_item(
        title=item.title,
        description=item.attributes.get("description") or item.title if item.attributes else item.title,
        price=float(item.price),
        images=images,
        latitude=latitude,
        longitude=longitude,
        category=item.category if hasattr(item, 'category') else None,
        condition=item.condition.value if hasattr(item, 'condition') and item.condition else None,
    ))

    if not listing_id:
        raise ValueError("Failed to get listing ID from OfferUp")

    listing_url = client.get_listing_url(listing_id)

    # Update cross post
    cross_post.external_id = listing_id
    cross_post.listing_url = listing_url
    cross_post.status = "live"
    cross_post.meta = {
        **cross_post.meta,
        "listing_id": listing_id,
        "user_id": offerup_account.marketplace_account_id,
    }

    return {"status": "success", "listing_id": listing_id, "url": listing_url}
