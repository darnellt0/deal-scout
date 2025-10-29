from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.core.db import get_session  # noqa: E402
from app.core.models import (  # noqa: E402
    Comp,
    CrossPost,
    Listing,
    ListingScore,
    MyItem,
    Notification,
    Order,
    SnapJob,
)


def wipe_database(force: bool) -> None:
    if not force:
        response = input(
            "This will permanently delete fixture data from the dev database. Type 'yes' to continue: "
        ).strip()
        if response.lower() != "yes":
            print("Aborted.")
            return

    with get_session() as session:
        session.query(ListingScore).delete()
        session.query(Listing).delete()
        session.query(Notification).delete()
        session.query(Comp).delete()
        session.query(Order).delete()
        session.query(CrossPost).delete()
        session.query(SnapJob).delete()
        session.query(MyItem).delete()

    print("Development tables wiped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe development fixture data.")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt.")
    args = parser.parse_args()
    wipe_database(force=args.force)


if __name__ == "__main__":
    main()
