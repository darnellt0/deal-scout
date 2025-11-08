from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import redis
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import or_, text

from app.config import get_settings
from app.core.db import get_session, engine
from app.core.models import Base, Listing, ListingScore
from app.core.utils import haversine_distance
from app.core.exception_handlers import register_exception_handlers
# Seller routes (CORE MVP)
from app.routes.auth import router as auth_router
from app.routes.ebay_oauth import router as ebay_oauth_router
from app.routes.my_items import router as my_items_router
from app.routes.orders import router as orders_router
from app.routes.comps import router as comps_router
from app.routes.marketplace_accounts import router as marketplace_accounts_router
from app.routes.facebook_oauth import router as facebook_oauth_router
from app.routes.offerup_oauth import router as offerup_oauth_router
from app.routes.inventory import router as inventory_router
from app.routes.cross_posts import router as cross_posts_router

# Buyer routes (PARKED - enable with FEATURE_BUYER=true)
# from app.buyer.routes import router as buyer_router
# from app.routes.listings import router as listings_router
# from app.routes.notification_preferences import router as notification_preferences_router
# from app.routes.push_notifications import router as push_notifications_router
# from app.routes.deal_alerts import router as deal_alerts_router
from app.middleware.mode_from_path import PathModeMiddleware
from app.seller.post import router as post_router
from app.seller.snap import router as snap_router
from app.seller.pricing import router as pricing_router
from app.setup.router import router as setup_router
from app.tasks.router import router as tasks_router
from app.worker import celery_app
from app.api.routes import buyer as api_buyer_routes, seller as api_seller_routes
from app.api.deps import ensure_role_from_path

# Initialize logging early for use in lifespan
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deal_scout.api")


def _wait_for_db(max_wait_seconds: int = 30) -> bool:
    """
    Wait for database to be ready. Retries with exponential backoff.
    Returns True if DB is ready, False if timeout.
    """
    start_time = time.time()
    attempt = 0
    while time.time() - start_time < max_wait_seconds:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established (attempt %s)", attempt + 1)
            return True
        except Exception as exc:
            attempt += 1
            elapsed = time.time() - start_time
            remaining = max_wait_seconds - elapsed
            logger.warning(
                "Database not ready (attempt %s, %.1fs elapsed, %.1fs remaining): %s",
                attempt,
                elapsed,
                max(remaining, 0.0),
                type(exc).__name__,
            )
            time.sleep(min(2 ** attempt, 5))

    logger.error(
        "Database failed to become ready after %ss. Health checks may still respond OK, but queries can fail.",
        max_wait_seconds,
    )
    return False


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Wait for database to be ready before creating tables
    _wait_for_db()
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()

app = FastAPI(title="Deal Scout API", version="0.1.0", lifespan=lifespan)

# Register exception handlers
register_exception_handlers(app)

frontend_origins = {
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
    "http://127.0.0.1:3001",
}
allow_origins = list({*(settings.cors_origins if hasattr(settings, "cors_origins") else []), *frontend_origins})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PathModeMiddleware)

role_from_path_dependency = ensure_role_from_path()

# Safely mount static files only if directory exists
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    logger.warning("Static directory %s not found; skipping static mount.", static_dir)

REQUEST_COUNTER = Counter(
    "deal_scout_requests_total", "Total HTTP requests", ["method", "path", "status"]
)


@app.middleware("http")
async def log_and_count_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    path = request.url.path
    status = response.status_code
    REQUEST_COUNTER.labels(request.method, path, str(status)).inc()
    log_payload = {
        "method": request.method,
        "path": path,
        "status": status,
        "duration_ms": round(duration * 1000, 2),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(json.dumps(log_payload))
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/ping")
async def ping():
    """Quick ping endpoint for basic connectivity checks."""
    return {"pong": True, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/health")
async def health():
    db_ok = False
    redis_ok = False
    queue_depth = None

    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.exception("Database health check failed")

    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        redis_ok = True
        queue_depth = redis_client.llen("celery")
    except Exception:
        logger.exception("Redis health check failed")

    ok = db_ok and redis_ok
    payload = {
        "ok": ok,
        "db": db_ok,
        "redis": redis_ok,
        "queue_depth": queue_depth,
        "version": app.version,
        "time": datetime.now(timezone.utc).isoformat(),
    }
    status_code = 200 if ok else 503
    return JSONResponse(payload, status_code=status_code)


# BUYER ENDPOINT (PARKED)
# Restore if FEATURE_BUYER=true
# @app.get("/listings")
# async def public_listings(...):
#     """Fetch marketplace deal listings for buyers"""
#     ...

# Authentication routes
app.include_router(auth_router)

# Core seller routes (MVP)
app.include_router(my_items_router)
app.include_router(orders_router)
app.include_router(comps_router)  # Used for pricing suggestions
app.include_router(marketplace_accounts_router)
app.include_router(inventory_router)

# Seller workflows
app.include_router(
    snap_router,
    prefix="/seller",
    tags=["seller"],
    dependencies=[Depends(role_from_path_dependency)],
)
app.include_router(
    post_router,
    prefix="/seller",
    tags=["seller"],
    dependencies=[Depends(role_from_path_dependency)],
)
app.include_router(
    pricing_router,
    prefix="/seller",
    tags=["seller"],
    dependencies=[Depends(role_from_path_dependency)],
)
app.include_router(
    cross_posts_router,
    prefix="/seller",
    tags=["seller"],
    dependencies=[Depends(role_from_path_dependency)],
)

# OAuth integrations
app.include_router(ebay_oauth_router, prefix="/ebay", tags=["ebay"])
app.include_router(facebook_oauth_router)
app.include_router(offerup_oauth_router)

# Admin/utility routes
app.include_router(api_seller_routes.router)
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(setup_router, prefix="/setup", tags=["setup"])

# Buyer routes (PARKED - restore if FEATURE_BUYER=true)
# app.include_router(listings_router)
# app.include_router(notification_preferences_router)
# app.include_router(push_notifications_router)
# app.include_router(deal_alerts_router)
# app.include_router(buyer_router, prefix="/buyer", tags=["buyer"], dependencies=[Depends(role_from_path_dependency)])
# app.include_router(api_buyer_routes.router)


# BUYER SCAN ENDPOINT (PARKED)
# Restore if FEATURE_BUYER=true
# @app.post("/scan/run")
# async def trigger_scan_run(...):
#     """Trigger marketplace scanning for buyer deal discovery"""
#     ...
