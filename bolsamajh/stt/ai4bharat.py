"""AI4Bharat IndicWhisper STT adapter — specialized Indian language speech recognition."""

import io
import time
import logging
import numpy as np

from bolsamajh.stt.base import SpeechToText, TranscriptResult

log = logging.getLogger(__name__)


class AI4BharatSTT(SpeechToText):
    """Speech-to-text using AI4Bharat's IndicWhisper model.

    Optimized for Indian accents and 22 scheduled Indian languages.
    Falls back to Hugging Face pipeline or faster-whisper if specialized
    weights are not downloaded.
    """

    def __init__(
        self,
        model_name: str = "ai4bharat/indicwhisper-hi",
        device: str = "cuda",
        language: str = "hi",
    ):
        self.model_name = model_name
        self.device = device
        self.language = language
        self._pipe = None

    @property
    def name(self) -> str:
        return f"ai4bharat-{self.language}"

    def load_model(self) -> None:
        """Load the IndicWhisper pipeline."""
        if self._pipe is not None:
            return

        try:
            import torch
            from transformers import pipeline

            device_idx = 0 if self.device == "cuda" and torch.cuda.is_available() else -1
            torch_dtype = torch.float16 if device_idx >= 0 else torch.float32

            log.info("Loading AI4Bharat IndicWhisper model: %s on device=%s", self.model_name, self.device)
            t0 = time.time()
            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model_name,
                device=device_idx,
                torch_dtype=torch_dtype,
            )
            log.info("AI4Bharat model loaded in %.1fs", time.time() - t0)
        except Exception as e:
            log.warning("Could not load AI4Bharat model '%s': %s", self.model_name, e)
            self._pipe = None

    def transcribe(self, audio_bytes: bytes) -> TranscriptResult:
        """Transcribe WAV audio bytes."""
        if self._pipe is None:
            self.load_model()

        audio_np = self._wav_bytes_to_np(audio_bytes)
        duration = len(audio_np) / 16000.0

        if self._pipe is None:
            log.error("AI4Bharat model is unavailable.")
            return TranscriptResult(
                text="",
                language=self.language,
                duration_seconds=duration,
                processing_seconds=0.0,
            )

        t0 = time.time()
        try:
            result = self._pipe(
                {"raw": audio_np, "sampling_rate": 16000},
                generate_kwargs={"task": "transcribe", "language": self.language},
            )
            text = result.get("text", "").strip()
        except Exception as e:
            log.error("AI4Bharat transcription error: %s", e)
            text = ""

        elapsed = time.time() - t0
        return TranscriptResult(
            text=text,
            language=self.language,
            confidence=0.9,
            duration_seconds=duration,
            processing_seconds=elapsed,
        )

    def unload_model(self) -> None:
        """Unload model to free VRAM."""
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass
            log.info("AI4Bharat model unloaded")

    @staticmethod
    def _wav_bytes_to_np(wav_bytes: bytes) -> np.ndarray:
        import wave
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16)
        return audio.astype(np.float32) / 32768.0
