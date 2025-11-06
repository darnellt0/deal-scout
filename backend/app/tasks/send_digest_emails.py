"""Celery tasks for sending daily and weekly digest emails (Phase 7)."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.models import (
    DealAlertRule,
    Listing,
    ListingScore,
    NotificationPreferences,
    User,
    WatchlistItem,
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

# Jinja2 environment for email templates
jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)


async def _get_user_deals(
    db: AsyncSession,
    user: User,
    since: datetime,
) -> List[Dict]:
    """Get deals that match user's alert rules since a given time."""
    # Get user's active rules
    result = await db.execute(
        select(DealAlertRule).where(
            and_(
                DealAlertRule.user_id == user.id,
                DealAlertRule.enabled == True,
            )
        )
    )
    rules = result.scalars().all()

    all_deals = []

    for rule in rules:
        # Query listings matching the rule
        query = select(Listing).where(
            and_(
                Listing.available == True,
                Listing.created_at >= since,
            )
        )

        # Apply rule filters
        if rule.min_price is not None:
            query = query.where(Listing.price >= rule.min_price)
        if rule.max_price is not None:
            query = query.where(Listing.price <= rule.max_price)
        if rule.categories:
            query = query.where(Listing.category.in_(rule.categories))
        if rule.condition:
            query = query.where(Listing.condition == rule.condition)

        query = query.order_by(desc(Listing.created_at)).limit(50)

        result = await db.execute(query)
        listings = result.scalars().all()

        # Filter by keywords in memory
        for listing in listings:
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

            # Get deal score if available
            score_result = await db.execute(
                select(ListingScore).where(
                    and_(
                        ListingScore.listing_id == listing.id,
                        ListingScore.metric == "deal_score",
                    )
                )
            )
            score = score_result.scalar_one_or_none()

            all_deals.append({
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "price": listing.price,
                "category": listing.category,
                "condition": listing.condition.value if listing.condition else None,
                "url": listing.url,
                "thumbnail_url": listing.thumbnail_url,
                "source": listing.source,
                "deal_score": score.value if score else None,
                "matched_rule": rule.name,
            })

    # Remove duplicates and sort by deal score
    unique_deals = {d["id"]: d for d in all_deals}.values()
    sorted_deals = sorted(
        unique_deals,
        key=lambda x: x["deal_score"] or 0,
        reverse=True
    )

    return list(sorted_deals)[:10]  # Return top 10


async def _get_price_drops(db: AsyncSession, user: User) -> List[Dict]:
    """Get price drops on user's watchlist."""
    result = await db.execute(
        select(WatchlistItem).where(
            and_(
                WatchlistItem.user_id == user.id,
                WatchlistItem.alert_sent == True,
            )
        )
    )
    watchlist_items = result.scalars().all()

    price_drops = []
    for item in watchlist_items:
        # Get current listing
        listing_result = await db.execute(
            select(Listing).where(Listing.id == item.listing_id)
        )
        listing = listing_result.scalar_one_or_none()

        if listing and item.last_price and listing.price < item.last_price:
            price_drops.append({
                "title": listing.title,
                "current_price": listing.price,
                "was_price": item.last_price,
                "savings": item.last_price - listing.price,
                "url": listing.url,
            })

    return price_drops


async def _send_daily_digest_to_user(db: AsyncSession, user: User):
    """Send daily digest email to a single user."""
    from app.notify.email import send_email_async

    # Get deals from the last 24 hours
    since = datetime.utcnow() - timedelta(days=1)
    deals = await _get_user_deals(db, user, since)

    # Calculate stats
    total_deals = len(deals)
    avg_price = sum(d["price"] for d in deals) / total_deals if total_deals > 0 else 0
    free_deals = sum(1 for d in deals if d["price"] == 0)

    # Get matching rules count
    matching_rules = len(set(d["matched_rule"] for d in deals))

    # Render email template
    template = jinja_env.get_template("emails/daily_digest.html")
    html_content = template.render(
        title="Daily Deal Digest",
        header_title="Your Daily Deals",
        header_subtitle=f"{datetime.utcnow().strftime('%A, %B %d, %Y')}",
        deals=deals,
        total_deals=total_deals,
        avg_price=round(avg_price, 2),
        free_deals=free_deals,
        matching_rules=matching_rules,
        preferences_url=f"{settings.frontend_url}/settings/notifications",
        unsubscribe_url=f"{settings.frontend_url}/settings/notifications/unsubscribe",
        year=datetime.utcnow().year,
        recommendations=[],  # TODO: Implement recommendations
    )

    try:
        await send_email_async(
            to=user.email,
            subject=f"Your Daily Deal Digest - {total_deals} New Deals",
            body=html_content,
        )
        logger.info(f"Daily digest sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send daily digest to {user.email}: {e}")


