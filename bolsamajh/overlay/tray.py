from __future__ import annotations

"""BolSamajh system-tray icon using pystray."""

import logging
import webbrowser
from typing import Callable, Optional

from PIL import Image, ImageDraw, ImageFont

try:
    import pystray
    from pystray import MenuItem as Item
except Exception:
    pystray = None
    Item = None

from bolsamajh import __version__

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
    draw.text(((size - tw) / 2, (size - th) / 2 - 4), "B", fill=(255, 255, 255, 255), font=font)
    return img


def create_tray(
    config,
    on_quit_callback: Optional[Callable[[], None]] = None,
    on_open_studio_callback: Optional[Callable[[], None]] = None,
) -> Optional[pystray.Icon]:
    """Create and return the system-tray icon with Script Control menu."""
    if pystray is None or Item is None:
        log.warning("pystray is not available; system tray icon disabled.")
        return None

    def on_quit(icon, item):
        log.info("Quitting BolSamajh…")
        if on_quit_callback:
            on_quit_callback()
        icon.stop()

    def on_open_studio(icon=None, item=None):
        log.info("Opening BolSamajh Studio...")
        if on_open_studio_callback:
            on_open_studio_callback()
        else:
            webbrowser.open("http://localhost:8000")

    def toggle_headphone(icon, item):
        config.headphone_mode = not getattr(config, "headphone_mode", False)
        mode_str = "Headphone" if config.headphone_mode else "Speaker"
        log.info("Audio mode switched to: %s mode", mode_str)

    def set_script(mode: str):
        def _handler(icon, item):
            log.info("Script mode switched to: %s", mode)
            config.dictation.script = mode

        return _handler

    icon = pystray.Icon(
        name="BolSamajh",
        icon=_create_icon_image(),
        title="BolSamajh — Bolo. Samjho.",
        menu=pystray.Menu(
            Item("Open BolSamajh Studio (Wispr Flow UI)", on_open_studio, default=True),
            Item(f"BolSamajh v{__version__}", lambda *a: None, enabled=False),
            pystray.Menu.SEPARATOR,
            Item(
                "Headphone Mode",
                toggle_headphone,
                checked=lambda item: getattr(config, "headphone_mode", False),
            ),
            pystray.Menu.SEPARATOR,
            Item(
                "Script Control",
                pystray.Menu(
                    Item(
                        "Natural (Mixed)",
                        set_script("natural"),
                        checked=lambda item: (
                            getattr(config.dictation, "script", "natural") == "natural"
                        ),
                        radio=True,
                    ),
                    Item(
                        "Roman (English Letters)",
                        set_script("roman"),
                        checked=lambda item: (
                            getattr(config.dictation, "script", "natural") == "roman"
                        ),
                        radio=True,
                    ),
                    Item(
                        "Devanagari (Hindi Script)",
                        set_script("devanagari"),
                        checked=lambda item: (
                            getattr(config.dictation, "script", "natural") == "devanagari"
                        ),
                        radio=True,
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            Item("Quit", on_quit),
        ),
    )
    return icon
