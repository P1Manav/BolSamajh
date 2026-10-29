"""Piper TTS adapter — 100% offline local text-to-speech using ONNX models."""

import asyncio
import hashlib
import io
import logging
import os
import sys
import threading
import wave
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
# Pinned to specific Hugging Face commit hash for supply-chain integrity:
# Commit: 5041a7a49ae5b3a0f30e6837769eb03fdbb231bd
_PIPER_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/5041a7a49ae5b3a0f30e6837769eb03fdbb231bd/hi/hi_IN/pratham/medium"
_MODEL_FILENAME = "hi_IN-pratham-medium.onnx"
_CONFIG_FILENAME = "hi_IN-pratham-medium.onnx.json"

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
        log.warning(
            "SHA-256 mismatch for %s: expected %s, got %s", filepath.name, expected_sha256, actual
        )
        return False
    return True


def _download_file_with_timeout(url: str, dest_path: Path, timeout_sec: float = 30.0) -> None:
    """Download file over HTTP with explicit timeout and progress logging."""
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "BolSamajh-Piper/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        temp_dest = dest_path.with_suffix(".tmp")
        with open(temp_dest, "wb") as f:
            while chunk := resp.read(65536):
                f.write(chunk)
        temp_dest.replace(dest_path)


class PiperTTSAdapter(TextToSpeech):
    """Offline local TTS using Piper ONNX models.

    Supports verified open models: hi_IN-pratham-medium.
    Respects language constraints, downloads with timeout, and saves models to user data directory.
    """

    def __init__(self, model_path: str = "", allow_edge_fallback: bool = False):
        self.model_path = model_path
        self.allow_edge_fallback = allow_edge_fallback
        self._voice = None
        self._voice_lock = threading.Lock()
        self._speaking = False
        self._stop_event = threading.Event()

        # Locate model directory outside the repo tree in user data directory
        base_user_data = Path(
            os.getenv(
                "BOLSAMAJH_MODELS_DIR", Path.home() / ".cache" / "bolsamajh" / "models" / "piper"
            )
        )
        # Fall back to repo models/piper if user already downloaded weights there
        repo_models = Path(__file__).parent.parent.parent / "models" / "piper"
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass and (Path(meipass) / "models" / "piper" / _MODEL_FILENAME).exists():
                repo_models = Path(meipass) / "models" / "piper"
            else:
                exe_cand = Path(sys.executable).parent / "_internal" / "models" / "piper"
                if (exe_cand / _MODEL_FILENAME).exists():
                    repo_models = exe_cand
        if repo_models.exists() and (repo_models / _MODEL_FILENAME).exists():
            self._models_dir = repo_models
        else:
            self._models_dir = base_user_data
        self._models_dir.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "piper-offline"

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    def reset_stop(self) -> None:
        """Clear stop event at turn start."""
        self._stop_event.clear()

    def _ensure_model(self) -> tuple[Path, Path]:
        """Ensure model and json config files exist and pass SHA-256 verification."""
        if self.model_path and Path(self.model_path).exists():
            model_file = Path(self.model_path)
            json_file = (
                model_file.with_suffix(".onnx.json")
                if not model_file.name.endswith(".json")
                else model_file
            )
            if not json_file.exists():
                json_file = Path(str(model_file) + ".json")
            return model_file, json_file

        model_file = self._models_dir / _MODEL_FILENAME
        json_file = self._models_dir / _CONFIG_FILENAME

        valid_model = model_file.exists() and _verify_sha256(model_file, _MODEL_SHA256)
        valid_config = json_file.exists() and _verify_sha256(json_file, _CONFIG_SHA256)

        if not valid_model or not valid_config:
            log.info("Downloading Piper Hindi voice (%s) with timeout...", _MODEL_FILENAME)
            _download_file_with_timeout(
                f"{_PIPER_HF_BASE}/{_MODEL_FILENAME}", model_file, timeout_sec=60.0
            )
            _download_file_with_timeout(
                f"{_PIPER_HF_BASE}/{_CONFIG_FILENAME}", json_file, timeout_sec=30.0
            )

            if not _verify_sha256(model_file, _MODEL_SHA256):
                raise ValueError(
                    f"Downloaded Piper model {model_file.name} failed SHA-256 verification!"
                )
            if not _verify_sha256(json_file, _CONFIG_SHA256):
                raise ValueError(
                    f"Downloaded Piper config {json_file.name} failed SHA-256 verification!"
                )

            log.info("Piper Hindi voice verified and saved to %s", model_file)

        return model_file, json_file

    def _load_voice(self):
        """Load PiperVoice model into memory."""
        if self._voice is not None:
            return

        with self._voice_lock:
            if self._voice is not None:
                return

            from piper.voice import PiperVoice

            model_file, json_file = self._ensure_model()
            log.info("Loading Piper offline voice from %s...", model_file.name)
            self._voice = PiperVoice.load(str(model_file), config_path=str(json_file))
            log.info("Piper offline voice loaded successfully.")

    def synthesize_to_bytes(self, text: str) -> bytes:
        """Synthesize text offline using Piper ONNX and return raw WAV bytes."""
        if not text.strip():
            return b""

        if self._voice is None:
            self._load_voice()

        has_devanagari = any("\u0900" <= c <= "\u097f" for c in text)
        has_gujarati = any("\u0a80" <= c <= "\u0aff" for c in text)
        if has_gujarati and not has_devanagari:
            try:
                from aksharamukha import transliterate

                text = transliterate.process("Gujarati", "Devanagari", text)
            except Exception as e:
                log.debug("Transliteration to Devanagari skipped: %s", e)

        wav_io = io.BytesIO()

        try:
            with wave.open(wav_io, "wb") as wav_file:
                if hasattr(self._voice, "synthesize_wav"):
                    self._voice.synthesize_wav(text, wav_file)
                else:
                    self._voice.synthesize(text, wav_file)
        except Exception:
            chunks = []
            for chunk in self._voice.synthesize(text):
                if hasattr(chunk, "audio_int16_bytes"):
                    chunks.append(chunk.audio_int16_bytes)
                elif hasattr(chunk, "audio"):
                    chunks.append(bytes(chunk.audio))
                elif isinstance(chunk, (bytes, bytearray)):
                    chunks.append(bytes(chunk))
            raw_bytes = b"".join(chunks)
            sr = getattr(getattr(self._voice, "config", None), "sample_rate", 22050)
            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sr)
                wav_file.writeframes(raw_bytes)

        return wav_io.getvalue()

    async def synthesize(self, text: str, lang: str = "hi") -> bytes:
        """Synthesize text offline using Piper ONNX and return raw WAV bytes."""
        if not text.strip() or self._stop_event.is_set():
            return b""

        # Respect language: Piper model is specifically Hindi (hi_IN-pratham-medium)
        if lang in ("en", "english", "gu", "gujarati"):
            if self.allow_edge_fallback:
                log.warning("Piper TTS is Hindi-only. Delegating %s text to Edge-TTS.", lang)
                from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter

                edge = EdgeTTSAdapter()
                return await edge.synthesize(text, lang=lang)
            else:
                log.warning(
                    "Piper offline TTS only voices Hindi text. Refusing non-Hindi audio for lang='%s'.",
                    lang,
                )
                return b""

        return await asyncio.to_thread(self.synthesize_to_bytes, text)

    async def play(self, audio_bytes: bytes) -> None:
        """Play synthesized WAV audio bytes."""
        if not audio_bytes or self._stop_event.is_set():
            return

        self._speaking = True
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                sr = wf.getframerate()
                n_frames = wf.getnframes()
                raw_frames = wf.readframes(n_frames)
                audio_data = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0

            if sd is None:
                log.warning("sounddevice is not available; cannot play synthesized audio")
                return

            if self._playback_callback:
                try:
                    self._playback_callback()
                except Exception as e:
                    log.debug("Playback callback error: %s", e)

            sd.play(audio_data, samplerate=sr)
            while True:
                if self._stop_event.is_set():
                    sd.stop()
                    return
                stream = sd.get_stream()
                if stream is None or not stream.active:
                    break
                await asyncio.sleep(0.04)

        except Exception as e:
            log.error("Piper TTS playback error: %s", e)
        finally:
            self._speaking = False

    async def speak(
        self,
        text: str,
        lang: Literal["hi", "en", "gu"] = "hi",
    ) -> None:
        """Synthesize and play speech. Respects language support boundaries."""
        if not text.strip() or self._stop_event.is_set():
            return

        audio_bytes = await self.synthesize(text, lang)
        if audio_bytes and not self._stop_event.is_set():
            await self.play(audio_bytes)

    def stop(self) -> None:
        """Stop speech immediately."""
        self._stop_event.set()
        if sd is not None:
            try:
                sd.stop()
            except Exception:
                pass
        self._speaking = False
