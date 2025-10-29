"""Rate limiting middleware for production."""

import logging
import time
from typing import Callable, Optional

import redis
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)

# Rate limit configurations (requests per second)
RATE_LIMITS = {
    # Endpoint patterns -> (requests_per_second, window_seconds)
    "/api/": (30, 60),  # API: 30 req/sec
    "/ebay/": (5, 60),  # OAuth: 5 req/sec
    "/seller/": (10, 60),  # Seller: 10 req/sec
    "/buyer/": (20, 60),  # Buyer: 20 req/sec
    "/auth": (2, 60),  # Auth: 2 req/sec (strict)
    "/health": (100, 60),  # Health: 100 req/sec (monitoring)
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.redis_client: Optional[redis.Redis] = None
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/"]:
            return await call_next(request)

        # Get client identifier (IP address)
        client_id = self._get_client_id(request)

        # Determine rate limit for this endpoint
        limit = self._get_rate_limit(request.url.path)

        if limit is None:
            # No rate limit for this endpoint
            return await call_next(request)

        # Check rate limit
        if not self._check_rate_limit(client_id, limit):
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path}"
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": "60"},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        requests_per_sec, window = limit
        response.headers["X-RateLimit-Limit"] = str(requests_per_sec)
        response.headers["X-RateLimit-Window"] = str(window)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try X-Forwarded-For (from reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to client IP
        return request.client.host if request.client else "unknown"

    def _get_rate_limit(self, path: str) -> Optional[tuple]:
        """Get rate limit for endpoint."""
        for pattern, limit in RATE_LIMITS.items():
            if path.startswith(pattern):
                return limit
        return None

    def _check_rate_limit(self, client_id: str, limit: tuple) -> bool:
        """Check if client is within rate limit using Redis."""
        requests_per_sec, window = limit
        max_requests = requests_per_sec * window

        try:
            if self.redis_client is None:
                self.redis_client = redis.from_url(self.settings.redis_url)

            key = f"rate_limit:{client_id}"
            current = self.redis_client.incr(key)

            # Set expiration on first request
            if current == 1:
                self.redis_client.expire(key, window)

            return current <= max_requests

        except redis.RedisError as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # On Redis error, allow request but log it
            return True


def setup_rate_limiting(app: FastAPI) -> None:
    """Add rate limiting middleware to FastAPI app."""
    app.add_middleware(RateLimitMiddleware)
