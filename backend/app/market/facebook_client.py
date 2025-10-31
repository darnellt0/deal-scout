"""Facebook Marketplace API client for posting and managing listings."""

import httpx
import logging
from typing import Dict, List, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class FacebookMarketplaceClient:
    """Client for Facebook Marketplace API operations."""

    # Facebook Graph API version
    API_VERSION = "v18.0"

    # Category mapping from our system to Facebook
    CATEGORY_MAPPING = {
        "electronics": "3000",
        "furniture": "3001",
        "home_appliances": "3002",
        "clothing": "3003",
        "shoes": "3004",
        "books": "3005",
        "sports": "3006",
        "toys": "3007",
        "collectibles": "3008",
        "garden": "3009",
        "other": "3010",
    }

    # Condition mapping
    CONDITION_MAPPING = {
        "new": "NEW",
        "like_new": "LIKE_NEW",
        "good": "USED",
        "fair": "USED",
        "poor": "USED",
    }

    def __init__(self, access_token: str, page_id: str):
        """
        Initialize Facebook Marketplace client.

        Args:
            access_token: Facebook page access token
            page_id: Facebook page ID for marketplace posting
        """
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = f"https://graph.facebook.com/{self.API_VERSION}"

    async def post_item(
        self,
        title: str,
        description: str,
        price: float,
        images: List[str],
        category: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> Optional[str]:
        """
        Post an item to Facebook Marketplace.

        Args:
            title: Item title
            description: Item description
            price: Item price in USD
            images: List of image URLs
            category: Item category
            condition: Item condition (new, like_new, good, fair, poor)

        Returns:
            Facebook marketplace listing ID if successful, None otherwise
        """
        try:
            # Upload images first
            photo_ids = []
            for image_url in images:
                if image_url:  # Skip empty URLs
                    photo_id = await self._upload_photo(image_url)
                    if photo_id:
                        photo_ids.append(photo_id)

            # Map category and condition
            fb_category = self.CATEGORY_MAPPING.get(
                category.lower() if category else "other",
                "3010"  # Default to "other"
            )

            fb_condition = self.CONDITION_MAPPING.get(
                condition.lower() if condition else "good",
                "USED"
            )

            # Create marketplace listing
            url = f"{self.base_url}/{self.page_id}/feed"

            # Facebook marketplace listing payload
            payload = {
                "message": f"{title}\n\n{description}",
                "type": "MARKETPLACE_LISTING",
                "marketplace_listing": {
                    "name": title,
                    "description": description,
                    "price_currency": "USD",
                    "price_amount": int(price * 100),  # Convert to cents
                    "category_specific_fields": {
                        "category": fb_category,
                        "condition": fb_condition,
                    },
                },
                "access_token": self.access_token,
            }

            # Add photos if available
            if photo_ids:
                payload["marketplace_listing"]["photo_ids"] = photo_ids

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            result = response.json()
            listing_id = result.get("id")

            if listing_id:
                logger.info(
                    f"Successfully posted item to Facebook Marketplace: {listing_id}"
                )
                return listing_id
            else:
                logger.error(f"No listing ID in Facebook response: {result}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error posting item to Facebook: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting item to Facebook: {e}")
            return None

    async def _upload_photo(self, image_url: str) -> Optional[str]:
        """
        Upload a photo to Facebook.

        Args:
            image_url: URL of image to upload

        Returns:
            Photo ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{self.page_id}/photos"

            params = {
                "url": image_url,
                "access_token": self.access_token,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)
                response.raise_for_status()

            result = response.json()
            photo_id = result.get("id")

            if photo_id:
                logger.debug(f"Successfully uploaded photo to Facebook: {photo_id}")
                return photo_id
            else:
                logger.warning(f"No photo ID in Facebook response: {result}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"Failed to upload photo to Facebook: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading photo: {e}")
            return None

    async def update_item(
        self,
        listing_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        availability: Optional[str] = None,
    ) -> bool:
        """
        Update an existing Facebook Marketplace listing.

        Args:
            listing_id: Facebook listing ID
            title: New title
            description: New description
            price: New price in USD
            availability: "AVAILABLE" or "SOLD"

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/{listing_id}"

            payload = {"access_token": self.access_token}

            # Add optional fields
            if title:
                payload["title"] = title
            if description:
                payload["description"] = description
            if price is not None:
                payload["price"] = str(int(price * 100))  # In cents
            if availability:
                payload["availability"] = availability

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            logger.info(f"Successfully updated Facebook listing: {listing_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to update Facebook listing: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating Facebook listing: {e}")
            return False

    async def delete_item(self, listing_id: str) -> bool:
        """
        Delete a listing from Facebook Marketplace.

        Args:
            listing_id: Facebook listing ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/{listing_id}"

            params = {"access_token": self.access_token}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(url, params=params)
                response.raise_for_status()

            logger.info(f"Successfully deleted Facebook listing: {listing_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to delete Facebook listing: {e}")
            if hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting Facebook listing: {e}")
            return False

    async def get_listing(self, listing_id: str) -> Optional[Dict]:
        """
        Get details of a Facebook Marketplace listing.

        Args:
            listing_id: Facebook listing ID

        Returns:
            Listing data if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{listing_id}"

            params = {
                "fields": "id,name,description,price,availability,image,created_time",
                "access_token": self.access_token,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

            result = response.json()
            logger.debug(f"Retrieved Facebook listing: {listing_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Failed to get Facebook listing: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting Facebook listing: {e}")
            return None

    async def search_listings(self, query: str, limit: int = 10) -> Optional[List[Dict]]:
        """
        Search for marketplace listings.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of listings if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/marketplace_search"

            params = {
                "q": query,
                "type": "marketplace_listing",
                "limit": limit,
                "access_token": self.access_token,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

            result = response.json()
            listings = result.get("data", [])
            logger.debug(f"Found {len(listings)} Facebook listings for query: {query}")
            return listings

        except httpx.HTTPError as e:
            logger.error(f"Failed to search Facebook listings: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error searching listings: {e}")
            return None

    def get_listing_url(self, listing_id: str) -> str:
        """
        Get the direct URL to a Facebook Marketplace listing.

        Args:
            listing_id: Facebook listing ID

        Returns:
            Facebook Marketplace URL
        """
        return f"https://www.facebook.com/marketplace/item/{listing_id}/"
