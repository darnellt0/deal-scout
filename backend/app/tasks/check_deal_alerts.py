"""Celery task for checking deal alert rules and sending notifications."""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.models import DealAlertRule, Listing, NotificationPreferences, User
from app.worker import celery_app

logger = logging.getLogger("deal_scout.tasks.check_deal_alerts")

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


async def _find_matching_listings(db: AsyncSession, rule: DealAlertRule) -> List[Listing]:
    """Find listings that match a deal alert rule."""
    query = select(Listing).where(Listing.available == True)

    # Price range filter
    if rule.min_price is not None:
        query = query.where(Listing.price >= rule.min_price)
    if rule.max_price is not None:
        query = query.where(Listing.price <= rule.max_price)

    # Category filter (OR logic)
    if rule.categories:
        query = query.where(Listing.category.in_(rule.categories))

    # Condition filter
    if rule.condition:
        query = query.where(Listing.condition == rule.condition)

    # Order by newest first and limit to 1000
    query = query.order_by(Listing.created_at.desc()).limit(1000)

    # Execute query
    result = await db.execute(query)
    listings = result.scalars().all()

    # Filter by keywords (in-memory, after basic DB filters)
    filtered_listings = []
    for listing in listings:
        # Skip if we already have this listing checked
        if rule.last_triggered_at and listing.created_at < rule.last_triggered_at:
            continue

        # Check keywords (OR logic - match any)
        if rule.keywords:
            title_lower = listing.title.lower()
            desc_lower = (listing.description or "").lower()
            keyword_match = any(
                keyword.lower() in title_lower or keyword.lower() in desc_lower
                for keyword in rule.keywords
            )
            if not keyword_match:
                continue

        # Check exclude keywords (NOT logic - exclude all)
        if rule.exclude_keywords:
            title_lower = listing.title.lower()
            desc_lower = (listing.description or "").lower()
            exclude_match = any(
                keyword.lower() in title_lower or keyword.lower() in desc_lower
                for keyword in rule.exclude_keywords
            )
            if exclude_match:
                continue

        filtered_listings.append(listing)

    return filtered_listings


