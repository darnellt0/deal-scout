"""Setup router for first-run checklist and system verification."""

from __future__ import annotations

import logging
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import redis
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.config import get_settings
from app.core.db import get_session
from app.worker import celery_app
from app.notify.channels import send_email, send_discord, send_sms

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()


# ============================================================================
# Data Models
# ============================================================================

class CheckStatus:
    """Represents a single system check."""

    def __init__(self, check_id: str, label: str, status: str, details: str = ""):
        self.id = check_id
        self.label = label
        self.status = status  # 'ok', 'warn', 'fail'
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "details": self.details,
        }


# ============================================================================
# Health Check Functions
# ============================================================================

def check_database() -> CheckStatus:
    """Check database connectivity."""
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        return CheckStatus("db", "Database connected", "ok", "PostgreSQL/SQLite reachable")
    except Exception as e:
        logger.exception("Database check failed")
        return CheckStatus("db", "Database connected", "fail", str(e))


def check_redis() -> CheckStatus:
    """Check Redis connectivity."""
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        return CheckStatus("redis", "Redis connected", "ok", "Redis PING successful")
    except Exception as e:
        logger.exception("Redis check failed")
        return CheckStatus("redis", "Redis connected", "fail", str(e))


def check_celery_worker() -> CheckStatus:
    """Check if Celery worker is running by enqueueing a ping task."""
    try:
        # Enqueue a low-priority ping task and wait up to 2 seconds
        result = celery_app.send_task("app.tasks.ping", queue="celery")
        start_time = time.time()

        while time.time() - start_time < 2.0:
            if result.ready():
                if result.successful():
                    return CheckStatus(
                        "worker",
                        "Background worker running",
                        "ok",
                        "Worker responded to ping",
                    )
                else:
                    return CheckStatus(
                        "worker",
                        "Background worker running",
                        "warn",
                        "Worker task failed",
                    )
            time.sleep(0.1)

        # Non-blocking fallback: return unknown if no response within 2s
        return CheckStatus(
            "worker",
            "Background worker running",
            "warn",
            "No response within 2s (may still be running)",
        )
    except Exception as e:
        logger.exception("Celery worker check failed")
        return CheckStatus(
            "worker", "Background worker running", "warn", f"Could not verify: {e}"
        )


def check_scheduler() -> CheckStatus:
    """Check if Celery beat scheduler is active."""
    try:
        redis_client = redis.from_url(settings.redis_url)
        last_scan_ts_key = "celery:beat:last_scan_ts"
        last_scan_ts_raw = redis_client.get(last_scan_ts_key)

        if not last_scan_ts_raw:
            return CheckStatus(
                "scheduler",
                "Scan scheduler active",
                "warn",
                "No recent scan activity recorded",
            )

        last_scan_ts = float(last_scan_ts_raw)
        now_ts = time.time()
        time_since_scan = now_ts - last_scan_ts

        if time_since_scan < 600:  # Within last 10 minutes
            return CheckStatus(
                "scheduler",
                "Scan scheduler active",
                "ok",
                f"Last scan {int(time_since_scan)}s ago",
            )
        else:
            return CheckStatus(
                "scheduler",
                "Scan scheduler active",
                "warn",
                f"Last scan {int(time_since_scan)}s ago (>10m)",
            )
    except Exception as e:
        logger.exception("Scheduler check failed")
        return CheckStatus(
            "scheduler", "Scan scheduler active", "warn", str(e)
        )


