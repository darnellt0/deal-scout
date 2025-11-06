"""eBay cross-post publishing routes."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import SessionLocal
from app.core.models import CrossPostResult, Listing, SellerIntegration, User
from app.integrations.ebay import EbayClient, EbayIntegrationError, EbayValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/ebay", tags=["ebay-publish"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Request/Response Models
# ============================================================================


class PublishResponse(BaseModel):
    """Response after successful publishing."""
    success: bool
    provider: str = "ebay"
    listing_id: int
    offer_id: str
    item_id: str
    url: str
    message: str


class PublishErrorDetail(BaseModel):
    """Detailed error information for publish failures."""
    error: str
    status_code: int | None = None
    missing_aspects: List[Dict[str, Any]] = []
    required_fields: List[str] = []
    suggested_category_id: str | None = None


class PublishError(BaseModel):
    """Error response for publish failures."""
    success: bool = False
    provider: str = "ebay"
    error: str
    detail: PublishErrorDetail


# ============================================================================
# Helper Functions
# ============================================================================


def map_condition_to_ebay(condition: str | None) -> str:
    """Map Deal Scout condition to eBay inventory condition.

    Args:
        condition: Deal Scout condition (poor, fair, good, great, excellent)

    Returns:
        eBay condition code
    """
    condition_map = {
        "excellent": "USED_EXCELLENT",
        "great": "USED_VERY_GOOD",
        "good": "USED_GOOD",
        "fair": "USED_ACCEPTABLE",
        "poor": "FOR_PARTS_OR_NOT_WORKING",
    }
    return condition_map.get(condition or "good", "USED_GOOD")


def build_inventory_item_payload(
    listing: Listing,
    category_id: str,
    aspects: Dict[str, List[str]],
) -> Dict[str, Any]:
    """Build eBay inventory item payload from Deal Scout listing.

    Args:
        listing: Deal Scout listing
        category_id: eBay category ID
        aspects: Item aspects (key-value pairs)

    Returns:
        Inventory item payload for eBay API
    """
    # Get images (eBay requires HTTPS URLs)
    images = []
    if listing.thumbnail_url and listing.thumbnail_url.startswith("http"):
        images.append(listing.thumbnail_url)
    # TODO: Add more images from listing if available

    # Build product details
    product = {
        "title": listing.title[:80],  # eBay max title length
        "description": listing.description or listing.title,
        "aspects": aspects,
        "imageUrls": images if images else None,
    }

    # Build availability
    availability = {
        "shipToLocationAvailability": {
            "quantity": 1,  # Default to 1, can be customized
        }
    }

    # Build payload
    payload = {
        "product": product,
        "condition": map_condition_to_ebay(listing.condition.value if listing.condition else None),
        "availability": availability,
    }

    return payload


def build_offer_payload(
    sku: str,
    listing: Listing,
    category_id: str,
    integration: SellerIntegration,
) -> Dict[str, Any]:
    """Build eBay offer payload.

    Args:
        sku: Stock Keeping Unit
        listing: Deal Scout listing
        category_id: eBay category ID
        integration: Seller integration with policy IDs

    Returns:
        Offer payload for eBay API
    """
    # Build pricing
    pricing_summary = {
        "price": {
            "value": str(listing.price),
            "currency": "USD",
        }
    }

    # Build listing policies
    listing_policies = {
        "paymentPolicyId": integration.payment_policy_id,
        "fulfillmentPolicyId": integration.fulfillment_policy_id,
        "returnPolicyId": integration.return_policy_id,
    }

    # Build listing description (can be different from product description)
    listing_description = listing.description or listing.title

    # Build payload
    payload = {
        "sku": sku,
        "marketplaceId": integration.marketplace_id,
        "format": "FIXED_PRICE",
        "availableQuantity": 1,
        "categoryId": category_id,
        "listingDescription": listing_description,
        "listingPolicies": listing_policies,
        "merchantLocationKey": integration.location_key,
        "pricingSummary": pricing_summary,
    }

    return payload


async def validate_and_get_aspects(
    client: EbayClient,
    access_token: str,
    category_id: str,
    listing: Listing,
) -> Dict[str, List[str]]:
    """Validate and build aspects for the listing.

    Args:
        client: eBay client
        access_token: Access token
        category_id: eBay category ID
        listing: Deal Scout listing

    Returns:
        Dictionary of aspect name -> values

    Raises:
        EbayValidationError: If required aspects are missing
    """
    # Get category aspects
    aspects_list = await client.taxonomy_get_aspects(access_token, category_id)

    # Build aspects from listing
    # This is a simplified version - in production, you'd map listing attributes
    # to eBay aspects more intelligently
    aspects: Dict[str, List[str]] = {}

    # Map condition
    if listing.condition:
        aspects["Condition"] = [listing.condition.value.capitalize()]

    # Check for required aspects
    missing_required = []
    for aspect in aspects_list:
        if aspect.get("aspectConstraint", {}).get("aspectMode") == "REQUIRED":
            aspect_name = aspect["localizedAspectName"]
            if aspect_name not in aspects:
                missing_required.append({
                    "name": aspect_name,
                    "required": True,
                    "values": aspect.get("aspectValues", []),
                })

    if missing_required:
        error_msg = f"Missing {len(missing_required)} required aspects for this category"
        raise EbayValidationError(
            error_msg,
            status_code=422,
            response_body={"missing_aspects": missing_required},
        )

    return aspects


# ============================================================================
# Routes
# ============================================================================


@router.post("/publish/{listing_id}", response_model=PublishResponse)
async def publish_listing_to_ebay(
    listing_id: int = Path(..., description="Deal Scout listing ID to publish"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PublishResponse:
    """Publish a Deal Scout listing to eBay.

    This endpoint orchestrates the full cross-posting workflow:
    1. Load seller's eBay integration (tokens, policies, location)
    2. Load Deal Scout listing
    3. Suggest/validate eBay category
    4. Get and validate required aspects
    5. Create inventory item
    6. Create offer
    7. Publish offer
    8. Save cross-post result

    Args:
        listing_id: ID of listing to publish
        db: Database session
        current_user: Authenticated user

    Returns:
        PublishResponse with eBay item details and URL

    Raises:
        HTTPException: Various errors with detailed messages and fix suggestions
    """
    try:
        # Step 1: Load seller's eBay integration
        integration = (
            db.query(SellerIntegration)
            .filter(
                SellerIntegration.seller_id == current_user.id,
                SellerIntegration.provider == "ebay",
            )
            .first()
        )

        if not integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "eBay not connected",
                    "action": "Connect your eBay account at /integrations/ebay/connect",
                },
            )

        # Check if integration is bootstrapped
        if not all([
            integration.payment_policy_id,
            integration.fulfillment_policy_id,
            integration.return_policy_id,
            integration.location_key,
        ]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "eBay integration not fully configured",
                    "action": "Run /integrations/ebay/bootstrap to complete setup",
                },
            )

        # Step 2: Load Deal Scout listing
        listing = db.query(Listing).filter(Listing.id == listing_id).first()

        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Listing {listing_id} not found",
            )

        client = EbayClient()

        # Step 3: Get or suggest category
        category_id = None

        # First try to suggest category from title
        logger.info(f"Suggesting eBay category for listing: {listing.title}")
        category_id = await client.taxonomy_suggest_category(
            integration.access_token,
            listing.title,
        )

        if not category_id:
            # Fallback to a default category (can be improved)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Could not determine eBay category",
                    "suggestion": "Please specify a category manually",
                    "listing_title": listing.title,
                },
            )

        logger.info(f"Using eBay category: {category_id}")

        # Step 4: Get and validate aspects
        try:
            aspects = await validate_and_get_aspects(
                client,
                integration.access_token,
                category_id,
                listing,
            )
        except EbayValidationError as e:
            # Return detailed error with missing aspects
            missing_aspects = e.response_body.get("missing_aspects", [])
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": str(e),
                    "missing_aspects": missing_aspects,
                    "category_id": category_id,
                    "action": "Add required aspects to listing before publishing",
                },
            )

        # Step 5: Build SKU (unique identifier)
        sku = f"DS-{listing_id}"

        # Step 6: Create/update inventory item
        logger.info(f"Creating inventory item with SKU: {sku}")
        inventory_payload = build_inventory_item_payload(
            listing,
            category_id,
            aspects,
        )

        await client.upsert_inventory_item(
            integration.access_token,
            sku,
            inventory_payload,
        )

        # Step 7: Create offer
        logger.info(f"Creating offer for SKU: {sku}")
        offer_payload = build_offer_payload(
            sku,
            listing,
            category_id,
            integration,
        )

        offer_id = await client.create_offer(
            integration.access_token,
            offer_payload,
        )

        # Step 8: Publish offer
        logger.info(f"Publishing offer: {offer_id}")
        publish_result = await client.publish_offer(
            integration.access_token,
            offer_id,
        )

        # Step 9: Save cross-post result
        crosspost = CrossPostResult(
            listing_id=listing_id,
            provider="ebay",
            provider_offer_id=offer_id,
            provider_item_id=publish_result["itemId"],
            provider_url=publish_result["url"],
            status="published",
            raw_response=publish_result,
        )
        db.add(crosspost)
        db.commit()
        db.refresh(crosspost)

        logger.info(
            f"Successfully published listing {listing_id} to eBay: {publish_result['url']}"
        )

        return PublishResponse(
            success=True,
            listing_id=listing_id,
            offer_id=offer_id,
            item_id=publish_result["itemId"],
            url=publish_result["url"],
            message="Successfully published to eBay",
        )

    except HTTPException:
        raise
    except EbayValidationError as e:
        # Validation errors with field details
        logger.error(f"Validation error publishing listing {listing_id}: {e}")

        error_detail = PublishErrorDetail(
            error=str(e),
            status_code=e.status_code,
            required_fields=e.response_body.get("required_fields", []),
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_detail.model_dump(),
        )
    except EbayIntegrationError as e:
        # Other eBay API errors
        logger.error(f"eBay API error publishing listing {listing_id}: {e}")

        # If 401, suggest re-connecting
        if e.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "eBay authentication expired",
                    "action": "Re-connect your eBay account at /integrations/ebay/connect",
                },
            )

        error_detail = PublishErrorDetail(
            error=str(e),
            status_code=e.status_code,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail.model_dump(),
        )
    except Exception as e:
        logger.error(f"Unexpected error publishing listing {listing_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish listing: {str(e)}",
        )


@router.get("/listings/{listing_id}/status")
async def get_crosspost_status(
    listing_id: int = Path(..., description="Listing ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get cross-post status for a listing.

    Args:
        listing_id: Listing ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Cross-post status and details
    """
    crosspost = (
        db.query(CrossPostResult)
        .filter(
            CrossPostResult.listing_id == listing_id,
            CrossPostResult.provider == "ebay",
        )
        .order_by(CrossPostResult.created_at.desc())
        .first()
    )

    if not crosspost:
        return {
            "listing_id": listing_id,
            "provider": "ebay",
            "published": False,
        }

    return {
        "listing_id": listing_id,
        "provider": "ebay",
        "published": True,
        "status": crosspost.status,
        "item_id": crosspost.provider_item_id,
        "url": crosspost.provider_url,
        "published_at": crosspost.created_at.isoformat(),
    }
