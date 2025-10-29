"""Middleware modules."""

from app.middleware.rate_limiting import setup_rate_limiting

__all__ = ["setup_rate_limiting"]
