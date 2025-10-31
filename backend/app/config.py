from __future__ import annotations

import logging
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Find the .env file - check parent directories
def _find_env_file():
    """Find .env file in project root or parent directories."""
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Search up to 5 levels up
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        current = current.parent
    # Return default if not found (will be created on first run)
    return Path.cwd() / ".env"


class Settings(BaseSettings):
    """Production-ready settings with validation and defaults."""

    # Application
    app_timezone: str = Field("America/Los_Angeles", json_schema_extra={"env": "APP_TIMEZONE"})
    default_city: str = Field("San Jose, CA", json_schema_extra={"env": "DEFAULT_CITY"})
    default_radius_mi: int = Field(50, json_schema_extra={"env": "DEFAULT_RADIUS_MI"})
    free_priority: bool = Field(True, json_schema_extra={"env": "FREE_PRIORITY"})
    demo_mode: bool = Field(False, json_schema_extra={"env": "DEMO_MODE"})
    log_level: str = Field("INFO", json_schema_extra={"env": "LOG_LEVEL"})

    # Database (Required)
    database_url: str = Field(..., json_schema_extra={"env": "DATABASE_URL"})
    database_pool_size: int = Field(10, json_schema_extra={"env": "DATABASE_POOL_SIZE"})
    database_max_overflow: int = Field(20, json_schema_extra={"env": "DATABASE_MAX_OVERFLOW"})

    # Redis (Required)
    redis_url: str = Field(..., json_schema_extra={"env": "REDIS_URL"})
    redis_socket_timeout: int = Field(5, json_schema_extra={"env": "REDIS_SOCKET_TIMEOUT"})

    # AI Services
    openai_api_key: str = Field("", json_schema_extra={"env": "OPENAI_API_KEY"})
    vision_enabled: bool = Field(True, json_schema_extra={"env": "VISION_ENABLED"})
    rembg_enabled: bool = Field(True, json_schema_extra={"env": "REMBG_ENABLED"})

    # eBay
    ebay_env: str = Field("sandbox", json_schema_extra={"env": "EBAY_ENV"})
    ebay_app_id: str = Field("", json_schema_extra={"env": "EBAY_APP_ID"})
    ebay_cert_id: str = Field("", json_schema_extra={"env": "EBAY_CERT_ID"})
    ebay_dev_id: str = Field("", json_schema_extra={"env": "EBAY_DEV_ID"})
    ebay_oauth_token: str = Field("", json_schema_extra={"env": "EBAY_OAUTH_TOKEN"})
    ebay_refresh_token: str = Field("", json_schema_extra={"env": "EBAY_REFRESH_TOKEN"})
    ebay_redirect_uri: str = Field("urn:ietf:wg:oauth:2.0:oob", json_schema_extra={"env": "EBAY_REDIRECT_URI"})
    ebay_scope: str = Field("", json_schema_extra={"env": "EBAY_SCOPE"})
    ebay_marketplace_id: str = Field("EBAY_US", json_schema_extra={"env": "EBAY_MARKETPLACE_ID"})

    # Craigslist
    cl_region: str = Field("sfbay", json_schema_extra={"env": "CL_REGION"})
    cl_search_furn: str = Field("sss", json_schema_extra={"env": "CL_SEARCH_FURN"})
    cl_enable_free: bool = Field(True, json_schema_extra={"env": "CL_ENABLE_FREE"})

    # Email
    email_from: str = Field("alerts@local.test", json_schema_extra={"env": "EMAIL_FROM"})
    smtp_host: str = Field("mailhog", json_schema_extra={"env": "SMTP_HOST"})
    smtp_port: int = Field(1025, json_schema_extra={"env": "SMTP_PORT"})
    smtp_user: Optional[str] = Field(None, json_schema_extra={"env": "SMTP_USER"})
    smtp_password: Optional[str] = Field(None, json_schema_extra={"env": "SMTP_PASSWORD"})
    smtp_use_tls: bool = Field(True, json_schema_extra={"env": "SMTP_USE_TLS"})

    # Discord
    discord_webhook_url: str = Field("", json_schema_extra={"env": "DISCORD_WEBHOOK_URL"})

    # Twilio SMS
    twilio_account_sid: str = Field("", json_schema_extra={"env": "TWILIO_ACCOUNT_SID"})
    twilio_auth_token: str = Field("", json_schema_extra={"env": "TWILIO_AUTH_TOKEN"})
    twilio_from: str = Field("", json_schema_extra={"env": "TWILIO_FROM"})
    alert_sms_to: str = Field("", json_schema_extra={"env": "ALERT_SMS_TO"})
