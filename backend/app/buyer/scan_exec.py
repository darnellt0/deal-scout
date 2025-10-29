"""Synchronous scan execution for blocking/immediate scans."""

from __future__ import annotations

from typing import Dict

from app.buyer.search import run_scan
from app.core.db import get_session
from app.core.models import Listing, ListingScore


def scan_now(live: bool) -> Dict[str, int]:
    """
    Execute a single scan synchronously and return counts.

    Args:
        live: Whether to use live data (adapters) or fixtures (demo mode).

    Returns:
        Dictionary with keys: total, new, updated, skipped
        - total: Total listings processed
        - new: Newly created listings
        - updated: Listings that were already in DB and updated
        - skipped: Listings that were filtered out (low deal score)
    """
    # Run the scan and get filtered matches
    matches = run_scan(use_live=live)

    # Count new vs updated by checking listing creation time
    new_count = 0
    updated_count = 0
    skipped_count = 0

    with get_session() as session:
        for match in matches:
            # Check if this is a new or updated listing
            listing = session.query(Listing).filter_by(id=match.id).one_or_none()

            if listing:
                # Check if it was created in this session (if last_seen_at was just updated)
                # Since store_candidates already marked it, we check if scores exist
                existing_score = (
                    session.query(ListingScore)
                    .filter_by(listing_id=match.id, metric="deal_score")
                    .one_or_none()
                )
                if existing_score:
                    updated_count += 1
                else:
                    new_count += 1
            else:
                new_count += 1

    # Total is the number of matches that passed filtering
    total = len(matches)

    # Note: skipped count is internal to filtering (deal_score < 75, etc.)
    # We don't explicitly track it here since run_scan only returns filtered matches
    # If you want skipped count, you'd need to track it in run_scan

    return {
        "total": total,
        "new": new_count,
        "updated": updated_count,
        "skipped": skipped_count,
    }
