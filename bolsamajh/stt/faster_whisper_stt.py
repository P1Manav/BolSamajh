"""faster-whisper STT adapter — CTranslate2-backed Whisper for fast local transcription."""

import io
import time
import logging
import numpy as np
from bolsamajh.stt.base import SpeechToText, TranscriptResult

log = logging.getLogger(__name__)


MODEL_NAME_MAP = {
    "medium": "medium",
    "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
    "whisper-hinglish-swift": "MSpider3/whisper-hindi2hinglish-swift-ct2",
    "whisper-hindi2hinglish-prime": "Oriserve/Whisper-Hindi2Hinglish-Prime",
    "base": "base",
    "small": "small",
    "tiny": "tiny",
}


def resolve_model_id(model_name: str) -> str:
    """Resolve shorthand model aliases to exact HuggingFace or standard model IDs."""
    return MODEL_NAME_MAP.get(model_name, model_name)


class FasterWhisperSTT(SpeechToText):
    """Speech-to-text using faster-whisper (CTranslate2 backend)."""

    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cuda",
        compute_type: str = "int8_float16",
        language: str = "auto",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model = None

    @property
    def name(self) -> str:
        return f"faster-whisper-{self.model_size}"

    def load_model(self) -> None:
        """Load the faster-whisper model with alias resolution."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        resolved_model = resolve_model_id(self.model_size)
        log.info("Loading faster-whisper model '%s' (resolved to '%s') on %s (%s)…",
                 self.model_size, resolved_model, self.device, self.compute_type)
        t0 = time.time()
        self._model = WhisperModel(
            resolved_model,
            device=self.device,
            compute_type=self.compute_type,
        )
        log.info("Model loaded in %.1fs", time.time() - t0)

    def transcribe(self, audio_bytes: bytes) -> TranscriptResult:
        """Transcribe WAV audio bytes with silence and duration gates."""
        if self._model is None:
            self.load_model()

        # Convert WAV bytes to numpy float32 array
        audio_np = self._wav_bytes_to_np(audio_bytes)
        duration = len(audio_np) / 16000.0

        # Minimum duration gate: clips < 0.4s are discarded as transient noise
        if duration < 0.4:
            log.debug("Audio clip too short (%.2fs < 0.4s); skipping.", duration)
            return TranscriptResult(
                text="",
                language="",
                confidence=0.0,
                duration_seconds=duration,
                processing_seconds=0.0
            )

        # Silence / low-energy gate: discard audio with RMS energy below 0.003
        rms = float(np.sqrt(np.mean(audio_np ** 2))) if len(audio_np) > 0 else 0.0
        if rms < 0.003:
            log.debug("Audio clip RMS (%.5f) below silence threshold; skipping.", rms)
            return TranscriptResult(
                text="",
                language="",
                confidence=0.0,
                duration_seconds=duration,
                processing_seconds=0.0
            )

        log.debug("Transcribing %.1fs of audio (RMS=%.4f)…", duration, rms)
        t0 = time.time()

        transcribe_kwargs = {
            "beam_size": 5,
            "best_of": 5,
            "temperature": 0.0,
            "condition_on_previous_text": False,
            "vad_filter": True,
            "vad_parameters": dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        }

        # Language auto-detection with short-clip fallback (< 2.0s -> fallback to "hi")
        target_lang = self.language
        if (not target_lang or target_lang.lower() == "auto") and duration < 2.0:
            target_lang = "hi"
            log.info("Audio duration %.2fs < 2.0s: falling back from language='auto' to default 'hi'", duration)

        if target_lang and target_lang.lower() != "auto":
            transcribe_kwargs["language"] = target_lang

        segments, info = self._model.transcribe(audio_np, **transcribe_kwargs)

        # Collect all segment texts
        texts = []
        for segment in segments:
            texts.append(segment.text.strip())

        text = " ".join(texts).strip()

        # Filter out common Whisper hallucination tokens on near-silent clips
        import re
        hallucination_pattern = re.compile(
            r"^(thank you|thank you very much|thanks for watching|subtitles by|subscribe|thank you\.)$",
            re.IGNORECASE
        )
        if hallucination_pattern.match(text) or text == "[BLANK_AUDIO]":
            log.debug("Discarded hallucinated token: %r", text)
            text = ""

        elapsed = time.time() - t0

        log.info("Transcribed in %.2fs (RTF=%.2f): %s",
                 elapsed, elapsed / max(duration, 0.01), text[:80])

        return TranscriptResult(
            text=text,
            language=info.language if info else (self.language or "unknown"),
            confidence=info.language_probability if info else 0.0,
            duration_seconds=duration,
            processing_seconds=elapsed,
        )

    def unload_model(self) -> None:
        """Unload model to free VRAM."""
        if self._model is not None:
            del self._model
            self._model = None
            # Trigger CUDA memory cleanup
            try:
                import torch
                torch.cuda.empty_cache()
            except ImportError:
                pass
            log.info("faster-whisper model unloaded")

    @staticmethod
    def _wav_bytes_to_np(wav_bytes: bytes) -> np.ndarray:
        """Convert WAV bytes to float32 numpy array normalized to [-1, 1]."""
        import wave
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
        return audio.astype(np.float32) / 32768.0
