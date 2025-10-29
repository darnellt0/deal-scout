"""Input validation and sanitization utilities."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Validation error with a user-friendly message."""

    pass


def validate_email(email: str) -> str:
    """Validate and normalize email address."""
    if not email:
        raise ValidationError("Email cannot be empty")

    email = email.strip().lower()
    # Simple email validation
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise ValidationError(f"Invalid email address: {email}")

    return email


def validate_phone_number(phone: str) -> str:
    """Validate and normalize phone number."""
    if not phone:
        raise ValidationError("Phone number cannot be empty")

    phone = re.sub(r"\D", "", phone)
    if len(phone) < 10:
        raise ValidationError("Phone number must be at least 10 digits")

    return f"+{phone}" if not phone.startswith("+") else phone


def validate_price(price: float, min_price: float = 0, max_price: float = 1000000) -> float:
    """Validate price is within acceptable range."""
    if not isinstance(price, (int, float)):
        raise ValidationError("Price must be a number")

    if price < min_price or price > max_price:
        raise ValidationError(f"Price must be between ${min_price} and ${max_price}")

    return float(price)


def validate_url(url: str) -> str:
    """Validate URL format."""
    if not url:
        raise ValidationError("URL cannot be empty")

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        raise ValidationError("URL must start with http:// or https://")

    if len(url) > 2000:
        raise ValidationError("URL is too long")

    return url


def validate_string_length(
    value: str, min_length: int = 1, max_length: int = 1000, field_name: str = "value"
) -> str:
    """Validate string length."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    if len(value) < min_length or len(value) > max_length:
        raise ValidationError(
            f"{field_name} must be between {min_length} and {max_length} characters"
        )

    return value.strip()


def sanitize_html(html: str) -> str:
    """Basic HTML sanitization to prevent XSS."""
    # Remove script tags and event handlers
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"on\w+\s*=\s*['\"][^'\"]*['\"]", "", html, flags=re.IGNORECASE)
    html = re.sub(r"on\w+\s*=\s*[^\s>]*", "", html, flags=re.IGNORECASE)

    return html


def sanitize_sql_identifier(identifier: str, max_length: int = 63) -> str:
    """Sanitize SQL identifiers (table/column names)."""
    if not identifier:
        raise ValidationError("Identifier cannot be empty")

    # Allow only alphanumeric and underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "", identifier)

    if not sanitized:
        raise ValidationError("Identifier contains no valid characters")

    if len(sanitized) > max_length:
        raise ValidationError(f"Identifier exceeds {max_length} characters")

    return sanitized


def validate_json_dict(data: Any, required_keys: Optional[list[str]] = None) -> dict:
    """Validate data is a dictionary and contains required keys."""
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")

    if required_keys:
        missing = set(required_keys) - set(data.keys())
        if missing:
            raise ValidationError(f"Missing required keys: {missing}")

    return data
