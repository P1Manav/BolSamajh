"""Abstract base for speech-to-text adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranscriptResult:
    """Result from a speech-to-text transcription."""
    text: str
    language: str = ""
    confidence: float = 0.0
    duration_seconds: float = 0.0
    processing_seconds: float = 0.0   # Wall-clock time for transcription


class SpeechToText(ABC):
    """Abstract speech-to-text adapter interface."""

    @abstractmethod
    def load_model(self) -> None:
        """Load the STT model into memory. Call once at startup."""
        ...

    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> TranscriptResult:
        """Transcribe WAV audio bytes to text.

        Args:
            audio_bytes: 16-bit PCM WAV data at 16 kHz mono.

        Returns:
            TranscriptResult with transcribed text and metadata.
        """
        ...

    @abstractmethod
    def unload_model(self) -> None:
        """Unload the model to free VRAM/RAM."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this STT engine."""
        ...
