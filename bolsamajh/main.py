"""BolSamajh — main entry point.

Run with:  python -m bolsamajh
"""

import sys
import threading
import logging

from bolsamajh.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bolsamajh")


def main() -> None:
    """Launch BolSamajh: system-tray icon + global hotkey listener."""
    config = load_config()
    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("BolSamajh v%s — %s", "0.1.0", "Bolo. Samjho.")
    log.info("Config: STT=%s  LLM=%s  TTS=%s  Script=%s",
             config.stt.engine, config.llm.engine,
             config.tts.engine, config.dictation.script)

    # --- System tray (runs on main thread for Windows) ---
    from bolsamajh.overlay.tray import create_tray
    tray = create_tray(config)

    log.info("BolSamajh is running. Use hotkeys or the tray icon.")
    log.info("Hotkeys:  Dictation=%s  DocLoad=%s  DocAsk=%s  Command=%s  Stop=%s",
             config.hotkeys.dictation, config.hotkeys.doc_load,
             config.hotkeys.doc_ask, config.hotkeys.command,
             config.hotkeys.stop)

    tray.run()


if __name__ == "__main__":
    main()
