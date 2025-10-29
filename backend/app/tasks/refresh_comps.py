from __future__ import annotations

from celery import shared_task

from app.core.db import get_session
from app.core.models import Comp, Condition, Listing


@shared_task(name="app.tasks.refresh_comps.refresh_comps_task")
def refresh_comps_task():
    created = 0
    with get_session() as session:
        listings = (
            session.query(Listing)
            .filter(Listing.price > 0)
            .order_by(Listing.created_at.desc())
            .limit(20)
            .all()
        )
        for listing in listings:
            comp = Comp(
                category=_infer_category(listing.title),
                title=listing.title,
                price=listing.price,
                condition=listing.condition or Condition.good,
                source=listing.source,
                meta={"listing_id": listing.id},
            )
            session.add(comp)
            created += 1
    return {"comps_created": created}


def _infer_category(title: str) -> str:
    title_lower = title.lower()
    if "couch" in title_lower or "sofa" in title_lower or "sectional" in title_lower:
        return "couch"
    if "island" in title_lower:
        return "kitchen island"
    return "other"
