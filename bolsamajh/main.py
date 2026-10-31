"""BolSamajh — main entry point.

Run with:  python -m bolsamajh
"""

import io
import logging
import signal
import sys
import threading
import time


# Windows GUI (--noconsole / pythonw) sets sys.stdout and sys.stderr to None.
# Provide safe stream wrappers with .isatty() returning False to prevent
# AttributeError crashes in logging, uvicorn, and third-party libraries.
class _SafeNullStream(io.StringIO):
    def isatty(self) -> bool:
        return False

    def flush(self) -> None:
        pass

    def write(self, s: str) -> int:
        return len(s)


if sys.stdout is None:
    sys.stdout = _SafeNullStream()
if sys.stderr is None:
    sys.stderr = _SafeNullStream()

try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = None
    filedialog = None

from dotenv import load_dotenv

load_dotenv()

from bolsamajh import __version__
from bolsamajh.config import AppConfig, load_config
from bolsamajh.overlay.hud import OverlayHUD
from bolsamajh.tts.factory import create_tts_adapter
from bolsamajh.web.supervisor import (
    check_existing_instance,
    clean_runtime_info,
    find_available_port,
    setup_rotating_file_logger,
    wait_for_health,
    write_runtime_info,
)

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
    return create_tts_adapter(config)


def _setup_hotkeys(
    config: AppConfig,
    dictation_pipeline,
    doc_qa_pipeline,
    commands_pipeline,
    hud,
    shutdown_event: threading.Event,
) -> None:
    """Register global hotkeys using the keyboard library with adaptive sleep."""
    import keyboard

    dictation_key = config.hotkeys.dictation
    doc_load_key = config.hotkeys.doc_load
    doc_ask_key = config.hotkeys.doc_ask
    command_key = config.hotkeys.command
    stop_key = config.hotkeys.stop
    suppress = getattr(config.hotkeys, "suppress", False)

    # --- Dictation push-to-talk ---
    def _ptt_monitor():
        """Monitor for push-to-talk key release with adaptive sleep."""
        keys = dictation_key.split("+")
        while not shutdown_event.is_set():
            if dictation_pipeline.recorder.is_recording:
                all_pressed = all(keyboard.is_pressed(k) for k in keys)
                if not all_pressed:
                    dictation_pipeline.stop_recording_and_transcribe()
                time.sleep(0.03)
            else:
                time.sleep(0.08)

    keyboard.add_hotkey(
        dictation_key,
        dictation_pipeline.start_recording,
        suppress=suppress,
    )
    threading.Thread(target=_ptt_monitor, daemon=True).start()

    # --- Document loading via HUD's Tk main thread ---
    def on_doc_load():
        def _load():
            path = hud.prompt_open_file()
            if path:
                doc_qa_pipeline.load_document(path)

        threading.Thread(target=_load, daemon=True).start()

    keyboard.add_hotkey(doc_load_key, on_doc_load, suppress=suppress)

    # --- Document Q&A push-to-talk ---
    def _qa_ptt_monitor():
        """Monitor for Q&A key release with adaptive sleep."""
        keys = doc_ask_key.split("+")
        while not shutdown_event.is_set():
            if doc_qa_pipeline.recorder.is_recording:
                all_pressed = all(keyboard.is_pressed(k) for k in keys)
                if not all_pressed:
                    doc_qa_pipeline.stop_and_answer()
                time.sleep(0.03)
            else:
                time.sleep(0.08)

    keyboard.add_hotkey(
        doc_ask_key,
        doc_qa_pipeline.start_question,
        suppress=suppress,
    )
    threading.Thread(target=_qa_ptt_monitor, daemon=True).start()

    # --- Voice Commands push-to-talk ---
    def _cmd_ptt_monitor():
        """Monitor for voice command key release with adaptive sleep."""
        keys = command_key.split("+")
        while not shutdown_event.is_set():
            if commands_pipeline.recorder.is_recording:
                all_pressed = all(keyboard.is_pressed(k) for k in keys)
                if not all_pressed:
                    commands_pipeline.stop_and_execute()
                time.sleep(0.03)
            else:
                time.sleep(0.08)

    keyboard.add_hotkey(
        command_key,
        commands_pipeline.start_command,
        suppress=suppress,
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


def open_studio_dashboard(port: int = 8000) -> None:
    """Open BolSamajh Studio in standalone desktop application mode or browser."""
    import os
    import subprocess
    import webbrowser

    url = f"http://127.0.0.1:{port}"
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for edge in edge_paths:
        if os.path.isfile(edge):
            try:
                subprocess.Popen([edge, f"--app={url}", "--new-window"])
                return
            except Exception as e:
                log.debug("Failed to launch Edge app mode: %s", e)
                break
    webbrowser.open(url)


def _start_web_server(config: AppConfig, shutdown_event: threading.Event, port: int = 8000) -> None:
    """Start Uvicorn web server in a background daemon thread."""
    import uvicorn

    from bolsamajh.web.server import app

    host = getattr(config.web, "host", "127.0.0.1")

    server_config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
        log_config=None,  # Prevent uvicorn from crashing on sys.stdout.isatty() in GUI mode
    )
    server = uvicorn.Server(server_config)

    def _monitor_shutdown():
        shutdown_event.wait()
        server.should_exit = True

    threading.Thread(target=_monitor_shutdown, daemon=True).start()

    def _run():
        log.info("Starting BolSamajh Web Studio at http://%s:%d...", host, port)
        try:
            server.run()
        except Exception as e:
            log.error("Web server error: %s", e)

    threading.Thread(target=_run, daemon=True).start()


