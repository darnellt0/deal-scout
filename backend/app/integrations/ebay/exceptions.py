"""eBay integration exceptions."""

from typing import Any, Dict, Optional


class EbayIntegrationError(Exception):
    """Base exception for eBay integration errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
        error_id: Optional[str] = None,
    ):
        """Initialize eBay integration error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code from eBay API
            response_body: Full response body from eBay API
            error_id: eBay error ID for tracking
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body or {}
        self.error_id = error_id

    def __str__(self) -> str:
        """String representation of error."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.error_id:
            parts.append(f"[Error ID: {self.error_id}]")
        return " ".join(parts)


class EbayAuthenticationError(EbayIntegrationError):
    """Raised when authentication fails or token is invalid."""
    pass


class EbayAuthorizationError(EbayIntegrationError):
    """Raised when user lacks permission for requested action."""
    pass


class EbayValidationError(EbayIntegrationError):
    """Raised when request validation fails."""
    pass


class EbayResourceNotFoundError(EbayIntegrationError):
    """Raised when requested resource doesn't exist."""
    pass


class EbayConflictError(EbayIntegrationError):
    """Raised when there's a conflict (e.g., duplicate offer)."""
    pass


class EbayRateLimitError(EbayIntegrationError):
    """Raised when rate limit is exceeded."""
    pass
