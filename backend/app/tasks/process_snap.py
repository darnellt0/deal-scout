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
        session.commit()

        # Preprocess images
        images, metadata = preprocess_images(job.input_photos)

        # Use Claude vision API to detect items with real vision analysis
        category, attributes = detect_item(job.input_photos)

        # Estimate condition from vision data if available
        condition = attributes.get("condition", "good")
        if not condition or condition == "unknown":
            condition = estimate_condition(
                [attributes.get("item_type", "")],
                metadata[0] if metadata else {"condition_hint": "good"}
            )

        # Generate metadata for listing generation
        listing_metadata = {
            "category": category,
            "item_type": attributes.get("item_type", ""),
            "condition": condition,
            "attributes": {k: v for k, v in attributes.items() if k not in ["item_type", "condition", "notes"]},
            "notes": attributes.get("notes", ""),
        }

        # Generate title and description using vision data
        title, description = generate_listing(listing_metadata)

        # Estimate price - use Claude's pricing if available
        from app.vision.claude_vision import estimate_price_with_claude
        suggested_price = estimate_price_with_claude(category, attributes)
        if not suggested_price or suggested_price == 0:
            # Fallback pricing logic
            suggested_price = 200 if category != "furniture" else 150

        # Update job with results
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

        # Create MyItem from the snap job
        condition_enum = (
            Condition(condition) if condition in Condition._value2member_map_ else Condition.good
        )

        item = MyItem(
            user_id=job.user_id,
            title=title,
            category=category,
            attributes=attributes,
            condition=condition_enum,
            price=suggested_price,
            status="draft",
        )
        session.add(item)
        session.commit()

    return {"job_id": job_id, "status": "ready"}
