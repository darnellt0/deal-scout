from __future__ import annotations

import base64
import io
import logging
from typing import List, Tuple

from PIL import Image, ImageEnhance

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _decode_image(data: str) -> Image.Image:
    if data.startswith("http"):
        raise ValueError("Remote image URLs not supported in cleanup pipeline yet.")
    binary = base64.b64decode(data)
    return Image.open(io.BytesIO(binary))


def brighten_image(image: Image.Image) -> Image.Image:
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(1.2)


def cleanup_image(data: str) -> Tuple[str, dict]:
    """Return cleaned base64 image and metadata."""
    try:
        image = _decode_image(data)
        image = image.convert("RGB")
        image = brighten_image(image)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        cleaned = base64.b64encode(buffer.getvalue()).decode("utf-8")
        metadata = {"width": image.width, "height": image.height}
        return cleaned, metadata
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Image cleanup failed: %s", exc)
        return data, {"error": str(exc)}


def batch_cleanup(images: List[str]) -> Tuple[List[str], List[dict]]:
    cleaned_images = []
    metadata = []
    for image in images:
        cleaned, info = cleanup_image(image)
        cleaned_images.append(cleaned)
        metadata.append(info)
    return cleaned_images, metadata
