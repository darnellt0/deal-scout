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
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.utils import utcnow


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


# Many-to-many association table for User and Role
user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    """Role model for many-to-many user roles."""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Many-to-many relationship with Role
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles_table,
        lazy="selectin",
    )

    @property
    def role_names(self) -> List[str]:
        """Return list of role names from the many-to-many relationship."""
        return [role.name for role in self.roles]


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    listing: Mapped[Listing] = relationship(back_populates="scores")


class Comp(Base):
    __tablename__ = "comps"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float)
    condition: Mapped[Optional[Condition]] = mapped_column(Enum(Condition))
    source: Mapped[str] = mapped_column(String(50))
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )


class MarketplaceAccount(Base):
    __tablename__ = "marketplace_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    platform: Mapped[str] = mapped_column(String(50), index=True)
    marketplace_account_id: Mapped[Optional[str]] = mapped_column(String(255))
    account_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    credentials: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Product(Base):
    """Single Source of Truth product record."""

    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("sku", name="uq_products_sku"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    original_cost: Mapped[Numeric] = mapped_column(Numeric(10, 2))
    base_price: Mapped[Numeric] = mapped_column(
        Numeric(10, 2),
        doc="Baseline price used before marketplace adjustments.",
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, default="")
    current_inventory: Mapped[int] = mapped_column(Integer, default=1)
    internal_location: Mapped[Optional[str]] = mapped_column(String(64))
    is_listed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    listings: Mapped[List["MarketplaceListing"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class MarketplaceListing(Base):
    """Marketplace-specific listing derived from the SSOT product."""

    __tablename__ = "marketplace_listings"
    __table_args__ = (
        UniqueConstraint("platform_listing_id", name="uq_marketplace_listing_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    platform_name: Mapped[str] = mapped_column(String(32), index=True)
    platform_listing_id: Mapped[str] = mapped_column(String(128), unique=True)
    platform_price: Mapped[Numeric] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    product: Mapped[Product] = relationship(back_populates="listings")
    orders: Mapped[List["SalesOrder"]] = relationship(
        back_populates="marketplace_listing", cascade="all, delete-orphan"
    )


class SalesOrder(Base):
    """Sales order created when a marketplace sale is confirmed."""

    __tablename__ = "sales_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_listing_id: Mapped[int] = mapped_column(
        ForeignKey("marketplace_listings.id"),
        index=True,
    )
    platform_name: Mapped[str] = mapped_column(String(32), index=True)
    sale_price: Mapped[Numeric] = mapped_column(Numeric(10, 2))
    platform_fee_rate: Mapped[Numeric] = mapped_column(Numeric(5, 4))
    shipping_cost: Mapped[Numeric] = mapped_column(Numeric(10, 2), default=0)
    net_profit: Mapped[Numeric] = mapped_column(Numeric(10, 2))
    sale_date: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    marketplace_listing: Mapped[MarketplaceListing] = relationship(
        back_populates="orders"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    cross_post_id: Mapped[int] = mapped_column(ForeignKey("cross_posts.id"))
    platform_order_id: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(50))
    total: Mapped[float] = mapped_column(Float)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
