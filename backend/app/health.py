"""Health check and liveness probe endpoints."""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import redis
from sqlalchemy import text

from app.config import get_settings
from app.core.db import get_session

logger = logging.getLogger(__name__)

settings = get_settings()


class HealthStatus:
    """Health status tracker."""

    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.last_check: Optional[datetime] = None
        self.cache: Dict[str, Any] = {}

    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now(timezone.utc) - self.start_time).total_seconds()

    def cache_result(self, key: str, value: Any, ttl_seconds: int = 30) -> None:
        """Cache health check result."""
        self.cache[key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl_seconds,
        }

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached health check result if not expired."""
        if key not in self.cache:
            return None

        cached = self.cache[key]
        age = time.time() - cached["timestamp"]

        if age > cached["ttl"]:
            del self.cache[key]
            return None

        return cached["value"]


health_status = HealthStatus()


def check_database() -> Dict[str, Any]:
    """Check database connectivity and health."""
    cached = health_status.get_cached("database")
    if cached is not None:
        return cached

    result = {"status": "unknown", "details": {}}

    try:
        with get_session() as session:
            # Simple connectivity check
            session.execute(text("SELECT 1"))

            # Get database size
            db_size = session.execute(
                text(
                    "SELECT pg_database.datname, "
                    "pg_size_pretty(pg_database_size(pg_database.datname)) AS size "
                    "FROM pg_database WHERE datname = current_database()"
                )
            ).fetchone()

            result["status"] = "healthy"
            result["details"]["size"] = db_size[1] if db_size else "unknown"
            result["details"]["url_safe"] = "***" in settings.database_url

    except Exception as e:
        logger.exception("Database health check failed")
        result["status"] = "unhealthy"
        result["details"]["error"] = str(e)

    health_status.cache_result("database", result)
    return result


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity and health."""
    cached = health_status.get_cached("redis")
    if cached is not None:
        return cached

    result = {"status": "unknown", "details": {}}

    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()

        # Get memory info
        info = redis_client.info("memory")
        result["status"] = "healthy"
        result["details"]["memory_used"] = info.get("used_memory_human")
        result["details"]["memory_peak"] = info.get("used_memory_peak_human")

        # Get queue depth
        queue_depth = redis_client.llen("celery")
        result["details"]["queue_depth"] = queue_depth

    except Exception as e:
        logger.exception("Redis health check failed")
        result["status"] = "unhealthy"
        result["details"]["error"] = str(e)

    health_status.cache_result("redis", result)
    return result


def check_external_services() -> Dict[str, Any]:
    """Check external service connectivity (not critical)."""
    result = {}

    # OpenAI
    if settings.openai_api_key:
        try:
            import openai

            openai.api_key = settings.openai_api_key
            # Just verify the key is valid format (don't make API call for every health check)
            result["openai"] = (
                "configured"
                if settings.openai_api_key.startswith("sk-")
                else "invalid"
            )
        except Exception as e:
            logger.debug(f"OpenAI check failed: {e}")
            result["openai"] = "error"
    else:
        result["openai"] = "not_configured"

    # eBay
    result["ebay"] = "configured" if settings.ebay_app_id else "not_configured"

    # SMTP
    result["smtp"] = "configured" if settings.smtp_host else "not_configured"

    # Discord
    result["discord"] = (
        "configured" if settings.discord_webhook_url else "not_configured"
    )

    # Twilio
    result["twilio"] = (
        "configured"
        if (settings.twilio_account_sid and settings.twilio_auth_token)
        else "not_configured"
    )

    return result


async def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status."""
    db_status = check_database()
    redis_status = check_redis()
    external_status = check_external_services()

    # Determine overall health
    critical_healthy = (
        db_status["status"] == "healthy" and redis_status["status"] == "healthy"
    )

    overall_status = "healthy" if critical_healthy else "degraded"
    if not critical_healthy:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": health_status.get_uptime_seconds(),
        "version": "0.1.0",
        "environment": "production" if settings.is_production() else "development",
        "database": db_status,
        "redis": redis_status,
        "external_services": external_status,
    }


async def get_liveness() -> Dict[str, Any]:
    """Get liveness probe status (is app running?)."""
    return {
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": health_status.get_uptime_seconds(),
    }


async def get_readiness() -> Dict[str, Any]:
    """Get readiness probe status (is app ready to serve?)."""
    db_status = check_database()
    redis_status = check_redis()

    ready = (
        db_status["status"] == "healthy" and redis_status["status"] == "healthy"
    )

    return {
        "ready": ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_ready": db_status["status"] == "healthy",
        "redis_ready": redis_status["status"] == "healthy",
    }
