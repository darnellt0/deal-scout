import os
import sys
import types
from datetime import datetime, timezone, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_cross_posts_api.db")

# Provide lightweight bcrypt stub for hashing in model creation
bcrypt_stub = types.ModuleType("bcrypt")
bcrypt_stub.gensalt = lambda rounds=12: b"salt"
bcrypt_stub.hashpw = lambda password, salt: b"hashed"
bcrypt_stub.checkpw = lambda password, hashed: True
sys.modules.setdefault("bcrypt", bcrypt_stub)

check_deal_alerts_stub = types.ModuleType("app.tasks.check_deal_alerts")
sys.modules.setdefault("app.tasks.check_deal_alerts", check_deal_alerts_stub)

from app.core.db import engine, get_session  # noqa: E402
from app.core.models import Base, CrossPost, MyItem, User, UserRole  # noqa: E402
from app.main import app  # noqa: E402

SECRET = "dev-secret-key-change-in-production"


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def cleanup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "username": "seller",
        "email": "seller@example.com",
        "role": "seller",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def seed_cross_post() -> tuple[int, int, int]:
    with get_session() as session:
        user = User(
            username="seller",
            email="seller@example.com",
            password_hash="hashed",
            role=UserRole.seller,
        )
        session.add(user)
        session.flush()

        item = MyItem(
            user_id=user.id,
            title="Test Item",
            category="general",
            attributes={},
            price=199.99,
            status="active",
        )
        session.add(item)
        session.flush()

        cross_post = CrossPost(
            my_item_id=item.id,
            platform="ebay",
            listing_url="https://example.com/listing",
            status="pending",
            meta={"notes": "test note", "snap_job_id": 123},
        )
        session.add(cross_post)
        session.flush()

        cross_post_id = cross_post.id
        user_id = user.id
        my_item_id = item.id

    return cross_post_id, user_id, my_item_id


def test_list_cross_posts_returns_records():
    cross_post_id, user_id, my_item_id = seed_cross_post()
    client = TestClient(app)
    token = create_token(user_id)

    response = client.get(
        "/seller/cross-posts",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    record = data[0]
    assert record["id"] == cross_post_id
    assert record["platform"] == "ebay"
    assert record["status"] == "pending"
    assert record["notes"] == "test note"
    assert record["snap_job_id"] == 123
    assert record["item"]["id"] == my_item_id
    assert record["item"]["title"] == "Test Item"
