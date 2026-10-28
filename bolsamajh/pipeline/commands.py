"""Voice Commands Pipeline — select text in any app, speak command, replace in-place.

Workflow:
1. User highlights text in any app (Notepad, browser, Word, IDE, Slack).
2. User holds Ctrl+Shift+C and speaks instruction (e.g. "make it formal", "translate to Hindi", "summarize").
3. Pipeline captures selected text via clipboard.
4. Voice command is transcribed by STT.
5. LLM executes instruction on selected text.
6. Transformed text replaces selection via clipboard paste.
"""

import time
import asyncio
import logging
import threading

from bolsamajh.config import AppConfig
from bolsamajh.stt.base import SpeechToText
from bolsamajh.llm.base import LLMAdapter
from bolsamajh.overlay.hud import OverlayHUD
from bolsamajh.utils.audio import MicRecorder
from bolsamajh.utils.clipboard import get_selected_text, insert_text

log = logging.getLogger(__name__)

import re

COMMAND_SYSTEM_PROMPT = """You are BolSamajh In-App Voice Editor.
The user has highlighted text in their application and given a voice command in English, Hindi, or Hinglish.

STRICT INSTRUCTIONS:
1. Return ONLY the transformed text.
2. Do NOT add conversational replies, greetings, or explanations (no "Here is the revised text:", no "Sure!").
3. Do NOT wrap output in markdown code blocks or quotes unless the original text was code.
4. Preserve the core meaning, facts, and structure unless the command explicitly requests otherwise.
5. If the user command is in Hinglish (e.g., "formal email bana do", "chhota kar do", "grammar fix karo"), understand the intent and apply it accurately.
"""


def _clean_llm_response(raw: str) -> str:
    """Robustly clean LLM output: strip code fences, preamble phrases, and quotes."""
    cleaned = raw.strip()

    # 1. Strip markdown code fences (e.g. ```markdown ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()

    # 2. Strip common conversational preambles ("Here is...", "Sure! Here is...", "Revised text:", etc.)
    cleaned = re.sub(
        r"^(?:Here\s+(?:is|are)|Here's|Sure!?|Certainly!?|Below\s+is|This\s+is|Revised\s+text:?|Modified\s+text:?)[^\n:]*[:\n]\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # 3. Strip surrounding quotes if model added them
    if (cleaned.startswith('"""') and cleaned.endswith('"""')) or \
       (cleaned.startswith("'''") and cleaned.endswith("'''")):
        cleaned = cleaned[3:-3].strip()
    elif (cleaned.startswith('"') and cleaned.endswith('"')) or \
         (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    return cleaned


class VoiceCommandsPipeline:
    """Execute voice commands on selected text in any desktop app."""

    def __init__(
        self,
        config: AppConfig,
        stt: SpeechToText,
        llm: LLMAdapter,
        hud: OverlayHUD,
    ):
        self.config = config
        self.stt = stt
        self.llm = llm
        self.hud = hud
        self.recorder = MicRecorder()
        self._selected_text: str = ""
        self._selection_event = threading.Event()
        self._processing = False
        self._processing_lock = threading.Lock()
        self._worker_thread: threading.Thread | None = None
        self._cancel_requested: bool = False

    def start_command(self) -> None:
        """Start listening for command immediately; capture highlighted text in parallel."""
        with self._processing_lock:
            if self.recorder.is_recording or self._processing:
                return

        self._cancel_requested = False
        # 1. Start audio recording IMMEDIATELY to prevent clipping opening syllables
        self.hud.set_state("listening", "Listening command…")
        self.recorder.start()

        # 2. Capture highlighted text in parallel thread so recording is completely unblocked
        self._selection_event.clear()

        def _capture():
            self._selected_text = get_selected_text()
            log.info("Voice command captured selection (%d chars): %s",
                     len(self._selected_text), self._selected_text[:40])
            self._selection_event.set()

        threading.Thread(target=_capture, daemon=True).start()

    def cancel(self) -> None:
        """Cancel command recording and join worker thread."""
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
        log.info("Voice Command: cancelled by user")

    def stop_and_execute(self) -> None:
        """Stop listening and execute command on selected text."""
        if not self.recorder.is_recording:
            return

        self.hud.set_state("processing")
        wav_bytes = self.recorder.stop()

        if not wav_bytes:
            self.hud.set_state("error")
            return

        thread = threading.Thread(
            target=self._process_command,
            args=(wav_bytes,),
            daemon=True,
        )
        self._worker_thread = thread
        thread.start()

    def _process_command(self, wav_bytes: bytes) -> None:
        """Background: STT -> LLM transform -> replace selection."""
        with self._processing_lock:
            self._processing = True
        t0 = time.time()

        try:
            if self._cancel_requested:
                return
            # Ensure selection capture thread has completed
            self._selection_event.wait(timeout=1.0)

            # 1. Transcribe voice command
            result = self.stt.transcribe(wav_bytes)
            command_text = result.text.strip()

            if not command_text:
                log.warning("No speech detected in voice command")
                self.hud.show_text("No command heard", duration_ms=2000)
                return

            log.info("Voice command heard: '%s'", command_text)
            self.hud.set_state("processing", f"Command: {command_text[:20]}…")

            # 2. Check if text is selected
            target_text = self._selected_text
            if not target_text or not target_text.strip():
                # Try one more time to grab selection if it wasn't captured earlier
                target_text = get_selected_text()

            if not target_text or not target_text.strip():
                log.warning("No text selected in active application")
                self.hud.show_text("Select text first! ⚠️", duration_ms=2500)
                return

            # 3. Format LLM prompt
            prompt = (
                f"COMMAND: {command_text}\n\n"
                f"ORIGINAL TEXT:\n\"\"\"\n{target_text}\n\"\"\"\n\n"
                f"MODIFIED TEXT:"
            )

            # 4. Generate modified text via LLM
            output_text = asyncio.run(
                self.llm.generate(prompt=prompt, system=COMMAND_SYSTEM_PROMPT)
            )

            # Clean output robustly
            cleaned_output = _clean_llm_response(output_text)

            elapsed = time.time() - t0
            log.info("Command completed in %.2fs. Replacing selection.", elapsed)

            # 5. Replace text in active window
            if self._cancel_requested:
                log.info("Voice command cancelled before insertion")
                return

            inserted = insert_text(cleaned_output)
            if inserted:
                self.hud.set_state("done", f"Done! ({elapsed:.1f}s)")
            else:
                log.warning("Voice command: text insertion failed")
                self.hud.set_state("error")

        except Exception as e:
            log.error("Voice command execution failed: %s", e, exc_info=True)
            self.hud.set_state("error")
        finally:
            with self._processing_lock:
                self._processing = False
            self._selected_text = ""
