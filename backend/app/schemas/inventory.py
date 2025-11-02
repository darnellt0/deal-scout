from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class PublishListingRequest(BaseModel):
    marketplace_name: str = Field(..., min_length=1, max_length=32)
    price_adjustment_rate: float = Field(..., gt=0.0)


class SaleWebhookPayload(BaseModel):
    platform_listing_id: str
    final_sale_price: Decimal
    shipping_cost: Optional[Decimal] = Decimal("0.00")

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )

    @field_validator("final_sale_price", "shipping_cost", mode="before")
    def validate_decimal(cls, value):
        if value is None:
            return None
        return Decimal(str(value))


class MarketplaceListingResponse(BaseModel):
    id: int
    product_id: int
    platform_name: str
    platform_listing_id: str
    platform_price: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class SalesOrderResponse(BaseModel):
    id: int
    marketplace_listing_id: int
    platform_name: str
    sale_price: Decimal
    platform_fee_rate: Decimal
    shipping_cost: Decimal
    net_profit: Decimal

    model_config = ConfigDict(from_attributes=True)
