import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app
from app.core.db import engine
from app.core.models import Base

Base.metadata.create_all(bind=engine)


def test_health(monkeypatch):
    class DummyRedis:
        def ping(self):
            return True

        def llen(self, _):
            return 0

    monkeypatch.setattr("app.main.redis", SimpleNamespace(from_url=lambda url: DummyRedis()))
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["db"] is True
    assert body["redis"] is True
    assert body["queue_depth"] == 0
