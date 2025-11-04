"""
Celery tasks for copywriting and listing text generation.
"""
from __future__ import annotations

import logging

from celery import shared_task

from app.core.db import get_session
from app.core.models import SnapJob
from app.seller.copywriter import generate_copy

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.copywriter.write_listing")
def write_listing(job_id: int):
    """
    Generate listing copy for a SnapJob.

    This task reads vision data (category, attributes, condition) and pricing data
    from the SnapJob, then generates comprehensive listing copy including:
    - Title
    - Description
    - Bullet point highlights
    - Tags

    Results are stored in SnapJob.meta['copy'] and also in the legacy fields
    (suggested_title, suggested_description) for backwards compatibility.

    Args:
        job_id: The SnapJob ID to process

    Returns:
        Dict with status and generated copy data
    """
    logger.info("Starting copywriter task for job_id=%s", job_id)

    with get_session() as session:
        job = session.get(SnapJob, job_id)

        if not job:
            logger.error("Job not found: job_id=%s", job_id)
            return {"error": "job not found", "job_id": job_id}

        try:
            # Extract inputs from the SnapJob
            category = job.detected_category or "item"
            attributes = job.detected_attributes or {}
            condition = job.condition_guess or "good"
            price = job.suggested_price
            photos_count = len(job.processed_images or job.input_photos or [])

            logger.info(
                "Generating copy for job_id=%s: category=%s, condition=%s, price=%s",
                job_id,
                category,
                condition,
                price,
            )

            # Generate comprehensive copy
            copy_data = generate_copy(
                category=category,
                attributes=attributes,
                condition=condition,
                price=price,
                photos_count=photos_count,
            )

            # Store in meta.copy for structured access
            if job.meta is None:
                job.meta = {}
            job.meta["copy"] = copy_data

            # Also store in legacy fields for backwards compatibility
            job.suggested_title = copy_data["title"]
            job.suggested_description = copy_data["description"]
            job.title_suggestion = copy_data["title"]
            job.description_suggestion = copy_data["description"]

            # Mark the session as dirty to ensure the update is committed
            session.add(job)
            session.commit()

            logger.info(
                "Copywriter task completed for job_id=%s: confidence=%.2f",
                job_id,
                copy_data["confidence"],
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "copy": copy_data,
            }

        except Exception as exc:
            logger.error(
                "Copywriter task failed for job_id=%s: %s",
                job_id,
                exc,
                exc_info=True,
            )
            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(exc),
            }
