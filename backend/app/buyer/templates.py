from __future__ import annotations

from pathlib import Path

from app.config import get_settings

SETTINGS = get_settings()

DEFAULT_TEMPLATE = "Hi! Is this still available? I can pick up today."


def load_template(name: str = "default") -> str:
    template_dir = SETTINGS.template_dir
    template_path = template_dir / f"{name}.txt"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8").strip()
    return DEFAULT_TEMPLATE
