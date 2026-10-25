"""Unit tests for LLM adapters and fallback mechanism."""

import pytest
from typing import AsyncIterator
from bolsamajh.llm.base import LLMAdapter
from bolsamajh.llm.fallback import FallbackLLMAdapter
from bolsamajh.llm.google_ai import GoogleAIAdapter
from bolsamajh.llm.ollama_adapter import OllamaAdapter


class MockLLMAdapter(LLMAdapter):
    def __init__(self, name_str: str, should_fail: bool = False, response_text: str = "mock answer"):
        self._name = name_str
        self.should_fail = should_fail
        self.response_text = response_text

    @property
    def name(self) -> str:
        return self._name

    async def is_available(self) -> bool:
        return not self.should_fail

    async def generate(self, prompt: str, system: str = "") -> str:
        if self.should_fail:
            raise RuntimeError(f"{self._name} failed!")
        return f"{self.response_text} for {prompt}"

    async def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        if self.should_fail:
            raise RuntimeError(f"{self._name} stream failed!")
        for word in self.response_text.split():
            yield word + " "


@pytest.mark.anyio
async def test_fallback_primary_success():
    primary = MockLLMAdapter("primary", should_fail=False, response_text="primary answer")
    secondary = MockLLMAdapter("secondary", should_fail=False, response_text="secondary answer")
    fallback = FallbackLLMAdapter(primary, secondary)

    assert await fallback.is_available()
    res = await fallback.generate("test prompt")
    assert "primary answer" in res
    assert fallback.active_engine == "primary"


@pytest.mark.anyio
async def test_fallback_secondary_when_primary_fails():
    primary = MockLLMAdapter("primary", should_fail=True)
    secondary = MockLLMAdapter("secondary", should_fail=False, response_text="secondary answer")
    fallback = FallbackLLMAdapter(primary, secondary)

    assert await fallback.is_available()
    res = await fallback.generate("test prompt")
    assert "secondary answer" in res
    assert fallback.active_engine == "secondary"


@pytest.mark.anyio
async def test_google_ai_headers_and_config():
    adapter = GoogleAIAdapter(model="gemini-1.5-flash")
    headers = adapter._get_headers()
    assert "x-goog-api-key" in headers
    assert "Content-Type" in headers
    assert adapter.name == "google-ai/gemini-1.5-flash"


def test_ollama_num_ctx():
    adapter = OllamaAdapter(model="gemma3:4b", num_ctx=8192)
    assert adapter.num_ctx == 8192


@pytest.mark.anyio
async def test_google_ai_default_model_and_error_handling(monkeypatch):
    # Verify default model is gemini-2.0-flash
    adapter = GoogleAIAdapter()
    assert adapter.model == "gemini-2.0-flash"
    assert adapter.name == "google-ai/gemini-2.0-flash"

    # Verify list_available_models returns empty list when no key is set
    assert await adapter.list_available_models() == []

