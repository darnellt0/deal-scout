"""Marketplace account management endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.models import User, MarketplaceAccount
from app.core.auth import get_current_user, require_seller

router = APIRouter(prefix="/marketplace-accounts", tags=["marketplace-accounts"])


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
async def list_marketplace_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all marketplace accounts for the current user."""
    accounts = (
        db.query(MarketplaceAccount)
        .filter(MarketplaceAccount.user_id == current_user.id)
        .all()
    )

    return [
        {
            "id": account.id,
            "platform": account.platform,
            "account_username": account.account_username,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
        }
        for account in accounts
    ]


@router.get("/{account_id}")
async def get_marketplace_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details for a specific marketplace account."""
    account = (
        db.query(MarketplaceAccount)
        .filter(
            MarketplaceAccount.id == account_id,
            MarketplaceAccount.user_id == current_user.id,
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")

    return {
        "id": account.id,
        "platform": account.platform,
        "account_username": account.account_username,
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
    }


@router.post("")
async def create_marketplace_account(
    platform: str,
    account_username: str,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Create a new marketplace account connection (seller only)."""
    # Check if account already exists for this platform
    existing = (
        db.query(MarketplaceAccount)
        .filter(
            MarketplaceAccount.user_id == current_user.id,
            MarketplaceAccount.platform == platform,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Account for {platform} already exists",
        )

    account = MarketplaceAccount(
        user_id=current_user.id,
        platform=platform,
        account_username=account_username,
        is_active=True,
    )
    db.add(account)
    db.commit()

    return {
        "id": account.id,
        "platform": account.platform,
        "account_username": account.account_username,
        "is_active": account.is_active,
        "message": f"Marketplace account for {platform} created successfully",
    }


@router.patch("/{account_id}")
async def update_marketplace_account(
    account_id: int,
    is_active: Optional[bool] = None,
    account_username: Optional[str] = None,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Update a marketplace account (seller only)."""
    account = (
        db.query(MarketplaceAccount)
        .filter(
            MarketplaceAccount.id == account_id,
            MarketplaceAccount.user_id == current_user.id,
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")

    if is_active is not None:
        account.is_active = is_active
    if account_username is not None:
        account.account_username = account_username

    db.commit()

    return {
        "id": account.id,
        "platform": account.platform,
        "account_username": account.account_username,
        "is_active": account.is_active,
        "message": "Marketplace account updated successfully",
    }


@router.delete("/{account_id}")
async def delete_marketplace_account(
    account_id: int,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Delete a marketplace account (seller only)."""
    account = (
        db.query(MarketplaceAccount)
        .filter(
            MarketplaceAccount.id == account_id,
            MarketplaceAccount.user_id == current_user.id,
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")

    platform = account.platform
    db.delete(account)
    db.commit()

    return {"message": f"Marketplace account for {platform} deleted successfully"}


@router.post("/{account_id}/disconnect")
async def disconnect_marketplace_account(
    account_id: int,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Disconnect a marketplace account (set is_active to False) (seller only)."""
    account = (
        db.query(MarketplaceAccount)
        .filter(
            MarketplaceAccount.id == account_id,
            MarketplaceAccount.user_id == current_user.id,
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")

    if not account.is_active:
        raise HTTPException(status_code=400, detail="Account is already disconnected")

    account.is_active = False
    db.commit()

    return {
        "message": f"Marketplace account for {account.platform} disconnected successfully"
    }


@router.post("/{account_id}/reconnect")
async def reconnect_marketplace_account(
    account_id: int,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db),
):
    """Reconnect a marketplace account (set is_active to True) (seller only)."""
    account = (
        db.query(MarketplaceAccount)
        .filter(
            MarketplaceAccount.id == account_id,
            MarketplaceAccount.user_id == current_user.id,
        )
        .first()
    )

    if not account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")

    if account.is_active:
        raise HTTPException(status_code=400, detail="Account is already connected")

    account.is_active = True
    db.commit()

    return {
        "message": f"Marketplace account for {account.platform} reconnected successfully"
    }
