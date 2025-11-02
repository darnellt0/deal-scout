from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path, status
from sqlalchemy.exc import NoResultFound

from app.schemas.inventory import (
    MarketplaceListingResponse,
    PublishListingRequest,
    SaleWebhookPayload,
    SalesOrderResponse,
)
from app.services.inventory import InventoryService

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])
inventory_service = InventoryService()


@router.post(
    "/{product_id}/publish/",
    response_model=MarketplaceListingResponse,
    status_code=status.HTTP_201_CREATED,
)
def publish_listing(
    product_id: int = Path(..., ge=1),
    payload: PublishListingRequest = ...,
):
    try:
        listing = inventory_service.publish_listing(
            product_id=product_id,
            marketplace_name=payload.marketplace_name,
            price_adjustment_rate=payload.price_adjustment_rate,
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Product not found") from None
    return listing


@router.post(
    "/webhooks/{marketplace_name}/",
    response_model=SalesOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def handle_sale_webhook(
    marketplace_name: str,
    payload: SaleWebhookPayload,
):
    data = payload.model_dump()
    data["marketplace_name"] = marketplace_name
    try:
        order = inventory_service.handle_sale_webhook(data)
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Listing not found") from None
    return order
