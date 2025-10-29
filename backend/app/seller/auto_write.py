from __future__ import annotations

import logging
from textwrap import shorten
from typing import Dict, Tuple

import openai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_listing(metadata: Dict) -> Tuple[str, str]:
    """Generate a title and description for a listing using OpenAI if available."""
    title = metadata.get("title_hint") or metadata.get("category", "Great Find").title()
    description = (
        "Quality item sourced via Deal Scout. Includes auto-generated description."
    )

    if not settings.openai_api_key:
        return shorten(title, 80), description

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
