"""BolSamajh system-tray icon using pystray."""

import logging
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as Item

log = logging.getLogger(__name__)


def _create_icon_image(size: int = 64) -> Image.Image:
    """Generate a simple tray icon — a blue microphone-style circle with 'B'."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Blue circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=(59, 130, 246, 255))
    # White "B" in center
    try:
        font = ImageFont.truetype("arial.ttf", size // 2)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "B", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 4), "B",
              fill=(255, 255, 255, 255), font=font)
    return img


def create_tray(config) -> pystray.Icon:
    """Create and return the system-tray icon (call .run() to start)."""
    def on_quit(icon, item):
        log.info("Quitting BolSamajh…")
        icon.stop()

    icon = pystray.Icon(
        name="BolSamajh",
        icon=_create_icon_image(),
        title="BolSamajh — Bolo. Samjho.",
        menu=pystray.Menu(
            Item("BolSamajh v0.1.0", lambda *a: None, enabled=False),
            pystray.Menu.SEPARATOR,
            Item("Quit", on_quit),
        ),
    )
    return icon
