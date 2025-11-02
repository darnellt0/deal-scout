#!/usr/bin/env python3
"""
Database seeding script for development.

This script populates the database with sample data for testing and development.
Run this script from the project root: python backend/scripts/seed_database.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.models import (
    Base,
    Listing,
    ListingScore,
    Comp,
    UserPref,
    Notification,
    MyItem,
    MarketplaceAccount,
    CrossPost,
    Order,
    SnapJob,
    Condition,
)


def get_engine():
    """Get database engine from settings."""
    settings = get_settings()
    return create_engine(settings.database_url, echo=False)


def seed_marketplace_accounts(session):
    """Seed marketplace account data."""
    print("Seeding marketplace accounts...")

    accounts = [
        MarketplaceAccount(
            platform="ebay",
            connected=True,
            credentials={"api_key": "test_ebay_key", "seller_id": "test_seller"},
        ),
        MarketplaceAccount(
            platform="facebook",
            connected=False,
            credentials={"access_token": "test_token"},
        ),
        MarketplaceAccount(
            platform="offerup",
            connected=False,
            credentials={},
        ),
    ]

    for account in accounts:
        existing = session.query(MarketplaceAccount).filter_by(platform=account.platform).first()
        if not existing:
            session.add(account)
    session.commit()
    print(f"✓ Created {len(accounts)} marketplace accounts")


def seed_listings(session):
    """Seed marketplace listing data."""
    print("Seeding listings...")

    now = datetime.now(timezone.utc)
    listings = [
        Listing(
            source="ebay",
            source_id="ebay-001",
            title="Vintage MacBook Pro 15 inch 2015",
            description="Great condition, fully functional, includes charger",
            price=599.99,
            condition=Condition.good,
            category="Electronics - Computers",
            url="https://ebay.com/itm/123456789",
            thumbnail_url="https://example.com/thumb1.jpg",
            location={"city": "San Jose", "state": "CA", "coords": [37.3382, -121.8863]},
            available=True,
            last_seen_at=now,
        ),
        Listing(
            source="facebook",
            source_id="fb-marketplace-001",
            title="Mountain Bike Trek X-Caliber",
            description="2021 Trek X-Caliber, 29er wheels, excellent condition",
            price=1200.00,
            condition=Condition.excellent,
            category="Sports & Outdoors - Bikes",
            url="https://facebook.com/marketplace/123",
            location={"city": "San Francisco", "state": "CA", "coords": [37.7749, -122.4194]},
            available=True,
            last_seen_at=now,
        ),
        Listing(
            source="offerup",
            source_id="offerup-001",
            title="Nintendo Switch OLED",
            description="Brand new sealed in box",
            price=349.99,
            condition=None,
            category="Electronics - Gaming",
            url="https://offerup.com/item/123",
            available=True,
            last_seen_at=now,
        ),
        Listing(
            source="ebay",
            source_id="ebay-002",
            title="Vintage Leather Jacket",
            description="Classic black leather bomber jacket, size M",
            price=89.99,
            condition=Condition.fair,
            category="Clothing & Accessories - Jackets",
            url="https://ebay.com/itm/987654321",
            available=True,
            last_seen_at=now,
        ),
    ]

    for listing in listings:
        existing = session.query(Listing).filter_by(source_id=listing.source_id).first()
        if not existing:
            session.add(listing)
    session.commit()

    # Add listing scores
    listings_in_db = session.query(Listing).all()
    for listing in listings_in_db:
        if session.query(ListingScore).filter_by(listing_id=listing.id).first() is None:
            score = ListingScore(
                listing_id=listing.id,
                metric="deal_score",
                value=Decimal(str(max(1, min(100, 100 - (listing.price / 10))))),
            )
            session.add(score)
    session.commit()
    print(f"✓ Created {len(listings)} listings with scores")


def seed_comps(session):
    """Seed comparable pricing data."""
    print("Seeding comps...")

    comps = [
        Comp(
            source="ebay",
            category="Electronics - Computers",
            title="MacBook Pro 15 2015",
            price=549.99,
            condition=Condition.good,
            meta={"memory": "8GB", "storage": "256GB"},
        ),
        Comp(
            source="ebay",
            category="Electronics - Computers",
            title="MacBook Pro 15 2015 16GB",
            price=649.99,
            condition=Condition.good,
            meta={"memory": "16GB", "storage": "512GB"},
        ),
        Comp(
            source="offerup",
            category="Sports & Outdoors - Bikes",
            title="Trek X-Caliber 29",
            price=1150.00,
            condition=Condition.excellent,
            meta={"year": "2021"},
        ),
    ]

    for comp in comps:
        session.add(comp)
    session.commit()
    print(f"✓ Created {len(comps)} comparables")


def seed_my_items(session):
    """Seed user's items data."""
    print("Seeding my items...")

    items = [
        MyItem(
            title="iPhone 12 Pro",
            category="Electronics - Phones",
            attributes={"color": "Space Black", "storage": "128GB"},
            condition=Condition.excellent,
            price=750.00,
            status="available",
        ),
        MyItem(
            title="AirPods Pro",
            category="Electronics - Audio",
            attributes={"color": "White"},
            condition=Condition.excellent,
            price=200.00,
            status="available",
        ),
        MyItem(
            title="Used Textbooks Bundle",
            category="Books & Media",
            attributes={"count": 5, "subjects": ["Python", "Data Science", "Web Dev"]},
            condition=Condition.good,
            price=75.00,
            status="draft",
        ),
    ]

    for item in items:
        session.add(item)
    session.commit()
    print(f"✓ Created {len(items)} my items")


