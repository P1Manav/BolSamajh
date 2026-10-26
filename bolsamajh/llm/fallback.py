"""Automatic fallback LLM adapter — gracefully switches between Ollama and Google AI."""

import logging
from typing import AsyncIterator

from bolsamajh.llm.base import LLMAdapter

log = logging.getLogger(__name__)


class FallbackLLMAdapter(LLMAdapter):
    """Wraps a primary and secondary LLM adapter, falling back automatically."""

    def __init__(self, primary: LLMAdapter, secondary: LLMAdapter):
        self.primary = primary
        self.secondary = secondary
        self._active_engine = primary.name

    @property
    def name(self) -> str:
        return f"fallback({self.primary.name} -> {self.secondary.name})"

    @property
    def active_engine(self) -> str:
        return self._active_engine

    @property
    def fallback_status(self) -> str:
        """Return human-readable status of the fallback engine."""
        if getattr(self.secondary, "disabled", False):
            return "LLM fallback unavailable"
        if hasattr(self.secondary, "_api_key") and not getattr(self.secondary, "_api_key", ""):
            return "LLM fallback unavailable"
        return "available"

    async def is_available(self) -> bool:
        """Available if either primary or secondary is available."""
        if await self.primary.is_available():
            self._active_engine = self.primary.name
            return True
        if self.fallback_status != "LLM fallback unavailable" and await self.secondary.is_available():
            self._active_engine = self.secondary.name
            return True
        return False

    async def generate(self, prompt: str, system: str = "") -> str:
        """Attempt generation with primary; fall back to secondary on failure."""
        try:
            res = await self.primary.generate(prompt, system=system)
            self._active_engine = self.primary.name
            return res
        except Exception as e:
            if self.fallback_status == "LLM fallback unavailable":
                log.warning("Primary LLM (%s) failed: %s. LLM fallback unavailable.", self.primary.name, e)
                raise RuntimeError(f"Primary LLM ({self.primary.name}) failed and LLM fallback unavailable: {e}")
            log.warning("Primary LLM (%s) failed: %s. Falling back to %s...",
                        self.primary.name, e, self.secondary.name)
            try:
                res = await self.secondary.generate(prompt, system=system)
                self._active_engine = self.secondary.name
                return res
            except Exception as e_sec:
                log.warning("Secondary LLM (%s) failed: %s", self.secondary.name, e_sec)
                raise RuntimeError(f"Both primary ({self.primary.name}) and secondary ({self.secondary.name}) failed: {e_sec}")

    async def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Attempt streaming with primary; fall back to secondary if primary fails early."""
        try:
            started = False
            async for token in self.primary.generate_stream(prompt, system=system):
                started = True
                yield token
            self._active_engine = self.primary.name
            return
        except Exception as e:
            if started:
                # If streaming already started and yielded tokens, we cannot cleanly re-stream from secondary
                log.error("Primary LLM (%s) streaming aborted mid-stream: %s", self.primary.name, e)
                raise
            if self.fallback_status == "LLM fallback unavailable":
                log.warning("Primary LLM (%s) failed to start stream: %s. LLM fallback unavailable.", self.primary.name, e)
                raise RuntimeError(f"Primary LLM ({self.primary.name}) failed and LLM fallback unavailable: {e}")
            log.warning("Primary LLM (%s) failed to start stream: %s. Falling back to %s...",
                        self.primary.name, e, self.secondary.name)
            try:
                async for token in self.secondary.generate_stream(prompt, system=system):
                    yield token
                self._active_engine = self.secondary.name
            except Exception as e_sec:
                log.warning("Secondary LLM (%s) streaming failed: %s", self.secondary.name, e_sec)
                raise RuntimeError(f"Both primary ({self.primary.name}) and secondary ({self.secondary.name}) streaming failed: {e_sec}")