async def _send_weekly_digest_to_user(db: AsyncSession, user: User):
    """Send weekly digest email to a single user."""
    from app.notify.email import send_email_async

    # Get deals from the last 7 days
    since = datetime.utcnow() - timedelta(days=7)
    deals = await _get_user_deals(db, user, since)

    # Calculate stats
    total_deals = len(deals)
    free_deals = sum(1 for d in deals if d["price"] == 0)
    matching_rules = len(set(d["matched_rule"] for d in deals))

    # Calculate estimated savings (rough estimate)
    total_saved = sum(d["price"] * 0.3 for d in deals if d["deal_score"] and d["deal_score"] > 0.7)

    # Get price drops
    price_drops = await _get_price_drops(db, user)

    # Render email template
    template = jinja_env.get_template("emails/weekly_digest.html")
    html_content = template.render(
        title="Weekly Deal Digest",
        header_title="Your Weekly Deals",
        header_subtitle=f"Week of {(datetime.utcnow() - timedelta(days=7)).strftime('%B %d')} - {datetime.utcnow().strftime('%B %d, %Y')}",
        deals=deals,
        total_deals=total_deals,
        free_deals=free_deals,
        matching_rules=matching_rules,
        total_saved=round(total_saved, 2),
        price_drops=price_drops,
        preferences_url=f"{settings.frontend_url}/settings/notifications",
        unsubscribe_url=f"{settings.frontend_url}/settings/notifications/unsubscribe",
        year=datetime.utcnow().year,
        recommendations=[],  # TODO: Implement recommendations
    )

    try:
        await send_email_async(
            to=user.email,
            subject=f"Your Weekly Deal Digest - {total_deals} New Deals",
            body=html_content,
        )
        logger.info(f"Weekly digest sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send weekly digest to {user.email}: {e}")


@celery_app.task(name="send_daily_digests")
def send_daily_digests():
    """Celery task to send daily digest emails to all users with daily frequency."""
    import asyncio

    asyncio.run(_send_daily_digests_async())


async def _send_daily_digests_async():
    """Async function to send daily digests."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all users with daily digest preference
            result = await db.execute(
                select(User)
                .join(NotificationPreferences, NotificationPreferences.user_id == User.id)
                .where(
                    and_(
                        NotificationPreferences.enabled == True,
                        NotificationPreferences.frequency == "daily",
                        User.is_active == True,
                    )
                )
            )
            users = result.scalars().all()

            logger.info(f"Sending daily digests to {len(users)} users")

            for user in users:
                try:
                    await _send_daily_digest_to_user(db, user)
                except Exception as e:
                    logger.error(f"Error sending daily digest to user {user.id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in send_daily_digests: {e}", exc_info=True)


@celery_app.task(name="send_weekly_digests")
def send_weekly_digests():
    """Celery task to send weekly digest emails to all users with weekly frequency."""
    import asyncio

    asyncio.run(_send_weekly_digests_async())


async def _send_weekly_digests_async():
    """Async function to send weekly digests."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all users with weekly digest preference
            result = await db.execute(
                select(User)
                .join(NotificationPreferences, NotificationPreferences.user_id == User.id)
                .where(
                    and_(
                        NotificationPreferences.enabled == True,
                        NotificationPreferences.frequency == "weekly",
                        User.is_active == True,
                    )
                )
            )
            users = result.scalars().all()

            logger.info(f"Sending weekly digests to {len(users)} users")

            for user in users:
                try:
                    await _send_weekly_digest_to_user(db, user)
                except Exception as e:
                    logger.error(f"Error sending weekly digest to user {user.id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in send_weekly_digests: {e}", exc_info=True)
