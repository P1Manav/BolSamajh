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
import re
from typing import Optional

from bolsamajh.config import AppConfig
from bolsamajh.stt.base import SpeechToText
from bolsamajh.llm.base import LLMAdapter
from bolsamajh.overlay.hud import OverlayHUD
from bolsamajh.utils.audio import MicRecorder
from bolsamajh.utils.clipboard import get_selected_text, insert_text

log = logging.getLogger(__name__)

COMMAND_SYSTEM_PROMPT = """You are BolSamajh In-App Voice Editor.
The user has highlighted text in their application and given a voice command in English, Hindi, or Hinglish.

STRICT INSTRUCTIONS:
1. Return ONLY the transformed text.
2. Do NOT add conversational replies, greetings, or explanations (no "Here is the revised text:", no "Sure!").
3. Do NOT wrap output in markdown code blocks or quotes unless the original text was code.
4. Preserve the core meaning, facts, and structure unless the command explicitly requests otherwise.
5. If the user command is in Hinglish (e.g., "formal email bana do", "chhota kar do", "grammar fix karo"), understand the intent and apply it accurately.
"""


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
        self._processing = False

    def start_command(self) -> None:
        """Start listening for command; capture highlighted text."""
        if self.recorder.is_recording or self._processing:
            return

        # Attempt to capture highlighted text at the start of command
        self._selected_text = get_selected_text()
        log.info("Voice command triggered. Selected text length: %d chars", len(self._selected_text))

        self.hud.set_state("listening", "Listening command…")
        self.recorder.start()

    def cancel(self) -> None:
        """Cancel command recording and reset HUD."""
        if self.recorder.is_recording:
            self.recorder.cancel()
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
        thread.start()

    def _process_command(self, wav_bytes: bytes) -> None:
        """Background: STT -> LLM transform -> replace selection."""
        self._processing = True
        t0 = time.time()

        try:
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

            # Clean output
            cleaned_output = output_text.strip()
            # Remove enclosing quotes if model added them
            if (cleaned_output.startswith('"""') and cleaned_output.endswith('"""')) or \
               (cleaned_output.startswith("'''") and cleaned_output.endswith("'''")):
                cleaned_output = cleaned_output[3:-3].strip()
            elif (cleaned_output.startswith('"') and cleaned_output.endswith('"')) or \
                 (cleaned_output.startswith("'") and cleaned_output.endswith("'")):
                cleaned_output = cleaned_output[1:-1].strip()

            elapsed = time.time() - t0
            log.info("Command completed in %.2fs. Replacing selection.", elapsed)

            # 5. Replace text in active window
            insert_text(cleaned_output)
            self.hud.set_state("done", f"Done! ({elapsed:.1f}s)")

        except Exception as e:
            log.error("Voice command execution failed: %s", e, exc_info=True)
            self.hud.set_state("error")
        finally:
            self._processing = False
            self._selected_text = ""
