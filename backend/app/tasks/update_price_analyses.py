"""Celery task for updating price analyses."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.models import Listing, PriceAnalysis
from app.ml.pricing_analyzer import PriceAnalyzer
from app.worker import celery_app

logger = logging.getLogger("deal_scout.tasks.update_price_analyses")

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


@celery_app.task(name="update_all_price_analyses")
def update_all_price_analyses():
    """Update price analyses for all active listings (runs daily)."""
    import asyncio

    asyncio.run(_update_all_price_analyses_async())


async def _update_all_price_analyses_async():
    """Async function to update price analyses."""
    async with AsyncSessionLocal() as db:
        try:
            # Get active listings that need analysis
            # Priority: listings without recent analysis or with stale analysis
            cutoff = datetime.utcnow() - timedelta(days=1)

            # Get all active listings
            result = await db.execute(
                select(Listing)
                .where(Listing.available == True)
                .order_by(Listing.created_at.desc())
                .limit(1000)  # Limit to prevent overwhelming the system
            )
            listings = result.scalars().all()

            logger.info(f"Found {len(listings)} active listings to analyze")

            analyzer = PriceAnalyzer(db)
            updated_count = 0
            skipped_count = 0

            for listing in listings:
                try:
                    # Check if listing has recent analysis
                    analysis_result = await db.execute(
                        select(PriceAnalysis)
                        .where(
                            and_(
                                PriceAnalysis.listing_id == listing.id,
                                PriceAnalysis.analyzed_at >= cutoff,
                            )
                        )
                        .order_by(PriceAnalysis.analyzed_at.desc())
                        .limit(1)
                    )
                    existing_analysis = analysis_result.scalar_one_or_none()

                    if existing_analysis:
                        logger.debug(
                            f"Skipping listing {listing.id} - recently analyzed"
                        )
                        skipped_count += 1
                        continue

                    # Run analysis
                    analysis_data = await analyzer.analyze_listing_price(listing.id)

                    if analysis_data:
                        # Save analysis
                        analysis = PriceAnalysis(**analysis_data)
                        db.add(analysis)
                        updated_count += 1

                        # Commit every 10 analyses to avoid huge transactions
                        if updated_count % 10 == 0:
                            await db.commit()
                            logger.info(f"Progress: {updated_count} analyses saved")

                except Exception as e:
                    logger.error(
                        f"Error analyzing listing {listing.id}: {e}", exc_info=True
                    )
                    continue

            # Final commit
            await db.commit()

            logger.info(
                f"Price analysis update complete: {updated_count} updated, {skipped_count} skipped"
            )

        except Exception as e:
            logger.error(f"Error in update_all_price_analyses: {e}", exc_info=True)


@celery_app.task(name="analyze_new_listings")
def analyze_new_listings():
    """Analyze newly added listings (runs hourly)."""
    import asyncio

    asyncio.run(_analyze_new_listings_async())


async def _analyze_new_listings_async():
    """Async function to analyze new listings."""
    async with AsyncSessionLocal() as db:
        try:
            # Get listings added in the last hour
            cutoff = datetime.utcnow() - timedelta(hours=1)

            result = await db.execute(
                select(Listing)
                .where(
                    and_(
                        Listing.available == True,
                        Listing.created_at >= cutoff,
                    )
                )
            )
            new_listings = result.scalars().all()

            if not new_listings:
                logger.info("No new listings to analyze")
                return

            logger.info(f"Analyzing {len(new_listings)} new listings")

            analyzer = PriceAnalyzer(db)
            analyzed_count = 0

            for listing in new_listings:
                try:
                    # Check if already analyzed
                    analysis_result = await db.execute(
                        select(PriceAnalysis)
                        .where(PriceAnalysis.listing_id == listing.id)
                        .limit(1)
                    )
                    if analysis_result.scalar_one_or_none():
                        continue

                    # Run analysis
                    analysis_data = await analyzer.analyze_listing_price(listing.id)

                    if analysis_data:
                        analysis = PriceAnalysis(**analysis_data)
                        db.add(analysis)
                        analyzed_count += 1

                except Exception as e:
                    logger.error(
                        f"Error analyzing new listing {listing.id}: {e}", exc_info=True
                    )
                    continue

            if analyzed_count > 0:
                await db.commit()
                logger.info(f"Analyzed {analyzed_count} new listings")

        except Exception as e:
            logger.error(f"Error in analyze_new_listings: {e}", exc_info=True)
