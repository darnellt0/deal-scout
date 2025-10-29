from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.dev_fixtures.loader import load_comps_from_fixture, load_listings_from_fixture  # noqa: E402


def run_samples() -> None:
    script = ROOT / "samples" / "generate_sample_images.py"
    subprocess.check_call([sys.executable, str(script)])


def main() -> None:
    run_samples()
    fixtures_dir = ROOT / "data" / "fixtures"

    couch_counts = load_listings_from_fixture(fixtures_dir / "listings.couches.json")
    island_counts = load_listings_from_fixture(
        fixtures_dir / "listings.kitchen_islands.json"
    )
    couch_comps = load_comps_from_fixture(
        "furniture>sofas", fixtures_dir / "sold_comps.couch.json"
    )
    island_comps = load_comps_from_fixture(
        "kitchen>islands", fixtures_dir / "sold_comps.kitchen_island.json"
    )

    print(
        f"Couch listings inserted: {couch_counts[0]}, updated: {couch_counts[1]}"
    )
    print(
        f"Kitchen island listings inserted: {island_counts[0]}, updated: {island_counts[1]}"
    )
    print(f"Comps inserted: {couch_comps + island_comps}")


if __name__ == "__main__":
    main()
