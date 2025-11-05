"""Celery tasks for sending digest emails (daily and weekly)."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.models import (
    DealAlertRule,
    Listing,
    NotificationPreferences,
    User,
)
from app.worker import celery_app

logger = logging.getLogger("deal_scout.tasks.send_digest_emails")

settings = get_settings()

# Async database setup
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)

# Jinja2 template environment
templates_path = Path(__file__).parent.parent / "core" / "email_templates"
jinja_env = Environment(loader=FileSystemLoader(str(templates_path)))


async def _find_matching_listings_for_user(
    db: AsyncSession, user: User, hours: int = 24
) -> List[Listing]:
    """Find listings matching user's alert rules from the past N hours."""

    # Get user's active alert rules
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.user_id == user.id,
                DealAlertRule.enabled == True,
            )
        )
    )
    rules = result.scalars().all()

    if not rules:
        return []

    # Get listings from the past N hours
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    all_matching_listings = []
    seen_listing_ids = set()

    for rule in rules:
        # Build base query
        query = select(Listing).where(
            and_(
                Listing.available == True,
                Listing.created_at >= cutoff,
            )
        )

        # Apply filters
        if rule.min_price is not None:
            query = query.where(Listing.price >= rule.min_price)
        if rule.max_price is not None:
            query = query.where(Listing.price <= rule.max_price)
        if rule.categories:
            query = query.where(Listing.category.in_(rule.categories))
        if rule.condition:
            query = query.where(Listing.condition == rule.condition)

        # Order by score and created date
        query = query.order_by(Listing.created_at.desc()).limit(100)

        # Execute query
        listings_result = await db.execute(query)
        listings = listings_result.scalars().all()

        # Filter by keywords in-memory
        for listing in listings:
            # Skip duplicates
            if listing.id in seen_listing_ids:
                continue

            # Check keywords (OR logic)
            if rule.keywords:
                title_lower = listing.title.lower()
                desc_lower = (listing.description or "").lower()
                keyword_match = any(
                    keyword.lower() in title_lower or keyword.lower() in desc_lower
                    for keyword in rule.keywords
                )
                if not keyword_match:
                    continue

            # Check exclude keywords (NOT logic)
            if rule.exclude_keywords:
                title_lower = listing.title.lower()
                desc_lower = (listing.description or "").lower()
                exclude_match = any(
                    keyword.lower() in title_lower or keyword.lower() in desc_lower
                    for keyword in rule.exclude_keywords
                )
                if exclude_match:
                    continue

            all_matching_listings.append(listing)
            seen_listing_ids.add(listing.id)

    # Sort by deal score (if available) and created date
    all_matching_listings.sort(
        key=lambda x: (
            -(x.deal_score.value if hasattr(x, "deal_score") and x.deal_score else 0),
            -x.created_at.timestamp(),
        )
    )

    return all_matching_listings[:20]  # Limit to top 20 deals


def _calculate_stats(listings: List[Listing]) -> dict:
    """Calculate statistics for digest email."""
    if not listings:
        return {"total_deals": 0, "avg_savings": 0}

    total_deals = len(listings)

    # Calculate average deal score as proxy for savings
    deal_scores = [
        listing.deal_score.value
        for listing in listings
        if hasattr(listing, "deal_score") and listing.deal_score
    ]
    avg_deal_score = sum(deal_scores) / len(deal_scores) if deal_scores else 0

    # Estimate savings based on deal score (rough approximation)
    avg_price = sum(listing.price for listing in listings) / len(listings)
    avg_savings = avg_price * avg_deal_score * 0.3  # Rough estimate

    return {
        "total_deals": total_deals,
        "avg_savings": round(avg_savings, 2),
    }


def _render_digest_email(
    user: User,
    listings: List[Listing],
    digest_type: str = "daily",
) -> tuple[str, str]:
    """Render digest email HTML and text versions."""

    # Prepare template context
    context = {
        "user_name": user.username or user.email.split("@")[0],
        "digest_date": datetime.utcnow().strftime("%B %d, %Y"),
        "digest_type": digest_type,
        "deal_count": len(listings),
        "stats": _calculate_stats(listings),
        "deals": [
            {
                "title": listing.title,
                "price": float(listing.price),
                "image_url": listing.thumbnail_url or listing.image_url,
                "category": listing.category,
                "condition": (
                    listing.condition.value
                    if hasattr(listing, "condition") and listing.condition
                    else None
                ),
                "marketplace": getattr(listing, "marketplace", None),
                "deal_score": (
                    listing.deal_score.value
                    if hasattr(listing, "deal_score") and listing.deal_score
                    else None
                ),
                "description": listing.description,
                "url": listing.url,
            }
            for listing in listings
        ],
        "app_url": settings.frontend_url or "http://localhost:3000",
        "unsubscribe_url": f"{settings.frontend_url or 'http://localhost:3000'}/unsubscribe?user_id={user.id}",
    }

    # Render templates
    html_template = jinja_env.get_template("digest.html")
    text_template = jinja_env.get_template("digest.txt")

    html_content = html_template.render(**context)
    text_content = text_template.render(**context)

    return html_content, text_content


