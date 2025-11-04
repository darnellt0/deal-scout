"""Background pipeline for processing snap jobs.

This module implements the complete snap-to-sell pipeline:
1. Vision → Detect item
2. Image Prep → Clean/standardize
3. Pricing → Pull comps & suggest price
4. Copywriter → Draft listing text
5. Compose Draft → Save for the UI
6. (Optional) Cross-post prep
7. Finalize Job
"""
from __future__ import annotations

import logging
from typing import Dict, Tuple

from celery import shared_task
from sqlalchemy import select

from app.config import get_settings
from app.core.db import get_session
from app.core.models import Condition, ListingDraft, MediaAsset, SnapJob
from app.seller.auto_write import generate_listing
from app.seller.pricing import PriceSuggestionRequest, load_local_comps, response_from_fixture
from app.vision.cleanup import preprocess_images
from app.vision.condition import estimate_condition
from app.vision.detector import detect_item

logger = logging.getLogger(__name__)
settings = get_settings()


def _log_progress(job: SnapJob, session, progress: int, message: str):
    """Helper to update job progress and log messages."""
    logger.info(f"Job {job.id}: {message} (progress: {progress}%)")
    # You could add a progress field to SnapJob model if needed
    session.commit()


def _detect_item_task(job: SnapJob, captions: list, metadata: list) -> Tuple[str, Dict]:
    """2.1 Vision → Detect item.

    Outputs: category, attributes (brand/model/color/size), condition, confidence score
    Stores JSON in SnapJob metadata.
    """
    logger.info(f"Job {job.id}: Running vision detection")

    # Extract vision labels if available from metadata
    vision_labels = []
    for meta in metadata:
        if 'labels' in meta:
            vision_labels.extend(meta['labels'])

    category, attributes = detect_item(vision_labels, captions)
    condition = estimate_condition(captions, metadata[0] if metadata else {})

    # Calculate confidence score (placeholder - would use actual vision model confidence)
    confidence_score = 0.85 if category != "unknown" else 0.5

    # Store in job
    job.detected_category = category
    job.detected_attributes = attributes
    job.condition_guess = condition

    return category, attributes


def _clean_images_task(job: SnapJob, session) -> list:
    """2.2 Image Prep → Clean/standardize.

    Steps: background removal, brighten, crop, square, web-size
    Writes processed URLs to MediaAsset.processed_url
    """
    logger.info(f"Job {job.id}: Cleaning and standardizing images")

    images, metadata = preprocess_images(job.input_photos)
    job.processed_images = images

    # Create MediaAsset records for each image
    for idx, (image_data, meta) in enumerate(zip(images, metadata)):
        media_asset = MediaAsset(
            user_id=job.user_id,
            snap_job_id=job.id,
            original_url=job.input_photos[idx] if idx < len(job.input_photos) else image_data,
            processed_url=image_data,
            media_type="image",
            width=meta.get('width'),
            height=meta.get('height'),
            processing_status="completed",
            processing_steps={
                "brightness": True,
                "compression": True,
            },
            display_order=idx
        )
        session.add(media_asset)

    session.commit()
    return images


def _suggest_pricing_task(job: SnapJob, category: str, condition: str) -> Dict:
    """2.3 Pricing → Pull comps & suggest price.

    Sources: comp providers/APIs or fixtures
    Outputs: price_suggested, price_low, price_high, rationale
    Stores in SnapJob metadata.
    """
    logger.info(f"Job {job.id}: Generating price suggestions")

    # Convert condition string to enum
    try:
        condition_enum = Condition(condition) if condition in Condition._value2member_map_ else Condition.good
    except (ValueError, KeyError):
        condition_enum = Condition.good

    # Build pricing request
    request = PriceSuggestionRequest(
        title=job.suggested_title or category,
        category=category,
        condition=condition_enum,
        attributes=job.detected_attributes or {}
    )

    # Try to get pricing from fixture first
    pricing_response = response_from_fixture(category, condition_enum)

    if not pricing_response:
        # Fallback: use simple pricing logic
        base_prices = {
            "couch": 150.0,
            "sofa": 150.0,
            "sectional": 300.0,
            "kitchen island": 250.0,
            "dining table": 200.0,
        }
        suggested = base_prices.get(category.lower(), 100.0)

        # Adjust by condition
        condition_multipliers = {
            "excellent": 1.3,
            "great": 1.1,
            "good": 1.0,
            "fair": 0.7,
            "poor": 0.5,
        }
        multiplier = condition_multipliers.get(condition, 1.0)
        suggested = suggested * multiplier

        pricing_data = {
            "price_suggested": round(suggested, 2),
            "price_low": round(suggested * 0.8, 2),
            "price_high": round(suggested * 1.2, 2),
            "rationale": f"Based on typical {category} prices in {condition} condition",
            "comparable_count": 0,
            "comparables": []
        }
    else:
        # Use fixture data
        pricing_data = {
            "price_suggested": pricing_response.suggested_price,
            "price_low": round(pricing_response.suggested_price * 0.8, 2),
            "price_high": round(pricing_response.suggested_price * 1.2, 2),
            "rationale": f"Based on {pricing_response.comparable_count} comparable sales",
            "comparable_count": pricing_response.comparable_count,
            "comparables": pricing_response.comparables
        }

    # Store in job
    job.suggested_price = pricing_data["price_suggested"]
    job.price_suggestion_cents = int(pricing_data["price_suggested"] * 100)

    return pricing_data


