"""Offerup API client for posting and managing listings."""

import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OfferupClient:
    """Client for Offerup API operations."""

    # Offerup API version
    API_VERSION = "v3"

    # Category mapping from our system to Offerup
    # Offerup uses category IDs
    CATEGORY_MAPPING = {
        "electronics": "1000",
        "furniture": "2000",
        "home_appliances": "3000",
        "clothing": "4000",
        "shoes": "4100",
        "books": "5000",
        "sports": "6000",
        "toys": "7000",
        "collectibles": "8000",
        "garden": "9000",
        "other": "9999",
    }

    # Condition mapping to Offerup format
    CONDITION_MAPPING = {
        "new": "new",
        "like_new": "like_new",
        "good": "used_good",
        "fair": "used_fair",
        "poor": "used_poor",
    }

    def __init__(self, access_token: str):
        """
        Initialize Offerup API client.

        Args:
            access_token: Offerup OAuth access token
        """
        self.access_token = access_token
        self.base_url = f"https://api.offerup.com/api/{self.API_VERSION}"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def post_item(
        self,
        title: str,
        description: str,
        price: float,
        images: List[str],
        latitude: float,
        longitude: float,
        category: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> Optional[str]:
        """
        Post an item to Offerup.

        Args:
            title: Item title
            description: Item description
            price: Item price in USD
            images: List of image URLs
            latitude: Seller location latitude
            longitude: Seller location longitude
            category: Item category
            condition: Item condition

        Returns:
            Offerup listing ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/listings"

            # Map category and condition
            offerup_category = self.CATEGORY_MAPPING.get(
                category.lower() if category else "other",
                "9999"  # Default to "other"
            )

            offerup_condition = self.CONDITION_MAPPING.get(
                condition.lower() if condition else "good",
                "used_good"
            )

            # Build listing payload
            payload = {
                "title": title,
                "description": description,
                "price": {
                    "amount": int(price * 100),  # In cents
                    "currency": "USD"
                },
                "category_id": offerup_category,
                "condition": offerup_condition,
                "photos": images,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                }
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()

            result = response.json()
            listing_id = result.get("id")

            if listing_id:
                logger.info(
                    f"Successfully posted item to Offerup: {listing_id}"
                )
                return listing_id
            else:
                logger.error(f"No listing ID in Offerup response: {result}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error posting item to Offerup: {e}")
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting item to Offerup: {e}")
            return None

    async def update_item(
        self,
        listing_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        condition: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an existing Offerup listing.

        Args:
            listing_id: Offerup listing ID
            title: New title
            description: New description
            price: New price in USD
            condition: New condition
            images: New images

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/listings/{listing_id}"

            payload = {}

            # Add optional fields
            if title:
                payload["title"] = title
            if description:
                payload["description"] = description
            if price is not None:
                payload["price"] = {
                    "amount": int(price * 100),
                    "currency": "USD"
                }
            if condition:
                offerup_condition = self.CONDITION_MAPPING.get(
                    condition.lower(),
                    "used_good"
                )
                payload["condition"] = offerup_condition
            if images:
                payload["photos"] = images

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()

            logger.info(f"Successfully updated Offerup listing: {listing_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to update Offerup listing: {e}")
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating Offerup listing: {e}")
            return False

    async def delete_item(self, listing_id: str) -> bool:
        """
        Delete a listing from Offerup.

        Args:
            listing_id: Offerup listing ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/listings/{listing_id}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    url,
                    headers=self.headers
                )
                response.raise_for_status()

            logger.info(f"Successfully deleted Offerup listing: {listing_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to delete Offerup listing: {e}")
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting Offerup listing: {e}")
            return False

    async def mark_sold(self, listing_id: str) -> bool:
        """
        Mark an Offerup listing as sold.

        Args:
            listing_id: Offerup listing ID

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/listings/{listing_id}/mark_sold"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json={}
                )
                response.raise_for_status()

            logger.info(f"Successfully marked Offerup listing as sold: {listing_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to mark Offerup listing as sold: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error marking listing as sold: {e}")
            return False

    async def get_listing(self, listing_id: str) -> Optional[Dict]:
        """
        Get details of an Offerup listing.

        Args:
            listing_id: Offerup listing ID

        Returns:
            Listing data if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/listings/{listing_id}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers=self.headers
                )
                response.raise_for_status()

            result = response.json()
            logger.debug(f"Retrieved Offerup listing: {listing_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Failed to get Offerup listing: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting Offerup listing: {e}")
            return None

    async def get_my_listings(self, limit: int = 20, offset: int = 0) -> Optional[List[Dict]]:
        """
        Get all listings for the authenticated user.

        Args:
            limit: Maximum number of listings to return
            offset: Pagination offset

        Returns:
            List of listings if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/users/me/listings"

            params = {
                "limit": limit,
                "offset": offset,
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()

            result = response.json()
            listings = result.get("data", [])
            logger.debug(f"Retrieved {len(listings)} Offerup listings")
            return listings

        except httpx.HTTPError as e:
            logger.error(f"Failed to get Offerup listings: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting listings: {e}")
            return None

    def get_listing_url(self, listing_id: str) -> str:
        """
        Get the direct URL to an Offerup listing.

        Args:
            listing_id: Offerup listing ID

        Returns:
            Offerup listing URL
        """
        return f"https://www.offerup.com/item/{listing_id}"
