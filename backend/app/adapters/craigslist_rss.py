from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Iterable, List
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

import httpx

from app.config import get_settings
from app.core.utils import load_default_preferences

logger = logging.getLogger(__name__)

GEORSS_TAG = "{http://www.georss.org/georss}point"


def fetch_listings(keywords: Iterable[str]) -> List[dict]:
    settings = get_settings()
    prefs = load_default_preferences()
    keyword_list = list(keywords)
    urls = list(_build_urls(keyword_list, prefs))
    items: List[dict] = []

    for url in urls:
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                parsed = _parse_rss(response.text, keyword_list)
                items.extend(parsed)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Craigslist RSS fetch failed (%s): %s", url, exc)

    if not items:
        items = _fallback_items(keyword_list)

    deduped = {item["id"]: item for item in items}
    return list(deduped.values())[:50]


def _build_urls(keywords: List[str], prefs: dict) -> Iterable[str]:
    settings = get_settings()
    base = f"https://{settings.cl_region}.craigslist.org"
    postal = "95113"
    radius = prefs.get("radius_mi", 50)
    if settings.cl_enable_free:
        params = {"format": "rss", "search_distance": radius, "postal": postal}
        yield f"{base}/search/zip?{urlencode(params)}"
    for keyword in keywords:
        max_price = None
        if "couch" in keyword or "sofa" in keyword or "sectional" in keyword:
            max_price = int(prefs.get("max_price_couch", 200))
        elif "island" in keyword:
            max_price = int(prefs.get("max_price_kitchen_island", 300))
        params = {
            "format": "rss",
            "query": keyword,
            "sort": "date",
            "search_distance": radius,
            "postal": postal,
        }
        if max_price:
            params["max_price"] = max_price
        yield f"{base}/search/{settings.cl_search_furn}?{urlencode(params)}"


def _parse_rss(xml_data: str, keywords: List[str]) -> List[dict]:
    items: List[dict] = []
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return items

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        if title and keywords and not any(k in title.lower() for k in keywords):
            continue

        link = item.findtext("link") or ""
        description = item.findtext("description") or ""
        pub_date = item.findtext("pubDate") or ""
        posted_at = _parse_pub_date(pub_date)
        price = _extract_price(title, description)
        coords = _extract_coords(item)
        location = item.findtext("{http://purl.org/dc/elements/1.1/subject}") or ""

        items.append(
            {
                "id": link or title,
                "source": "craigslist",
                "title": title,
                "description": description,
                "price": price,
                "condition": "good",
                "url": link,
                "thumbnail": None,
                "coords": coords or (None, None),
                "location_text": location,
                "posted_at": posted_at,
            }
        )
    return items


def _parse_pub_date(pub_date: str) -> datetime:
    try:
        return datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
    except Exception:
        return datetime.now(timezone.utc)


def _extract_price(*texts: str) -> float:
    for text in texts:
        if not text:
            continue
        match = re.search(r"\$([0-9]+)", text)
        if match:
            return float(match.group(1))
    return 0.0


def _extract_coords(item: ET.Element):
    geo = item.findtext(GEORSS_TAG)
    if geo:
        parts = geo.split()
        if len(parts) == 2:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                return None
    return None


def _fallback_items(keywords: List[str]) -> List[dict]:
    now = datetime.now(timezone.utc)
    synthetic = []
    for keyword in keywords[:2]:
        synthetic.append(
            {
                "id": f"craigslist-{keyword}",
                "source": "craigslist",
                "title": f"{keyword.title()} - Like New",
                "description": f"Synthetic sample listing for {keyword}",
                "price": 0,
                "condition": "great",
                "url": "https://craigslist.org/sample",
                "thumbnail": None,
                "coords": (37.3382, -121.8863),
                "location_text": "San Jose, CA",
                "posted_at": now,
            }
        )
    return synthetic
