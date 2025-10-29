from __future__ import annotations

from pathlib import Path
from typing import List

import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.core.db import get_session  # noqa: E402
from app.core.models import Condition, MyItem, SnapJob  # noqa: E402


def main() -> None:
    fixtures: List[dict] = [
        {
            "title": "Table Lamp",
            "category": "lighting",
            "condition": Condition.good,
            "price_cents": 4500,
            "image": "/static/samples/lamp_01.jpg",
            "description": "Warm table lamp with modern styling.",
        },
        {
            "title": "Kitchen Blender",
            "category": "appliances",
            "condition": Condition.excellent,
            "price_cents": 6500,
            "image": "/static/samples/blender_01.jpg",
            "description": "High speed blender ready for smoothies.",
        },
        {
            "title": "Dining Chair",
            "category": "furniture",
            "condition": Condition.good,
            "price_cents": 7500,
            "image": "/static/samples/chair_01.jpg",
            "description": "Solid oak chair with cushion seat.",
        },
    ]

    created = 0
    with get_session() as session:
        for fixture in fixtures:
            item = MyItem(
                title=fixture["title"],
                category=fixture["category"],
                attributes={"fixture": True},
                condition=fixture["condition"],
                price=fixture["price_cents"] / 100.0,
                status="draft",
            )
            session.add(item)
            session.flush()

            job = SnapJob(
                status="prepared",
                source="fixture",
                input_photos=[fixture["image"]],
                processed_images=[fixture["image"]],
                detected_category=fixture["category"],
                detected_attributes={"fixture": True, "source": "seed"},
                condition_guess=fixture["condition"].value,
                price_suggestion_cents=fixture["price_cents"],
                suggested_price=fixture["price_cents"] / 100.0,
                suggested_title=f"{fixture['title']} Ready to Post",
                suggested_description=fixture["description"],
                title_suggestion=f"{fixture['title']} Ready to Post",
                description_suggestion=fixture["description"],
            )
            session.add(job)
            created += 1

    print(f"Prepared {created} snap jobs with matching MyItem records.")


if __name__ == "__main__":
    main()
