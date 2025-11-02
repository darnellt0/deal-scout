from __future__ import annotations

import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Configure engine differently for SQLite vs Postgres
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        poolclass=NullPool,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    pool_class = NullPool if settings.demo_mode else QueuePool
    engine_kwargs = {
        "pool_pre_ping": True,
        "poolclass": pool_class,
        "echo": False,
        "connect_args": {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
        },
    }
    # Only add pool_size/max_overflow for QueuePool
    if pool_class == QueuePool:
        engine_kwargs["pool_size"] = settings.database_pool_size
        engine_kwargs["max_overflow"] = settings.database_max_overflow

    engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Configure connection on connect."""
    if settings.database_url.startswith("sqlite"):
        return
    cursor = dbapi_conn.cursor()
    cursor.execute("SET application_name = 'deal_scout'")
    cursor.close()


@contextmanager
def get_session():
    """Get a database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception("Database session error: %s", e)
        raise
    finally:
        session.close()
