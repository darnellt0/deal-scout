from __future__ import annotations

import logging
from celery import shared_task

from app.core.db import get_session
from app.core.models import SnapJob, Notification

# Import the individual task functions (not the Celery tasks themselves)
from app.tasks.vision import detect_item_task
from app.tasks.images import clean_images
from app.tasks.pricing import suggest_price
from app.tasks.copywriter import write_listing
from app.tasks.seller_draft import create_listing_draft

logger = logging.getLogger(__name__)


def update_progress(session, job_id: int, progress: int, status: str = "processing"):
    """Helper to update job progress and status."""
    job = session.get(SnapJob, job_id)
    if job:
        job.progress = progress
        job.status = status
        session.commit()


@shared_task(name="app.tasks.process_snap.process_snap_job")
def process_snap_job(job_id: int, locale: str = "San Jose, CA"):
    """
    Main pipeline for processing a snap job through all stages.

    Pipeline stages:
    1. Vision → Detect item (category, attributes, condition)
    2. Image Prep → Clean/standardize images
    3. Pricing → Pull comps & suggest price
    4. Copywriter → Draft listing text
    5. Compose Draft → Create ListingDraft for UI
    6. Finalize Job → Mark as completed

    Each stage writes progress logs and updates SnapJob.status and progress.

    Args:
        job_id: The SnapJob ID to process
        locale: Location for pricing (default: "San Jose, CA")

    Returns:
        dict with final status and results
    """
    logger.info(f"Starting snap job processing for job_id={job_id}")

    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"error": "job not found", "job_id": job_id}

        try:
            # Initialize job status
            job.status = "processing"
            job.progress = 0
            job.error_message = None
            session.commit()

            # ============================================================
            # STAGE 1: Vision - Detect Item
            # ============================================================
            logger.info(f"Job {job_id}: Stage 1 - Vision detection")
            update_progress(session, job_id, 10, "processing")

            vision_result = detect_item_task(job_id)
            if vision_result.get("status") == "error":
                raise Exception(f"Vision detection failed: {vision_result.get('error')}")

            update_progress(session, job_id, 25, "processing")

            # ============================================================
            # STAGE 2: Image Prep - Clean/Standardize
            # ============================================================
            logger.info(f"Job {job_id}: Stage 2 - Image processing")
            update_progress(session, job_id, 30, "processing")

            images_result = clean_images(job_id, enable_bg_removal=False)
            if images_result.get("status") == "error":
                logger.warning(f"Image processing failed: {images_result.get('error')}")
                # Continue anyway - we can still process with original images

            update_progress(session, job_id, 45, "processing")

            # ============================================================
            # STAGE 3: Pricing - Pull Comps & Suggest Price
            # ============================================================
            logger.info(f"Job {job_id}: Stage 3 - Pricing suggestion")
            update_progress(session, job_id, 50, "processing")

            pricing_result = suggest_price(job_id, locale=locale)
            if pricing_result.get("status") == "error":
                logger.warning(f"Pricing failed: {pricing_result.get('error')}")
                # Continue anyway - draft can still be created without pricing

            update_progress(session, job_id, 65, "processing")

            # ============================================================
            # STAGE 4: Copywriter - Draft Listing Text
            # ============================================================
            logger.info(f"Job {job_id}: Stage 4 - Copywriting")
            update_progress(session, job_id, 70, "processing")

            copy_result = write_listing(job_id)
            if copy_result.get("status") == "error":
                raise Exception(f"Copywriting failed: {copy_result.get('error')}")

            update_progress(session, job_id, 85, "processing")

            # ============================================================
            # STAGE 5: Compose Draft - Create ListingDraft
            # ============================================================
            logger.info(f"Job {job_id}: Stage 5 - Creating listing draft")
            update_progress(session, job_id, 90, "processing")

            draft_result = create_listing_draft(job_id)
            if draft_result.get("status") == "error":
                raise Exception(f"Draft creation failed: {draft_result.get('error')}")

            draft_id = draft_result.get("draft_id")
            update_progress(session, job_id, 95, "processing")

            # ============================================================
            # STAGE 6: Finalize Job
            # ============================================================
            logger.info(f"Job {job_id}: Stage 6 - Finalizing")

            # Refresh job to get latest data
            session.refresh(job)
            job.status = "completed"
            job.progress = 100
            session.commit()

            # TODO: Create notification for seller
            # notification = Notification(
            #     user_id=job.user_id,
            #     channel="email",
            #     payload={
            #         "type": "snap_job_completed",
            #         "job_id": job_id,
            #         "draft_id": draft_id,
            #         "title": copy_result.get("copy", {}).get("title"),
            #     },
            #     status="pending",
            # )
            # session.add(notification)
            # session.commit()

            logger.info(f"Job {job_id} completed successfully. Draft ID: {draft_id}")

            return {
                "status": "completed",
                "job_id": job_id,
                "draft_id": draft_id,
                "vision": vision_result.get("vision"),
                "pricing": pricing_result.get("pricing"),
                "copy": copy_result.get("copy"),
            }

        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)

            # Mark job as failed
            session.refresh(job)
            job.status = "failed"
            job.error_message = str(e)
            session.commit()

            return {
                "status": "failed",
                "job_id": job_id,
                "error": str(e),
            }
