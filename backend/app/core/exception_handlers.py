"""FastAPI exception handlers for structured error responses."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.errors import (
    APIException,
    DatabaseError,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    ValidationError as CustomValidationError,
)

logger = logging.getLogger("deal_scout.api")


def _generate_request_id(request: Request) -> str:
    """Extract or generate request ID."""
    return request.headers.get("X-Request-ID", request.url.path)


def _create_error_response(
    error_code: ErrorCode,
    message: str,
    status_code: int,
    request: Request,
    details: Optional[list[ErrorDetail]] = None,
) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        error=error_code,
        message=message,
        details=details or [],
        request_id=_generate_request_id(request),
        path=request.url.path,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with FastAPI app."""

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """Handle custom API exceptions."""
        logger.warning(
            f"API Exception: {exc.error_code.value} - {exc.message}",
            extra={"status_code": exc.status_code, "path": request.url.path},
        )
        response = exc.to_response()
        response.request_id = _generate_request_id(request)
        response.path = request.url.path
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        details = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"][1:]) if len(error["loc"]) > 1 else None
            details.append(
                ErrorDetail(
                    field=field,
                    message=error["msg"],
                    code=error["type"],
                )
            )

        logger.warning(
            "Pydantic validation error",
            extra={"path": request.url.path, "error_count": len(details)},
        )

        response = _create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            request=request,
            details=details,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        """Handle database integrity errors (unique constraints, foreign keys, etc)."""
        logger.error(
            "Database integrity error",
            extra={"path": request.url.path},
            exc_info=exc,
        )

        # Provide a user-friendly message
        error_msg = "Database constraint violation"
        if "unique" in str(exc).lower():
            error_msg = "Resource with this data already exists"
        elif "foreign key" in str(exc).lower():
            error_msg = "Referenced resource does not exist"

        response = _create_error_response(
            error_code=ErrorCode.CONFLICT,
            message=error_msg,
            status_code=status.HTTP_409_CONFLICT,
            request=request,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        """Handle general SQLAlchemy errors."""
        logger.error(
            "Database error",
            extra={"path": request.url.path},
            exc_info=exc,
        )

        response = _create_error_response(
            error_code=ErrorCode.DATABASE_ERROR,
            message="Database operation failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request=request,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            extra={"path": request.url.path},
            exc_info=exc,
        )

        response = _create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An internal error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request=request,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(exclude_none=True),
        )