async def _send_digest_to_user(
    db: AsyncSession,
    user: User,
    digest_type: str,
    hours: int,
):
    """Send digest email to a single user."""
    try:
        # Get matching listings
        listings = await _find_matching_listings_for_user(db, user, hours=hours)

        # Render email
        html_content, text_content = _render_digest_email(user, listings, digest_type)

        # Send email
        from app.notify.email import send_email_async

        subject = (
            f"Your Daily Deal Digest - {len(listings)} Deals"
            if digest_type == "daily"
            else f"Your Weekly Deal Digest - {len(listings)} Deals"
        )

        await send_email_async(
            to=user.email,
            subject=subject,
            body=html_content,
            text_body=text_content,
        )

        logger.info(
            f"Sent {digest_type} digest to {user.email} with {len(listings)} deals"
        )

    except Exception as e:
        logger.error(f"Failed to send digest to {user.email}: {e}", exc_info=True)


@celery_app.task(name="send_daily_digests")
def send_daily_digests():
    """Send daily digest emails to all users who opted in."""
    import asyncio

    asyncio.run(_send_daily_digests_async())


async def _send_daily_digests_async():
    """Async function to send daily digest emails."""
    async with AsyncSessionLocal() as db:
        try:
            # Get users with daily digest enabled
            result = await db.execute(
                select(User, NotificationPreferences)
                .join(
                    NotificationPreferences,
                    User.id == NotificationPreferences.user_id,
                )
                .where(
                    and_(
                        User.is_active == True,
                        NotificationPreferences.enabled == True,
                        NotificationPreferences.frequency == "daily",
                        NotificationPreferences.channels.contains(["email"]),
                    )
                )
            )
            users_prefs = result.all()

            logger.info(f"Sending daily digests to {len(users_prefs)} users")

            for user, prefs in users_prefs:
                # Check quiet hours
                if prefs.quiet_hours_enabled:
                    now = datetime.utcnow().strftime("%H:%M")
                    if (
                        prefs.quiet_hours_start
                        and prefs.quiet_hours_end
                        and prefs.quiet_hours_start <= now < prefs.quiet_hours_end
                    ):
                        logger.info(
                            f"Skipping {user.email} due to quiet hours"
                        )
                        continue

                await _send_digest_to_user(db, user, "daily", hours=24)

            logger.info("Daily digest emails sent successfully")

        except Exception as e:
            logger.error(f"Error sending daily digests: {e}", exc_info=True)


@celery_app.task(name="send_weekly_digests")
def send_weekly_digests():
    """Send weekly digest emails to all users who opted in."""
    import asyncio

    asyncio.run(_send_weekly_digests_async())


async def _send_weekly_digests_async():
    """Async function to send weekly digest emails."""
    async with AsyncSessionLocal() as db:
        try:
            # Get users with weekly digest enabled
            result = await db.execute(
                select(User, NotificationPreferences)
                .join(
                    NotificationPreferences,
                    User.id == NotificationPreferences.user_id,
                )
                .where(
                    and_(
                        User.is_active == True,
                        NotificationPreferences.enabled == True,
                        NotificationPreferences.frequency == "weekly",
                        NotificationPreferences.channels.contains(["email"]),
                    )
                )
            )
            users_prefs = result.all()

            logger.info(f"Sending weekly digests to {len(users_prefs)} users")

            for user, prefs in users_prefs:
                # Check quiet hours
                if prefs.quiet_hours_enabled:
                    now = datetime.utcnow().strftime("%H:%M")
                    if (
                        prefs.quiet_hours_start
                        and prefs.quiet_hours_end
                        and prefs.quiet_hours_start <= now < prefs.quiet_hours_end
                    ):
                        logger.info(
                            f"Skipping {user.email} due to quiet hours"
                        )
                        continue

                await _send_digest_to_user(db, user, "weekly", hours=168)  # 7 days

            logger.info("Weekly digest emails sent successfully")

        except Exception as e:
            logger.error(f"Error sending weekly digests: {e}", exc_info=True)


@celery_app.task(name="cleanup_old_notifications")
def cleanup_old_notifications():
    """Clean up old notification records (runs weekly)."""
    import asyncio

    asyncio.run(_cleanup_old_notifications_async())


async def _cleanup_old_notifications_async():
    """Async function to clean up old notification records."""
    from app.core.models import Notification

    async with AsyncSessionLocal() as db:
        try:
            # Delete notifications older than 90 days
            cutoff = datetime.utcnow() - timedelta(days=90)

            result = await db.execute(
                select(Notification).where(Notification.created_at < cutoff)
            )
            old_notifications = result.scalars().all()

            count = len(old_notifications)
            if count > 0:
                for notification in old_notifications:
                    await db.delete(notification)

                await db.commit()
                logger.info(f"Cleaned up {count} old notifications")
            else:
                logger.info("No old notifications to clean up")

        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}", exc_info=True)
