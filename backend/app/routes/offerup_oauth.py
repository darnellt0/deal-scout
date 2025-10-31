"""Offerup OAuth flow and authentication."""

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

router = APIRouter(prefix="/offerup", tags=["offerup-oauth"])

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
async def offerup_authorize(
    current_user: User = Depends(get_current_user),
):
    """
    Generate Offerup OAuth authorization URL.

    User should be redirected to this URL to start OAuth flow.
    Returns the Offerup authorization URL.
    """
    settings = get_settings()

    if not settings.offerup_client_id:
        raise HTTPException(
            status_code=400,
            detail="Offerup Client ID not configured"
        )

    # Generate state token for CSRF protection
    state = generate_state_token(current_user.id)

    # Offerup OAuth endpoint (using OfferUp's production auth)
    auth_url = "https://accounts.offerup.com/oauth/authorize"

    params = {
        "client_id": settings.offerup_client_id,
        "redirect_uri": f"{settings.backend_url}/offerup/callback",
        "scope": "listings:write listings:read users:read",
        "state": state,
        "response_type": "code",
    }

    # Build URL with parameters
    url_parts = [f"{auth_url}?"]
    for key, value in params.items():
        url_parts.append(f"{key}={value}&")

    auth_url_full = "".join(url_parts).rstrip("&")

    logger.info(f"Generated Offerup auth URL for user {current_user.id}")

    return {
        "authorization_url": auth_url_full,
        "state": state
    }


@router.get("/callback")
async def offerup_callback(
    code: str = Query(..., description="Authorization code from Offerup"),
    state: str = Query(..., description="State token for CSRF protection"),
    db: Session = Depends(get_db),
):
    """
    Handle OAuth callback from Offerup.

    Exchange authorization code for access token and store in database.
    """
    settings = get_settings()

    logger.info(f"Received Offerup callback with state: {state}")

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

    if not settings.offerup_client_id or not settings.offerup_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Offerup credentials not configured"
        )

    # Exchange code for access token
    token_url = "https://accounts.offerup.com/oauth/token"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.offerup_client_id,
                    "client_secret": settings.offerup_client_secret,
                    "redirect_uri": f"{settings.backend_url}/offerup/callback",
                }
            )
            response.raise_for_status()
            token_data = response.json()

    except httpx.HTTPError as e:
        logger.error(f"Failed to exchange code for token: {e}")
        if hasattr(e, "response") and hasattr(e.response, "text"):
            logger.error(f"Response: {e.response.text}")
        raise HTTPException(
            status_code=400,
            detail="Failed to authenticate with Offerup. Please try again."
        )

    access_token = token_data.get("access_token")
    if not access_token:
        logger.error("No access token in Offerup response")
        raise HTTPException(
            status_code=400,
            detail="Failed to get access token from Offerup"
        )

    # Get user info from Offerup
    user_info_url = "https://api.offerup.com/api/v3/users/me"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            user_info = response.json()

    except httpx.HTTPError as e:
        logger.error(f"Failed to get Offerup user info: {e}")
        if hasattr(e, "response") and hasattr(e.response, "text"):
            logger.error(f"Response: {e.response.text}")
        raise HTTPException(
            status_code=400,
            detail="Failed to retrieve your Offerup account information"
        )

    # Extract user info
    offerup_user_id = user_info.get("id")
    offerup_username = user_info.get("username", user_info.get("displayName", ""))

    if not offerup_user_id:
        logger.error(f"Invalid user info from Offerup: {user_info}")
        raise HTTPException(
            status_code=400,
            detail="Invalid user information from Offerup"
        )

    # Check if account already exists
    existing = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == user.id,
        MarketplaceAccount.marketplace == "offerup"
    ).first()

    try:
        if existing:
            # Update existing account
            existing.marketplace_account_id = offerup_user_id
            existing.account_username = offerup_username
            existing.access_token = access_token
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
            logger.info(f"Updated Offerup account for user {user_id}: {offerup_username}")
        else:
            # Create new account
            account = MarketplaceAccount(
                user_id=user.id,
                marketplace="offerup",
                marketplace_account_id=offerup_user_id,
                account_username=offerup_username,
                access_token=access_token,
                is_active=True,
                connected_at=datetime.utcnow(),
            )
            db.add(account)
            logger.info(f"Created new Offerup account for user {user_id}: {offerup_username}")

        db.commit()

        return {
            "success": True,
            "message": f"Offerup account '{offerup_username}' connected successfully",
            "username": offerup_username,
            "user_id": offerup_user_id,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store Offerup credentials: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to store Offerup credentials"
        )


@router.post("/authorize")
async def verify_offerup_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify Offerup connection is valid and token is not expired.

    Useful for testing or checking if authentication needs to be refreshed.
    """
    account = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == current_user.id,
        MarketplaceAccount.marketplace == "offerup"
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="No Offerup account connected for this user"
        )

    if not account.access_token:
        raise HTTPException(
            status_code=400,
            detail="Offerup account exists but no access token stored"
        )

    # Verify token by fetching user info
    user_info_url = "https://api.offerup.com/api/v3/users/me"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                user_info_url,
                headers={"Authorization": f"Bearer {account.access_token}"}
            )
            response.raise_for_status()

        user_info = response.json()
        is_valid = bool(user_info.get("id"))

        if not is_valid:
            logger.warning(f"Offerup token invalid for user {current_user.id}")
            account.is_active = False
            db.commit()

        return {
            "is_connected": True,
            "is_valid": is_valid,
            "username": account.account_username,
            "user_id": account.marketplace_account_id,
            "connected_at": account.connected_at.isoformat() if account.connected_at else None,
        }

    except httpx.HTTPError as e:
        logger.error(f"Failed to verify Offerup token: {e}")
        account.is_active = False
        db.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to verify Offerup token"
        )


@router.post("/disconnect")
async def disconnect_offerup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect Offerup account.

    This removes the stored access token and marks the account as inactive.
    """
    account = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == current_user.id,
        MarketplaceAccount.marketplace == "offerup"
    ).first()

    if not account:
        raise HTTPException(
            status_code=404,
            detail="No Offerup account connected"
        )

    try:
        account.is_active = False
        account.access_token = None  # Clear token
        db.commit()

        logger.info(f"Disconnected Offerup account for user {current_user.id}")

        return {
            "success": True,
            "message": "Offerup account disconnected"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to disconnect Offerup account: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect Offerup account"
        )
