from __future__ import annotations

import logging
import smtplib
import time
from email.message import EmailMessage
from typing import Optional

import httpx
from twilio.base.exceptions import TwilioException
from twilio.rest import Client as TwilioClient

from app.config import get_settings

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


def _retry_with_backoff(func, max_retries=MAX_RETRIES):
    """Execute function with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = RETRY_DELAY * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}"
            )
            time.sleep(delay)


def send_email(subject: str, html: str, to: Optional[str] = None) -> bool:
    """Send email with retry logic. Returns True if successful."""
    settings = get_settings()
    recipient = to or settings.email_from

    def _send():
        message = EmailMessage()
        message["From"] = settings.email_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content("Deal Scout notification")
        message.add_alternative(html, subtype="html")

        try:
            # Use TLS if configured
            smtp_class = smtplib.SMTP_SSL if settings.smtp_use_tls else smtplib.SMTP
            with smtp_class(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_use_tls and smtp_class == smtplib.SMTP:
                    server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(message)
            return True
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email to {recipient}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {e}")
            raise

    try:
        _retry_with_backoff(_send)
        logger.info(f"Email sent successfully to {recipient}: {subject}")
        return True
    except Exception as exc:
        logger.exception(f"Failed to send email after {MAX_RETRIES} attempts: {exc}")
        return False


def send_discord(message: str, embed: Optional[dict] = None) -> bool:
    """Send Discord webhook with retry logic. Returns True if successful."""
    settings = get_settings()
    if not settings.discord_webhook_url:
        logger.debug("Discord webhook not configured.")
        return False

    payload = {"content": message}
    if embed:
        payload["embeds"] = [embed]

    def _send():
        with httpx.Client(timeout=10.0) as client:
            response = client.post(settings.discord_webhook_url, json=payload)
            response.raise_for_status()
            return True

    try:
        _retry_with_backoff(_send)
        logger.info(f"Discord message sent successfully: {message[:50]}")
        return True
    except Exception as exc:
        logger.exception(f"Failed to send Discord message after {MAX_RETRIES} attempts: {exc}")
        return False


def send_sms(body: str, to_number: Optional[str] = None) -> bool:
    """Send SMS with retry logic. Returns True if successful."""
    settings = get_settings()
    if not (
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from
        and (to_number or settings.alert_sms_to)
    ):
        logger.debug("Twilio credentials or destination not configured.")
        return False

    to = to_number or settings.alert_sms_to

    def _send():
        client = TwilioClient(
            settings.twilio_account_sid, settings.twilio_auth_token
        )
        client.messages.create(to=to, from_=settings.twilio_from, body=body)
        return True

    try:
        _retry_with_backoff(_send)
        logger.info(f"SMS sent successfully to {to}: {body[:50]}")
        return True
    except TwilioException as exc:
        logger.exception(f"Failed to send SMS after {MAX_RETRIES} attempts: {exc}")
        return False
    except Exception as exc:
        logger.exception(f"Unexpected error sending SMS: {exc}")
        return False
