"""eBay OAuth authentication and integration routes."""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.db import SessionLocal
from app.core.models import SellerIntegration, User
from app.integrations.ebay import EbayClient, EbayIntegrationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/ebay", tags=["ebay-integration"])


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


class ConsentUrlResponse(BaseModel):
    """Response containing OAuth consent URL."""
    consent_url: str
    provider: str = "ebay"
    message: str = "Redirect user to this URL to authorize eBay access"


class OAuthCallbackResponse(BaseModel):
    """Response after successful OAuth callback."""
    success: bool
    provider: str = "ebay"
    message: str
    integration_id: int


class BootstrapResponse(BaseModel):
    """Response after bootstrapping eBay integration."""
    success: bool
    payment_policy_id: str
    fulfillment_policy_id: str
    return_policy_id: str
    location_key: str
    marketplace_id: str
    message: str


class IntegrationStatus(BaseModel):
    """Current integration status."""
    connected: bool
    provider: str = "ebay"
    marketplace_id: str | None = None
    has_policies: bool = False
    has_location: bool = False
    expires_at: datetime | None = None


# ============================================================================
# Routes
# ============================================================================


@router.get("/connect", response_model=ConsentUrlResponse)
async def get_ebay_consent_url(
    current_user: User = Depends(get_current_user),
) -> ConsentUrlResponse:
    """Get eBay OAuth consent URL.

    This endpoint generates the URL where users should be redirected
    to authorize Deal Scout to access their eBay account.

    Returns:
        ConsentUrlResponse with consent URL
    """
    try:
        client = EbayClient()

        # Use user ID as state for CSRF protection
        state = f"user_{current_user.id}"

        consent_url = client.build_consent_url(state=state)

        logger.info(f"Generated eBay consent URL for user {current_user.id}")

        return ConsentUrlResponse(
            consent_url=consent_url,
            message="Redirect user to consent_url to authorize eBay access",
        )
    except Exception as e:
        logger.error(f"Failed to generate consent URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate consent URL: {str(e)}",
        )


