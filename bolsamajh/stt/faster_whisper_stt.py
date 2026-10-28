"""faster-whisper STT adapter — CTranslate2-backed Whisper for fast local transcription."""

import io
import re
import time
import wave
import logging
import numpy as np
from bolsamajh.stt.base import SpeechToText, TranscriptResult

log = logging.getLogger(__name__)


# Verified CT2 model repositories on Hugging Face (containing model.bin)
MODEL_NAME_MAP = {
    "medium": "medium",
    "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
    "whisper-hinglish-swift": "MSpider3/whisper-hindi2hinglish-swift-ct2",
    "base": "base",
    "small": "small",
    "tiny": "tiny",
}

_HALLUCINATION_PHRASES = {
    "thank you", "thank you very much", "thanks for watching", "subtitles by",
    "subscribe", "thank you.", "[blank_audio]", "you", "bye", "so", "the end",
    "धन्यवाद", "देखने के लिए धन्यवाद", "सब्सक्राइब करें", "कृपया चैनल को सब्सक्राइब करें",
    "शुक्रिया", "नमस्ते", "धन्यवाद।"
}


def resolve_model_id(model_name: str) -> str:
    """Resolve shorthand model aliases to exact HuggingFace or standard model IDs."""
    return MODEL_NAME_MAP.get(model_name, model_name)


def _has_repeated_ngrams(text: str) -> bool:
    """Detect pathological repetition of n-grams (Whisper hallucination symptom)."""
    words = text.split()
    if len(words) >= 4:
        # Check repeated unigrams (>= 4 times consecutively)
        for i in range(len(words) - 3):
            if words[i].lower() == words[i+1].lower() == words[i+2].lower() == words[i+3].lower():
                return True
        # Check repeated bigrams (>= 3 times consecutively)
        if len(words) >= 6:
            bigrams = [f"{words[i]} {words[i+1]}".lower() for i in range(len(words) - 1)]
            for i in range(len(bigrams) - 2):
                if bigrams[i] == bigrams[i+1] == bigrams[i+2]:
                    return True
    return False


class FasterWhisperSTT(SpeechToText):
    """Speech-to-text using faster-whisper (CTranslate2 backend)."""

    def __init__(
        self,
        model_size: str = "large-v3-turbo",
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
        try:
            self._model = WhisperModel(
                resolved_model,
                device=self.device,
                compute_type=self.compute_type,
            )
        except Exception as e:
            if self.device != "cpu":
                log.warning("Failed to initialize model on %s (%s), falling back to CPU small model (int8): %s",
                            self.device, self.compute_type, e)
                self.device = "cpu"
                self.compute_type = "int8"
                self.model_size = "small"
                self._model = WhisperModel(
                    "small",
                    device="cpu",
                    compute_type="int8",
                )
            else:
                raise
        log.info("Model loaded in %.1fs", time.time() - t0)

    def transcribe(self, audio_bytes: bytes) -> TranscriptResult:
        """Transcribe WAV audio bytes with silence and duration gates."""
        if self._model is None:
            self.load_model()

        # Convert WAV bytes to numpy float32 array, normalized and resampled to 16 kHz mono
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

        # Do not force Hindi on short clips when language is auto
        target_lang = self.language
        if target_lang and target_lang.lower() != "auto":
            transcribe_kwargs["language"] = target_lang

        try:
            segments, info = self._model.transcribe(audio_np, **transcribe_kwargs)
            texts = []
            for segment in segments:
                # Segment-level hallucination filtering
                if getattr(segment, "no_speech_prob", 0.0) > 0.60:
                    continue
                if getattr(segment, "avg_logprob", 0.0) < -1.0:
                    continue
                texts.append(segment.text.strip())
        except Exception as e:
            if self.device != "cpu" and ("cublas" in str(e).lower() or "cuda" in str(e).lower()):
                log.warning("CUDA execution failed at runtime (%s), falling back to CPU small model (int8)", e)
                self.device = "cpu"
                self.compute_type = "int8"
                self.model_size = "small"
                self._model = None
                self.load_model()
                segments, info = self._model.transcribe(audio_np, **transcribe_kwargs)
                texts = []
                for segment in segments:
                    if getattr(segment, "no_speech_prob", 0.0) > 0.60:
                        continue
                    if getattr(segment, "avg_logprob", 0.0) < -1.0:
                        continue
                    texts.append(segment.text.strip())
            else:
                raise

        text = " ".join(texts).strip()

        # Strengthened hallucination and silence filtering
        norm_text = text.lower().strip()
        if norm_text in _HALLUCINATION_PHRASES or norm_text == "[blank_audio]":
            log.debug("Discarded hallucinated token: %r", text)
            text = ""
        elif _has_repeated_ngrams(text):
            log.debug("Discarded text with repeated n-grams: %r", text)
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
        """Convert WAV bytes to float32 numpy array normalized to [-1, 1] at 16 kHz mono."""
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            framerate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())

        if sampwidth == 2:
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            audio = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif sampwidth == 1:
            audio = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

        # Downmix multi-channel to mono
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        # Resample to 16 kHz if necessary
        if framerate != 16000 and len(audio) > 0:
            old_indices = np.linspace(0, len(audio) - 1, len(audio))
            target_length = int(len(audio) * 16000 / framerate)
            new_indices = np.linspace(0, len(audio) - 1, target_length)
            audio = np.interp(new_indices, old_indices, audio).astype(np.float32)

        return audio

