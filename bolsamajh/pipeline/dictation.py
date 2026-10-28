"""Dictation pipeline — hotkey → record → STT → cleanup → insert text."""

import logging
import threading
import time

from bolsamajh.config import AppConfig
from bolsamajh.overlay.hud import OverlayHUD
from bolsamajh.stt.base import SpeechToText
from bolsamajh.utils.audio import MicRecorder
from bolsamajh.utils.clipboard import insert_text
from bolsamajh.utils.text_cleanup import cleanup_text

log = logging.getLogger(__name__)


class DictationPipeline:
    """Push-to-talk dictation: record → transcribe → clean → paste."""

    def __init__(self, config: AppConfig, stt: SpeechToText, hud: OverlayHUD):
        self.config = config
        self.stt = stt
        self.hud = hud
        self.recorder = MicRecorder()
        self._processing = False
        self._processing_lock = threading.Lock()
        self._worker_thread: threading.Thread | None = None
        self._cancel_requested: bool = False

    def start_recording(self) -> None:
        """Begin push-to-talk recording."""
        with self._processing_lock:
            if self.recorder.is_recording or self._processing:
                return
        self._cancel_requested = False
        log.info("🎤 Dictation: recording started")
        self.hud.set_state("listening")
        self.recorder.start()

    def cancel(self) -> None:
        """Cancel recording immediately and join worker thread."""
        self._cancel_requested = True
        if self.recorder.is_recording:
            self.recorder.cancel()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=0.5)
            if not self._worker_thread.is_alive():
                self._worker_thread = None
        with self._processing_lock:
            self._processing = False
        self.hud.set_state("idle")
        log.info("Dictation: cancelled by user")

    def stop_recording_and_transcribe(self) -> None:
        """Stop recording, transcribe, clean up, and insert text.

        Runs transcription in a background thread to avoid blocking hotkeys.
        """
        if not self.recorder.is_recording:
            return

        log.info("⏹️ Dictation: recording stopped, processing…")
        self.hud.set_state("processing")

        wav_bytes = self.recorder.stop()
        if not wav_bytes:
            log.warning("No audio captured")
            self.hud.set_state("error")
            return

        # Process in background thread
        thread = threading.Thread(
            target=self._process_audio,
            args=(wav_bytes,),
            daemon=True,
        )
        self._worker_thread = thread
        thread.start()

    def _process_audio(self, wav_bytes: bytes) -> None:
        """Background: transcribe → clean → insert."""
        with self._processing_lock:
            self._processing = True
        t0 = time.time()

        try:
            if self._cancel_requested:
                return
            # 1. Transcribe
            result = self.stt.transcribe(wav_bytes)

            if not result.text.strip():
                log.warning("Empty transcription")
                self.hud.set_state("error")
                return

            # 2. Clean up
            cleaned = cleanup_text(
                result.text,
                remove_filler=self.config.dictation.remove_fillers,
                script=self.config.dictation.script,
            )

            if not cleaned.strip():
                log.warning("Text empty after cleanup")
                self.hud.set_state("error")
                return

            # 3. Insert into active app
            if self._cancel_requested:
                log.info("Dictation cancelled before insertion")
                return

            elapsed = time.time() - t0
            log.info(
                "✅ Dictation: inserting %d chars (%.2fs total): %s",
                len(cleaned),
                elapsed,
                cleaned[:80],
            )

            inserted = insert_text(cleaned)
            if inserted:
                self.hud.set_state("done", f"{elapsed:.1f}s")
            else:
                log.warning("Dictation: text insertion returned False")
                self.hud.set_state("error")

        except Exception as e:
            log.error("Dictation error: %s", e, exc_info=True)
            self.hud.set_state("error")

        finally:
            with self._processing_lock:
                self._processing = False