@router.get("/callback", response_model=OAuthCallbackResponse)
async def ebay_oauth_callback(
    code: str = Query(..., description="Authorization code from eBay"),
    state: str | None = Query(None, description="State parameter for CSRF protection"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OAuthCallbackResponse:
    """Handle eBay OAuth callback.

    This endpoint receives the authorization code from eBay after
    user consent and exchanges it for access/refresh tokens.

    Args:
        code: Authorization code from eBay OAuth flow
        state: State parameter (should match user ID)
        db: Database session
        current_user: Authenticated user

    Returns:
        OAuthCallbackResponse indicating success

    Raises:
        HTTPException: If token exchange fails or state doesn't match
    """
    try:
        # Validate state if provided
        if state and state != f"user_{current_user.id}":
            logger.warning(f"State mismatch for user {current_user.id}: {state}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter - possible CSRF attack",
            )

        client = EbayClient()

        # Exchange code for tokens
        logger.info(f"Exchanging authorization code for user {current_user.id}")
        tokens = await client.exchange_code_for_tokens(code)

        # Check if integration already exists
        integration = (
            db.query(SellerIntegration)
            .filter(
                SellerIntegration.seller_id == current_user.id,
                SellerIntegration.provider == "ebay",
            )
            .first()
        )

        if integration:
            # Update existing integration
            integration.access_token = tokens["access_token"]
            integration.refresh_token = tokens.get("refresh_token")
            integration.expires_at = tokens["expires_at"]
            integration.updated_at = datetime.utcnow()
            logger.info(f"Updated eBay integration for user {current_user.id}")
        else:
            # Create new integration
            integration = SellerIntegration(
                seller_id=current_user.id,
                provider="ebay",
                access_token=tokens["access_token"],
                refresh_token=tokens.get("refresh_token"),
                expires_at=tokens["expires_at"],
            )
            db.add(integration)
            logger.info(f"Created new eBay integration for user {current_user.id}")

        db.commit()
        db.refresh(integration)

        return OAuthCallbackResponse(
            success=True,
            message="Successfully connected eBay account. Run /bootstrap to complete setup.",
            integration_id=integration.id,
        )

    except EbayIntegrationError as e:
        logger.error(f"eBay integration error during callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect eBay account: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete eBay authentication: {str(e)}",
        )


@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap_ebay_integration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BootstrapResponse:
    """Bootstrap eBay integration with policies and location.

    This endpoint should be called once after OAuth connection to:
    1. Fetch account policies (payment, fulfillment, return)
    2. Select and save default policy IDs
    3. Create default inventory location
    4. Save marketplace ID

    Returns:
        BootstrapResponse with setup details

    Raises:
        HTTPException: If integration not found or bootstrap fails
    """
    try:
        # Get existing integration
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eBay integration not found. Please connect your eBay account first.",
            )

        client = EbayClient()

        # Step 1: Fetch and select policies
        logger.info(f"Fetching eBay policies for user {current_user.id}")
        policies = await client.get_policies(integration.access_token)

        # Select first policy of each type (user can change later if needed)
        payment_policies = policies.get("payment", [])
        fulfillment_policies = policies.get("fulfillment", [])
        return_policies = policies.get("return", [])

        if not payment_policies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No payment policies found. Please create policies in eBay Seller Hub first.",
            )

        if not fulfillment_policies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fulfillment policies found. Please create policies in eBay Seller Hub first.",
            )

        if not return_policies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No return policies found. Please create policies in eBay Seller Hub first.",
            )

        payment_policy_id = payment_policies[0]["paymentPolicyId"]
        fulfillment_policy_id = fulfillment_policies[0]["fulfillmentPolicyId"]
        return_policy_id = return_policies[0]["returnPolicyId"]

        logger.info(
            f"Selected policies - Payment: {payment_policy_id}, "
            f"Fulfillment: {fulfillment_policy_id}, Return: {return_policy_id}"
        )

        # Step 2: Create inventory location if not exists
        location_key = f"DEFAULT_{current_user.id}"

        if not integration.location_key:
            logger.info(f"Creating inventory location: {location_key}")

            # Create basic location payload
            # In production, this should use actual seller address
            location_payload = {
                "location": {
                    "address": {
                        "addressLine1": "123 Main St",
                        "city": "San Jose",
                        "stateOrProvince": "CA",
                        "postalCode": "95110",
                        "country": "US",
                    }
                },
                "locationInstructions": "Default inventory location",
                "name": "Primary Warehouse",
                "merchantLocationStatus": "ENABLED",
                "locationTypes": ["WAREHOUSE"],
            }

            try:
                await client.create_location(
                    integration.access_token,
                    location_key,
                    location_payload,
                )
                logger.info(f"Created inventory location: {location_key}")
            except EbayIntegrationError as e:
                # Location might already exist, which is fine
                if e.status_code != 409:  # 409 = Conflict (already exists)
                    raise
                logger.info(f"Inventory location already exists: {location_key}")

        # Step 3: Update integration with all configuration
        integration.payment_policy_id = payment_policy_id
        integration.fulfillment_policy_id = fulfillment_policy_id
        integration.return_policy_id = return_policy_id
        integration.location_key = location_key
        integration.marketplace_id = client.marketplace_id
        integration.updated_at = datetime.utcnow()

        db.commit()

        logger.info(f"Successfully bootstrapped eBay integration for user {current_user.id}")

        return BootstrapResponse(
            success=True,
            payment_policy_id=payment_policy_id,
            fulfillment_policy_id=fulfillment_policy_id,
            return_policy_id=return_policy_id,
            location_key=location_key,
            marketplace_id=client.marketplace_id,
            message="eBay integration fully configured and ready to use",
        )

    except HTTPException:
        raise
    except EbayIntegrationError as e:
        logger.error(f"eBay integration error during bootstrap: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bootstrap failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during bootstrap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bootstrap eBay integration: {str(e)}",
        )


@router.get("/status", response_model=IntegrationStatus)
async def get_integration_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IntegrationStatus:
    """Get current eBay integration status.

    Returns:
        IntegrationStatus with connection details
    """
    integration = (
        db.query(SellerIntegration)
        .filter(
            SellerIntegration.seller_id == current_user.id,
            SellerIntegration.provider == "ebay",
        )
        .first()
    )

    if not integration:
        return IntegrationStatus(
            connected=False,
            has_policies=False,
            has_location=False,
        )

    has_policies = bool(
        integration.payment_policy_id
        and integration.fulfillment_policy_id
        and integration.return_policy_id
    )

    has_location = bool(integration.location_key)

    return IntegrationStatus(
        connected=True,
        marketplace_id=integration.marketplace_id,
        has_policies=has_policies,
        has_location=has_location,
        expires_at=integration.expires_at,
    )


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_ebay(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Disconnect eBay integration.

    Removes OAuth tokens and configuration from database.
    Does not revoke tokens on eBay side (user can do that in eBay settings).
    """
    integration = (
        db.query(SellerIntegration)
        .filter(
            SellerIntegration.seller_id == current_user.id,
            SellerIntegration.provider == "ebay",
        )
        .first()
    )

    if integration:
        db.delete(integration)
        db.commit()
        logger.info(f"Disconnected eBay integration for user {current_user.id}")
