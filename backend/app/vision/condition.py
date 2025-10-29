from __future__ import annotations

from typing import Dict, List

CONDITION_HINTS = {
    "scratched": "fair",
    "damaged": "poor",
    "worn": "fair",
    "clean": "great",
    "pristine": "excellent",
    "unused": "excellent",
}


def estimate_condition(captions: List[str], metadata: Dict) -> str:
    text = " ".join(captions).lower()
    for keyword, condition in CONDITION_HINTS.items():
        if keyword in text:
            return condition
    return metadata.get("condition_hint", "good")
