"""Google AI Studio (Gemini) LLM adapter — free tier fallback.

Free-tier model candidate:
- Model: gemini-2.0-flash (unverified without active GOOGLE_AI_API_KEY).
- Configurable via GOOGLE_AI_MODEL or BOLSAMAJH_GOOGLE_AI_MODEL.
- Sends API key in 'x-goog-api-key' header instead of URL parameters.
- Uses native 'systemInstruction' instead of fake user/model turn pairs.
- Suppresses httpx / httpcore loggers to WARNING so API keys never leak into logs.
- Clear error diagnostics and automatic fallback on HTTP 404 / deprecated model IDs.
"""

import os
import json
import time
import logging
from typing import AsyncIterator, List

import httpx

from bolsamajh.llm.base import LLMAdapter

# Ensure HTTP client loggers never dump request URLs or auth headers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

# Google AI Studio endpoint
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GoogleAIAdapter(LLMAdapter):
    """LLM adapter for Google AI Studio (Gemini) free tier.

    Requires env var: GOOGLE_AI_API_KEY
    Configurable model via: GOOGLE_AI_MODEL or BOLSAMAJH_GOOGLE_AI_MODEL
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        self.model = os.getenv("BOLSAMAJH_GOOGLE_AI_MODEL", os.getenv("GOOGLE_AI_MODEL", model))
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = os.getenv("GOOGLE_AI_API_KEY", "")

    @property
    def name(self) -> str:
        return f"google-ai/{self.model}"

    def _get_headers(self) -> dict:
        """Header with API key; never expose in URL params."""
        return {
            "x-goog-api-key": self._api_key,
            "Content-Type": "application/json",
        }

    async def list_available_models(self) -> List[str]:
        """Query Google AI Studio models endpoint and return generateContent-capable model names."""
        if not self._api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_API_BASE}/models",
                    headers=self._get_headers(),
                )
                if resp.status_code != 200:
                    log.warning("Failed to list Google AI models: HTTP %d", resp.status_code)
                    return []
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        name = m.get("name", "").replace("models/", "")
                        models.append(name)
                return models
        except Exception as e:
            log.warning("Exception querying Google AI models: %s", e)
            return []

    async def is_available(self) -> bool:
        """Check if API key is set and endpoint responds."""
        if not self._api_key:
            log.debug("GOOGLE_AI_API_KEY not set")
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_API_BASE}/models/{self.model}",
                    headers=self._get_headers(),
                )
                if resp.status_code == 404:
                    log.error(
                        "Google AI model '%s' not found (HTTP 404). "
                        "The model may be deprecated, retired, or misspelled. "
                        "Set GOOGLE_AI_MODEL to an active model (e.g., 'gemini-2.0-flash'). "
                        "Check available models via https://ai.google.dev/models.",
                        self.model,
                    )
                    return False
                available = resp.status_code == 200
                log.info(
                    "Google AI Studio %s: %s",
                    self.model,
                    "available" if available else f"HTTP {resp.status_code}",
                )
                return available
        except Exception as e:
            log.debug("Google AI not reachable: %s", e)
            return False

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate using Gemini API with native systemInstruction and header auth."""
        t0 = time.time()

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_API_BASE}/models/{self.model}:generateContent",
                headers=self._get_headers(),
                json=payload,
            )
            if resp.status_code == 404:
                err_msg = (
                    f"Google AI model '{self.model}' returned HTTP 404 Not Found. "
                    f"The model may be deprecated, retired, or misspelled. "
                    f"Set GOOGLE_AI_MODEL in your environment to a currently available model."
                )
                log.error(err_msg)
                raise RuntimeError(err_msg)
            resp.raise_for_status()
            data = resp.json()

        # Extract text from response
        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

        elapsed = time.time() - t0
        log.info("Google AI generated %d chars in %.1fs", len(text), elapsed)
        return text

    async def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream using Gemini API (streamGenerateContent) with header auth."""
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{_API_BASE}/models/{self.model}:streamGenerateContent?alt=sse",
                headers=self._get_headers(),
                json=payload,
            ) as resp:
                if resp.status_code == 404:
                    err_msg = (
                        f"Google AI model '{self.model}' returned HTTP 404 Not Found. "
                        f"The model may be deprecated, retired, or misspelled. "
                        f"Set GOOGLE_AI_MODEL in your environment to a currently available model."
                    )
                    log.error(err_msg)
                    raise RuntimeError(err_msg)
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    token = part.get("text", "")
                                    if token:
                                        yield token
                        except json.JSONDecodeError:
                            continue
