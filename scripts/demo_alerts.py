from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.dev_fixtures.notifier_demo import create_demo_notifications  # noqa: E402


def main() -> None:
    created = create_demo_notifications(sample_n=5)
    print(f"Created {created} demo notifications.")


if __name__ == "__main__":
    main()