def seed_user_preferences(session):
    """Seed user preference data."""
    print("Seeding user preferences...")

    prefs = [
        UserPref(
            user_id="user_001",
            radius_mi=50,
            city="San Jose, CA",
            min_condition=Condition.good,
            max_price_couch=200.00,
            max_price_kitchen_island=500.00,
            keywords_include=["macbook", "laptop"],
            notify_channels=["email", "sms"],
        ),
        UserPref(
            user_id="user_002",
            radius_mi=100,
            city="San Francisco, CA",
            min_condition=Condition.fair,
            max_price_couch=150.00,
            max_price_kitchen_island=400.00,
            keywords_include=["bike", "bicycle"],
            notify_channels=["email"],
        ),
    ]

    for pref in prefs:
        session.add(pref)
    session.commit()
    print(f"✓ Created {len(prefs)} user preferences")


def seed_cross_posts(session):
    """Seed cross post data."""
    print("Seeding cross posts...")

    my_items = session.query(MyItem).all()
    if not my_items:
        print("  ⚠ No my items found, skipping cross posts")
        return

    cross_posts = []
    for item in my_items[:2]:  # Only use first 2 items
        for platform in ["ebay", "facebook"]:
            post = CrossPost(
                my_item_id=item.id,
                platform=platform,
                external_id=f"{platform}-{item.id}",
                listing_url=f"https://{platform}.com/item/{item.id}",
                status="active",
                meta={"posted_at": datetime.now(timezone.utc).isoformat()},
            )
            cross_posts.append(post)
            session.add(post)

    session.commit()
    print(f"✓ Created {len(cross_posts)} cross posts")


def seed_orders(session):
    """Seed order data."""
    print("Seeding orders...")

    cross_posts = session.query(CrossPost).all()
    if not cross_posts:
        print("  ⚠ No cross posts found, skipping orders")
        return

    orders = []
    for cp in cross_posts[:2]:  # Only use first 2 cross posts
        order = Order(
            cross_post_id=cp.id,
            platform_order_id=f"order-{cp.id}-001",
            status="completed",
            total=250.00,
            meta={"buyer": "test_buyer", "shipped": True},
        )
        orders.append(order)
        session.add(order)

    session.commit()
    print(f"✓ Created {len(orders)} orders")


def seed_snap_jobs(session):
    """Seed snap job data."""
    print("Seeding snap jobs...")

    snap_jobs = [
        SnapJob(
            status="completed",
            source="upload",
            input_photos=["photo1.jpg", "photo2.jpg"],
            processed_images=["processed1.jpg", "processed2.jpg"],
            detected_category="Electronics - Phones",
            detected_attributes={"color": "black", "brand": "Apple"},
            condition_guess="excellent",
            price_suggestion_cents=75000,
            suggested_title="iPhone 12 Pro Space Black",
            suggested_description="Used iPhone in excellent condition with all accessories",
        ),
        SnapJob(
            status="pending",
            source="upload",
            input_photos=["photo3.jpg"],
            processed_images=[],
            detected_category=None,
            detected_attributes={},
            condition_guess=None,
            price_suggestion_cents=None,
        ),
    ]

    for job in snap_jobs:
        session.add(job)
    session.commit()
    print(f"✓ Created {len(snap_jobs)} snap jobs")


def seed_notifications(session):
    """Seed notification data."""
    print("Seeding notifications...")

    notifications = [
        Notification(
            listing_id=1,
            channel="email",
            payload={"title": "New listing matches", "message": "Found a MacBook Pro for $599.99"},
            status="sent",
        ),
        Notification(
            channel="sms",
            payload={"title": "Order update", "message": "Your order has been shipped"},
            status="pending",
        ),
    ]

    for notif in notifications:
        session.add(notif)
    session.commit()
    print(f"✓ Created {len(notifications)} notifications")


def main():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("Database Seeding Script")
    print("=" * 60 + "\n")

    # Create engine and session
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created/verified\n")

        # Run seeders
        seed_marketplace_accounts(session)
        seed_listings(session)
        seed_comps(session)
        seed_my_items(session)
        seed_user_preferences(session)
        seed_cross_posts(session)
        seed_orders(session)
        seed_snap_jobs(session)
        seed_notifications(session)

        print("\n" + "=" * 60)
        print("Seeding completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
