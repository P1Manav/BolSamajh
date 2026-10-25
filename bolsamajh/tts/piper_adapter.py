"""Piper TTS adapter — 100% offline local text-to-speech using ONNX models."""

import io
import os
import wave
import logging
import threading
from pathlib import Path
from typing import Literal

import numpy as np
import sounddevice as sd

from bolsamajh.tts.base import TextToSpeech

log = logging.getLogger(__name__)

# Official Piper Hindi voices on Hugging Face (MIT licensed)
_PIPER_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/pratham/medium"
_MODEL_FILENAME = "hi_IN-pratham-medium.onnx"
_CONFIG_FILENAME = "hi_IN-pratham-medium.onnx.json"


class PiperTTSAdapter(TextToSpeech):
    """Offline local TTS using Piper ONNX models.

    Supports verified open models: hi_IN-pratham-medium, hi_IN-priyamvada-medium.
    """

    def __init__(self, model_path: str = ""):
        self.model_path = model_path
        self._voice = None
        self._speaking = False
        self._stop_event = threading.Event()
        self._models_dir = Path(__file__).parent.parent.parent / "models" / "piper"
        self._models_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "piper-offline"

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def _ensure_model(self) -> tuple[Path, Path]:
        """Ensure model and json config files exist, downloading if needed."""
        if self.model_path and Path(self.model_path).exists():
            model_file = Path(self.model_path)
            json_file = model_file.with_suffix(".onnx.json") if not model_file.name.endswith(".json") else model_file
            if not json_file.exists():
                json_file = Path(str(model_file) + ".json")
            return model_file, json_file

        model_file = self._models_dir / _MODEL_FILENAME
        json_file = self._models_dir / _CONFIG_FILENAME

        if not model_file.exists() or not json_file.exists():
            import urllib.request
            log.info("Downloading Piper Hindi voice (%s)...", _MODEL_FILENAME)
            urllib.request.urlretrieve(f"{_PIPER_HF_BASE}/{_MODEL_FILENAME}", model_file)
            urllib.request.urlretrieve(f"{_PIPER_HF_BASE}/{_CONFIG_FILENAME}", json_file)
            log.info("Piper Hindi voice downloaded to %s", model_file)

        return model_file, json_file

    def _load_voice(self):
        """Load PiperVoice model into memory."""
        if self._voice is not None:
            return

        from piper.voice import PiperVoice

        model_file, json_file = self._ensure_model()
        log.info("Loading Piper offline voice from %s...", model_file.name)
        self._voice = PiperVoice.load(str(model_file), config_path=str(json_file))
        log.info("Piper offline voice loaded successfully.")

    async def speak(
        self,
        text: str,
        lang: Literal["hi", "en", "gu"] = "hi",
    ) -> None:
        """Synthesize and play speech completely offline."""
        if not text.strip():
            return

        self._stop_event.clear()
        self._speaking = True

        try:
            self._load_voice()

            # Piper Hindi voice expects Devanagari script.
            # If Roman Hinglish text is provided, transliterate to Devanagari.
            has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
            if not has_devanagari:
                from aksharamukha import transliterate
                text = transliterate.process("ISO", "Devanagari", text)

            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wav_file:
                self._voice.synthesize(text, wav_file)

            if self._stop_event.is_set():
                return

            wav_io.seek(0)
            with wave.open(wav_io, "rb") as wf:
                sr = wf.getframerate()
                n_frames = wf.getnframes()
                audio_bytes = wf.readframes(n_frames)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            sd.play(audio_data, samplerate=sr)
            while sd.get_stream().active:
                if self._stop_event.is_set():
                    sd.stop()
                    return
                sd.sleep(50)

        except Exception as e:
            log.error("Piper TTS synthesis error: %s", e)
        finally:
            self._speaking = False

    def stop(self) -> None:
        """Stop speech immediately."""
        self._stop_event.set()
        try:
            sd.stop()
        except Exception:
            pass
        self._speaking = False