def check_ebay_connected() -> CheckStatus:
    """Check if eBay is connected via OAuth."""
    try:
        with get_session() as session:
            result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM marketplace_accounts
                    WHERE platform = 'ebay' AND connected = true AND credentials ->> 'refresh_token' IS NOT NULL
                    """
                )
            ).scalar()

            if result and result > 0:
                return CheckStatus(
                    "ebay", "eBay connected (OAuth)", "ok", "Connected account found"
                )
            else:
                return CheckStatus(
                    "ebay", "eBay connected (OAuth)", "warn", "No connected account"
                )
    except Exception as e:
        logger.exception("eBay check failed")
        return CheckStatus("ebay", "eBay connected (OAuth)", "warn", str(e))


def check_craigslist_configured() -> CheckStatus:
    """Check if Craigslist region is configured."""
    cl_region = settings.cl_region
    if cl_region:
        return CheckStatus(
            "craigslist",
            "Craigslist region configured",
            "ok",
            cl_region,
        )
    else:
        return CheckStatus(
            "craigslist",
            "Craigslist region configured",
            "warn",
            "CL_REGION not set",
        )


def check_email_configured() -> CheckStatus:
    """Check if email (SMTP) is reachable."""
    smtp_host = settings.smtp_host
    smtp_port = settings.smtp_port

    if not smtp_host:
        return CheckStatus("email", "Email delivery (MailHog)", "warn", "SMTP not configured")

    try:
        # Attempt to open a socket to SMTP server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((smtp_host, smtp_port))
        sock.close()

        if result == 0:
            return CheckStatus("email", "Email delivery (MailHog)", "ok", f"{smtp_host}:{smtp_port} reachable")
        else:
            return CheckStatus(
                "email",
                "Email delivery (MailHog)",
                "warn",
                f"{smtp_host}:{smtp_port} not reachable",
            )
    except Exception as e:
        logger.debug(f"Email check failed: {e}")
        return CheckStatus(
            "email", "Email delivery (MailHog)", "warn", f"Socket error: {e}"
        )


def check_discord_configured() -> CheckStatus:
    """Check if Discord webhook is configured."""
    if settings.discord_webhook_url:
        return CheckStatus(
            "discord", "Discord webhook set", "ok", "Webhook URL present"
        )
    else:
        return CheckStatus(
            "discord", "Discord webhook set", "warn", "DISCORD_WEBHOOK_URL not set"
        )


def check_sms_configured() -> CheckStatus:
    """Check if SMS (Twilio) is configured."""
    has_twilio = (
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from
    )
    has_sms_target = settings.alert_sms_to

    if has_twilio and has_sms_target:
        return CheckStatus(
            "sms", "SMS (Twilio) configured", "ok", "All credentials present"
        )
    elif has_twilio:
        return CheckStatus(
            "sms", "SMS (Twilio) configured", "warn", "Credentials present but no target number"
        )
    else:
        return CheckStatus(
            "sms", "SMS (Twilio) configured", "warn", "Twilio credentials not configured"
        )


def check_demo_mode() -> CheckStatus:
    """Check demo mode status."""
    mode = "on" if settings.demo_mode else "off"
    return CheckStatus("demo", "Demo Mode toggle", "ok", mode)


def check_comps_loaded() -> CheckStatus:
    """Check if local comps are loaded (furniture items)."""
    try:
        with get_session() as session:
            # Check for furniture>sofas and furniture>kitchen_island
            result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM comps
                    WHERE category IN ('furniture>sofas', 'furniture>kitchen_island')
                    """
                )
            ).scalar()

            if result and result > 0:
                return CheckStatus(
                    "comps",
                    "Local comps loaded",
                    "ok",
                    f"{result} comp entries found",
                )
            else:
                return CheckStatus(
                    "comps",
                    "Local comps loaded",
                    "warn",
                    "No comps found in database",
                )
    except Exception as e:
        logger.exception("Comps check failed")
        return CheckStatus("comps", "Local comps loaded", "warn", str(e))


def check_vision_pipeline() -> CheckStatus:
    """Check if vision pipeline is enabled and importable."""
    vision_enabled = settings.vision_enabled
    rembg_enabled = settings.rembg_enabled

    if not vision_enabled and not rembg_enabled:
        return CheckStatus(
            "vision",
            "Vision & background removal",
            "warn",
            "Both VISION_ENABLED and REMBG_ENABLED are false",
        )

    try:
        # Try importing the vision module
        import app.vision.detector

        details = []
        if vision_enabled:
            details.append("Vision enabled")
        if rembg_enabled:
            details.append("RemBG enabled")

        return CheckStatus(
            "vision",
            "Vision & background removal",
            "ok",
            " + ".join(details),
        )
    except ImportError as e:
        logger.exception("Vision module import failed")
        return CheckStatus(
            "vision",
            "Vision & background removal",
            "warn",
            f"Import error: {e}",
        )
    except Exception as e:
        logger.exception("Vision check failed")
        return CheckStatus(
            "vision",
            "Vision & background removal",
            "warn",
            f"Check failed: {e}",
        )


