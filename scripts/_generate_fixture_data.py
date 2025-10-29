"""One-time helper to generate large fixture datasets."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def iso8601(minutes_ago: int) -> str:
    now = datetime.now(timezone.utc)
    return (now - timedelta(minutes=minutes_ago)).isoformat()


def build_couch_fixtures(count: int = 1015) -> list[dict]:
    cities = [
        ("San Jose, CA", 37.3382, -121.8863),
        ("Santa Clara, CA", 37.3541, -121.9552),
        ("Fremont, CA", 37.5483, -121.9886),
        ("Redwood City, CA", 37.4852, -122.2364),
        ("Morgan Hill, CA", 37.1305, -121.6544),
        ("Sunnyvale, CA", 37.3688, -122.0363),
        ("Milpitas, CA", 37.4323, -121.8996),
    ]
    couch_images = [f"/static/samples/couch_{i:02d}.jpg" for i in range(1, 7)]
    prices = [0, 5000, 8000, 12000, 15000, 20000, 22000, 25000]
    conditions = ["good", "like_new", "fair"]

    listings: list[dict] = [
        {
            "source": "craigslist",
            "source_id": "couch-free-001",
            "title": "Free Plush Couch - Good Condition",
            "description": "Moving out, need gone today. No stains.",
            "price_cents": 0,
            "currency": "USD",
            "condition": "good",
            "category": "furniture>sofas",
            "posted_at": iso8601(45),
            "lat": 37.3382,
            "lng": -121.8863,
            "location_text": "San Jose, CA",
            "url": "https://example.invalid/listing/couch-free-001",
            "availability": "active",
            "images": [couch_images[0]],
        },
        {
            "source": "craigslist",
            "source_id": "couch-free-002",
            "title": "Free Leather Loveseat",
            "description": "Pickup in Santa Clara. Minor wear on arm.",
            "price_cents": 0,
            "currency": "USD",
            "condition": "good",
            "category": "furniture>sofas",
            "posted_at": iso8601(120),
            "lat": 37.3541,
            "lng": -121.9552,
            "location_text": "Santa Clara, CA",
            "url": "https://example.invalid/listing/couch-free-002",
            "availability": "active",
            "images": [couch_images[1]],
        },
        {
            "source": "fixture",
            "source_id": "couch-sectional-003",
            "title": "Gray Sectional with Chaise",
            "description": "Spacious sectional, includes chaise lounge.",
            "price_cents": 8000,
            "currency": "USD",
            "condition": "good",
            "category": "furniture>sofas",
            "posted_at": iso8601(180),
            "lat": 37.5483,
            "lng": -121.9886,
            "location_text": "Fremont, CA",
            "url": "https://example.invalid/listing/couch-sectional-003",
            "availability": "active",
            "images": [couch_images[2]],
        },
        {
            "source": "fixture",
            "source_id": "couch-ikea-004",
            "title": "IKEA FÄRLÖV Sofa - Like New",
            "description": "Less than a year old IKEA sofa, smoke free home.",
            "price_cents": 19900,
            "currency": "USD",
            "condition": "like_new",
            "category": "furniture>sofas",
            "posted_at": iso8601(60),
            "lat": 37.3688,
            "lng": -122.0363,
            "location_text": "Sunnyvale, CA",
            "url": "https://example.invalid/listing/couch-ikea-004",
            "availability": "active",
            "images": [couch_images[3]],
        },
        {
            "source": "fixture",
            "source_id": "couch-distant-005",
            "title": "Vallejo Sofa - Might Deliver",
            "description": "Comfortable sofa located well outside the default radius.",
            "price_cents": 12000,
            "currency": "USD",
            "condition": "good",
            "category": "furniture>sofas",
            "posted_at": iso8601(90),
            "lat": 38.1041,
            "lng": -122.2566,
            "location_text": "Vallejo, CA",
            "url": "https://example.invalid/listing/couch-distant-005",
            "availability": "active",
            "images": [couch_images[4]],
        },
    ]

    for idx in range(len(listings), count):
        city, lat, lng = random.choice(cities)
        condition = random.choice(conditions)
        price_cents = random.choice(prices)
        listings.append(
            {
                "source": "fixture",
                "source_id": f"couch-{idx:04d}",
                "title": f"{condition.title()} Couch #{idx:04d}",
                "description": f"Well-kept couch available in {city}.",
                "price_cents": price_cents,
                "currency": "USD",
                "condition": condition,
                "category": "furniture>sofas",
                "posted_at": iso8601(random.randint(10, 2800)),
                "lat": round(lat + random.uniform(-0.05, 0.05), 4),
                "lng": round(lng + random.uniform(-0.05, 0.05), 4),
                "location_text": city,
                "url": f"https://example.invalid/listing/couch-{idx:04d}",
                "availability": "active",
                "images": couch_images,
            }
        )
    return listings


def build_island_fixtures(count: int = 810) -> list[dict]:
    cities = [
        ("San Jose, CA", 37.3382, -121.8863),
        ("Santa Clara, CA", 37.3541, -121.9552),
        ("Fremont, CA", 37.5483, -121.9886),
        ("Redwood City, CA", 37.4852, -122.2364),
        ("Morgan Hill, CA", 37.1305, -121.6544),
        ("Sunnyvale, CA", 37.3688, -122.0363),
        ("Milpitas, CA", 37.4323, -121.8996),
    ]
    island_images = [f"/static/samples/island_{i:02d}.jpg" for i in range(1, 6)]
    prices = [0, 6000, 9000, 12000, 18000, 22000, 28000, 32000]
    conditions = ["good", "like_new", "fair"]

    listings: list[dict] = [
        {
            "source": "fixture",
            "source_id": "island-free-001",
            "title": "Free Rolling Kitchen Island",
            "description": "Rolling island with towel rack, needs pickup.",
            "price_cents": 0,
            "currency": "USD",
            "condition": "good",
            "category": "kitchen>islands",
            "posted_at": iso8601(70),
            "lat": 37.4852,
            "lng": -122.2364,
            "location_text": "Redwood City, CA",
            "url": "https://example.invalid/listing/island-free-001",
            "availability": "active",
            "images": [island_images[0]],
        },
        {
            "source": "fixture",
            "source_id": "island-butch-002",
            "title": "Butcher Block Kitchen Island",
            "description": "Solid wood top with storage shelves.",
            "price_cents": 12000,
            "currency": "USD",
            "condition": "good",
            "category": "kitchen>islands",
            "posted_at": iso8601(95),
            "lat": 37.3541,
            "lng": -121.9552,
            "location_text": "Santa Clara, CA",
            "url": "https://example.invalid/listing/island-butch-002",
            "availability": "active",
            "images": [island_images[1]],
        },
        {
            "source": "fixture",
            "source_id": "island-damaged-003",
            "title": "Damaged Prep Island",
            "description": "Needs refinishing, one drawer off track.",
            "price_cents": 4000,
            "currency": "USD",
            "condition": "fair",
            "category": "kitchen>islands",
            "posted_at": iso8601(150),
            "lat": 37.3382,
            "lng": -121.8863,
            "location_text": "San Jose, CA",
            "url": "https://example.invalid/listing/island-damaged-003",
            "availability": "active",
            "images": [island_images[2]],
        },
        {
            "source": "fixture",
            "source_id": "island-like-004",
            "title": "Like New Kitchen Island with Drawers",
            "description": "Barely used island, bright white finish.",
            "price_cents": 25000,
            "currency": "USD",
            "condition": "like_new",
            "category": "kitchen>islands",
            "posted_at": iso8601(40),
            "lat": 37.3688,
            "lng": -122.0363,
            "location_text": "Sunnyvale, CA",
            "url": "https://example.invalid/listing/island-like-004",
            "availability": "active",
            "images": [island_images[3]],
        },
    ]

    for idx in range(len(listings), count):
        city, lat, lng = random.choice(cities)
        condition = random.choice(conditions)
        price_cents = random.choice(prices)
        listings.append(
            {
                "source": "fixture",
                "source_id": f"island-{idx:04d}",
                "title": f"{condition.title()} Kitchen Island #{idx:04d}",
                "description": f"Spacious storage island available in {city}.",
                "price_cents": price_cents,
                "currency": "USD",
                "condition": condition,
                "category": "kitchen>islands",
                "posted_at": iso8601(random.randint(5, 3000)),
                "lat": round(lat + random.uniform(-0.05, 0.05), 4),
                "lng": round(lng + random.uniform(-0.05, 0.05), 4),
                "location_text": city,
                "url": f"https://example.invalid/listing/island-{idx:04d}",
                "availability": "active",
                "images": island_images,
            }
        )
    return listings


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    couches = build_couch_fixtures()
    islands = build_island_fixtures()
    (FIXTURES_DIR / "listings.couches.json").write_text(
        json.dumps(couches, indent=2), encoding="utf-8"
    )
    (FIXTURES_DIR / "listings.kitchen_islands.json").write_text(
        json.dumps(islands, indent=2), encoding="utf-8"
    )
    print(f"Generated {len(couches)} couch listings and {len(islands)} islands")


if __name__ == "__main__":
    main()
