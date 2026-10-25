"""faster-whisper STT adapter — CTranslate2-backed Whisper for fast local transcription."""

import io
import time
import logging
import numpy as np
from bolsamajh.stt.base import SpeechToText, TranscriptResult

log = logging.getLogger(__name__)


class FasterWhisperSTT(SpeechToText):
    """Speech-to-text using faster-whisper (CTranslate2 backend)."""

    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cuda",
        compute_type: str = "int8",
        language: str = "hi",
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
        """Load the faster-whisper model."""
        if self._model is not None:
            return

        from faster_whisper import WhisperModel

        log.info("Loading faster-whisper model '%s' on %s (%s)…",
                 self.model_size, self.device, self.compute_type)
        t0 = time.time()
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        log.info("Model loaded in %.1fs", time.time() - t0)

    def transcribe(self, audio_bytes: bytes) -> TranscriptResult:
        """Transcribe WAV audio bytes."""
        if self._model is None:
            self.load_model()

        # Convert WAV bytes to numpy float32 array
        audio_np = self._wav_bytes_to_np(audio_bytes)
        duration = len(audio_np) / 16000.0

        log.debug("Transcribing %.1fs of audio…", duration)
        t0 = time.time()

        segments, info = self._model.transcribe(
            audio_np,
            language=self.language,
            initial_prompt="Hinglish, Hindi, Devanagari, English. Bolo. Samjho.",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200,
            ),
        )


        # Collect all segment texts
        texts = []
        for segment in segments:
            texts.append(segment.text.strip())

        text = " ".join(texts)
        elapsed = time.time() - t0

        log.info("Transcribed in %.2fs (RTF=%.2f): %s",
                 elapsed, elapsed / max(duration, 0.01), text[:80])

        return TranscriptResult(
            text=text,
            language=info.language if info else self.language,
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
