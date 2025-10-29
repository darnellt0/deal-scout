"""Logging configuration for production and development."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from app.config import get_settings

settings = get_settings()


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> None:
    """Configure application-wide logging with rotation and formatting."""
    level = getattr(logging, log_level or settings.log_level, logging.INFO)

    # Create logs directory if it doesn't exist
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Format for logs
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        if log_level != "DEBUG"
        else "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (if log file specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # SQLAlchemy debug logging (only in DEBUG mode)
    if log_level == "DEBUG":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    # Celery logging
    logging.getLogger("celery").setLevel(level)

    # Third-party library logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("twilio").setLevel(logging.WARNING)


# Configure on import
if settings.log_level:
    log_file = Path("/var/log/deal-scout/app.log") if not settings.demo_mode else None
    setup_logging(log_level=settings.log_level, log_file=log_file)
