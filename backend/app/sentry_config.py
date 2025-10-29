"""Sentry error tracking configuration."""

import logging
from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def init_sentry() -> None:
    """Initialize Sentry error tracking.

    Should be called early in application startup, before any Sentry-instrumented
    code runs.
    """
    if not settings.sentry_dsn:
        logger.info("Sentry not configured (SENTRY_DSN not set)")
        return

    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            # Environment identification
            environment="production" if settings.is_production() else "development",
            release="deal-scout@0.1.0",
            # Integrations
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above
                    event_level=logging.ERROR,  # Error events
                ),
            ],
            # Performance monitoring
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.05,  # 5% with profiling (requires >= 1.25.0)
            # Options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personal data
            max_breadcrumbs=50,
            request_bodies="small",  # small | medium | always | never
            # Exclude certain errors
            ignore_errors=[
                "OperationalError",  # Database connection issues
                "ConnectionError",
            ],
        )

        logger.info("Sentry initialized successfully")

    except Exception as e:
        logger.exception(f"Failed to initialize Sentry: {e}")


def set_sentry_user(user_id: str, email: Optional[str] = None) -> None:
    """Set the current user context in Sentry.

    Args:
        user_id: Unique user identifier
        email: User email address (optional)
    """
    if not settings.sentry_dsn:
        return

    try:
        sentry_sdk.set_user(
            {
                "id": user_id,
                "email": email,
            }
        )
    except Exception as e:
        logger.debug(f"Failed to set Sentry user: {e}")


def clear_sentry_user() -> None:
    """Clear the user context in Sentry."""
    if not settings.sentry_dsn:
        return

    try:
        sentry_sdk.set_user(None)
    except Exception as e:
        logger.debug(f"Failed to clear Sentry user: {e}")


def add_sentry_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[dict] = None,
) -> None:
    """Add a breadcrumb to Sentry.

    Breadcrumbs are recorded events that led to an error.

    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Log level (debug, info, warning, error, fatal)
        data: Additional context data
    """
    if not settings.sentry_dsn:
        return

    try:
        sentry_sdk.capture_message(
            message=message,
            level=level,
        )
    except Exception as e:
        logger.debug(f"Failed to add Sentry breadcrumb: {e}")


def capture_exception(exception: Exception, context: Optional[dict] = None) -> str:
    """Capture an exception in Sentry.

    Args:
        exception: Exception to capture
        context: Additional context data

    Returns:
        Event ID for the captured exception
    """
    if not settings.sentry_dsn:
        return ""

    try:
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                event_id = sentry_sdk.capture_exception(exception)
        else:
            event_id = sentry_sdk.capture_exception(exception)

        return str(event_id) if event_id else ""

    except Exception as e:
        logger.debug(f"Failed to capture exception in Sentry: {e}")
        return ""


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[dict] = None,
) -> str:
    """Capture a message in Sentry.

    Args:
        message: Message to capture
        level: Log level (debug, info, warning, error, fatal)
        context: Additional context data

    Returns:
        Event ID for the captured message
    """
    if not settings.sentry_dsn:
        return ""

    try:
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                event_id = sentry_sdk.capture_message(message, level=level)
        else:
            event_id = sentry_sdk.capture_message(message, level=level)

        return str(event_id) if event_id else ""

    except Exception as e:
        logger.debug(f"Failed to capture message in Sentry: {e}")
        return ""
