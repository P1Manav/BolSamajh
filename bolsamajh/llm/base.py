"""Abstract base for LLM adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class LLMResponse:
    """Response from an LLM generation."""

    text: str
    model: str = ""
    tokens_used: int = 0
    processing_seconds: float = 0.0


class LLMAdapter(ABC):
    """Abstract LLM adapter interface."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate a complete response.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Returns:
            The generated text.
        """
        ...

    @abstractmethod
    async def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Generate a streaming response.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Yields:
            Text chunks as they are generated.
        """
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this LLM backend is available."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this LLM engine."""
        ...
