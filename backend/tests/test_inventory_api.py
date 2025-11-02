
import os
import sys
import types
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_inventory_api.db")

bcrypt_stub = types.ModuleType("bcrypt")
bcrypt_stub.gensalt = lambda rounds=12: b"salt"
bcrypt_stub.hashpw = lambda password, salt: b"hashed"
bcrypt_stub.checkpw = lambda password, hashed: True
sys.modules.setdefault("bcrypt", bcrypt_stub)

check_deal_alerts_stub = types.ModuleType("app.tasks.check_deal_alerts")
sys.modules.setdefault("app.tasks.check_deal_alerts", check_deal_alerts_stub)

from app.core.db import engine, get_session
from app.core.models import Base, MarketplaceListing, Product, SalesOrder
from app.main import app


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_product(
    sku: str = "SKU-001",
    base_price: Decimal = Decimal("100.00"),
    original_cost: Decimal = Decimal("40.00"),
) -> int:
    with get_session() as session:
        product = Product(
            sku=sku,
            base_price=base_price,
            original_cost=original_cost,
            title="Test Product",
            description="Demo",
            current_inventory=1,
            is_listed=False,
        )
        session.add(product)
        session.flush()
        product_id = product.id
    return product_id


def test_publish_listing_endpoint():
    product_id = create_product()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/inventory/{product_id}/publish/",
        json={"marketplace_name": "eBay", "price_adjustment_rate": 1.15},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["product_id"] == product_id
    assert data["platform_name"] == "ebay"
    assert Decimal(data["platform_price"]) == Decimal("115.00")
    assert data["is_active"] is True

    with get_session() as session:
        db_product: Product = session.get(Product, product_id)
        assert db_product.is_listed is True

        listings = (
            session.query(MarketplaceListing)
            .filter(MarketplaceListing.product_id == product_id)
            .all()
        )
        assert len(listings) == 1


def test_sale_webhook_endpoint_cross_delists():
    product_id = create_product(original_cost=Decimal("50.00"))

    with get_session() as session:
        product: Product = session.get(Product, product_id)
        product.is_listed = True
        ebay_listing = MarketplaceListing(
            product=product,
            platform_name="ebay",
            platform_listing_id="ebay-123",
            platform_price=Decimal("120.00"),
            is_active=True,
        )
        posh_listing = MarketplaceListing(
            product=product,
            platform_name="poshmark",
            platform_listing_id="posh-456",
            platform_price=Decimal("130.00"),
            is_active=True,
        )
        session.add_all([ebay_listing, posh_listing])
        session.flush()
        posh_id = posh_listing.id
        ebay_id = ebay_listing.id

    client = TestClient(app)
    payload = {
        "platform_listing_id": "posh-456",
        "final_sale_price": "150.00",
    }

    response = client.post("/api/v1/inventory/webhooks/poshmark/", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["marketplace_listing_id"] == posh_id
    assert Decimal(body["sale_price"]) == Decimal("150.00")
    assert Decimal(body["platform_fee_rate"]) == Decimal("0.20")
    assert Decimal(body["net_profit"]) == Decimal("70.00")

    with get_session() as session:
        product: Product = session.get(Product, product_id)
        assert product.current_inventory == 0
        assert product.is_listed is False

        posh_listing = session.get(MarketplaceListing, posh_id)
        assert posh_listing.is_active is False

        ebay_listing = session.get(MarketplaceListing, ebay_id)
        assert ebay_listing.is_active is False

        orders = session.query(SalesOrder).all()
        assert len(orders) == 1
        order = orders[0]
        assert Decimal(order.net_profit) == Decimal("70.00")
