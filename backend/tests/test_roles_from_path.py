from datetime import datetime, timezone, timedelta
import os
import sys
import types

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_roles_from_path.db")
os.environ.setdefault("JWT_SECRET_KEY", "dev-secret-key-change-in-production")

bcrypt_stub = types.ModuleType("bcrypt")
bcrypt_stub.gensalt = lambda rounds=12: b"salt"
bcrypt_stub.hashpw = lambda password, salt: b"hashed"
bcrypt_stub.checkpw = lambda password, hashed: True
sys.modules.setdefault("bcrypt", bcrypt_stub)

from app.core.db import engine, SessionLocal  # noqa: E402
from app.core.models import Base, User, UserRole  # noqa: E402
from app.main import app  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.buyer_profile import BuyerProfile  # noqa: E402
from app.models.seller_profile import SellerProfile  # noqa: E402

SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        if not session.query(Role).filter(Role.name == "buyer").first():
            session.add(Role(name="buyer"))
        if not session.query(Role).filter(Role.name == "seller").first():
            session.add(Role(name="seller"))
        session.commit()
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token_factory():
    def _create(user_role: UserRole = UserRole.buyer) -> tuple[str, int]:
        issued_at = datetime.now(timezone.utc)
        stamp = f"{issued_at.timestamp()}".replace(".", "")
        with SessionLocal() as session:
            user = User(
                username=f"user_{stamp}",
                email=f"user_{stamp}@example.com",
                password_hash="hashed",
                role=user_role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            payload = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "exp": issued_at + timedelta(hours=1),
                "iat": issued_at,
            }
            token = jwt.encode(payload, SECRET, algorithm="HS256")
            return token, user.id

    return _create


def test_auto_enable_buyer(client, auth_token_factory):
    token, user_id = auth_token_factory()
    response = client.get("/buyer/deals", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    with SessionLocal() as session:
        db_user = session.get(User, user_id)
        assert db_user is not None
        assert "buyer" in db_user.role_names
        assert session.get(BuyerProfile, user_id) is not None


def test_auto_enable_seller(client, auth_token_factory):
    token, user_id = auth_token_factory()
    response = client.post(
        "/seller/listings",
        json={"title": "Sample"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    with SessionLocal() as session:
        db_user = session.get(User, user_id)
        assert db_user is not None
        assert "seller" in db_user.role_names
        assert session.get(SellerProfile, user_id) is not None
