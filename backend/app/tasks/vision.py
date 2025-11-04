"""
Vision task module for the Snap Job pipeline.

This module handles item detection using computer vision to identify
category, attributes, and condition from uploaded photos.
"""
from __future__ import annotations

from typing import Optional
from celery import shared_task

from app.core.db import get_session
from app.core.models import SnapJob
from app.vision.detector import detect_item
from app.vision.condition import estimate_condition


@shared_task(name="app.tasks.vision.detect_item_task")
def detect_item_task(job_id: int) -> dict:
    """
    Detect item category, attributes, and condition from snap job photos.

    This task:
    1. Retrieves the SnapJob and its input photos
    2. Uses vision API to detect item type and attributes
    3. Estimates the item's condition
    4. Calculates a confidence score
    5. Stores results in SnapJob.meta.vision and updates detected fields

    Args:
        job_id: The SnapJob ID to process

    Returns:
        dict with status and detection results
    """
    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            return {"error": "job not found", "job_id": job_id}

        photos = job.input_photos
        if not photos:
            # No photos to process
            if not job.meta:
                job.meta = {}
            job.meta["vision"] = {
                "error": "No photos provided",
                "category": None,
                "attributes": {},
                "condition": None,
                "confidence": 0.0,
            }
            session.commit()
            return {"status": "error", "message": "No photos provided"}

        # Generate captions for images (placeholder - in production would use actual image analysis)
        captions = [f"Photo {idx}" for idx, _ in enumerate(photos, start=1)]

        # Detect item category and attributes
        try:
            category, attributes = detect_item([], captions)  # Empty images list, using captions
        except Exception as e:
            category = "unknown"
            attributes = {}
            confidence = 0.0
            error_msg = str(e)
        else:
            # Calculate confidence based on detection quality
            confidence = 0.85 if category and category != "unknown" else 0.3
            error_msg = None

        # Estimate condition from photos and metadata
        try:
            metadata = {"condition_hint": "good"}  # Placeholder - could extract from EXIF/analysis
            condition = estimate_condition(captions, metadata)
        except Exception as e:
            condition = "good"  # Default to good
            if error_msg:
                error_msg += f"; Condition error: {str(e)}"
            else:
                error_msg = f"Condition estimation error: {str(e)}"

        # Prepare vision metadata
        vision_data = {
            "category": category,
            "attributes": attributes or {},
            "condition": condition,
            "confidence": confidence,
            "photo_count": len(photos),
        }

        if error_msg:
            vision_data["error"] = error_msg

        # Store in job.meta.vision
        if not job.meta:
            job.meta = {}
        job.meta["vision"] = vision_data

        # Update the main detected fields for backward compatibility
        job.detected_category = category
        job.detected_attributes = attributes or {}
        job.condition_guess = condition

        session.commit()

        return {
            "status": "success" if not error_msg else "partial",
            "job_id": job_id,
            "vision": vision_data,
        }
