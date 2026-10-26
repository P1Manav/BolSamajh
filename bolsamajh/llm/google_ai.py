"""Google AI Studio (Gemini) LLM adapter — free tier fallback.

Free-tier model:
- Model: gemini-3.5-flash (unverified — run python scripts/check_gemini.py with your key).
- Configurable via GOOGLE_AI_MODEL or BOLSAMAJH_GOOGLE_AI_MODEL.
- Sends API key in 'x-goog-api-key' header instead of URL parameters.
- Uses native 'systemInstruction' instead of fake user/model turn pairs.
- Suppresses httpx / httpcore loggers to WARNING so API keys never leak into logs.
- Automatic selection: if configured model returns 404 (deprecated or unavailable),
  queries live models and selects the first available Flash-family model.
"""

import os
import json
import time
import logging
import asyncio
from typing import AsyncIterator, List, Optional, Set

import httpx

from bolsamajh.llm.base import LLMAdapter

# Ensure HTTP client loggers never dump request URLs or auth headers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

# Google AI Studio endpoint
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


_WARNED_MISSING_KEY = False


class GoogleAIAdapter(LLMAdapter):
    """LLM adapter for Google AI Studio (Gemini) free tier.

    Requires env var: GOOGLE_AI_API_KEY
    Configurable model via: GOOGLE_AI_MODEL or BOLSAMAJH_GOOGLE_AI_MODEL
    """

    def __init__(
        self,
        model: str = "gemini-3.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        backoff_seconds: float = 1.0,
    ):
        self.model = os.getenv("BOLSAMAJH_GOOGLE_AI_MODEL", os.getenv("GOOGLE_AI_MODEL", model))
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.backoff_seconds = backoff_seconds
        self._api_key = os.getenv("GOOGLE_AI_API_KEY", "").strip()
        self.disabled = False

        global _WARNED_MISSING_KEY
        if not self._api_key:
            self.disabled = True
            if not _WARNED_MISSING_KEY:
                log.warning("GOOGLE_AI_API_KEY not set; Gemini cloud fallback is disabled.")
                _WARNED_MISSING_KEY = True

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
        if self.disabled or not self._api_key:
            return []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_API_BASE}/models",
                    headers=self._get_headers(),
                )
                if resp.status_code != 200:
                    log.warning("Failed to list Google AI models: HTTP %d; disabling Gemini fallback.", resp.status_code)
                    self.disabled = True
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
            log.warning("Exception querying Google AI models: %s; disabling Gemini fallback.", e)
            self.disabled = True
            return []

    async def _get_flash_candidates(self, excluded: Optional[Set[str]] = None) -> List[str]:
        """Return candidate Flash-family models from live models endpoint."""
        if excluded is None:
            excluded = set()
        models = await self.list_available_models()
        candidates = [
            m for m in models
            if "flash" in m.lower()
            and not any(x in m.lower() for x in ["tts", "image", "transcribe"])
            and m not in excluded
        ]
        if not candidates:
            candidates = [m for m in models if "flash" in m.lower() and m not in excluded]
        return candidates

    async def is_available(self) -> bool:
        """Check if API key is set and endpoint responds."""
        if self.disabled or not self._api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_API_BASE}/models/{self.model}",
                    headers=self._get_headers(),
                )
                if resp.status_code == 404:
                    log.warning(
                        "Google AI model '%s' not found (HTTP 404). "
                        "Attempting automatic fallback to available Flash model...",
                        self.model,
                    )
                    candidates = await self._get_flash_candidates(excluded={self.model})
                    for candidate in candidates:
                        c_resp = await client.get(
                            f"{_API_BASE}/models/{candidate}",
                            headers=self._get_headers(),
                        )
                        if c_resp.status_code == 200:
                            log.warning("Automatically selected '%s' to replace '%s'", candidate, self.model)
                            self.model = candidate
                            return True
                    self.disabled = True
                    log.warning("Google AI model returned 404 and no Flash candidate found; disabling Gemini fallback.")
                    return False
                if resp.status_code != 200:
                    self.disabled = True
                    log.warning("Google AI model check failed (HTTP %d); disabling Gemini fallback.", resp.status_code)
                    return False
                log.info("Google AI Studio %s: available", self.model)
                return True
        except Exception as e:
            self.disabled = True
            log.warning("Google AI not reachable (%s); disabling Gemini fallback.", e)
            return False

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate using Gemini API with native systemInstruction and header auth."""
        if self.disabled or not self._api_key:
            raise RuntimeError("Gemini fallback unavailable: GOOGLE_AI_API_KEY not set or disabled.")

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

            # 429 rate limit: retry with backoff once, then fail soft
            if resp.status_code == 429:
                log.warning("Google AI model '%s' returned HTTP 429 rate limit. Retrying with backoff...", self.model)
                if self.backoff_seconds > 0:
                    await asyncio.sleep(self.backoff_seconds)
                resp = await client.post(
                    f"{_API_BASE}/models/{self.model}:generateContent",
                    headers=self._get_headers(),
                    json=payload,
                )
                if resp.status_code == 429:
                    self.disabled = True
                    log.warning("Google AI model '%s' rate limited after retry (HTTP 429); disabling fallback.", self.model)
                    raise RuntimeError("Google AI rate limit exceeded (HTTP 429) after retry.")

            if resp.status_code == 404:
                log.warning(
                    "Google AI model '%s' returned HTTP 404. Attempting automatic Flash-family selection...",
                    self.model,
                )
                attempted = {self.model}
                candidates = await self._get_flash_candidates(excluded=attempted)
                for candidate in candidates:
                    log.warning(
                        "Configured Google AI model '%s' not found (HTTP 404); automatically selecting fallback Flash model '%s'",
                        self.model,
                        candidate,
                    )
                    self.model = candidate
                    resp = await client.post(
                        f"{_API_BASE}/models/{self.model}:generateContent",
                        headers=self._get_headers(),
                        json=payload,
                    )
                    if resp.status_code == 200:
                        break
                    attempted.add(candidate)
                else:
                    self.disabled = True
                    err_msg = (
                        f"Google AI model returned HTTP 404 and no available Flash-family fallback could be selected. "
                        f"Set GOOGLE_AI_MODEL in your environment to a currently available model."
                    )
                    log.warning(err_msg)
                    raise RuntimeError(err_msg)

            resp.raise_for_status()
            data = resp.json()

        # Extract text from response
        text = ""
        candidates_data = data.get("candidates", [])
        if candidates_data:
            parts = candidates_data[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

        elapsed = time.time() - t0
        log.info("Google AI generated %d chars in %.1fs (model: %s)", len(text), elapsed, self.model)
        return text

    async def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream using Gemini API (streamGenerateContent) with header auth."""
        if self.disabled or not self._api_key:
            raise RuntimeError("Gemini fallback unavailable: GOOGLE_AI_API_KEY not set or disabled.")

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
            stream_url = f"{_API_BASE}/models/{self.model}:streamGenerateContent?alt=sse"
            async with client.stream(
                "POST",
                stream_url,
                headers=self._get_headers(),
                json=payload,
            ) as resp:
                # 429 rate limit: retry with backoff once, then fail soft
                if resp.status_code == 429:
                    log.warning("Google AI model '%s' returned HTTP 429 during stream. Retrying with backoff...", self.model)
                    if self.backoff_seconds > 0:
                        await asyncio.sleep(self.backoff_seconds)
                    retry_ctx = client.stream(
                        "POST",
                        stream_url,
                        headers=self._get_headers(),
                        json=payload,
                    )
                    c_resp = await retry_ctx.__aenter__()
                    if c_resp.status_code == 429:
                        await retry_ctx.__aexit__(None, None, None)
                        self.disabled = True
                        log.warning("Google AI model '%s' stream rate limited after retry (HTTP 429); disabling fallback.", self.model)
                        raise RuntimeError("Google AI stream rate limit exceeded (HTTP 429) after retry.")
                    resp = c_resp

                if resp.status_code == 404:
                    log.warning(
                        "Google AI model '%s' returned HTTP 404 during stream. Attempting automatic Flash-family selection...",
                        self.model,
                    )
                    attempted = {self.model}
                    candidates = await self._get_flash_candidates(excluded=attempted)
                    found_stream = None
                    for candidate in candidates:
                        log.warning(
                            "Configured Google AI model '%s' not found (HTTP 404); automatically selecting fallback Flash model '%s'",
                            self.model,
                            candidate,
                        )
                        self.model = candidate
                        stream_ctx = client.stream(
                            "POST",
                            f"{_API_BASE}/models/{self.model}:streamGenerateContent?alt=sse",
                            headers=self._get_headers(),
                            json=payload,
                        )
                        c_resp = await stream_ctx.__aenter__()
                        if c_resp.status_code == 200:
                            found_stream = (stream_ctx, c_resp)
                            break
                        await stream_ctx.__aexit__(None, None, None)
                        attempted.add(candidate)

                    if not found_stream:
                        self.disabled = True
                        err_msg = (
                            f"Google AI model returned HTTP 404 and no available Flash-family fallback could be selected. "
                            f"Set GOOGLE_AI_MODEL in your environment to a currently available model."
                        )
                        log.warning(err_msg)
                        raise RuntimeError(err_msg)

                    stream_ctx, resp = found_stream
                    try:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            line = line.strip()
                            if line.startswith("data: "):
                                try:
                                    data = json.loads(line[6:])
                                    candidates_data = data.get("candidates", [])
                                    if candidates_data:
                                        parts = candidates_data[0].get("content", {}).get("parts", [])
                                        for part in parts:
                                            token = part.get("text", "")
                                            if token:
                                                yield token
                                except json.JSONDecodeError:
                                    continue
                    finally:
                        await stream_ctx.__aexit__(None, None, None)
                    return

                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            candidates_data = data.get("candidates", [])
                            if candidates_data:
                                parts = candidates_data[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    token = part.get("text", "")
                                    if token:
                                        yield token
                        except json.JSONDecodeError:
                            continue
