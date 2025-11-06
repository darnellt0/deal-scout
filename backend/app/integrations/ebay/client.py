"""eBay REST API client for OAuth and inventory management.

This module provides a comprehensive client for interacting with eBay's
REST APIs, including:
- OAuth 2.0 authentication flow
- Token management and refresh
- Inventory Item API
- Offer API
- Taxonomy API (category suggestion and aspects)
- Location API
- Account policies API
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from .exceptions import (
    EbayAuthenticationError,
    EbayAuthorizationError,
    EbayConflictError,
    EbayIntegrationError,
    EbayRateLimitError,
    EbayResourceNotFoundError,
    EbayValidationError,
)

logger = logging.getLogger(__name__)


class EbayClient:
    """eBay REST API client with OAuth and inventory management.

    Handles authentication, token management, and all API calls needed
    for cross-posting listings to eBay.
    """

    # Base URLs
    SANDBOX_API_URL = "https://api.sandbox.ebay.com"
    PRODUCTION_API_URL = "https://api.ebay.com"
    SANDBOX_AUTH_URL = "https://auth.sandbox.ebay.com"
    PRODUCTION_AUTH_URL = "https://auth.ebay.com"

    # OAuth scopes needed for cross-posting
    DEFAULT_SCOPES = [
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.account",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    ]

    def __init__(self, env: Optional[str] = None):
        """Initialize eBay client.

        Args:
            env: Environment to use ('sandbox' or 'production'). If None, uses settings.
        """
        self.settings = get_settings()
        self.env = env or self.settings.ebay_env

        # Set base URLs based on environment
        if self.env == "production":
            self.api_base = self.PRODUCTION_API_URL
            self.auth_base = self.PRODUCTION_AUTH_URL
        else:
            self.api_base = self.SANDBOX_API_URL
            self.auth_base = self.SANDBOX_AUTH_URL

        self.client_id = self.settings.ebay_client_id
        self.client_secret = self.settings.ebay_client_secret
        self.redirect_uri = self.settings.ebay_redirect_uri
        self.marketplace_id = self.settings.ebay_marketplace_id

        logger.info(f"Initialized eBay client for {self.env} environment")

    def _get_basic_auth_header(self) -> str:
        """Generate Basic Auth header for OAuth token requests.

        Returns:
            Base64-encoded 'client_id:client_secret' string
        """
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def build_consent_url(
        self,
        state: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ) -> str:
        """Build eBay OAuth consent URL.

        Args:
            state: Optional state parameter for CSRF protection
            scopes: List of OAuth scopes. Uses DEFAULT_SCOPES if not provided.

        Returns:
            Full consent URL to redirect user to
        """
        scopes = scopes or self.DEFAULT_SCOPES
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
        }
        if state:
            params["state"] = state

        url = f"{self.auth_base}/oauth2/authorize?{urlencode(params)}"
        logger.info(f"Built consent URL with scopes: {scopes}")
        return url

    async def exchange_code_for_tokens(
        self, code: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Dictionary containing:
                - access_token: Bearer token for API requests
                - refresh_token: Token for refreshing access token
                - expires_at: Datetime when access token expires

        Raises:
            EbayAuthenticationError: If token exchange fails
        """
        url = f"{self.auth_base}/identity/v1/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": self._get_basic_auth_header(),
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data)
                response.raise_for_status()
                result = response.json()

                # Calculate expiration time
                expires_in = result.get("expires_in", 7200)  # Default 2 hours
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                logger.info(f"Successfully exchanged code for tokens (expires in {expires_in}s)")
                return {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token"),
                    "expires_at": expires_at,
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to exchange code: {e.response.text}")
            raise EbayAuthenticationError(
                "Failed to exchange authorization code for tokens",
                status_code=e.response.status_code,
                response_body=e.response.json() if e.response.text else {},
            )
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise EbayAuthenticationError(f"Token exchange failed: {str(e)}")

    async def refresh_access_token(
        self, refresh_token: str
    ) -> Dict[str, Any]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary containing:
                - access_token: New bearer token
                - expires_at: When new token expires

        Raises:
            EbayAuthenticationError: If refresh fails
        """
        url = f"{self.auth_base}/identity/v1/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": self._get_basic_auth_header(),
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(self.DEFAULT_SCOPES),
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data)
                response.raise_for_status()
                result = response.json()

                expires_in = result.get("expires_in", 7200)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                logger.info(f"Successfully refreshed access token (expires in {expires_in}s)")
                return {
                    "access_token": result["access_token"],
                    "expires_at": expires_at,
                }
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to refresh token: {e.response.text}")
            raise EbayAuthenticationError(
                "Failed to refresh access token",
                status_code=e.response.status_code,
                response_body=e.response.json() if e.response.text else {},
            )
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise EbayAuthenticationError(f"Token refresh failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        path: str,
        access_token: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_on_401: bool = True,
        refresh_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make authenticated API request with automatic token refresh.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            access_token: Current access token
            data: Request body (for POST/PUT)
            params: Query parameters
            retry_on_401: Whether to retry with refreshed token on 401
            refresh_token: Refresh token for automatic retry

        Returns:
            Response JSON data

        Raises:
            Various EbayIntegrationError subclasses based on status code
        """
        url = f"{self.api_base}{path}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data, params=params)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data, params=params)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle successful responses
                if 200 <= response.status_code < 300:
                    # Some DELETE requests return 204 No Content
                    if response.status_code == 204:
                        return {}
                    return response.json() if response.text else {}

                # Handle 401 Unauthorized - try refresh if available
                if response.status_code == 401 and retry_on_401 and refresh_token:
                    logger.info("Access token expired, refreshing...")
                    new_tokens = await self.refresh_access_token(refresh_token)
                    # Retry with new token (no retry on second attempt)
                    return await self._make_request(
                        method, path, new_tokens["access_token"], data, params,
                        retry_on_401=False,
                    )

                # Handle other errors
                self._raise_for_status(response)

        except httpx.HTTPStatusError as e:
            self._raise_for_status(e.response)
        except Exception as e:
            if isinstance(e, EbayIntegrationError):
                raise
            logger.error(f"Unexpected error in API request: {e}")
            raise EbayIntegrationError(f"API request failed: {str(e)}")

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise appropriate exception based on response status code.

        Args:
            response: HTTP response from eBay API

        Raises:
            Specific EbayIntegrationError subclass based on status code
        """
        try:
            body = response.json() if response.text else {}
        except Exception:
            body = {"message": response.text}

        error_message = body.get("message") or body.get("error_description") or "Unknown error"
        errors = body.get("errors", [])
        if errors and isinstance(errors, list):
            error_message = "; ".join([e.get("message", "") for e in errors if e.get("message")])

        status_code = response.status_code

        if status_code == 400:
            raise EbayValidationError(
                f"Validation error: {error_message}",
                status_code=status_code,
                response_body=body,
            )
        elif status_code == 401:
            raise EbayAuthenticationError(
                f"Authentication failed: {error_message}",
                status_code=status_code,
                response_body=body,
            )
        elif status_code == 403:
            raise EbayAuthorizationError(
                f"Authorization failed: {error_message}",
                status_code=status_code,
                response_body=body,
            )
        elif status_code == 404:
            raise EbayResourceNotFoundError(
                f"Resource not found: {error_message}",
                status_code=status_code,
                response_body=body,
            )
        elif status_code == 409:
            raise EbayConflictError(
                f"Conflict: {error_message}",
                status_code=status_code,
                response_body=body,
            )
        elif status_code == 422:
            raise EbayValidationError(
                f"Unprocessable entity: {error_message}",
                status_code=status_code,
                response_body=body,
            )
        elif status_code == 429:
            raise EbayRateLimitError(
                f"Rate limit exceeded: {error_message}",
                status_code=status_code,
                response_body=body,
            )
        else:
            raise EbayIntegrationError(
                f"eBay API error: {error_message}",
                status_code=status_code,
                response_body=body,
            )

    # ========================================================================
    # Account Policies API
    # ========================================================================

    async def get_policies(
        self, access_token: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all account policies (payment, fulfillment, return).

        Args:
            access_token: Valid access token

        Returns:
            Dictionary with keys:
                - payment: List of payment policies
                - fulfillment: List of fulfillment policies
                - return: List of return policies
        """
        logger.info("Fetching account policies from eBay")

        payment = await self._make_request(
            "GET",
            "/sell/account/v1/payment_policy",
            access_token,
            params={"marketplace_id": self.marketplace_id},
        )

        fulfillment = await self._make_request(
            "GET",
            "/sell/account/v1/fulfillment_policy",
            access_token,
            params={"marketplace_id": self.marketplace_id},
        )

        return_policy = await self._make_request(
            "GET",
            "/sell/account/v1/return_policy",
            access_token,
            params={"marketplace_id": self.marketplace_id},
        )

        result = {
            "payment": payment.get("paymentPolicies", []),
            "fulfillment": fulfillment.get("fulfillmentPolicies", []),
            "return": return_policy.get("returnPolicies", []),
        }

        logger.info(
            f"Found {len(result['payment'])} payment, "
            f"{len(result['fulfillment'])} fulfillment, "
            f"{len(result['return'])} return policies"
        )
        return result

    # ========================================================================
    # Location API
    # ========================================================================

    async def create_location(
        self,
        access_token: str,
        location_key: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create inventory location.

        Args:
            access_token: Valid access token
            location_key: Unique location identifier
            payload: Location data (address, name, etc.)

        Returns:
            Created location data
        """
        logger.info(f"Creating inventory location: {location_key}")
        return await self._make_request(
            "POST",
            f"/sell/inventory/v1/location/{location_key}",
            access_token,
            data=payload,
        )

    # ========================================================================
    # Inventory Item API
    # ========================================================================

    async def upsert_inventory_item(
        self,
        access_token: str,
        sku: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create or update inventory item.

        Args:
            access_token: Valid access token
            sku: Stock Keeping Unit (unique item identifier)
            payload: Inventory item data (product details, availability, etc.)

        Returns:
            Created/updated inventory item data
        """
        logger.info(f"Upserting inventory item with SKU: {sku}")
        return await self._make_request(
            "PUT",
            f"/sell/inventory/v1/inventory_item/{sku}",
            access_token,
            data=payload,
        )

    # ========================================================================
    # Offer API
    # ========================================================================

    async def create_offer(
        self,
        access_token: str,
        payload: Dict[str, Any],
    ) -> str:
        """Create offer for inventory item.

        Args:
            access_token: Valid access token
            payload: Offer data (SKU, price, category, policies, etc.)

        Returns:
            Created offer ID
        """
        logger.info(f"Creating offer for SKU: {payload.get('sku')}")
        response = await self._make_request(
            "POST",
            "/sell/inventory/v1/offer",
            access_token,
            data=payload,
        )
        offer_id = response.get("offerId")
        logger.info(f"Created offer: {offer_id}")
        return offer_id

    async def publish_offer(
        self,
        access_token: str,
        offer_id: str,
    ) -> Dict[str, Any]:
        """Publish offer to marketplace.

        Args:
            access_token: Valid access token
            offer_id: Offer ID to publish

        Returns:
            Dictionary containing:
                - listingId: eBay listing ID
                - itemId: eBay item ID (legacy)
                - url: Public listing URL
        """
        logger.info(f"Publishing offer: {offer_id}")
        response = await self._make_request(
            "POST",
            f"/sell/inventory/v1/offer/{offer_id}/publish",
            access_token,
        )

        listing_id = response.get("listingId")
        item_id = listing_id  # In newer API, listingId is the item ID

        # Build public URL
        if self.env == "production":
            url = f"https://www.ebay.com/itm/{item_id}"
        else:
            url = f"https://www.sandbox.ebay.com/itm/{item_id}"

        result = {
            "listingId": listing_id,
            "itemId": item_id,
            "url": url,
        }

        logger.info(f"Published offer successfully: {url}")
        return result

    # ========================================================================
    # Taxonomy API
    # ========================================================================

    async def taxonomy_suggest_category(
        self,
        access_token: str,
        query: str,
    ) -> Optional[str]:
        """Suggest eBay category ID based on item title/description.

        Args:
            access_token: Valid access token
            query: Item title or description

        Returns:
            Suggested category ID (as string) or None if no suggestion
        """
        logger.info(f"Suggesting category for query: {query[:50]}...")
        response = await self._make_request(
            "GET",
            "/commerce/taxonomy/v1/category_tree/0/get_category_suggestions",
            access_token,
            params={"q": query},
        )

        suggestions = response.get("categorySuggestions", [])
        if suggestions:
            category_id = suggestions[0]["category"]["categoryId"]
            category_name = suggestions[0]["category"]["categoryName"]
            logger.info(f"Suggested category: {category_name} (ID: {category_id})")
            return category_id

        logger.warning(f"No category suggestion found for query: {query[:50]}")
        return None

    async def taxonomy_get_aspects(
        self,
        access_token: str,
        category_id: str,
    ) -> List[Dict[str, Any]]:
        """Get required and recommended aspects for a category.

        Args:
            access_token: Valid access token
            category_id: eBay category ID

        Returns:
            List of aspects with name, mode (REQUIRED/RECOMMENDED), and allowed values
        """
        logger.info(f"Fetching aspects for category: {category_id}")
        response = await self._make_request(
            "GET",
            f"/commerce/taxonomy/v1/category_tree/0/get_item_aspects_for_category",
            access_token,
            params={"category_id": category_id},
        )

        aspects = response.get("aspects", [])
        logger.info(f"Found {len(aspects)} aspects for category {category_id}")
        return aspects
