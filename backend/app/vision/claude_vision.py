"""Vision analysis using Claude's vision capabilities."""

from __future__ import annotations

import base64
import logging
from typing import Dict, List, Tuple

import anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _load_image_as_base64(image_path: str) -> str:
    """Load an image file and convert to base64."""
    try:
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to load image {image_path}: {e}")
        return ""


def analyze_items_with_claude(image_paths: List[str]) -> Tuple[str, Dict]:
    """
    Analyze item images using Claude's vision capabilities.

    Returns:
        Tuple of (category, attributes_dict)
    """
    if not settings.anthropic_api_key:
        logger.warning("Claude API key not configured, using fallback detection")
        return "unknown", {}

    if not image_paths:
        return "unknown", {}

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Build message with all images
        content = [
            {
                "type": "text",
                "text": """Analyze these images and identify the item(s) being sold. Provide:
1. Main category (e.g., "furniture", "electronics", "decor", "kitchen", "home improvement")
2. Specific item type (e.g., "sectional sofa", "coffee table", "desk lamp")
3. Estimated condition (poor/fair/good/great/excellent) based on visible wear
4. Key attributes (color, material, estimated size/dimensions if visible)
5. Notable features or damage

Format your response as JSON with keys: category, item_type, condition, attributes, notes
Example:
{"category": "furniture", "item_type": "sectional sofa", "condition": "great", "attributes": {"color": "gray", "material": "fabric", "size": "L-shaped"}, "notes": "Minimal wear, clean condition"}"""
            }
        ]

        # Add images to the message
        for image_path in image_paths:
            image_data = _load_image_as_base64(image_path)
            if image_data:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data,
                    },
                })

        if len(content) == 1:
            # No images loaded successfully
            return "unknown", {}

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": content}],
        )

        response_text = message.content[0].text

        # Parse the JSON response
        import json
        try:
            data = json.loads(response_text)
            category = data.get("category", "unknown").lower()
            item_type = data.get("item_type", "")
            condition = data.get("condition", "good").lower()
            attributes = data.get("attributes", {})
            notes = data.get("notes", "")

            # Enhance attributes with parsed data
            enhanced_attributes = {
                "item_type": item_type,
                "condition": condition,
                "notes": notes,
                **attributes
            }

            logger.info(f"Detected item: {item_type} ({category}), condition: {condition}")
            return category, enhanced_attributes

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Claude response as JSON: {response_text}")
            return "unknown", {"raw_response": response_text}

    except Exception as e:
        logger.error(f"Claude vision analysis failed: {e}")
        return "unknown", {}


def estimate_price_with_claude(category: str, attributes: Dict) -> float:
    """Estimate listing price based on item analysis."""
    if not settings.anthropic_api_key:
        return 0

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        prompt = f"""Based on the following item details, estimate a fair market value for selling this item locally (on eBay, Facebook Marketplace, or similar).

Category: {category}
Attributes: {attributes}

Consider:
- Item condition
- Market demand
- Similar listings
- Local market (San Jose, CA area)

Respond with ONLY a single number (the price in USD, no $ sign, no explanation).
Example: 250"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()

        # Try to extract a number from the response
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', response_text)
        if numbers:
            price = float(numbers[0])
            logger.info(f"Estimated price for {category}: ${price}")
            return price

        return 0

    except Exception as e:
        logger.error(f"Price estimation failed: {e}")
        return 0
