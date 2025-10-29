from __future__ import annotations

from celery import shared_task

from app.core.db import get_session
from app.core.models import Condition, MyItem, SnapJob
from app.seller.auto_write import generate_listing
from app.vision.cleanup import preprocess_images
from app.vision.condition import estimate_condition
from app.vision.detector import detect_item


@shared_task(name="app.tasks.process_snap.process_snap_job")
def process_snap_job(job_id: int):
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

        item = MyItem(
            title=title,
            category=category,
            attributes=attributes,
            condition=condition_enum,
            price=suggested_price,
            status="draft",
        )
        session.add(item)

    return {"job_id": job_id, "status": "ready"}
