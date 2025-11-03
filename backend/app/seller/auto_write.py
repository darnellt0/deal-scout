from __future__ import annotations

import logging
from textwrap import shorten
from typing import Dict, Tuple

import openai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_listing(metadata: Dict) -> Tuple[str, str]:
    """
    Generate a title and description for a listing.
    Uses Claude if available (preferred), falls back to OpenAI, then defaults to metadata.
    """
    # Extract metadata
    item_type = metadata.get("item_type", "")
    category = metadata.get("category", "Item")
    condition = metadata.get("condition", "")
    attributes = metadata.get("attributes", {})
    notes = metadata.get("notes", "")

    # Build a fallback title from available data
    fallback_title = item_type or category
    if condition and condition not in fallback_title.lower():
        fallback_title = f"{fallback_title} - {condition.title()}"

    default_description = (
        "Quality item sourced via Deal Scout. "
        f"Condition: {condition or 'as described'}. "
        "Ships from San Jose, CA area."
    )

    title = shorten(fallback_title, 80)
    description = default_description

    # Try Claude API first
    if settings.anthropic_api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            prompt = f"""Create a compelling marketplace listing for this item.

Item Type: {item_type}
Category: {category}
Condition: {condition}
Attributes: {attributes}
Notes: {notes}

Respond with EXACTLY this format (two lines separated by a newline):
[Title - max 80 characters]
[Description - 2-3 sentences, friendly and appealing]

Example:
Gray Sectional Sofa - Great Condition
Large, clean sectional in excellent condition. Very comfortable and well-maintained. Perfect addition to any living space!"""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text.strip()
            parts = response_text.split("\n", 1)
            if len(parts) >= 2:
                title = shorten(parts[0].strip(), 80)
                description = parts[1].strip()
                return title, description
        except Exception as exc:
            logger.info("Claude generation unavailable: %s", exc)

    # Fallback to OpenAI if Claude is not available
    if settings.openai_api_key:
        openai.api_key = settings.openai_api_key
        prompt = (
            "Create a compelling marketplace listing. "
            "Return a short title (max 80 chars) and a friendly description."
            f"\nMetadata: {metadata}"
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You write concise, upbeat marketplace copy."},
                    {"role": "user", "content": prompt},
                ],
            )
            message = response["choices"][0]["message"]["content"]
            parts = message.split("\n", 1)
            title = shorten(parts[0].strip(), 80)
            description = parts[1].strip() if len(parts) > 1 else description
        except Exception as exc:  # pragma: no cover - optional integration
            logger.info("OpenAI generation unavailable: %s", exc)

    return title, description