def _write_listing_copy_task(job: SnapJob, category: str, attributes: Dict, condition: str, pricing_data: Dict) -> Tuple[str, str, list, list]:
    """2.4 Copywriter → Draft listing text.

    Inputs: vision + pricing + photos
    Outputs: title, description, bullet highlights, tags
    Stores in SnapJob metadata.
    """
    logger.info(f"Job {job.id}: Generating listing copy")

    metadata = {
        "category": category,
        "attributes": attributes,
        "condition": condition,
        "price": pricing_data["price_suggested"],
        "title_hint": f"{category.title()}"
    }

    title, description = generate_listing(metadata)

    # Generate bullet highlights from attributes
    bullet_highlights = []
    if attributes:
        for key, value in attributes.items():
            if value:
                bullet_highlights.append(f"{key.replace('_', ' ').title()}: {value}")

    # Generate tags
    tags = [category.lower()]
    if attributes:
        tags.extend([str(v).lower() for v in attributes.values() if v])
    tags.append(condition.lower())
    tags = list(set(tags))[:10]  # Deduplicate and limit to 10

    # Store in job
    job.suggested_title = title
    job.title_suggestion = title
    job.suggested_description = description
    job.description_suggestion = description

    return title, description, bullet_highlights, tags


def _create_listing_draft_task(job: SnapJob, session, category: str, attributes: Dict,
                                condition: str, title: str, description: str,
                                pricing_data: Dict, bullet_highlights: list, tags: list) -> ListingDraft:
    """2.5 Compose Draft → Save for the UI.

    Creates ListingDraft with:
    - category, attributes, condition
    - title, description, price_suggested
    - attached MediaAsset (processed)
    - status="draft"
    """
    logger.info(f"Job {job.id}: Creating listing draft")

    # Convert condition to enum
    try:
        condition_enum = Condition(condition) if condition in Condition._value2member_map_ else Condition.good
    except (ValueError, KeyError):
        condition_enum = Condition.good

    # Create the draft
    draft = ListingDraft(
        user_id=job.user_id,
        snap_job_id=job.id,
        status="draft",
        title=title,
        description=description,
        category=category,
        attributes=attributes,
        condition=condition_enum,
        price_suggested=pricing_data["price_suggested"],
        price_low=pricing_data["price_low"],
        price_high=pricing_data["price_high"],
        price_rationale=pricing_data["rationale"],
        bullet_highlights=bullet_highlights,
        tags=tags,
        seo_keywords=tags,
        vision_confidence=0.85,  # Would come from vision model
        meta={
            "vision": {
                "category": category,
                "attributes": attributes,
                "condition": condition,
                "confidence": 0.85
            },
            "pricing": pricing_data,
            "copy": {
                "title": title,
                "description": description,
                "bullet_highlights": bullet_highlights,
                "tags": tags
            }
        }
    )

    session.add(draft)
    session.commit()

    # Link MediaAssets to the draft
    media_assets = session.execute(
        select(MediaAsset).where(MediaAsset.snap_job_id == job.id)
    ).scalars().all()

    for asset in media_assets:
        asset.listing_draft_id = draft.id

    session.commit()

    logger.info(f"Job {job.id}: Created draft {draft.id}")
    return draft


@shared_task(name="app.tasks.process_snap.process_snap_job")
def process_snap_job(job_id: int):
    """Main pipeline task that orchestrates all subtasks.

    Returns:
        dict: Job status with draft_id if successful
    """
    try:
        with get_session() as session:
            job = session.get(SnapJob, job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return {"error": "job not found"}

            logger.info(f"Starting processing for job {job_id}")
            job.status = "processing"
            session.commit()

            # 2.1 Vision → Detect item (10% progress)
            _log_progress(job, session, 10, "Detecting item category and attributes")
            captions = [f"Photo {idx}" for idx, _ in enumerate(job.input_photos, start=1)]
            metadata = []
            category, attributes = _detect_item_task(job, captions, metadata)
            session.commit()

            # 2.2 Image Prep → Clean/standardize (30% progress)
            _log_progress(job, session, 30, "Cleaning and processing images")
            images = _clean_images_task(job, session)

            # 2.3 Pricing → Pull comps & suggest price (50% progress)
            _log_progress(job, session, 50, "Generating price suggestions")
            pricing_data = _suggest_pricing_task(job, category, job.condition_guess or "good")
            session.commit()

            # 2.4 Copywriter → Draft listing text (70% progress)
            _log_progress(job, session, 70, "Writing listing copy")
            title, description, bullet_highlights, tags = _write_listing_copy_task(
                job, category, attributes, job.condition_guess or "good", pricing_data
            )
            session.commit()

            # 2.5 Compose Draft → Save for the UI (85% progress)
            _log_progress(job, session, 85, "Creating listing draft")
            draft = _create_listing_draft_task(
                job, session, category, attributes, job.condition_guess or "good",
                title, description, pricing_data, bullet_highlights, tags
            )

            # 2.7 Finalize Job (100% progress)
            _log_progress(job, session, 100, "Pipeline completed successfully")
            job.status = "completed"
            session.commit()

            logger.info(f"Job {job_id} completed successfully. Draft ID: {draft.id}")
            return {
                "job_id": job_id,
                "status": "completed",
                "draft_id": draft.id,
                "title": title,
                "price": pricing_data["price_suggested"]
            }

    except Exception as e:
        logger.exception(f"Job {job_id} failed with error: {e}")
        with get_session() as session:
            job = session.get(SnapJob, job_id)
            if job:
                job.status = "failed"
                session.commit()
        return {"job_id": job_id, "status": "failed", "error": str(e)}
