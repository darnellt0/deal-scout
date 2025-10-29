from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import httpx
from sqlalchemy import select

from app.config import get_settings
from app.core.db import get_session
from app.core.models import MarketplaceAccount

logger = logging.getLogger(__name__)


class EbayClientError(Exception):
    """Base class for eBay integration errors."""


class EbayAuthError(EbayClientError):
    """Raised when authentication with eBay fails."""


class EbayApiError(EbayClientError):
    """Raised when eBay API responds with an error payload."""


@dataclass
class EbayEnvironment:
    auth_base: str
    api_base: str


def _env() -> EbayEnvironment:
    settings = get_settings()
    if settings.ebay_env.lower() == "production":
        return EbayEnvironment(
            auth_base="https://auth.ebay.com",
            api_base="https://api.ebay.com",
        )
    return EbayEnvironment(
        auth_base="https://auth.sandbox.ebay.com",
        api_base="https://api.sandbox.ebay.com",
    )


def _get_account() -> MarketplaceAccount:
    with get_session() as session:
        account = (
            session.execute(
                select(MarketplaceAccount).where(MarketplaceAccount.platform == "ebay")
            )
            .scalars()
            .one_or_none()
        )
        if account:
            return account
        account = MarketplaceAccount(platform="ebay", credentials={})
        session.add(account)
        session.flush()
        return account


def _save_credentials(data: Dict[str, str]) -> None:
    with get_session() as session:
        account = (
            session.execute(
                select(MarketplaceAccount).where(MarketplaceAccount.platform == "ebay")
            )
            .scalars()
            .one_or_none()
        )
        if account is None:
            account = MarketplaceAccount(
                platform="ebay",
                credentials=data,
                connected=data.get("connected", False),
            )
            session.add(account)
        else:
            credentials = account.credentials or {}
            credentials.update(data)
            account.credentials = credentials
            if "connected" in data:
                account.connected = bool(data["connected"])


def _get_credentials() -> Dict[str, str]:
    account = _get_account()
    return account.credentials or {}


def _basic_auth_header() -> str:
    settings = get_settings()
    token = f"{settings.ebay_app_id}:{settings.ebay_cert_id}"
    return base64.b64encode(token.encode("utf-8")).decode("utf-8")


def get_oauth_authorize_url(state: str = "deal-scout") -> str:
    settings = get_settings()
    env = _env()
    scope = settings.ebay_scope or "https://api.ebay.com/oauth/api_scope"
    query = {
        "client_id": settings.ebay_app_id,
        "redirect_uri": settings.ebay_redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "prompt": "login",
    }
    query_string = str(httpx.QueryParams(query))
    authorize_url = f"{env.auth_base}/oauth2/authorize?{query_string}"
    logger.info("Generated eBay authorize URL: %s", authorize_url)
    return authorize_url


def exchange_code_for_refresh_token(code: str) -> str:
    settings = get_settings()
    env = _env()
    token_url = f"{env.api_base}/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {_basic_auth_header()}",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.ebay_redirect_uri,
    }

    if settings.demo_mode:
        logger.info("Demo mode active; storing provided code as refresh token.")
        _save_credentials({"refresh_token": code, "connected": True})
        settings.ebay_refresh_token = code
        return code

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(token_url, data=data, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EbayAuthError(f"Failed to exchange code: {exc}") from exc

    payload = response.json()
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise EbayAuthError(f"Invalid response: {payload}")
    _save_credentials({"refresh_token": refresh_token, "connected": True})
    settings.ebay_refresh_token = refresh_token
    return refresh_token


def _get_refresh_token() -> Optional[str]:
    creds = _get_credentials()
    token = creds.get("refresh_token") or get_settings().ebay_refresh_token
    return token


def get_access_token(scopes: Optional[Iterable[str] | str] = None) -> str:
    settings = get_settings()
    env = _env()
    token_url = f"{env.api_base}/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {_basic_auth_header()}",
    }
    refresh_token = _get_refresh_token()
    if not refresh_token:
        raise EbayAuthError("No refresh token available. Authorize first.")

    if scopes is None:
        scope_value = settings.ebay_scope
    elif isinstance(scopes, str):
        scope_value = scopes
    else:
        scope_value = " ".join(scopes)

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": scope_value,
    }

    if settings.demo_mode:
        logger.info("Demo mode active; returning synthetic access token.")
        return "demo-access-token"

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(token_url, data=data, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EbayAuthError(f"Failed to refresh access token: {exc}") from exc

    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise EbayAuthError(f"Invalid token response: {payload}")
    return access_token


def _api_headers(access_token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_or_update_inventory(item: Dict) -> Dict:
    settings = get_settings()
    env = _env()
    sku = item.get("sku")
    if not sku:
        raise EbayApiError("Inventory item requires a SKU.")

    if settings.demo_mode:
        logger.info("Demo inventory upsert for SKU=%s", sku)
        return {"sku": sku, "status": "mocked"}

    url = f"{env.api_base}/sell/inventory/v1/inventory_item/{sku}"
    access_token = get_access_token()
    headers = _api_headers(access_token)

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.put(url, headers=headers, json=item)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise EbayApiError(f"Inventory upsert failed: {exc.response.text}") from exc
    except httpx.HTTPError as exc:
        raise EbayApiError(f"Inventory upsert failed: {exc}") from exc

    return {"sku": sku, "status": "updated"}


def create_offer(item: Dict, price: float, policies: Dict) -> Dict:
    settings = get_settings()
    env = _env()
    if settings.demo_mode:
        offer_id = f"demo-offer-{item.get('sku', 'unknown')}"
        logger.info("Demo offer created: %s", offer_id)
        return {"offerId": offer_id}

    access_token = get_access_token()
    url = f"{env.api_base}/sell/inventory/v1/offer"
    headers = _api_headers(access_token)

    body = {
        "sku": item.get("sku"),
        "marketplaceId": settings.ebay_marketplace_id,
        "availableQuantity": item.get("availableQuantity", 1),
        "format": "FIXED_PRICE",
        "listingDescription": item.get("description"),
        "pricingSummary": {"price": {"currency": "USD", "value": price}},
    }
    body.update(policies)

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, json=body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise EbayApiError(f"Offer creation failed: {exc.response.text}") from exc
    except httpx.HTTPError as exc:
        raise EbayApiError(f"Offer creation failed: {exc}") from exc

    return response.json()


def publish_offer(offer_id: str) -> str:
    settings = get_settings()
    env = _env()
    if settings.demo_mode:
        subdomain = "sandbox." if settings.ebay_env == "sandbox" else ""
        url = f"https://www.{subdomain}ebay.com/itm/{offer_id}"
        logger.info("Demo publish offer -> %s", url)
        return url

    access_token = get_access_token()
    url = f"{env.api_base}/sell/inventory/v1/offer/{offer_id}/publish"
    headers = _api_headers(access_token)

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise EbayApiError(f"Publish failed: {exc.response.text}") from exc
    except httpx.HTTPError as exc:
        raise EbayApiError(f"Publish failed: {exc}") from exc

    payload = response.json()
    listing_id = payload.get("listingId", offer_id)
    listing_url = payload.get(
        "listingUrl",
        f"https://www.ebay.com/itm/{listing_id}",
    )
    return listing_url
