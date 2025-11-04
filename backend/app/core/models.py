from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Condition(enum.Enum):
    poor = "poor"
    fair = "fair"
    good = "good"
    great = "great"
    excellent = "excellent"


class UserRole(enum.Enum):
    """User roles for role-based access control."""
    admin = "admin"
    seller = "seller"
    buyer = "buyer"
    guest = "guest"


class User(Base):
    """User account model for authentication and authorization."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(128))
    last_name: Mapped[Optional[str]] = mapped_column(String(128))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.buyer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships could be added later for user_prefs, my_items, etc.


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    source_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, default=0)
    condition: Mapped[Optional[Condition]] = mapped_column(Enum(Condition))
    category: Mapped[Optional[str]] = mapped_column(String(120), index=True)
    url: Mapped[str] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    location: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    available: Mapped[bool] = mapped_column(Boolean, default=True)

    scores: Mapped[List["ListingScore"]] = relationship(back_populates="listing")


class ListingScore(Base):
    __tablename__ = "listing_scores"
    __table_args__ = (
        UniqueConstraint("listing_id", "metric", name="uq_listing_metric"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    metric: Mapped[str] = mapped_column(String(50))
    value: Mapped[float] = mapped_column(Float)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    listing: Mapped[Listing] = relationship(back_populates="scores")


class Comp(Base):
    __tablename__ = "comps"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float)
    condition: Mapped[Optional[Condition]] = mapped_column(Enum(Condition))
    source: Mapped[str] = mapped_column(String(50))
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class UserPref(Base):
    __tablename__ = "user_prefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    radius_mi: Mapped[int] = mapped_column(Integer, default=50)
    city: Mapped[str] = mapped_column(String(255), default="San Jose, CA")
    min_condition: Mapped[Condition] = mapped_column(
        Enum(Condition), default=Condition.good
    )
    max_price_couch: Mapped[float] = mapped_column(Float, default=150)
    max_price_kitchen_island: Mapped[float] = mapped_column(Float, default=300)
    keywords_include: Mapped[List[str]] = mapped_column(JSON, default=list)
    notify_channels: Mapped[List[str]] = mapped_column(JSON, default=lambda: ["email"])
    saved_deals: Mapped[List[int]] = mapped_column(JSON, default=list)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    search_radius_mi: Mapped[int] = mapped_column(Integer, default=50)
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MyItem(Base):
    __tablename__ = "my_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    condition: Mapped[Optional[Condition]] = mapped_column(Enum(Condition))
    price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MarketplaceAccount(Base):
    __tablename__ = "marketplace_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    marketplace: Mapped[str] = mapped_column(String(50), index=True)
    marketplace_account_id: Mapped[Optional[str]] = mapped_column(String(255))
    account_username: Mapped[str] = mapped_column(String(255))
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CrossPost(Base):
    __tablename__ = "cross_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    my_item_id: Mapped[int] = mapped_column(ForeignKey("my_items.id"), index=True)
    platform: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[Optional[str]] = mapped_column(String(120))
    listing_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    cross_post_id: Mapped[int] = mapped_column(ForeignKey("cross_posts.id"))
    platform_order_id: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(50))
    total: Mapped[float] = mapped_column(Float)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SnapJob(Base):
    __tablename__ = "snap_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    source: Mapped[str] = mapped_column(String(50), default="upload")
    input_photos: Mapped[List[str]] = mapped_column(JSON, default=list)
    processed_images: Mapped[List[str]] = mapped_column(JSON, default=list)
    detected_category: Mapped[Optional[str]] = mapped_column(String(120))
    detected_attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    condition_guess: Mapped[Optional[str]] = mapped_column(String(50))
    price_suggestion_cents: Mapped[Optional[int]] = mapped_column(Integer)
    suggested_price: Mapped[Optional[float]] = mapped_column(Float)
    suggested_title: Mapped[Optional[str]] = mapped_column(String(255))
    suggested_description: Mapped[Optional[str]] = mapped_column(Text)
    title_suggestion: Mapped[Optional[str]] = mapped_column(String(255))
    description_suggestion: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ============================================================================
# PHASE 7: INTELLIGENT NOTIFICATIONS & DEAL DISCOVERY
# ============================================================================


class DealAlertRule(Base):
    """User-created rules for custom deal alerts and notifications."""
    __tablename__ = "deal_alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))  # e.g., "Budget Gaming PC"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Matching Criteria
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list)  # OR logic
    exclude_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)  # NOT logic
    categories: Mapped[List[str]] = mapped_column(JSON, default=list)  # OR logic
    condition: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "good"

    # Price Criteria
    min_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Location Criteria
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    radius_mi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Deal Score Criteria (0.0 to 1.0)
    min_deal_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Notification Settings
    notification_channels: Mapped[List[str]] = mapped_column(JSON, default=lambda: ["email"])

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class NotificationPreferences(Base):
    """User notification preferences and settings."""
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    # Notification Channels
    channels: Mapped[List[str]] = mapped_column(JSON, default=lambda: ["email"])

    # Frequency Settings
    frequency: Mapped[str] = mapped_column(String(50), default="immediate")  # immediate, daily, weekly
    digest_time: Mapped[str] = mapped_column(String(5), default="09:00")  # HH:MM format

    # Quiet Hours (no notifications)
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # HH:MM

    # Category Filters
    category_filters: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Rate Limiting
    max_per_day: Mapped[int] = mapped_column(Integer, default=10)

    # Phone Number for SMS
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Discord Webhook
    discord_webhook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WatchlistItem(Base):
    """User's watchlist items for price tracking."""
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)

    # Price tracking
    price_alert_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    last_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ============================================================================
