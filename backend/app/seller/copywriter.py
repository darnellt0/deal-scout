"""
Copywriter module for generating marketplace listing copy.

This module provides AI-powered text generation for listing titles, descriptions,
bullet point highlights, and tags to optimize marketplace listings.
"""
from __future__ import annotations

import json
import logging
from textwrap import shorten
from typing import Dict, List, Optional, Tuple

import openai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_copy(
    category: str,
    attributes: Dict,
    condition: str,
    price: Optional[float] = None,
    photos_count: int = 0,
) -> Dict[str, any]:
    """
    Generate comprehensive listing copy including title, description, highlights, and tags.

    Args:
        category: Item category (e.g., "couch", "laptop", "shoes")
        attributes: Dict of item attributes (brand, model, color, size, etc.)
        condition: Item condition (e.g., "excellent", "good", "fair")
        price: Suggested price (optional, for context)
        photos_count: Number of photos available

    Returns:
        Dict with keys: title, description, highlights (list), tags (list), confidence
    """
    # Build fallback response
    fallback_title = _build_fallback_title(category, attributes)
    fallback_description = _build_fallback_description(
        category, attributes, condition, price
    )
    fallback_highlights = _build_fallback_highlights(attributes, condition)
    fallback_tags = _build_fallback_tags(category, attributes)

    fallback_response = {
        "title": fallback_title,
        "description": fallback_description,
        "highlights": fallback_highlights,
        "tags": fallback_tags,
        "confidence": 0.5,
    }

    # Return fallback if no OpenAI API key
    if not settings.openai_api_key:
        logger.info("OpenAI API key not configured, using fallback copy")
        return fallback_response

    # Generate AI-powered copy
    try:
        openai.api_key = settings.openai_api_key

        # Build context for the AI
        context = _build_context(category, attributes, condition, price, photos_count)

        # Create the prompt
        system_prompt = """You are an expert marketplace copywriter. Your job is to create
compelling, accurate, and SEO-optimized listing copy that sells items quickly at fair prices.

Write clear, honest descriptions that highlight value and build buyer confidence.
Use natural language that appeals to your target marketplace audience.
Focus on what makes the item desirable and worth purchasing.

Return your response as a valid JSON object with these exact keys:
{
  "title": "80 character max, keyword-rich title",
  "description": "2-4 paragraph description with details and benefits",
  "highlights": ["3-5 bullet points of key features/benefits"],
  "tags": ["5-10 relevant search tags"]
}"""

        user_prompt = f"""Create a compelling marketplace listing for this item:

Category: {category}
Attributes: {json.dumps(attributes, indent=2)}
Condition: {condition}
{f'Suggested Price: ${price:.2f}' if price else ''}
{f'Photos Available: {photos_count}' if photos_count else ''}

Generate copy that:
- Has a clear, descriptive title under 80 characters
- Includes a detailed description highlighting value and condition
- Lists 3-5 key features as bullet points
- Suggests 5-10 relevant search tags

Return only the JSON object, no other text."""

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        message = response["choices"][0]["message"]["content"].strip()

        # Parse JSON response
        try:
            copy_data = json.loads(message)

            # Validate and clean the response
            title = shorten(copy_data.get("title", fallback_title), 80)
            description = copy_data.get("description", fallback_description)
            highlights = copy_data.get("highlights", fallback_highlights)
            tags = copy_data.get("tags", fallback_tags)

            # Ensure highlights and tags are lists
            if not isinstance(highlights, list):
                highlights = fallback_highlights
            if not isinstance(tags, list):
                tags = fallback_tags

            # Limit highlights to 5 items
            highlights = highlights[:5]
            # Limit tags to 10 items
            tags = tags[:10]

            return {
                "title": title,
                "description": description,
                "highlights": highlights,
                "tags": tags,
                "confidence": 0.9,
            }

        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI JSON response, using fallback")
            # Try to extract title and description from unstructured response
            lines = message.split("\n")
            if len(lines) >= 2:
                fallback_response["title"] = shorten(lines[0].strip(), 80)
                fallback_response["description"] = "\n".join(lines[1:]).strip()
                fallback_response["confidence"] = 0.6
            return fallback_response

    except Exception as exc:
        logger.warning("OpenAI generation failed: %s", exc)
        return fallback_response