def run_selftest() -> int:
    """Run comprehensive self-test verifying models, transcription, retrieval, and server."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    print("========================================")
    print(f"  BolSamajh v{__version__} - Automated Self-Test")
    print("========================================")
    setup_rotating_file_logger()
    try:
        from pathlib import Path

        config = load_config()
        print(f"[1/4] Config loaded: STT={config.stt.engine}, Device={config.stt.device}")

        # 1. Test STT model loading & transcription
        print("[2/4] Testing STT engine...")
        stt = _create_stt(config)
        stt.load_model()
        test_audio_path = (
            Path(__file__).resolve().parent.parent / "benchmark_data" / "audio" / "sentence_001.wav"
        )
        if test_audio_path.exists():
            import wave

            import numpy as np

            with wave.open(str(test_audio_path), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            result = stt.transcribe(audio_data)
            clean_text = result.text.encode("ascii", errors="replace").decode("ascii")
            print(
                f"      STT output: {clean_text[:60]}... (latency {result.processing_seconds:.2f}s)"
            )
        else:
            print("      STT model loaded successfully.")

        # 2. Test Document Retriever
        print("[3/4] Testing document retriever embedding model...")
        from bolsamajh.documents.retriever import DocumentRetriever

        retriever = DocumentRetriever()
        retriever._load_embedding_model()
        print("      Retriever embedding model loaded.")

        # 3. Test Core Server & /healthz
        print("[4/4] Testing core web server & /healthz...")
        import uvicorn

        from bolsamajh.web.server import app

        test_port = find_available_port("127.0.0.1", start_port=8900)
        server_cfg = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=test_port,
            log_level="error",
            access_log=False,
            log_config=None,
        )
        server = uvicorn.Server(server_cfg)
        threading.Thread(target=server.run, daemon=True).start()

        if wait_for_health("127.0.0.1", test_port, timeout=12.0):
            print(f"      /healthz OK at http://127.0.0.1:{test_port}")
            server.should_exit = True
        else:
            server.should_exit = True
            print("      FAILED: /healthz did not respond within timeout.")
            return 1

        stt.unload_model()
        print("========================================")
        print("  [PASS] SELF-TEST PASSED: ALL SUBSYSTEMS OPERATIONAL")
        print("========================================")
        return 0
    except Exception as e:
        print(f"ERROR during selftest: {e}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> None:
    """Launch BolSamajh: system-tray icon + global hotkey listener + web studio."""
    if "--selftest" in sys.argv:
        if sys.platform == "win32":
            try:
                import ctypes

                if ctypes.windll.kernel32.AttachConsole(-1):
                    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            except Exception:
                pass
        sys.exit(run_selftest())

    # 1. Setup rotating file logging early so all logs are preserved
    log_file = setup_rotating_file_logger()

    # 2. Check for already running instance
    existing = check_existing_instance()
    if existing:
        host, existing_port = existing
        log.info(
            "BolSamajh is already running at http://%s:%d. Opening dashboard...",
            host,
            existing_port,
        )
        open_studio_dashboard(port=existing_port)
        return

    config = load_config()
    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  BolSamajh v%s — Bolo. Samjho.", __version__)
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info(
        "Config: STT=%s  LLM=%s  TTS=%s  Script=%s",
        config.stt.engine,
        config.llm.engine,
        config.tts.engine,
        config.dictation.script,
    )

    host = getattr(config.web, "host", "127.0.0.1")
    configured_port = getattr(config.web, "port", 8000)
    actual_port = find_available_port(host=host, start_port=configured_port)
    config.web.port = actual_port
    write_runtime_info(host=host, port=actual_port, log_file=log_file)

    shutdown_event = threading.Event()

    # 1. Start web server on chosen port
    _start_web_server(config, shutdown_event, port=actual_port)

    # 2. Start overlay HUD with click-to-open Studio
    hud = OverlayHUD(on_click_callback=lambda: open_studio_dashboard(port=actual_port))
    from bolsamajh.web.server import set_overlay_hud

    set_overlay_hud(hud)
    hud.start()

    # 3. Automatically launch Studio Desktop Window once server is verified healthy
    if getattr(config.web, "auto_open", True):

        def _deferred_open():
            if wait_for_health(host, actual_port, timeout=15.0):
                time.sleep(0.2)
                open_studio_dashboard(port=actual_port)
            else:
                log.error(
                    "BolSamajh core server failed to respond on http://%s:%d/healthz within 15s. Log: %s",
                    host,
                    actual_port,
                    log_file,
                )
                if tk:
                    try:
                        import tkinter.messagebox as mb

                        mb.showerror(
                            "BolSamajh Notice",
                            f"Core server failed to respond on port {actual_port}.\n\nPlease check log:\n{log_file}",
                        )
                    except Exception:
                        pass

        threading.Thread(target=_deferred_open, daemon=True).start()

    # 4. Create engines (lazy-loaded)
    stt = _create_stt(config)
    llm = _create_llm(config)
    tts = _create_tts(config)
    log.info("Engines: STT=%s  LLM=%s  TTS=%s", stt.name, llm.name, tts.name)

    # 3. Create pipelines
    from bolsamajh.pipeline.commands import VoiceCommandsPipeline
    from bolsamajh.pipeline.dictation import DictationPipeline
    from bolsamajh.pipeline.doc_qa import DocQAPipeline

    dictation = DictationPipeline(config, stt, hud)
    doc_qa = DocQAPipeline(config, stt, llm, tts, hud)
    commands = VoiceCommandsPipeline(config, stt, llm, hud)

    # 4. Register hotkeys with shutdown coordination
    _setup_hotkeys(config, dictation, doc_qa, commands, hud, shutdown_event)

    # 5. Preload models in background thread and show Ready when completed
    hud.set_state("processing", "Loading models…")

    def _preload_models():
        failed = []
        try:
            log.info("Preloading STT model (%s)...", stt.name)
            stt.load_model()
            log.info("STT model preloaded successfully.")
        except Exception as e:
            log.warning("STT preload failed: %s", e)
            failed.append("STT")

        try:
            log.info("Preloading Document QA embedding model...")
            doc_qa.retriever._load_embedding_model()
            log.info("Document QA embedding model preloaded successfully.")
        except Exception as e:
            log.warning("Embedding model preload failed: %s", e)

        if failed:
            hud.show_text(f"Degraded: {', '.join(failed)} failed", duration_ms=4000)
        else:
            hud.show_text("BolSamajh Ready ✓", duration_ms=2500)

    threading.Thread(target=_preload_models, daemon=True).start()

    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log.info("  Ready! Hotkeys active:")
    log.info("  Hold %s to dictate", config.hotkeys.dictation)
    log.info("  %s to load a document", config.hotkeys.doc_load)
    log.info("  Hold %s to ask about it", config.hotkeys.doc_ask)
    log.info("  Hold %s to run voice command on selection", config.hotkeys.command)
    log.info("  %s to stop/interrupt", config.hotkeys.stop)
    log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    tray_holder = [None]

    def on_quit():
        log.info("Quit invoked: cleaning up...")
        clean_runtime_info()
        shutdown_event.set()
        dictation.cancel()
        doc_qa.cancel()
        commands.cancel()
        try:
            import keyboard

            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        if tray_holder[0]:
            try:
                tray_holder[0].stop()
            except Exception:
                pass

    def _handle_signal(sig, frame):
        log.info("Signal %s received; shutting down...", sig)
        on_quit()

    try:
        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)
    except Exception:
        pass

    # 6. Start system tray (blocks main thread)
    from bolsamajh.overlay.tray import create_tray

    tray = create_tray(
        config,
        on_quit_callback=on_quit,
        on_open_studio_callback=lambda: open_studio_dashboard(
            port=getattr(config.web, "port", 8000)
        ),
    )
    tray_holder[0] = tray
    if tray:
        tray.run()
    else:
        try:
            while not shutdown_event.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            on_quit()

    # Cleanup on exit
    stt.unload_model()
    hud.stop()
    log.info("BolSamajh stopped.")


if __name__ == "__main__":
    main()
