"""Google AI Studio (Gemini) LLM adapter — free tier fallback."""

import os
import json
import time
import logging
from typing import AsyncIterator

import httpx

from bolsamajh.llm.base import LLMAdapter

log = logging.getLogger(__name__)

# Google AI Studio free tier endpoint
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GoogleAIAdapter(LLMAdapter):
    """LLM adapter for Google AI Studio (Gemini) free tier.

    Free tier limits (as of Oct 2026):
    - Gemini 2.0 Flash: 15 RPM, 1M tokens/day
    - No credit card required

    Requires env var: GOOGLE_AI_API_KEY
    """

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._api_key = os.getenv("GOOGLE_AI_API_KEY", "")

    @property
    def name(self) -> str:
        return f"google-ai/{self.model}"

    async def is_available(self) -> bool:
        """Check if API key is set and endpoint responds."""
        if not self._api_key:
            log.debug("GOOGLE_AI_API_KEY not set")
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_API_BASE}/models/{self.model}",
                    params={"key": self._api_key},
                )
                available = resp.status_code == 200
                log.info("Google AI Studio %s: %s",
                         self.model, "available" if available else "not available")
                return available
        except Exception as e:
            log.debug("Google AI not reachable: %s", e)
            return False

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate using Gemini API."""
        t0 = time.time()

        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_API_BASE}/models/{self.model}:generateContent",
                params={"key": self._api_key},
                json=payload,
            )
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
        """Stream using Gemini API (streamGenerateContent)."""
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{_API_BASE}/models/{self.model}:streamGenerateContent",
                params={"key": self._api_key, "alt": "sse"},
                json=payload,
            ) as resp:
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
                                    text = part.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
