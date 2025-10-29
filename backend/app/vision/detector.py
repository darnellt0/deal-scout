from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from app.config import get_settings

settings = get_settings()

KEYWORD_TO_CATEGORY = {
    "couch": "couch",
    "sofa": "couch",
    "sectional": "couch",
    "kitchen": "kitchen island",
    "island": "kitchen island",
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


def detect_item(vision_labels: List[str], captions: List[str]) -> Tuple[str, Dict]:
    if not settings.vision_enabled:
        return "unknown", {}

    category, attributes = detect_from_text(captions)
    if category == "unknown" and vision_labels:
        for label in vision_labels:
            normalized = label.lower()
            if normalized in KEYWORD_TO_CATEGORY:
                category = KEYWORD_TO_CATEGORY[normalized]
                attributes["vision_label"] = label
                break

    return category, attributes
