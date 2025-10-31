"""Facebook Marketplace OAuth flow and authentication."""

import httpx
import logging
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.auth import get_current_user
from app.core.db import SessionLocal
from app.core.models import User, MarketplaceAccount
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/facebook", tags=["facebook-oauth"])

# In-memory state storage (use Redis in production)
_state_tokens = {}


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_state_token(user_id: int) -> str:
    """Generate and store state token for OAuth security."""
    token = secrets.token_urlsafe(32)
    # Store with 10 minute expiry
    _state_tokens[token] = {
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    return token


def verify_state_token(token: str) -> Optional[int]:
    """Verify state token and return user_id if valid."""
    if token not in _state_tokens:
        logger.warning(f"Invalid state token: {token}")
        return None

    token_data = _state_tokens[token]

    if datetime.utcnow() > token_data["expires_at"]:
        logger.warning(f"State token expired: {token}")
        del _state_tokens[token]
        return None

    # Token is valid, remove it (one-time use)
    user_id = token_data["user_id"]
    del _state_tokens[token]

    return user_id


@router.get("/authorize")
async def facebook_authorize(
    current_user: User = Depends(get_current_user),
):
    """
    Generate Facebook OAuth authorization URL.

    User should be redirected to this URL to start OAuth flow.
    Returns the Facebook authorization URL.
    """
    settings = get_settings()

    if not settings.facebook_app_id:
        raise HTTPException(
            status_code=400,
            detail="Facebook App ID not configured"
        )

    # Generate state token for CSRF protection
    state = generate_state_token(current_user.id)

    # Facebook OAuth endpoint
    auth_url = "https://www.facebook.com/v18.0/dialog/oauth"

    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": f"{settings.backend_url}/facebook/callback",
        "scope": "pages_manage_metadata,pages_read_engagement,pages_manage_posts,pages_manage_engagement,business_basic",
        "state": state,
        "response_type": "code",
    }

    # Build URL with parameters
    url_parts = [f"{auth_url}?"]
    for key, value in params.items():
        url_parts.append(f"{key}={value}&")

    auth_url_full = "".join(url_parts).rstrip("&")

    logger.info(f"Generated Facebook auth URL for user {current_user.id}")

    return {
        "authorization_url": auth_url_full,
        "state": state
    }


@router.get("/callback")
async def facebook_callback(
    code: str = Query(..., description="Authorization code from Facebook"),
    state: str = Query(..., description="State token for CSRF protection"),
    db: Session = Depends(get_db),
):
    """
    Handle OAuth callback from Facebook.

    Exchange authorization code for access token and store in database.
    """
    settings = get_settings()

    logger.info(f"Received Facebook callback with state: {state}")

    # Verify state token
    user_id = verify_state_token(state)
    if not user_id:
        logger.error(f"Invalid or expired state token: {state}")
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state token. Please try again."
        )

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not settings.facebook_app_id or not settings.facebook_app_secret:
        raise HTTPException(
            status_code=500,
            detail="Facebook credentials not configured"
        )

    # Exchange code for access token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                token_url,
                params={
                    "client_id": settings.facebook_app_id,
                    "client_secret": settings.facebook_app_secret,
                    "redirect_uri": f"{settings.backend_url}/facebook/callback",
                    "code": code,
                }
            )
            response.raise_for_status()
            token_data = response.json()

    except httpx.HTTPError as e:
        logger.error(f"Failed to exchange code for token: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to authenticate with Facebook. Please try again."
        )

    access_token = token_data.get("access_token")
    if not access_token:
        logger.error("No access token in Facebook response")
        raise HTTPException(
            status_code=400,
            detail="Failed to get access token from Facebook"
        )

    # Get user's Facebook pages
    pages_url = "https://graph.facebook.com/me/accounts"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                pages_url,
                params={"access_token": access_token}
            )
            response.raise_for_status()
            pages_data = response.json()

    except httpx.HTTPError as e:
        logger.error(f"Failed to get Facebook pages: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to retrieve your Facebook pages"
        )

    pages = pages_data.get("data", [])

    if not pages:
        logger.warning(f"No Facebook pages found for user {user_id}")
        raise HTTPException(
            status_code=400,
            detail="No Facebook pages found. Please create a Facebook page first."
        )

    # Store first page as default (user can select different pages later)
    page = pages[0]
    page_id = page.get("id")
    page_name = page.get("name")

    if not page_id or not page_name:
        logger.error(f"Invalid page data from Facebook: {page}")
        raise HTTPException(
            status_code=400,
            detail="Invalid page data from Facebook"
        )

    # Check if account already exists
    existing = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == user.id,
        MarketplaceAccount.marketplace == "facebook"
    ).first()

    try:
        if existing:
            # Update existing account
            existing.marketplace_account_id = page_id
            existing.account_username = page_name
            existing.access_token = access_token
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
            logger.info(f"Updated Facebook account for user {user_id}: {page_name}")
        else:
            # Create new account
            account = MarketplaceAccount(
                user_id=user.id,
                marketplace="facebook",
                marketplace_account_id=page_id,
                account_username=page_name,
                access_token=access_token,
                is_active=True,
                connected_at=datetime.utcnow(),
            )
            db.add(account)
            logger.info(f"Created new Facebook account for user {user_id}: {page_name}")

        db.commit()

        return {
            "success": True,
            "message": f"Facebook page '{page_name}' connected successfully",
            "page_name": page_name,
            "page_id": page_id,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store Facebook credentials: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store Facebook credentials"
        )


@router.post("/authorize")
async def verify_facebook_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify Facebook connection is valid and token is not expired.

    Useful for testing or checking if authentication needs to be refreshed.
    """
    account = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == current_user.id,
        MarketplaceAccount.marketplace == "facebook"
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="No Facebook account connected for this user"
        )

    if not account.access_token:
        raise HTTPException(
            status_code=400,
            detail="Facebook account exists but no access token stored"
        )

    settings = get_settings()

    # Verify token is still valid using Facebook debug API
    debug_url = "https://graph.facebook.com/debug_token"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                debug_url,
                params={
                    "input_token": account.access_token,
                    "access_token": f"{settings.facebook_app_id}|{settings.facebook_app_secret}"
                }
            )
            response.raise_for_status()

        token_info = response.json()
        data = token_info.get("data", {})
        is_valid = data.get("is_valid", False)

        if not is_valid:
            logger.warning(f"Facebook token invalid for user {current_user.id}")
            account.is_active = False
            db.commit()

        return {
            "is_connected": True,
            "is_valid": is_valid,
            "app_id": data.get("app_id"),
            "user_id": data.get("user_id"),
            "page_name": account.account_username,
            "page_id": account.marketplace_account_id,
            "connected_at": account.connected_at.isoformat() if account.connected_at else None,
        }

    except httpx.HTTPError as e:
        logger.error(f"Failed to verify Facebook token: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to verify Facebook token"
        )


@router.post("/disconnect")
async def disconnect_facebook(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect Facebook Marketplace account.

    This removes the stored access token and marks the account as inactive.
    """
    account = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == current_user.id,
        MarketplaceAccount.marketplace == "facebook"
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="No Facebook account connected"
        )

    try:
        account.is_active = False
        account.access_token = None  # Clear token
        db.commit()

        logger.info(f"Disconnected Facebook account for user {current_user.id}")

        return {
            "success": True,
            "message": "Facebook Marketplace account disconnected"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to disconnect Facebook account: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect Facebook account"
        )
