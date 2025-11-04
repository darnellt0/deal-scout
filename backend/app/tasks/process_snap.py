from __future__ import annotations

from typing import List, Optional

from celery import shared_task

from app.core.db import get_session
from app.core.models import Condition, MyItem, SnapJob
from app.seller.auto_write import generate_listing
from app.vision.cleanup import preprocess_images
from app.vision.condition import estimate_condition
from app.vision.detector import detect_item


@shared_task(name="app.tasks.process_snap.process_snap_job")
def process_snap_job(job_id: int, enable_crosspost_prep: bool = False, platforms: Optional[List[str]] = None):
    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            return {"error": "job not found"}

        job.status = "processing"
        images, metadata = preprocess_images(job.input_photos)
        captions = [
            f"Photo {idx}" for idx, _ in enumerate(images, start=1)
        ]  # placeholder captions
        category, attributes = detect_item([], captions)
        condition = estimate_condition(
            captions, metadata[0] if metadata else {"condition_hint": "good"}
        )

        title, description = generate_listing(
            {
                "category": category,
                "attributes": attributes,
                "condition": condition,
            }
        )

        suggested_price = 0 if category == "couch" else 200

        job.detected_category = category
        job.detected_attributes = attributes
        job.processed_images = images
        job.condition_guess = condition
        job.price_suggestion_cents = int(suggested_price * 100)
        job.suggested_title = title
        job.suggested_description = description
        job.suggested_price = suggested_price
        job.title_suggestion = title
        job.description_suggestion = description
        job.status = "ready"

        condition_enum = (
            Condition(condition) if condition in Condition._value2member_map_ else Condition.good
        )

        # Add processed images and description to attributes
        item_attributes = attributes.copy()
        item_attributes["images"] = images  # Store processed images
        item_attributes["description"] = description  # Store generated description

        item = MyItem(
            title=title,
            category=category,
            attributes=item_attributes,
            condition=condition_enum,
            price=suggested_price,
            status="draft",
            user_id=job.user_id,
        )
        session.add(item)
        session.commit()

        # Store item_id for cross-post prep
        item_id = item.id

    # Step 2.6: Optional cross-post prep
    if enable_crosspost_prep:
        from app.tasks.cross_post import prepare_crosspost

        # Call cross-post preparation task
        try:
            crosspost_result = prepare_crosspost(job_id, platforms)
            return {
                "job_id": job_id,
                "status": "ready",
                "item_id": item_id,
                "crosspost_prep": crosspost_result,
            }
        except Exception as e:
            # Log error but don't fail the entire job
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Cross-post prep failed for job {job_id}: {e}", exc_info=True)
            return {
                "job_id": job_id,
                "status": "ready",
                "item_id": item_id,
                "crosspost_prep": {"error": str(e)},
            }

    return {"job_id": job_id, "status": "ready", "item_id": item_id}
