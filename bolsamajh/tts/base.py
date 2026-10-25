"""Abstract base for TTS adapters."""

from abc import ABC, abstractmethod
from typing import Literal


class TextToSpeech(ABC):
    """Abstract text-to-speech adapter interface."""

    @abstractmethod
    async def speak(
        self,
        text: str,
        lang: Literal["hi", "en", "gu"] = "hi",
    ) -> None:
        """Speak the given text aloud.

        Args:
            text: Text to speak.
            lang: Language code for voice selection.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop any ongoing speech playback immediately."""
        ...

    @property
    @abstractmethod
    def is_speaking(self) -> bool:
        """Whether audio is currently playing."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this TTS engine."""
        ...
