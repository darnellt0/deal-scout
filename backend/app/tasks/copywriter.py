"""
Copywriter task module for the Snap Job pipeline.

This module generates listing text (title, description, bullet points, tags)
based on vision detection, pricing data, and photos.
"""
from __future__ import annotations

from typing import List, Tuple
from celery import shared_task

from app.core.db import get_session
from app.core.models import SnapJob
from app.seller.auto_write import generate_listing


def extract_highlights(description: str, max_highlights: int = 5) -> List[str]:
    """
    Extract key bullet highlights from a description.

    Args:
        description: The full item description
        max_highlights: Maximum number of highlights to extract

    Returns:
        List of highlight strings
    """
    if not description:
        return []

    # Split into sentences
    sentences = [s.strip() for s in description.split('.') if s.strip()]

    # Take first few sentences as highlights
    highlights = sentences[:max_highlights]

    # Clean up highlights
    highlights = [h if h.endswith('.') else f"{h}." for h in highlights]

    return highlights


def generate_tags(category: str, attributes: dict, condition: str) -> List[str]:
    """
    Generate searchable tags for the listing.

    Args:
        category: Item category
        attributes: Item attributes (brand, model, color, size, etc.)
        condition: Item condition

    Returns:
        List of tag strings
    """
    tags = []

    # Add category tags
    if category:
        # Split hierarchical categories (e.g., "furniture>sofas" -> ["furniture", "sofas"])
        category_parts = category.lower().split('>')
        tags.extend(category_parts)

    # Add attribute tags
    if attributes:
        for key, value in attributes.items():
            if value and isinstance(value, str):
                tags.append(value.lower())

    # Add condition tag
    if condition:
        tags.append(condition.lower())

    # Remove duplicates and empty tags
    tags = list(set(tag.strip() for tag in tags if tag and tag.strip()))

    return tags[:10]  # Limit to 10 tags


@shared_task(name="app.tasks.copywriter.write_listing")
def write_listing(job_id: int) -> dict:
    """
    Generate listing copy (title, description, highlights, tags) for a snap job.

    This task:
    1. Retrieves the SnapJob with vision and pricing data
    2. Uses AI/templates to generate:
        - Compelling title
        - Detailed description
        - Bullet point highlights
        - Search tags
    3. Stores results in SnapJob.meta.copy and updates suggested fields

    Args:
        job_id: The SnapJob ID to process

    Returns:
        dict with status and generated copy
    """
    with get_session() as session:
        job = session.get(SnapJob, job_id)
        if not job:
            return {"error": "job not found", "job_id": job_id}

        # Get vision and pricing data from meta
        vision_data = job.meta.get("vision", {}) if job.meta else {}
        pricing_data = job.meta.get("pricing", {}) if job.meta else {}

        category = vision_data.get("category") or job.detected_category
        attributes = vision_data.get("attributes") or job.detected_attributes or {}
        condition = vision_data.get("condition") or job.condition_guess

        if not category:
            # Can't write copy without category
            if not job.meta:
                job.meta = {}
            job.meta["copy"] = {
                "error": "No category available for copywriting",
                "title": "Untitled Item",
                "description": "",
                "bullet_highlights": [],
                "tags": [],
            }
            session.commit()
            return {"status": "error", "message": "No category available"}

        try:
            # Generate listing using existing auto_write module
            item_data = {
                "category": category,
                "attributes": attributes,
                "condition": condition,
            }
            title, description = generate_listing(item_data)

            # Extract bullet highlights from description
            highlights = extract_highlights(description, max_highlights=5)

            # Generate tags
            tags = generate_tags(category, attributes, condition)

            # Add pricing info to description if available
            price_suggested = pricing_data.get("price_suggested")
            if price_suggested:
                pricing_note = f"\n\nSuggested price: ${price_suggested:.2f}"
                if pricing_data.get("price_low") and pricing_data.get("price_high"):
                    pricing_note += f" (typical range: ${pricing_data['price_low']:.2f} - ${pricing_data['price_high']:.2f})"
                # Note: We add to metadata but don't include in final description
                # Seller can see pricing separately

            # Prepare copy metadata
            copy_data = {
                "title": title,
                "description": description,
                "bullet_highlights": highlights,
                "tags": tags,
                "word_count": len(description.split()) if description else 0,
            }

            # Store in job.meta.copy
            if not job.meta:
                job.meta = {}
            job.meta["copy"] = copy_data

            # Update the main suggested fields for backward compatibility
            job.suggested_title = title
            job.title_suggestion = title
            job.suggested_description = description
            job.description_suggestion = description

            session.commit()

            return {
                "status": "success",
                "job_id": job_id,
                "copy": copy_data,
            }

        except Exception as e:
            # Store error in job metadata
            if not job.meta:
                job.meta = {}
            job.meta["copy"] = {
                "error": str(e),
                "title": "",
                "description": "",
                "bullet_highlights": [],
                "tags": [],
            }
            session.commit()

            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e),
            }
