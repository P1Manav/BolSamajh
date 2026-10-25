"""Edge-TTS adapter — free Microsoft Edge text-to-speech service."""

import io
import asyncio
import logging
import threading
from typing import Literal

import numpy as np
import sounddevice as sd

from bolsamajh.tts.base import TextToSpeech

log = logging.getLogger(__name__)

# Voice mapping per language
_VOICES = {
    "hi": "hi-IN-SwaraNeural",
    "en": "en-IN-NeerjaNeural",
    "gu": "gu-IN-DhwaniNeural",
}


class EdgeTTSAdapter(TextToSpeech):
    """TTS using Microsoft Edge's free speech service.

    No API key needed — uses the same endpoint as Edge browser's
    Read Aloud feature.
    """

    def __init__(self):
        self._stop_event = threading.Event()
        self._speaking = False
        self._playback_thread: threading.Thread | None = None

    @property
    def name(self) -> str:
        return "edge-tts"

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    async def speak(
        self,
        text: str,
        lang: Literal["hi", "en", "gu"] = "hi",
    ) -> None:
        """Generate speech and play it."""
        import edge_tts

        if not text.strip():
            return

        self._stop_event.clear()
        self._speaking = True

        # Pre-process text according to voice requirements:
        # 1. hi-IN-SwaraNeural expects Devanagari script for Hindi/Hinglish phonetics
        if lang == "hi" and not any('\u0900' <= c <= '\u097F' for c in text):
            try:
                from aksharamukha import transliterate
                text = transliterate.process("ISO", "Devanagari", text)
            except Exception as e:
                log.debug("Transliteration to Devanagari skipped: %s", e)

        # 2. gu-IN-DhwaniNeural requires Gujarati script
        elif lang == "gu" and not any('\u0A80' <= c <= '\u0AFF' for c in text):
            try:
                from aksharamukha import transliterate
                text = transliterate.process("ISO", "Gujarati", text)
            except Exception as e:
                log.debug("Transliteration to Gujarati skipped: %s", e)

        voice = _VOICES.get(lang, _VOICES["hi"])
        log.info("Edge-TTS: speaking %d chars with voice %s", len(text), voice)

        try:
            communicate = edge_tts.Communicate(text, voice)

            # Collect audio data
            audio_data = io.BytesIO()
            async for chunk in communicate.stream():
                if self._stop_event.is_set():
                    log.info("Edge-TTS: interrupted")
                    return
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])

            if self._stop_event.is_set():
                return

            # Play the audio
            audio_bytes = audio_data.getvalue()
            if audio_bytes:
                self._play_audio_bytes(audio_bytes)

        except Exception as e:
            log.error("Edge-TTS error: %s", e)
        finally:
            self._speaking = False

    def _play_audio_bytes(self, audio_bytes: bytes) -> None:
        """Play MP3 audio bytes using sounddevice."""
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
                    arr = arr.mean(axis=0)  # Mix to mono
                frames.append(arr)

            if not frames or self._stop_event.is_set():
                return

            audio = np.concatenate(frames).astype(np.float32)
            # Normalize
            if audio.max() > 1.0:
                audio = audio / 32768.0

            sample_rate = audio_stream.rate or 24000

            # Play with sounddevice (blocking but interruptible)
            sd.play(audio, samplerate=sample_rate)

            # Wait for playback to finish, checking for stop
            while sd.get_stream().active:
                if self._stop_event.is_set():
                    sd.stop()
                    return
                sd.sleep(50)

        except Exception as e:
            log.error("Audio playback error: %s", e)

    def stop(self) -> None:
        """Stop speech immediately."""
        self._stop_event.set()
        try:
            sd.stop()
        except Exception:
            pass
        self._speaking = False
        log.info("Edge-TTS: stopped")