def check_static_samples() -> CheckStatus:
    """Check if static sample images are available."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    samples_dir = backend_dir / "static" / "samples"

    if samples_dir.exists():
        files = list(samples_dir.glob("*"))
        if files:
            return CheckStatus(
                "static",
                "Sample images available",
                "ok",
                f"{len(files)} files in {samples_dir.relative_to(backend_dir)}",
            )
        else:
            return CheckStatus(
                "static",
                "Sample images available",
                "warn",
                f"Directory exists but is empty",
            )
    else:
        return CheckStatus(
            "static",
            "Sample images available",
            "warn",
            f"Directory does not exist: {samples_dir.relative_to(backend_dir)}",
        )


# ============================================================================
# Status Endpoint
# ============================================================================

@router.get("/status")
async def get_setup_status() -> Dict[str, Any]:
    """
    GET /setup/status

    Returns a comprehensive JSON summary of system setup checks.
    This is used by the First-Run Checklist banner to show setup progress.
    """
    checks: List[CheckStatus] = [
        check_database(),
        check_redis(),
        check_celery_worker(),
        check_scheduler(),
        check_ebay_connected(),
        check_craigslist_configured(),
        check_email_configured(),
        check_discord_configured(),
        check_sms_configured(),
        check_demo_mode(),
        check_comps_loaded(),
        check_vision_pipeline(),
        check_static_samples(),
    ]

    # Calculate progress: count of "ok" checks / total checks
    ok_count = sum(1 for check in checks if check.status == "ok")
    total_count = len(checks)
    progress = ok_count / total_count if total_count > 0 else 0.0

    # Overall status: "ok" if all critical checks pass
    critical_checks = {"db", "redis"}
    critical_ok = all(
        check.status == "ok"
        for check in checks
        if check.id in critical_checks
    )
    overall_ok = critical_ok

    return {
        "ok": overall_ok,
        "checks": [check.to_dict() for check in checks],
        "progress": progress,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Test Notification Endpoint
# ============================================================================

def send_test_notification() -> Dict[str, Any]:
    """
    Send a demo notification through all enabled channels.
    Returns per-channel results.
    """
    results = {
        "email": {"sent": False, "details": ""},
        "discord": {"sent": False, "details": ""},
        "sms": {"sent": False, "details": ""},
    }

    # Test email (MailHog)
    if settings.smtp_host:
        try:
            subject = "[Deal Scout] Test Notification"
            html = """
            <html>
                <body>
                    <h2>Deal Scout - Test Notification</h2>
                    <p>This is a test notification from the First-Run Checklist.</p>
                    <p>Email delivery is working correctly!</p>
                    <hr/>
                    <p><small>Sent via Deal Scout Setup Verification</small></p>
                </body>
            </html>
            """
            success = send_email(subject, html)
            results["email"]["sent"] = success
            results["email"]["details"] = "Email sent via SMTP" if success else "Email delivery failed"
        except Exception as e:
            logger.exception("Email test failed")
            results["email"]["details"] = str(e)
    else:
        results["email"]["details"] = "SMTP not configured"

    # Test Discord webhook
    if settings.discord_webhook_url:
        try:
            message = "Deal Scout Test Notification"
            embed = {
                "title": "First-Run Checklist Verification",
                "description": "This is a test notification from the setup verification.",
                "color": 5763719,  # Nice blue color
            }
            success = send_discord(message, embed)
            results["discord"]["sent"] = success
            results["discord"]["details"] = "Discord message sent" if success else "Discord delivery failed"
        except Exception as e:
            logger.exception("Discord test failed")
            results["discord"]["details"] = str(e)
    else:
        results["discord"]["details"] = "Discord webhook not configured"

    # Test SMS (Twilio)
    if (
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.alert_sms_to
    ):
        try:
            message = "Deal Scout setup verification: SMS delivery working!"
            success = send_sms(message, settings.alert_sms_to)
            results["sms"]["sent"] = success
            results["sms"]["details"] = "SMS sent via Twilio" if success else "SMS delivery failed"
        except Exception as e:
            logger.exception("SMS test failed")
            results["sms"]["details"] = str(e)
    else:
        results["sms"]["details"] = "Twilio credentials or target not configured"

    return results


@router.post("/test-notification")
async def test_notification() -> Dict[str, Any]:
    """
    POST /setup/test-notification

    Send demo notifications through all enabled channels (email, Discord, SMS).
    Returns per-channel results with success/failure details.
    """
    try:
        results = send_test_notification()
        any_sent = any(r["sent"] for r in results.values())

        return {
            "success": any_sent,
            "details": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("Test notification failed")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dismiss Endpoint
# ============================================================================

@router.post("/dismiss")
async def dismiss_checklist() -> Dict[str, Any]:
    """
    POST /setup/dismiss

    Record that the user has dismissed the First-Run Checklist banner.
    This is a single-user MVP implementation using Redis.
    """
    try:
        redis_client = redis.from_url(settings.redis_url)
        # Store a simple flag: "setup:dismissed" → timestamp
        redis_client.set("setup:dismissed", int(time.time()), ex=None)  # No expiration

        return {
            "dismissed": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("Dismiss checklist failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/is-dismissed")
async def is_checklist_dismissed() -> Dict[str, Any]:
    """
    GET /setup/is-dismissed

    Check if the First-Run Checklist has been dismissed by the user.
    """
    try:
        redis_client = redis.from_url(settings.redis_url)
        dismissed_ts = redis_client.get("setup:dismissed")

        return {
            "dismissed": dismissed_ts is not None,
            "dismissed_at": (
                datetime.fromtimestamp(int(dismissed_ts), tz=timezone.utc).isoformat()
                if dismissed_ts
                else None
            ),
        }
    except Exception as e:
        logger.exception("Check dismiss status failed")
        raise HTTPException(status_code=500, detail=str(e))
