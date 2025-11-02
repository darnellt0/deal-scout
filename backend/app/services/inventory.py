from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.models import MarketplaceListing, Product, SalesOrder


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PlatformFeeSchedule:
    fees: Dict[str, Decimal]

    def get_fee_rate(self, platform: str) -> Decimal:
        return self.fees.get(platform.lower(), Decimal("0.12"))


class InventoryService:
    """Service layer for SSOT inventory operations."""

    def __init__(self):
        self.fee_schedule = PlatformFeeSchedule(
            fees={
                "ebay": Decimal("0.13"),
                "poshmark": Decimal("0.20"),
                "mercari": Decimal("0.12"),
                "depop": Decimal("0.10"),
                "facebook": Decimal("0.05"),
            }
        )

    def _get_session(self) -> Session:
        return get_session().__enter__()

    def publish_listing(
        self,
        product_id: int,
        marketplace_name: str,
        price_adjustment_rate: float,
    ) -> MarketplaceListing:
        """Create a marketplace listing for the given product."""
        with get_session() as session:
            product = session.get(Product, product_id)
            if product is None:
                raise NoResultFound(f"Product {product_id} not found")

            rate = Decimal(str(price_adjustment_rate))
            platform_price = _quantize_money(Decimal(product.base_price) * rate)

            print(
                f"API Call: Creating listing for {product.title} on "
                f"{marketplace_name} at ${platform_price}"
            )

            listing = MarketplaceListing(
                product=product,
                platform_name=marketplace_name.lower(),
                platform_listing_id=str(uuid.uuid4()),
                platform_price=platform_price,
                is_active=True,
            )
            session.add(listing)
            product.is_listed = True
            session.flush()
            session.refresh(listing)
            return listing

    def handle_sale_webhook(self, platform_data: dict) -> SalesOrder:
        """
        Process a sale webhook payload and synchronise SSOT data.

        Expected platform_data keys:
            - platform_listing_id
            - final_sale_price
            - shipping_cost (optional)
        """
        with get_session() as session:
            listing = (
                session.query(MarketplaceListing)
                .filter(
                    MarketplaceListing.platform_listing_id
                    == platform_data["platform_listing_id"]
                )
                .one()
            )
            product = listing.product

            sale_price = _quantize_money(Decimal(str(platform_data["final_sale_price"])))
            shipping_cost = _quantize_money(
                Decimal(str(platform_data.get("shipping_cost", "0")))
            )
            fee_rate = self.fee_schedule.get_fee_rate(listing.platform_name)

            listing.is_active = False
            product.current_inventory = 0
            product.is_listed = False

            siblings = (
                session.query(MarketplaceListing)
                .filter(
                    MarketplaceListing.product_id == product.id,
                    MarketplaceListing.id != listing.id,
                    MarketplaceListing.is_active.is_(True),
                )
                .all()
            )

            for sibling in siblings:
                print(
                    f"API Call: Delisting Product ID {product.id} from {sibling.platform_name}"
                )
                sibling.is_active = False

            fee_amount = _quantize_money(sale_price * fee_rate)
            net_profit = _quantize_money(
                sale_price - fee_amount - Decimal(product.original_cost) - shipping_cost
            )

            order = SalesOrder(
                marketplace_listing=listing,
                platform_name=listing.platform_name,
                sale_price=sale_price,
                platform_fee_rate=fee_rate,
                shipping_cost=shipping_cost,
                net_profit=net_profit,
            )
            session.add(order)
            session.flush()
            session.refresh(order)
            return order
