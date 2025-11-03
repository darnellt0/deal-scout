from __future__ import annotations

import logging
from collections import Counter
from typing import Dict, List, Tuple

from app.config import get_settings
from app.vision.claude_vision import analyze_items_with_claude

logger = logging.getLogger(__name__)
settings = get_settings()

KEYWORD_TO_CATEGORY = {
    "couch": "furniture",
    "sofa": "furniture",
    "sectional": "furniture",
    "kitchen": "kitchen",
    "island": "kitchen",
    "table": "furniture",
    "desk": "furniture",
    "chair": "furniture",
    "bed": "furniture",
    "lamp": "lighting",
    "light": "lighting",
}


def detect_from_text(captions: List[str]) -> Tuple[str, Dict]:
    tokens = []
    for caption in captions:
        tokens.extend(caption.lower().split())
    counts = Counter(tokens)

    best_category = "unknown"
    attributes: Dict[str, str] = {}

    for keyword, category in KEYWORD_TO_CATEGORY.items():
        if counts[keyword]:
            best_category = category
            attributes["keyword"] = keyword
            break

    return best_category, attributes


def detect_item(image_paths: List[str], captions: List[str] = None) -> Tuple[str, Dict]:
    """
    Detect items from images using Claude vision API if available.
    Falls back to keyword-based detection if Claude is not configured.

    Args:
        image_paths: List of image file paths to analyze
        captions: Optional list of image captions (for backward compatibility)

    Returns:
        Tuple of (category, attributes_dict)
    """
    if not settings.vision_enabled:
        return "unknown", {}

    # Try Claude vision API first if configured
    if settings.anthropic_api_key:
        category, attributes = analyze_items_with_claude(image_paths)
        if category != "unknown":
            return category, attributes

    # Fallback to text-based detection
    if captions:
        return detect_from_text(captions)

    return "unknown", {}
