"""Pydantic v2 schemas for API serialization and validation."""

from app.schemas.user import UserOut, UserCreate, UserLogin, TokenResponse
from app.schemas.listing import ListingOut, ListingCreate, ListingUpdate, ListingScoreOut
from app.schemas.comp import CompOut
from app.schemas.pref import UserPrefOut, UserPrefUpdate
from app.schemas.notification import NotificationOut
from app.schemas.marketplace import MarketplaceAccountOut, MarketplaceAccountCreate
from app.schemas.my_item import MyItemOut, MyItemCreate, MyItemUpdate
from app.schemas.cross_post import CrossPostOut, CrossPostCreate
from app.schemas.order import OrderOut
from app.schemas.inventory import (
    PublishListingRequest,
    SaleWebhookPayload,
    MarketplaceListingResponse,
    SalesOrderResponse,
)
from app.schemas.snap_job import SnapJobOut, SnapJobUpdate
from app.schemas.common import Page, PageMeta, PageResponse

__all__ = [
    # User & Authentication
    "UserOut",
    "UserCreate",
    "UserLogin",
    "TokenResponse",
    # Listings
    "ListingOut",
    "ListingCreate",
    "ListingUpdate",
    "ListingScoreOut",
    # Comps
    "CompOut",
    # User Preferences
    "UserPrefOut",
    "UserPrefUpdate",
    # Notifications
    "NotificationOut",
    # Marketplace
    "MarketplaceAccountOut",
    "MarketplaceAccountCreate",
    # My Items
    "MyItemOut",
    "MyItemCreate",
    "MyItemUpdate",
    # Cross Posts
    "CrossPostOut",
    "CrossPostCreate",
    # Orders
    "OrderOut",
    # Inventory
    "PublishListingRequest",
    "SaleWebhookPayload",
    "MarketplaceListingResponse",
    "SalesOrderResponse",
    # Snap Jobs
    "SnapJobOut",
    "SnapJobUpdate",
    # Common
    "Page",
    "PageMeta",
    "PageResponse",
]
