"""
Image processing task module for the Snap Job pipeline.

This module handles cleaning and standardizing images:
- Background removal
- Brightness/contrast adjustment
- Cropping and squaring
- Resizing to web-optimized dimensions
"""
from __future__ import annotations

from celery import shared_task

from app.core.db import get_session
from app.core.models import SnapJob, MediaAsset
from app.vision.cleanup import preprocess_images


@shared_task(name="app.tasks.images.clean_images")
def clean_images(job_id: int, enable_bg_removal: bool = False) -> dict:
    """
    Clean and standardize images for a snap job.

    This task:
    1. Retrieves the SnapJob and its input photos
    2. Processes each image:
        - Optional: Remove background
        - Brighten/adjust contrast
        - Crop to center focus
        - Square aspect ratio
        - Resize to web-optimized size (e.g., 800x800)
    3. Creates MediaAsset records for each processed image
    4. Stores processed image URLs in SnapJob.processed_images

    Args:
        job_id: The SnapJob ID to process
        enable_bg_removal: Whether to remove backgrounds (default: False)

    Returns:
        dict with status and processed image info
    """
    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            return {"error": "job not found", "job_id": job_id}

        photos = job.input_photos
        if not photos:
            return {"status": "error", "message": "No photos to process"}

        try:
            # Process images using the cleanup module
            processed_images, metadata = preprocess_images(photos)

            # Create MediaAsset records for each processed image
            media_assets = []
            for idx, (original_url, processed_url, meta) in enumerate(
                zip(photos, processed_images, metadata)
            ):
                asset = MediaAsset(
                    snap_job_id=job_id,
                    original_url=original_url,
                    processed_url=processed_url,
                    processing_status="completed",
                    processing_options={
                        "background_removal": enable_bg_removal,
                        "brighten": True,
                        "crop": True,
                        "square": True,
                        "web_size": True,
                    },
                    width=meta.get("width"),
                    height=meta.get("height"),
                    file_size_bytes=meta.get("file_size"),
                    mime_type=meta.get("mime_type", "image/jpeg"),
                    display_order=idx,
                )
                session.add(asset)
                media_assets.append(asset)

            # Update job with processed images
            job.processed_images = processed_images

            # Store metadata in job.meta.images
            if not job.meta:
                job.meta = {}
            job.meta["images"] = {
                "original_count": len(photos),
                "processed_count": len(processed_images),
                "background_removal_enabled": enable_bg_removal,
                "processing_metadata": metadata,
            }

            session.commit()

            return {
                "status": "success",
                "job_id": job_id,
                "original_count": len(photos),
                "processed_count": len(processed_images),
                "processed_urls": processed_images,
                "media_asset_ids": [asset.id for asset in media_assets],
            }

        except Exception as e:
            # Store error in job metadata
            if not job.meta:
                job.meta = {}
            job.meta["images"] = {
                "error": str(e),
                "original_count": len(photos),
                "processed_count": 0,
            }
            session.commit()

            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e),
            }
