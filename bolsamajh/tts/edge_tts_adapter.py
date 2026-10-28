"""Edge-TTS adapter — free Microsoft Edge text-to-speech service."""

import asyncio
import io
import logging
import os
import re
import threading
from typing import Callable, Literal, Optional

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

from bolsamajh.tts.base import TextToSpeech

log = logging.getLogger(__name__)


class EdgeTTSAdapter(TextToSpeech):
    """TTS using Microsoft Edge's free speech service.

    No API key needed — uses the same endpoint as Edge browser's Read Aloud feature.
    Supports configurable voices per language and Roman Hinglish voice selection.
    """

    def __init__(
        self,
        voice_hi: str = "hi-IN-SwaraNeural",
        voice_en: str = "en-IN-NeerjaNeural",
        voice_gu: str = "gu-IN-DhwaniNeural",
        voice_roman: str = "en-IN-NeerjaNeural",
    ):
        self.voice_hi = os.getenv("BOLSAMAJH_EDGE_VOICE_HI", voice_hi)
        self.voice_en = os.getenv("BOLSAMAJH_EDGE_VOICE_EN", voice_en)
        self.voice_gu = os.getenv("BOLSAMAJH_EDGE_VOICE_GU", voice_gu)
        self.voice_roman = os.getenv("BOLSAMAJH_ROMAN_VOICE", voice_roman)
        self._stop_event = threading.Event()
        self._speaking = False
        self._on_playback_start: Optional[Callable[[], None]] = None

    @property
    def name(self) -> str:
        return "edge-tts"

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def reset_stop(self) -> None:
        """Clear stop event at the start of a new conversation turn."""
        self._stop_event.clear()

    def set_playback_start_callback(self, callback: Optional[Callable[[], None]]) -> None:
        """Register a callback triggered when the first audio sample begins playing."""
        self._on_playback_start = callback

    def _select_voice(self, text: str, lang: str) -> str:
        """Select appropriate voice based on language and script."""
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", text))
        has_gujarati = bool(re.search(r"[\u0A80-\u0AFF]", text))

        if lang in ("gu", "gujarati"):
            return self.voice_gu
        elif lang in ("en", "english"):
            return self.voice_en
        elif lang in ("hi", "hindi", "hinglish"):
            if not has_devanagari and not has_gujarati:
                # Pure Roman Hinglish -> use configured Roman voice (e.g. en-IN-NeerjaNeural)
                return self.voice_roman
            return self.voice_hi
        return self.voice_hi

    async def synthesize(self, text: str, lang: str = "hi") -> bytes:
        """Synthesize text to audio bytes without playing."""
        if not text.strip() or self._stop_event.is_set():
            return b""

        import edge_tts

        # Pre-process text according to script requirements
        has_devanagari = any("\u0900" <= c <= "\u097f" for c in text)
        has_gujarati = any("\u0a80" <= c <= "\u0aff" for c in text)

        if lang == "hi" and has_gujarati and not has_devanagari:
            try:
                from aksharamukha import transliterate

                text = transliterate.process("Gujarati", "Devanagari", text)
            except Exception as e:
                log.debug("Transliteration to Devanagari skipped: %s", e)
        elif lang == "gu" and has_devanagari and not has_gujarati:
            try:
                from aksharamukha import transliterate

                text = transliterate.process("Devanagari", "Gujarati", text)
            except Exception as e:
                log.debug("Transliteration to Gujarati skipped: %s", e)

        voice = self._select_voice(text, lang)
        try:
            communicate = edge_tts.Communicate(text, voice)
            audio_data = io.BytesIO()
            async for chunk in communicate.stream():
                if self._stop_event.is_set():
                    log.info("Edge-TTS: stream synthesis interrupted")
                    return b""
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])

            return audio_data.getvalue()
        except Exception as e:
            log.error("Edge-TTS synthesis error: %s", e)
            return b""

    async def play(self, audio_bytes: bytes) -> None:
        """Play synthesized audio bytes."""
        if not audio_bytes or self._stop_event.is_set():
            return
        self._speaking = True
        try:
            await self._play_audio_bytes_async(audio_bytes)
        finally:
            self._speaking = False

    async def speak(
        self,
        text: str,
        lang: Literal["hi", "en", "gu"] = "hi",
    ) -> None:
        """Generate speech and play it. Stoppable and non-blocking."""
        if not text.strip() or self._stop_event.is_set():
            return

        audio_bytes = await self.synthesize(text, lang)
        if audio_bytes and not self._stop_event.is_set():
            await self.play(audio_bytes)

    async def _play_audio_bytes_async(self, audio_bytes: bytes) -> None:
        """Decode and play MP3 audio without blocking the event loop."""
        try:
            import av

            container = av.open(io.BytesIO(audio_bytes))
            audio_stream = container.streams.audio[0]

            frames = []
            for frame in container.decode(audio_stream):
                if self._stop_event.is_set():
                    return
                arr = frame.to_ndarray()
                if arr.ndim > 1:
                    arr = arr.mean(axis=0)
                frames.append(arr)

            if not frames or self._stop_event.is_set():
                return

            audio = np.concatenate(frames).astype(np.float32)
            if audio.max() > 1.0:
                audio = audio / 32768.0

            sample_rate = audio_stream.rate or 24000

            if sd is None:
                log.warning("sounddevice is not available; cannot play synthesized audio")
                return

            # Start playback
            sd.play(audio, samplerate=sample_rate)

            # Notify listeners (e.g. BargeInMonitor) that first sample began playing
            if self._on_playback_start:
                try:
                    self._on_playback_start()
                except Exception as e:
                    log.debug("Error in on_playback_start callback: %s", e)

            # Wait for playback to finish asynchronously, checking for stop event
            while True:
                if self._stop_event.is_set():
                    sd.stop()
                    return
                stream = sd.get_stream()
                if stream is None or not stream.active:
                    break
                await asyncio.sleep(0.04)

        except Exception as e:
            log.error("Audio playback error: %s", e)

    def stop(self) -> None:
        """Stop speech immediately."""
        self._stop_event.set()
        if sd is not None:
            try:
                sd.stop()
            except Exception:
                pass
        self._speaking = False
        log.info("Edge-TTS: stopped")