# Facebook Marketplace    facebook_app_id: str = Field("", json_schema_extra={"env": "FACEBOOK_APP_ID"})    facebook_app_secret: str = Field("", json_schema_extra={"env": "FACEBOOK_APP_SECRET"})    # Offerup    offerup_client_id: str = Field("", json_schema_extra={"env": "OFFERUP_CLIENT_ID"})    offerup_client_secret: str = Field("", json_schema_extra={"env": "OFFERUP_CLIENT_SECRET"})    # Backend URL for OAuth callbacks    backend_url: str = Field("http://localhost:8000", json_schema_extra={"env": "BACKEND_URL"})

    # Seller/Snap Studio
    legal_mode: str = Field("api_only", json_schema_extra={"env": "LEGAL_MODE"})
    headless_enabled: bool = Field(False, json_schema_extra={"env": "HEADLESS_ENABLED"})
    price_suggestion_mode: str = Field("ebay_only", json_schema_extra={"env": "PRICE_SUGGESTION_MODE"})
    buyer_auto_message: bool = Field(True, json_schema_extra={"env": "BUYER_AUTO_MESSAGE"})

    # Storage
    template_dir: Path = Field(Path("/app/data/templates"), json_schema_extra={"env": "TEMPLATE_DIR"})
    static_data_dir: Path = Field(Path("/app/data"), json_schema_extra={"env": "STATIC_DATA_DIR"})

    # Cloud Storage (S3)
    aws_region: Optional[str] = Field(None, json_schema_extra={"env": "AWS_REGION"})
    aws_access_key_id: Optional[str] = Field(None, json_schema_extra={"env": "AWS_ACCESS_KEY_ID"})
    aws_secret_access_key: Optional[str] = Field(None, json_schema_extra={"env": "AWS_SECRET_ACCESS_KEY"})
    s3_bucket: Optional[str] = Field(None, json_schema_extra={"env": "S3_BUCKET"})
    s3_image_prefix: str = Field("images/", json_schema_extra={"env": "S3_IMAGE_PREFIX"})

    # Monitoring
    sentry_dsn: Optional[str] = Field(None, json_schema_extra={"env": "SENTRY_DSN"})

    # Search defaults
    default_keywords: List[str] = Field(
        default_factory=lambda: ["couch", "sofa", "sectional", "kitchen island"],
        json_schema_extra={"env": "KEYWORDS_INCLUDE"},
    )

    # CORS Configuration - stored as string, parsed in model_validator
    cors_origins_raw: Optional[str] = Field(
        None,
        json_schema_extra={"env": "CORS_ORIGINS"},
    )

    @field_validator("ebay_env")
    @classmethod
    def validate_ebay_env(cls, v):
        if v not in ("sandbox", "production"):
            raise ValueError("ebay_env must be 'sandbox' or 'production'")
        return v

    @field_validator("legal_mode")
    @classmethod
    def validate_legal_mode(cls, v):
        if v not in ("api_only", "guided", "off"):
            raise ValueError("legal_mode must be one of: api_only, guided, off")
        return v

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.demo_mode and self.ebay_env == "production"

    def has_s3_config(self) -> bool:
        """Check if S3 is properly configured."""
        return all(
            [
                self.aws_region,
                self.aws_access_key_id,
                self.aws_secret_access_key,
                self.s3_bucket,
            ]
        )

    @staticmethod
    def _parse_cors_origins(value: Optional[str]) -> List[str]:
        """Parse CORS origins from string."""
        if value is None or value == "":
            return ["http://localhost:3000"]
        value = value.strip()
        if not value:
            return ["http://localhost:3000"]
        if value.startswith("["):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        if "," in value:
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return [value]

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins from raw string."""
        return self._parse_cors_origins(self.cors_origins_raw)

    model_config = SettingsConfigDict(
        env_file=str(_find_env_file()),
        env_file_encoding="utf-8",
        case_sensitive=False,
        json_file=None,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Get CORS origins from environment variable if set
    cors_env = os.getenv("CORS_ORIGINS")
    if cors_env:
        # Will be processed by the validator
        pass
    settings = Settings()

    # Log warnings for production issues
    if settings.is_production():
        if not settings.openai_api_key:
            logger.warning("Production mode: OPENAI_API_KEY is not configured")
        if not settings.ebay_app_id:
            logger.warning("Production mode: eBay credentials are not configured")
        if settings.demo_mode:
            logger.warning("Production mode: DEMO_MODE is enabled (should be false)")

    return settings
