import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.market.ebay_client import (
    create_offer,
    create_or_update_inventory,
    exchange_code_for_refresh_token,
    get_oauth_authorize_url,
)
from app.config import get_settings
from app.core.db import engine, get_session
from app.core.models import Base, MarketplaceAccount

Base.metadata.create_all(bind=engine)


def test_authorize_url_includes_sandbox():
    settings = get_settings()
    settings.ebay_env = "sandbox"
    settings.ebay_app_id = "demo-app"
    url = get_oauth_authorize_url()
    assert "auth.sandbox.ebay.com" in url
    assert "client_id=demo-app" in url


def test_exchange_demo_mode_stores_token():
    settings = get_settings()
    settings.demo_mode = True
    token = exchange_code_for_refresh_token("demo-token")
    assert token == "demo-token"
    with get_session() as session:
        account = session.query(MarketplaceAccount).filter_by(platform="ebay").one()
        assert account.credentials["refresh_token"] == "demo-token"
        assert account.connected is True


def test_inventory_and_offer_demo_mode():
    settings = get_settings()
    settings.demo_mode = True
    inventory = create_or_update_inventory({"sku": "TEST-SKU"})
    assert inventory["status"] == "mocked"
    offer = create_offer({"sku": "TEST-SKU"}, price=100.0, policies={})
    assert offer["offerId"].startswith("demo-offer")