def _build_context(
    category: str,
    attributes: Dict,
    condition: str,
    price: Optional[float],
    photos_count: int,
) -> str:
    """Build a context string for the AI prompt."""
    context_parts = [f"Category: {category}"]

    if attributes:
        for key, value in attributes.items():
            context_parts.append(f"{key.title()}: {value}")

    context_parts.append(f"Condition: {condition}")

    if price:
        context_parts.append(f"Price: ${price:.2f}")

    if photos_count:
        context_parts.append(f"Photos: {photos_count}")

    return "\n".join(context_parts)


def _build_fallback_title(category: str, attributes: Dict) -> str:
    """Build a basic fallback title from category and attributes."""
    parts = []

    # Add brand if available
    if "brand" in attributes:
        parts.append(str(attributes["brand"]))

    # Add model if available
    if "model" in attributes:
        parts.append(str(attributes["model"]))

    # Add category
    parts.append(category.title())

    # Add color if available and not too long yet
    if "color" in attributes and len(" ".join(parts)) < 60:
        parts.append(f"- {attributes['color']}")

    title = " ".join(parts) if parts else "Quality Item for Sale"
    return shorten(title, 80)


def _build_fallback_description(
    category: str, attributes: Dict, condition: str, price: Optional[float]
) -> str:
    """Build a basic fallback description."""
    parts = [
        f"Quality {category} in {condition} condition.",
        "",
        "Item Details:",
    ]

    # Add key attributes
    if attributes:
        for key, value in attributes.items():
            if key in ["brand", "model", "color", "size", "material"]:
                parts.append(f"- {key.title()}: {value}")

    parts.append("")
    parts.append("Sourced and verified via Deal Scout.")

    if price:
        parts.append(f"Competitively priced at ${price:.2f}.")

    parts.append("")
    parts.append("Please review photos and contact with any questions.")

    return "\n".join(parts)


def _build_fallback_highlights(attributes: Dict, condition: str) -> List[str]:
    """Build basic fallback highlights."""
    highlights = [f"Condition: {condition.title()}"]

    if "brand" in attributes:
        highlights.append(f"Brand: {attributes['brand']}")

    if "model" in attributes:
        highlights.append(f"Model: {attributes['model']}")

    if "color" in attributes:
        highlights.append(f"Color: {attributes['color']}")

    if "size" in attributes:
        highlights.append(f"Size: {attributes['size']}")

    # Ensure we have at least 3 highlights
    while len(highlights) < 3:
        highlights.append("Quality item, ready to ship")

    return highlights[:5]


def _build_fallback_tags(category: str, attributes: Dict) -> List[str]:
    """Build basic fallback tags."""
    tags = [category.lower()]

    if "brand" in attributes:
        tags.append(str(attributes["brand"]).lower())

    if "model" in attributes:
        tags.append(str(attributes["model"]).lower())

    if "color" in attributes:
        tags.append(str(attributes["color"]).lower())

    if "material" in attributes:
        tags.append(str(attributes["material"]).lower())

    # Add generic tags
    tags.extend(["quality", "deal", "resale"])

    return tags[:10]


# Legacy compatibility function
def generate_listing(metadata: Dict) -> Tuple[str, str]:
    """
    Legacy function for backwards compatibility.
    Generates only title and description.

    Args:
        metadata: Dict with category, attributes, condition, etc.

    Returns:
        Tuple of (title, description)
    """
    category = metadata.get("category", "item")
    attributes = metadata.get("attributes", {})
    condition = metadata.get("condition", "good")
    price = metadata.get("price")

    copy_data = generate_copy(category, attributes, condition, price)

    return copy_data["title"], copy_data["description"]
