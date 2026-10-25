"""BolSamajh — main entry point.

Run with:  python -m bolsamajh
"""

import sys
import time
import asyncio
import threading
import logging
from tkinter import filedialog
import tkinter as tk

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


def _create_llm(config: AppConfig):
    """Create the LLM adapter based on config with auto-fallback."""
    from bolsamajh.llm.factory import create_llm_adapter
    return create_llm_adapter(config)


def _create_tts(config: AppConfig):
    """Create the TTS adapter based on config."""
    if config.tts.engine == "edge_tts":
        from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter
        return EdgeTTSAdapter()
    elif config.tts.engine == "piper":
        from bolsamajh.tts.piper_adapter import PiperTTSAdapter
        return PiperTTSAdapter(model_path=config.tts.piper_model_path)
    else:
        raise ValueError(f"Unknown TTS engine: {config.tts.engine}")


def _prompt_document_path() -> str | None:
    """Show a file dialog or URL prompt for document loading."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        title="BolSamajh — Load Document",
        filetypes=[
            ("Documents", "*.pdf;*.docx;*.doc"),
            ("PDF Files", "*.pdf"),
            ("Word Documents", "*.docx;*.doc"),
            ("All Files", "*.*"),
        ],
    )
    root.destroy()
    return file_path if file_path else None


def _setup_hotkeys(config: AppConfig, dictation_pipeline, doc_qa_pipeline, commands_pipeline) -> None:
    """Register global hotkeys using the keyboard library."""
    import keyboard

    dictation_key = config.hotkeys.dictation
    doc_load_key = config.hotkeys.doc_load
    doc_ask_key = config.hotkeys.doc_ask
    command_key = config.hotkeys.command
    stop_key = config.hotkeys.stop

    # --- Dictation push-to-talk ---
    def _ptt_monitor():
        """Monitor for push-to-talk key release."""
        keys = dictation_key.split("+")
        while True:
            time.sleep(0.05)
            if dictation_pipeline.recorder.is_recording:
                all_pressed = all(keyboard.is_pressed(k) for k in keys)
                if not all_pressed:
                    dictation_pipeline.stop_recording_and_transcribe()

    keyboard.add_hotkey(
        dictation_key,
        dictation_pipeline.start_recording,
        suppress=False,
    )
    threading.Thread(target=_ptt_monitor, daemon=True).start()

    # --- Document loading ---
    def on_doc_load():
        def _load():
            path = _prompt_document_path()
            if path:
                doc_qa_pipeline.load_document(path)
        threading.Thread(target=_load, daemon=True).start()

    keyboard.add_hotkey(doc_load_key, on_doc_load, suppress=False)

    # --- Document Q&A push-to-talk ---
    def _qa_ptt_monitor():
        """Monitor for Q&A key release."""
        keys = doc_ask_key.split("+")
        while True:
            time.sleep(0.05)
            if doc_qa_pipeline.recorder.is_recording:
                all_pressed = all(keyboard.is_pressed(k) for k in keys)
                if not all_pressed:
                    doc_qa_pipeline.stop_and_answer()

    keyboard.add_hotkey(
        doc_ask_key,
        doc_qa_pipeline.start_question,
        suppress=False,
    )
    threading.Thread(target=_qa_ptt_monitor, daemon=True).start()

    # --- Voice Commands push-to-talk ---
    def _cmd_ptt_monitor():
        """Monitor for voice command key release."""
        keys = command_key.split("+")
        while True:
            time.sleep(0.05)
            if commands_pipeline.recorder.is_recording:
                all_pressed = all(keyboard.is_pressed(k) for k in keys)
                if not all_pressed:
                    commands_pipeline.stop_and_execute()

    keyboard.add_hotkey(
        command_key,
        commands_pipeline.start_command,
        suppress=False,
    )
    threading.Thread(target=_cmd_ptt_monitor, daemon=True).start()

    # --- Stop / interrupt / cancel active recording ---
    def on_stop():
        log.info("Escape pressed: cancelling active recording and interrupting speech")
        dictation_pipeline.cancel()
        doc_qa_pipeline.cancel()
        commands_pipeline.cancel()
        doc_qa_pipeline.interrupt()

    keyboard.add_hotkey(stop_key, on_stop, suppress=False)

    log.info("Hotkeys registered:")
    log.info("  Dictation:     %s (hold to talk)", dictation_key)
    log.info("  Load Doc:      %s", doc_load_key)
    log.info("  Ask Doc:       %s (hold to talk)", doc_ask_key)
    log.info("  Voice Command: %s (hold to speak on selection)", command_key)
    log.info("  Stop:          %s", stop_key)


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

    # 2. Create engines (lazy-loaded)
    stt = _create_stt(config)
    llm = _create_llm(config)
    tts = _create_tts(config)
    log.info("Engines: STT=%s  LLM=%s  TTS=%s", stt.name, llm.name, tts.name)

    # 3. Create pipelines
    from bolsamajh.pipeline.dictation import DictationPipeline
    from bolsamajh.pipeline.doc_qa import DocQAPipeline
    from bolsamajh.pipeline.commands import VoiceCommandsPipeline

    dictation = DictationPipeline(config, stt, hud)
    doc_qa = DocQAPipeline(config, stt, llm, tts, hud)
    commands = VoiceCommandsPipeline(config, stt, llm, hud)

    # 4. Register hotkeys
    _setup_hotkeys(config, dictation, doc_qa, commands)

    # 5. Show ready state
    hud.show_text("BolSamajh Ready ✓", duration_ms=2500)

    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  Ready! Hotkeys active.")
    log.info("  Hold Ctrl+Shift+Space to dictate")
    log.info("  Ctrl+Shift+D to load a document")
    log.info("  Hold Ctrl+Shift+A to ask about it")
    log.info("  Hold Ctrl+Shift+C to run voice command on selection")
    log.info("  Escape to stop/interrupt")
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


    # 6. Start system tray (blocks main thread)
    from bolsamajh.overlay.tray import create_tray
    tray = create_tray(config)
    tray.run()

    # Cleanup on exit
    stt.unload_model()
    hud.stop()
    log.info("BolSamajh stopped.")


if __name__ == "__main__":
    main()
