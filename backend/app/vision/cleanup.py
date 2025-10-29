from __future__ import annotations

from typing import List, Tuple

from app.seller.images import batch_cleanup


def preprocess_images(images: List[str]) -> Tuple[List[str], List[dict]]:
    """Shared entry point for the vision pipeline to clean images."""
    return batch_cleanup(images)
