"""Vision analysis using Google Gemini's vision capabilities."""

from __future__ import annotations

import base64
import logging
from typing import Dict, List, Tuple

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


def analyze_items_with_gemini(image_paths: List[str]) -> Tuple[str, Dict]:
    """
    Analyze item images using Google Gemini's vision capabilities.

    Returns:
        Tuple of (category, attributes_dict)
    """
    if not settings.google_api_key:
        logger.warning("Google Gemini API key not configured, using fallback detection")
        return "unknown", {}

    if not image_paths:
        return "unknown", {}

    try:
        import google.generativeai as genai

        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)

        # Use Gemini 1.5 Pro for vision tasks (best for multimodal)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')

        # Build prompt
        prompt = """Analyze these images and identify the item(s) being sold. Provide:
1. Main category (e.g., "furniture", "electronics", "decor", "kitchen", "home improvement")
2. Specific item type (e.g., "sectional sofa", "coffee table", "desk lamp")
3. Estimated condition (poor/fair/good/great/excellent) based on visible wear
4. Key attributes (color, material, estimated size/dimensions if visible)
5. Notable features or damage

Format your response as JSON with keys: category, item_type, condition, attributes, notes
Example:
{"category": "furniture", "item_type": "sectional sofa", "condition": "great", "attributes": {"color": "gray", "material": "fabric", "size": "L-shaped"}, "notes": "Minimal wear, clean condition"}"""

        # Prepare images for Gemini
        import PIL.Image
        images = []
        for image_path in image_paths:
            try:
                img = PIL.Image.open(image_path)
                images.append(img)
            except Exception as e:
                logger.warning(f"Failed to load image {image_path}: {e}")
                continue

        if not images:
            logger.warning("No images successfully loaded")
            return "unknown", {}

        # Generate content with prompt + images
        response = model.generate_content([prompt] + images)
        response_text = response.text

        # Parse the JSON response
        import json
        try:
            # Extract JSON from response (Gemini might wrap it in markdown)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

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

            logger.info(f"Gemini detected item: {item_type} ({category}), condition: {condition}")
            return category, enhanced_attributes

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Gemini response as JSON: {response_text}")
            return "unknown", {"raw_response": response_text}

    except ImportError:
        logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
        return "unknown", {}
    except Exception as e:
        logger.error(f"Gemini vision analysis failed: {e}")
        return "unknown", {}


def estimate_price_with_gemini(category: str, attributes: Dict) -> float:
    """Estimate listing price based on item analysis using Gemini."""
    if not settings.google_api_key:
        return 0

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')  # Use Flash for text-only tasks

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

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Try to extract a number from the response
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', response_text)
        if numbers:
            price = float(numbers[0])
            logger.info(f"Gemini estimated price for {category}: ${price}")
            return price

        return 0

    except ImportError:
        logger.error("google-generativeai package not installed")
        return 0
    except Exception as e:
        logger.error(f"Gemini price estimation failed: {e}")
        return 0
