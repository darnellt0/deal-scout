"""
Seller draft task module for the Snap Job pipeline.

This module creates a ListingDraft from the processed SnapJob data,
making it ready for seller review and editing in the UI.
"""
from __future__ import annotations

from celery import shared_task

from app.core.db import get_session
from app.core.models import SnapJob, ListingDraft, MediaAsset, Condition


@shared_task(name="app.tasks.seller_draft.create_listing_draft")
def create_listing_draft(job_id: int) -> dict:
    """
    Create a ListingDraft from a completed SnapJob.

    This task:
    1. Retrieves the SnapJob with all processed data (vision, pricing, copy, images)
    2. Creates a new ListingDraft record with:
        - Category, attributes, condition
        - Title, description, bullet highlights, tags
        - Price suggestions (low, suggested, high) and rationale
        - Processed image URLs
        - Status = "draft"
    3. Links MediaAssets to the new draft
    4. Returns the draft ID for UI display

    Args:
        job_id: The SnapJob ID to create a draft from

    Returns:
        dict with status and draft_id
    """
    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            return {"error": "job not found", "job_id": job_id}

        # Extract data from job.meta
        meta = job.meta or {}
        vision_data = meta.get("vision", {})
        pricing_data = meta.get("pricing", {})
        copy_data = meta.get("copy", {})

        # Get category, attributes, condition
        category = vision_data.get("category") or job.detected_category or "unknown"
        attributes = vision_data.get("attributes") or job.detected_attributes or {}
        condition_str = vision_data.get("condition") or job.condition_guess or "good"

        # Convert condition string to enum
        try:
            condition = Condition(condition_str)
        except (ValueError, KeyError):
            condition = Condition.good

        # Get copy (title, description, highlights, tags)
        title = copy_data.get("title") or job.suggested_title or "Untitled Item"
        description = copy_data.get("description") or job.suggested_description
        bullet_highlights = copy_data.get("bullet_highlights", [])
        tags = copy_data.get("tags", [])

        # Get pricing
        price_suggested = pricing_data.get("price_suggested")
        price_low = pricing_data.get("price_low")
        price_high = pricing_data.get("price_high")
        pricing_rationale = pricing_data.get("rationale")

        # Get processed images
        images = job.processed_images or []

        try:
            # Create the ListingDraft
            draft = ListingDraft(
                user_id=job.user_id,
                snap_job_id=job_id,
                category=category,
                attributes=attributes,
                condition=condition,
                title=title,
                description=description,
                bullet_highlights=bullet_highlights,
                tags=tags,
                price_suggested=price_suggested,
                price_low=price_low,
                price_high=price_high,
                pricing_rationale=pricing_rationale,
                images=images,
                status="draft",
            )
            session.add(draft)
            session.flush()  # Get the draft ID

            # Link MediaAssets to the draft
            media_assets = (
                session.query(MediaAsset)
                .filter(MediaAsset.snap_job_id == job_id)
                .all()
            )
            for asset in media_assets:
                asset.listing_draft_id = draft.id

            session.commit()

            return {
                "status": "success",
                "job_id": job_id,
                "draft_id": draft.id,
                "category": category,
                "title": title,
                "price_suggested": price_suggested,
            }

        except Exception as e:
            session.rollback()
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e),
            }
