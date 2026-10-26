"""Unit tests for LLM adapters and fallback mechanism."""

import pytest
import httpx
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
    # Verify default model is gemini-3.5-flash
    adapter = GoogleAIAdapter()
    assert adapter.model == "gemini-3.5-flash"
    assert adapter.name == "google-ai/gemini-3.5-flash"

    # Verify list_available_models returns empty list when no key is set
    assert await adapter.list_available_models() == []


@pytest.mark.anyio
async def test_google_ai_fallback_on_404(monkeypatch):
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "test-key")
    adapter = GoogleAIAdapter(model="gemini-deprecated-model")

    # Mock list_available_models to return candidates
    async def mock_list(self):
        return ["gemini-deprecated-model", "gemini-3.5-flash"]

    monkeypatch.setattr(GoogleAIAdapter, "list_available_models", mock_list)

    # Mock httpx.AsyncClient.post
    posted_urls = []

    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("error", request=None, response=self)

    async def mock_post(client_self, url, **kwargs):
        posted_urls.append(url)
        if "gemini-deprecated-model" in url:
            return MockResponse(404, {"error": "Not Found"})
        elif "gemini-3.5-flash" in url:
            return MockResponse(
                200,
                {"candidates": [{"content": {"parts": [{"text": "fallback success"}]}}]},
            )
        return MockResponse(404, {})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await adapter.generate("test prompt")
    assert result == "fallback success"
    assert adapter.model == "gemini-3.5-flash"
    assert any("gemini-deprecated-model" in u for u in posted_urls)
    assert any("gemini-3.5-flash" in u for u in posted_urls)


@pytest.mark.anyio
async def test_google_ai_no_key_path(monkeypatch):
    """Test path: no key set disables Gemini adapter and fails soft."""
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    adapter = GoogleAIAdapter()
    assert adapter.disabled is True
    assert await adapter.is_available() is False
    assert await adapter.list_available_models() == []
    with pytest.raises(RuntimeError, match="Gemini fallback unavailable"):
        await adapter.generate("test prompt")

    # Verify FallbackLLMAdapter marks fallback unavailable
    primary_fail = MockLLMAdapter("primary", should_fail=True)
    fallback = FallbackLLMAdapter(primary=primary_fail, secondary=adapter)
    assert fallback.fallback_status == "LLM fallback unavailable"
    with pytest.raises(RuntimeError, match="LLM fallback unavailable"):
        await fallback.generate("test prompt")


@pytest.mark.anyio
async def test_google_ai_404_discovery_empty(monkeypatch):
    """Test path: 404 with empty discovery fails soft."""
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "test-key")
    adapter = GoogleAIAdapter(model="gemini-nonexistent")

    async def mock_list(self):
        return []

    monkeypatch.setattr(GoogleAIAdapter, "list_available_models", mock_list)

    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("error", request=None, response=self)

    async def mock_post(client_self, url, **kwargs):
        return MockResponse(404, {"error": "Not Found"})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(RuntimeError, match="no available Flash-family fallback"):
        await adapter.generate("test prompt")
    assert adapter.disabled is True


@pytest.mark.anyio
async def test_google_ai_429_retry_success(monkeypatch):
    """Test path: 429 rate limit retried with backoff once and succeeds."""
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "test-key")
    adapter = GoogleAIAdapter(model="gemini-3.5-flash", backoff_seconds=0.001)

    call_count = 0

    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("error", request=None, response=self)

    async def mock_post(client_self, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MockResponse(429, {"error": "Resource Exhausted"})
        return MockResponse(
            200,
            {"candidates": [{"content": {"parts": [{"text": "success after retry"}]}}]},
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    res = await adapter.generate("test prompt")
    assert res == "success after retry"
    assert call_count == 2
    assert adapter.disabled is False


@pytest.mark.anyio
async def test_google_ai_429_retry_fail_soft(monkeypatch):
    """Test path: 429 rate limit retried once then fails soft."""
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "test-key")
    adapter = GoogleAIAdapter(model="gemini-3.5-flash", backoff_seconds=0.001)

    call_count = 0

    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("error", request=None, response=self)

    async def mock_post(client_self, url, **kwargs):
        nonlocal call_count
        call_count += 1
        return MockResponse(429, {"error": "Resource Exhausted"})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(RuntimeError, match="rate limit exceeded"):
        await adapter.generate("test prompt")
    assert call_count == 2
    assert adapter.disabled is True


def test_api_status_reports_llm_fallback_unavailable(monkeypatch):
    """Test that /api/status reports 'LLM fallback unavailable' when no key is set."""
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)
    from fastapi.testclient import TestClient
    from bolsamajh.web.server import app

    client = TestClient(app)
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["llm_fallback"] == "LLM fallback unavailable"



