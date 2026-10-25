"""BolSamajh — main entry point.

Run with:  python -m bolsamajh
"""

import sys
import time
import threading
import logging

from bolsamajh.config import load_config, AppConfig
from bolsamajh.overlay.hud import OverlayHUD

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("bolsamajh")


def _create_stt(config: AppConfig):
    """Create the STT engine based on config."""
    if config.stt.engine == "faster_whisper":
        from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT
        return FasterWhisperSTT(
            model_size=config.stt.model_size,
            device=config.stt.device,
            compute_type=config.stt.compute_type,
            language=config.stt.language,
        )
    else:
        raise ValueError(f"Unknown STT engine: {config.stt.engine}")


def _setup_hotkeys(config: AppConfig, dictation_pipeline) -> None:
    """Register global hotkeys using the keyboard library."""
    import keyboard

    # Track dictation key state for push-to-talk
    dictation_key = config.hotkeys.dictation

    def on_dictation_press(_event=None):
        dictation_pipeline.start_recording()

    def on_dictation_release(_event=None):
        dictation_pipeline.stop_recording_and_transcribe()

    # Register push-to-talk: press to start, release to stop
    keyboard.on_press_key(
        dictation_key.split("+")[-1],  # The main key
        lambda e: on_dictation_press()
        if all(keyboard.is_pressed(k) for k in dictation_key.split("+")[:-1])
        else None,
        suppress=False,
    )

    # Use add_hotkey for the full combo with on_release
    keyboard.add_hotkey(
        dictation_key,
        on_dictation_press,
        suppress=False,
        trigger_on_release=False,
    )

    # For push-to-talk release detection: poll-based approach
    # We detect when the dictation hotkey combo is released
    _ptt_active = threading.Event()

    def _ptt_monitor():
        """Monitor for push-to-talk key release."""
        keys = dictation_key.split("+")
        while True:
            time.sleep(0.05)
            if dictation_pipeline.recorder.is_recording:
                # Check if any key in the combo was released
                all_pressed = all(keyboard.is_pressed(k) for k in keys)
                if not all_pressed:
                    on_dictation_release()

    monitor_thread = threading.Thread(target=_ptt_monitor, daemon=True)
    monitor_thread.start()

    log.info("Hotkeys registered: dictation=%s", dictation_key)


def main() -> None:
    """Launch BolSamajh: system-tray icon + global hotkey listener."""
    config = load_config()
    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  BolSamajh v0.1.0 — Bolo. Samjho.")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("Config: STT=%s  LLM=%s  TTS=%s  Script=%s",
             config.stt.engine, config.llm.engine,
             config.tts.engine, config.dictation.script)

    # 1. Start overlay HUD
    hud = OverlayHUD()
    hud.start()

    # 2. Create STT engine (lazy-loads model on first use)
    stt = _create_stt(config)
    log.info("STT engine: %s (model loads on first use)", stt.name)

    # 3. Create dictation pipeline
    from bolsamajh.pipeline.dictation import DictationPipeline
    dictation = DictationPipeline(config, stt, hud)

    # 4. Register hotkeys
    _setup_hotkeys(config, dictation)

    # 5. Show ready state
    hud.show_text("BolSamajh Ready ✓", duration_ms=2000)

    # 6. Start system tray (blocks main thread)
    log.info("Hotkeys:  Dictation=%s  Stop=%s",
             config.hotkeys.dictation, config.hotkeys.stop)
    log.info("Ready! Hold %s to dictate.", config.hotkeys.dictation)

    from bolsamajh.overlay.tray import create_tray
    tray = create_tray(config)
    tray.run()

    # Cleanup on exit
    stt.unload_model()
    hud.stop()
    log.info("BolSamajh stopped.")


if __name__ == "__main__":
    main()
