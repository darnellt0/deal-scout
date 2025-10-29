"""Structured error handling and custom exceptions."""

from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_QUERY_PARAM = "INVALID_QUERY_PARAM"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # Authentication/Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Business logic errors
    INVALID_STATE = "INVALID_STATE"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    RATE_LIMITED = "RATE_LIMITED"


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = Field(None, description="Field name if field-specific error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")


class ErrorResponse(BaseModel):
    """Standardized API error response."""

    error: ErrorCode = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: list[ErrorDetail] = Field(default_factory=list, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    path: Optional[str] = Field(None, description="Request path")


class APIException(Exception):
    """Base API exception."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int,
        details: Optional[list[ErrorDetail]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        self.request_id = request_id
        self.path = path
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        """Convert exception to error response."""
        return ErrorResponse(
            error=self.error_code,
            message=self.message,
            details=self.details,
            request_id=self.request_id,
            path=self.path,
        )


class ValidationError(APIException):
    """Validation error exception."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[list[ErrorDetail]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=422,
            details=details,
            request_id=request_id,
            path=path,
        )


class NotFoundError(APIException):
    """Resource not found exception."""

    def __init__(
        self,
        resource: str,
        resource_id: Any = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        message = f"{resource} not found"
        if resource_id:
            message += f" (id: {resource_id})"

        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=message,
            status_code=404,
            request_id=request_id,
            path=path,
        )


class ConflictError(APIException):
    """Resource conflict exception."""

    def __init__(
        self,
        message: str,
        details: Optional[list[ErrorDetail]] = None,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.CONFLICT,
            message=message,
            status_code=409,
            details=details,
            request_id=request_id,
            path=path,
        )


class UnauthorizedError(APIException):
    """Authentication error exception."""

    def __init__(
        self,
        message: str = "Authentication required",
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=401,
            request_id=request_id,
            path=path,
        )


class ForbiddenError(APIException):
    """Authorization error exception."""

    def __init__(
        self,
        message: str = "Access denied",
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=403,
            request_id=request_id,
            path=path,
        )


class InvalidStateError(APIException):
    """Invalid state transition exception."""

    def __init__(
        self,
        message: str,
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.INVALID_STATE,
            message=message,
            status_code=409,
            request_id=request_id,
            path=path,
        )


class DatabaseError(APIException):
    """Database operation error exception."""

    def __init__(
        self,
        message: str = "Database error occurred",
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            status_code=500,
            request_id=request_id,
            path=path,
        )


class ServiceUnavailableError(APIException):
    """Service unavailable exception."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
            status_code=503,
            request_id=request_id,
            path=path,
        )


class RateLimitError(APIException):
    """Rate limit exceeded exception."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        request_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        super().__init__(
            error_code=ErrorCode.RATE_LIMITED,
            message=message,
            status_code=429,
            request_id=request_id,
            path=path,
        )