# SNAP-TO-SELL PIPELINE: COMPOSE DRAFT MODELS
# ============================================================================


class MediaAsset(Base):
    """Media assets (images/videos) with processing metadata."""
    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    snap_job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("snap_jobs.id"), nullable=True, index=True
    )
    listing_draft_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("listing_drafts.id"), nullable=True, index=True
    )

    # URLs
    original_url: Mapped[str] = mapped_column(String(500))
    processed_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Media metadata
    media_type: Mapped[str] = mapped_column(String(50), default="image")  # image, video
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Processing metadata
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, completed, failed
    processing_steps: Mapped[dict] = mapped_column(JSON, default=dict)  # {brightness: true, bg_removal: true, etc.}
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Extracted text from image

    # Vision metadata
    vision_labels: Mapped[List[str]] = mapped_column(JSON, default=list)
    vision_captions: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Display order (for listing galleries)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ListingDraft(Base):
    """Draft listings created by the compose draft pipeline."""
    __tablename__ = "listing_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    snap_job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("snap_jobs.id"), nullable=True, index=True
    )

    # Status
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, published, archived

    # Listing details
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(120))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)  # brand, model, color, size, etc.
    condition: Mapped[Optional[Condition]] = mapped_column(Enum(Condition))

    # Pricing
    price_suggested: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Copywriting metadata
    bullet_highlights: Mapped[List[str]] = mapped_column(JSON, default=list)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    seo_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Vision metadata (from pipeline)
    vision_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 to 1.0

    # Pipeline metadata
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # vision, pricing, copy metadata

    # Versioning (for edit history)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_draft_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("listing_drafts.id"), nullable=True
    )

    # Publication tracking
    published_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("my_items.id"), nullable=True
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class CrossPostJob(Base):
    """Background job tracking for cross-posting to marketplaces."""
    __tablename__ = "cross_post_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    snap_job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("snap_jobs.id"), nullable=True, index=True
    )
    listing_draft_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("listing_drafts.id"), nullable=True, index=True
    )
    my_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("my_items.id"), nullable=True, index=True
    )

    # Target platforms
    platforms: Mapped[List[str]] = mapped_column(JSON, default=list)  # ["ebay", "facebook", "offerup"]

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0 to 100
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Platform-specific metadata
    platform_metadata: Mapped[dict] = mapped_column(JSON, default=dict)  # {ebay: {...}, facebook: {...}}

    # Results (created CrossPost IDs)
    cross_post_ids: Mapped[List[int]] = mapped_column(JSON, default=list)

    # Logs
    logs: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
