"""Generate simple placeholder imagery for offline demos."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - installation step
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent / "backend" / "static" / "samples"
BASE_DIR.mkdir(parents=True, exist_ok=True)

CANVAS_SIZE = (1024, 768)


def _font(size: int = 48) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def create_couch_variants() -> None:
    colors = [
        ("couch_01.jpg", "#f2f2f2", "#2b7a78"),
        ("couch_02.jpg", "#e8f8f5", "#3f72af"),
        ("couch_03.jpg", "#fef6e4", "#ff7f50"),
        ("couch_04.jpg", "#f0f4f8", "#8367c7"),
        ("couch_05.jpg", "#faf3dd", "#d66853"),
        ("couch_06.jpg", "#f7f7ff", "#1b998b"),
    ]
    for name, bg, sofa in colors:
        image = Image.new("RGB", CANVAS_SIZE, color=bg)
        draw = ImageDraw.Draw(image)
        # Draw base sofa block
        draw.rounded_rectangle(
            [150, 360, 874, 580], radius=50, fill=sofa, outline="#1f2933", width=6
        )
        # Draw seat cushions
        draw.rectangle([190, 380, 420, 520], fill="#ffffff33", outline=None)
        draw.rectangle([440, 380, 670, 520], fill="#ffffff33", outline=None)
        draw.rectangle([690, 380, 830, 520], fill="#ffffff33", outline=None)
        draw.text((180, 120), "Deal Scout Couch", font=_font(56), fill="#1f2933")
        draw.text((180, 200), "Offline Fixture Preview", font=_font(36), fill="#1f2933")
        image.save(BASE_DIR / name, format="JPEG", subsampling=0, quality=90)


def create_island_variants() -> None:
    colors = [
        ("island_01.jpg", "#f4f1de", "#3d5a80"),
        ("island_02.jpg", "#f0efeb", "#ed6a5a"),
        ("island_03.jpg", "#fdf0d5", "#2a9d8f"),
        ("island_04.jpg", "#f5f3f4", "#8d99ae"),
        ("island_05.jpg", "#f2f7ff", "#9b5de5"),
    ]
    for name, bg, block in colors:
        image = Image.new("RGB", CANVAS_SIZE, color=bg)
        draw = ImageDraw.Draw(image)
        draw.rectangle([180, 320, 860, 560], fill=block, outline="#1f2933", width=6)
        # Drawer lines
        for y in (360, 420, 480):
            draw.line((200, y, 840, y), fill="#1f2933", width=3)
        # Handles
        for x in (260, 420, 580, 740):
            draw.rectangle([x, 335, x + 90, 355], fill="#f1faee")
        draw.text((220, 120), "Kitchen Island Fixture", font=_font(56), fill="#1f2933")
        image.save(BASE_DIR / name, format="JPEG", subsampling=0, quality=90)


def create_misc_items() -> None:
    items: Iterable[Tuple[str, str, str]] = [
        ("blender_01.jpg", "#fff1e6", "#e56b6f"),
        ("lamp_01.jpg", "#eaffe4", "#6a994e"),
        ("chair_01.jpg", "#edf2fb", "#577590"),
    ]
    for name, bg, accent in items:
        image = Image.new("RGB", CANVAS_SIZE, color=bg)
        draw = ImageDraw.Draw(image)
        if "blender" in name:
            draw.rectangle([460, 300, 560, 600], fill=accent, outline="#1f2933", width=6)
            draw.polygon(
                [(450, 300), (580, 300), (540, 180), (490, 180)],
                fill="#f7ede2",
                outline="#1f2933",
            )
            draw.text((350, 120), "Blender Fixture", font=_font(56), fill="#1f2933")
        elif "lamp" in name:
            draw.rectangle([500, 320, 540, 620], fill="#1f2933")
            draw.polygon(
                [(420, 320), (620, 320), (560, 200), (480, 200)],
                fill=accent,
                outline="#1f2933",
            )
            draw.text((360, 120), "Lamp Fixture", font=_font(56), fill="#1f2933")
        else:  # chair
            draw.rectangle([420, 360, 620, 600], fill=accent, outline="#1f2933", width=6)
            draw.rectangle([440, 260, 600, 360], fill="#f1faee", outline="#1f2933")
            draw.text((360, 120), "Chair Fixture", font=_font(56), fill="#1f2933")
        draw.text((320, 660), "Deal Scout Samples", font=_font(32), fill="#1f2933")
        image.save(BASE_DIR / name, format="JPEG", subsampling=0, quality=90)


def main() -> None:
    create_couch_variants()
    create_island_variants()
    create_misc_items()
    print(f"Generated sample images in {BASE_DIR}")


if __name__ == "__main__":
    main()