async def _send_notification(
    db: AsyncSession, user: User, rule: DealAlertRule, listing: Listing
):
    """Send notification to user about matching deal."""
    from app.notify.email import send_email_async

    prefs = await db.execute(
        select(NotificationPreferences).where(NotificationPreferences.user_id == user.id)
    )
    prefs = prefs.scalar_one_or_none()

    # Get channels from rule, fallback to preferences
    channels = rule.notification_channels or ["email"]
    if prefs:
        # Use intersection of rule channels and enabled channels
        enabled_channels = set(prefs.channels) & set(channels)
        if not enabled_channels:
            enabled_channels = set(channels)

    # Check quiet hours
    if prefs and prefs.quiet_hours_enabled:
        now = datetime.utcnow().strftime("%H:%M")
        if prefs.quiet_hours_start and prefs.quiet_hours_end:
            if prefs.quiet_hours_start <= now < prefs.quiet_hours_end:
                logger.info(f"Skipping notification due to quiet hours for user {user.id}")
                return

    # Send via email
    if "email" in channels:
        try:
            await send_email_async(
                to=user.email,
                subject=f"Deal Alert: {rule.name}",
                body=f"""
                <h2>New Deal Matching Your Alert: {rule.name}</h2>
                <h3>{listing.title}</h3>
                <p><strong>Price:</strong> ${listing.price}</p>
                <p><strong>Category:</strong> {listing.category}</p>
                <p><strong>Condition:</strong> {listing.condition.value if listing.condition else 'N/A'}</p>
                <p><a href="{listing.url}">View Listing</a></p>
                """,
            )
            logger.info(f"Email sent to {user.email} for listing {listing.id}")
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")

    # Send via Discord (if configured)
    if "discord" in channels and prefs and prefs.discord_webhook_url:
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                embed = {
                    "title": f"Deal Alert: {rule.name}",
                    "description": listing.title,
                    "color": 0x00FF00,
                    "fields": [
                        {"name": "Price", "value": f"${listing.price}", "inline": True},
                        {"name": "Category", "value": listing.category or "N/A", "inline": True},
                        {
                            "name": "Condition",
                            "value": listing.condition.value if listing.condition else "N/A",
                            "inline": True,
                        },
                        {"name": "Link", "value": f"[View Listing]({listing.url})", "inline": False},
                    ],
                }
                if listing.thumbnail_url:
                    embed["thumbnail"] = {"url": listing.thumbnail_url}

                async with session.post(
                    prefs.discord_webhook_url, json={"embeds": [embed]}
                ) as resp:
                    if resp.status == 204:
                        logger.info(f"Discord notification sent for listing {listing.id}")
                    else:
                        logger.error(f"Failed to send Discord notification: {resp.status}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    # Send via SMS (if configured and Twilio is available)
    if "sms" in channels and prefs and prefs.phone_verified and prefs.phone_number:
        try:
            from twilio.rest import Client

            twilio_sid = getattr(settings, "twilio_account_sid", None)
            twilio_token = getattr(settings, "twilio_auth_token", None)
            twilio_from = getattr(settings, "twilio_phone_number", None)

            if twilio_sid and twilio_token and twilio_from:
                client = Client(twilio_sid, twilio_token)
                message = client.messages.create(
                    body=f"Deal Alert: {listing.title} - ${listing.price}\n{listing.url}",
                    from_=twilio_from,
                    to=prefs.phone_number,
                )
                logger.info(f"SMS sent to {prefs.phone_number} for listing {listing.id}")
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")


@celery_app.task(name="check_all_deal_alerts")
def check_all_deal_alerts():
    """Celery task to check all enabled deal alert rules."""
    import asyncio

    asyncio.run(_check_all_deal_alerts_async())


async def _check_all_deal_alerts_async():
    """Async function to check all deal alert rules."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all enabled rules
            result = await db.execute(
                select(DealAlertRule).where(DealAlertRule.enabled == True)
            )
            rules = result.scalars().all()

            logger.info(f"Checking {len(rules)} enabled deal alert rules")

            for rule in rules:
                try:
                    # Get user info
                    user_result = await db.execute(select(User).where(User.id == rule.user_id))
                    user = user_result.scalar_one_or_none()

                    if not user or not user.is_active:
                        logger.debug(f"Skipping rule {rule.id}: user not found or inactive")
                        continue

                    # Find matching listings
                    matching_listings = await _find_matching_listings(db, rule)

                    if matching_listings:
                        logger.info(
                            f"Rule {rule.id} ({rule.name}): Found {len(matching_listings)} matches"
                        )

                        # Send notifications for up to 5 top matches
                        for listing in matching_listings[:5]:
                            await _send_notification(db, user, rule, listing)

                        # Update last_triggered_at
                        rule.last_triggered_at = datetime.utcnow()
                        await db.commit()
                    else:
                        logger.debug(f"Rule {rule.id} ({rule.name}): No matches found")

                except Exception as e:
                    logger.error(f"Error processing rule {rule.id}: {e}", exc_info=True)
                    continue

        except Exception as e:
            logger.error(f"Error in check_all_deal_alerts: {e}", exc_info=True)


@celery_app.task(name="check_price_drops")
def check_price_drops():
    """Celery task to check for price drops on watchlisted items."""
    import asyncio

    asyncio.run(_check_price_drops_async())


async def _check_price_drops_async():
    """Async function to check price drops on watchlisted items."""
    from app.core.models import WatchlistItem

    async with AsyncSessionLocal() as db:
        try:
            # Get all watchlist items with price alerts
            result = await db.execute(
                select(WatchlistItem).where(
                    and_(
                        WatchlistItem.price_alert_threshold.isnot(None),
                        WatchlistItem.alert_sent == False,
                    )
                )
            )
            watchlist_items = result.scalars().all()

            logger.info(f"Checking {len(watchlist_items)} watchlist items for price drops")

            for item in watchlist_items:
                try:
                    # Get listing
                    listing_result = await db.execute(
                        select(Listing).where(Listing.id == item.listing_id)
                    )
                    listing = listing_result.scalar_one_or_none()

                    if not listing:
                        continue

                    # Check if price dropped below threshold
                    if listing.price < item.price_alert_threshold:
                        logger.info(
                            f"Price drop detected: {listing.title} - ${listing.price} (threshold: ${item.price_alert_threshold})"
                        )

                        # Get user
                        user_result = await db.execute(
                            select(User).where(User.id == item.user_id)
                        )
                        user = user_result.scalar_one_or_none()

                        if user:
                            # Send email notification
                            from app.notify.email import send_email_async

                            try:
                                await send_email_async(
                                    to=user.email,
                                    subject=f"Price Drop Alert: {listing.title}",
                                    body=f"""
                                    <h2>Price Drop on Your Watchlist Item!</h2>
                                    <h3>{listing.title}</h3>
                                    <p><strong>Previous Threshold:</strong> ${item.price_alert_threshold}</p>
                                    <p><strong>Current Price:</strong> ${listing.price}</p>
                                    <p><strong>Savings:</strong> ${item.price_alert_threshold - listing.price}</p>
                                    <p><a href="{listing.url}">View Listing</a></p>
                                    """,
                                )
                                logger.info(f"Price drop alert sent to {user.email}")
                            except Exception as e:
                                logger.error(f"Failed to send price drop alert: {e}")

                        # Mark as sent
                        item.alert_sent = True
                        item.last_price = listing.price
                        await db.commit()

                except Exception as e:
                    logger.error(f"Error processing watchlist item {item.id}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in check_price_drops: {e}", exc_info=True)
