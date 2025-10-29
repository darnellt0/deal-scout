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
    platform: Mapped[str] = mapped_column(String(50))
    account_username: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
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
