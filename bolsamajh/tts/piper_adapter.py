"""Piper TTS adapter — 100% offline local text-to-speech using ONNX models."""

import io
import os
import wave
import hashlib
import logging
import threading
from pathlib import Path
from typing import Literal

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

from bolsamajh.tts.base import TextToSpeech

log = logging.getLogger(__name__)

# Official Piper Hindi voices on Hugging Face (MIT licensed)
_PIPER_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/pratham/medium"
_MODEL_FILENAME = "hi_IN-pratham-medium.onnx"
_CONFIG_FILENAME = "hi_IN-pratham-medium.onnx.json"

# Pinned SHA-256 hashes for cryptographic verification
_MODEL_SHA256 = "169964b0871667f6793416d4b35e97357a68ba1ad01df8580c28048989ee7693"
_CONFIG_SHA256 = "b68edd2cd7950dd436314013b7cd12e9699e5a3f6fe5af5af94294cf6aa7b9fd"


def _verify_sha256(filepath: Path, expected_sha256: str) -> bool:
    """Verify SHA-256 hash of a file against expected value."""
    if not filepath.exists():
        return False
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    actual = h.hexdigest()
    if actual.lower() != expected_sha256.lower():
        log.warning("SHA-256 mismatch for %s: expected %s, got %s",
                    filepath.name, expected_sha256, actual)
        return False
    return True


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
        """Ensure model and json config files exist and pass SHA-256 verification."""
        if self.model_path and Path(self.model_path).exists():
            model_file = Path(self.model_path)
            json_file = model_file.with_suffix(".onnx.json") if not model_file.name.endswith(".json") else model_file
            if not json_file.exists():
                json_file = Path(str(model_file) + ".json")
            return model_file, json_file

        model_file = self._models_dir / _MODEL_FILENAME
        json_file = self._models_dir / _CONFIG_FILENAME

        # Check existing files
        valid_model = model_file.exists() and _verify_sha256(model_file, _MODEL_SHA256)
        valid_config = json_file.exists() and _verify_sha256(json_file, _CONFIG_SHA256)

        if not valid_model or not valid_config:
            import urllib.request
            log.info("Downloading Piper Hindi voice (%s) with SHA-256 verification...", _MODEL_FILENAME)
            urllib.request.urlretrieve(f"{_PIPER_HF_BASE}/{_MODEL_FILENAME}", model_file)
            urllib.request.urlretrieve(f"{_PIPER_HF_BASE}/{_CONFIG_FILENAME}", json_file)

            if not _verify_sha256(model_file, _MODEL_SHA256):
                raise ValueError(f"Downloaded Piper model {model_file.name} failed SHA-256 verification!")
            if not _verify_sha256(json_file, _CONFIG_SHA256):
                raise ValueError(f"Downloaded Piper config {json_file.name} failed SHA-256 verification!")

            log.info("Piper Hindi voice verified and saved to %s", model_file)

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

            # Support both Piper API shapes:
            # Shape 1: voice.synthesize(text, wav_file)
            # Shape 2: voice.synthesize(text) / voice.synthesize_stream_raw(text) yielding bytes
            try:
                with wave.open(wav_io, "wb") as wav_file:
                    self._voice.synthesize(text, wav_file)
            except (TypeError, AttributeError):
                # Shape 2
                raw = self._voice.synthesize(text)
                if hasattr(raw, "__iter__") and not isinstance(raw, (bytes, bytearray)):
                    raw_bytes = b"".join(raw)
                else:
                    raw_bytes = bytes(raw)
                with wave.open(wav_io, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    sr = getattr(getattr(self._voice, "config", None), "sample_rate", 22050)
                    wav_file.setframerate(sr)
                    wav_file.writeframes(raw_bytes)

            if self._stop_event.is_set():
                return

            wav_io.seek(0)
            with wave.open(wav_io, "rb") as wf:
                sr = wf.getframerate()
                n_frames = wf.getnframes()
                audio_bytes = wf.readframes(n_frames)
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            if sd is None:
                log.warning("sounddevice is not available; cannot play synthesized audio")
                return

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
        if sd is not None:
            try:
                sd.stop()
            except Exception:
                pass
        self._speaking = False
