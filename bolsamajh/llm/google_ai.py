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

import asyncio
import json
import logging
import os
import time
from typing import AsyncIterator, List, Optional, Set, Tuple

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
        max_tokens: int = 2048,
        backoff_seconds: float = 1.0,
    ):
        self.model = os.getenv("BOLSAMAJH_GOOGLE_AI_MODEL", os.getenv("GOOGLE_AI_MODEL", model))
        self.temperature = temperature
        self.max_tokens = max(max_tokens, 2048)
        self.backoff_seconds = backoff_seconds
        self._api_key = os.getenv("GOOGLE_AI_API_KEY", "").strip()
        self._disabled_until: float = 0.0
        self._consecutive_errors: int = 0
        self._explicitly_disabled: bool = False

        global _WARNED_MISSING_KEY
        if not self._api_key:
            self._explicitly_disabled = True
            if not _WARNED_MISSING_KEY:
                log.warning("GOOGLE_AI_API_KEY not set; Gemini cloud fallback is disabled.")
                _WARNED_MISSING_KEY = True

    @property
    def disabled(self) -> bool:
        if self._explicitly_disabled:
            return True
        if not self._api_key:
            return True
        if time.time() < self._disabled_until:
            return True
        return False

    @disabled.setter
    def disabled(self, val: bool) -> None:
        self._explicitly_disabled = val
        if val:
            self._disabled_until = float("inf")
        else:
            self._disabled_until = 0.0
            self._consecutive_errors = 0

    def _record_error(self, base_cooldown: float = 30.0) -> None:
        """Trigger exponential backoff cooldown without permanently disabling."""
        self._consecutive_errors += 1
        cooldown = min(base_cooldown * (2 ** (self._consecutive_errors - 1)), 600.0)
        self._disabled_until = time.time() + cooldown
        log.warning(
            "Google AI adapter entered cooldown for %.1fs until %.1f (error count: %d)",
            cooldown,
            self._disabled_until,
            self._consecutive_errors,
        )

    def _record_success(self) -> None:
        self._consecutive_errors = 0
        self._disabled_until = 0.0

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
                    log.warning("Failed to list Google AI models: HTTP %d", resp.status_code)
                    self._record_error(base_cooldown=60.0)
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
            self._record_error(base_cooldown=60.0)
            return []

    async def _get_flash_candidates(self, excluded: Optional[Set[str]] = None) -> List[str]:
        """Return candidate Flash-family models deterministically sorted."""
        import re

        if excluded is None:
            excluded = set()
        models = await self.list_available_models()
        candidates = [
            m
            for m in models
            if "flash" in m.lower()
            and not any(x in m.lower() for x in ["tts", "image", "transcribe", "embedding"])
            and m not in excluded
        ]

        def _rank(m: str) -> tuple:
            # Prefer non-preview/experimental first
            is_exp = 1 if ("preview" in m.lower() or "exp" in m.lower()) else 0
            # Parse version number if present (e.g. 2.5, 2.0, 1.5)
            v_match = re.search(r"(\d+(?:\.\d+)?)", m)
            version = float(v_match.group(1)) if v_match else 0.0
            return (is_exp, -version, m)

        candidates.sort(key=_rank)
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
                            log.warning(
                                "Automatically selected '%s' to replace '%s'", candidate, self.model
                            )
                            self.model = candidate
                            self._record_success()
                            return True
                    self._record_error(base_cooldown=300.0)
                    log.warning("Google AI model returned 404 and no Flash candidate found.")
                    return False
                if resp.status_code != 200:
                    self._record_error(base_cooldown=60.0)
                    log.warning("Google AI model check failed (HTTP %d).", resp.status_code)
                    return False
                self._record_success()
                log.info("Google AI Studio %s: available", self.model)
                return True
        except Exception as e:
            self._record_error(base_cooldown=60.0)
            log.warning("Google AI not reachable (%s).", e)
            return False

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate using Gemini API with native systemInstruction and header auth."""
        if self.disabled or not self._api_key:
            raise RuntimeError(
                "Gemini fallback unavailable: GOOGLE_AI_API_KEY not set or disabled."
            )

        t0 = time.time()

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        if "2." in self.model:
            payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_API_BASE}/models/{self.model}:generateContent",
                headers=self._get_headers(),
                json=payload,
            )

            # 429 rate limit: retry with backoff once
            if resp.status_code == 429:
                log.warning(
                    "Google AI model '%s' returned HTTP 429 rate limit. Retrying with backoff...",
                    self.model,
                )
                if self.backoff_seconds > 0:
                    await asyncio.sleep(self.backoff_seconds)
                resp = await client.post(
                    f"{_API_BASE}/models/{self.model}:generateContent",
                    headers=self._get_headers(),
                    json=payload,
                )
                if resp.status_code == 429:
                    self._record_error(base_cooldown=60.0)
                    log.warning(
                        "Google AI model '%s' rate limited after retry (HTTP 429).", self.model
                    )
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
                        "Configured Google AI model '%s' not found (HTTP 404); trying '%s'",
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
                    self._record_error(base_cooldown=300.0)
                    err_msg = "Google AI model returned HTTP 404 and no available Flash-family fallback candidate succeeded."
                    log.warning(err_msg)
                    raise RuntimeError(err_msg)

            resp.raise_for_status()
            data = resp.json()

        # Check safety blocks explicitly
        candidates_data = data.get("candidates", [])
        if not candidates_data:
            block_reason = data.get("promptFeedback", {}).get("blockReason")
            if block_reason:
                raise RuntimeError(
                    f"Google AI generation blocked by safety filters: {block_reason}"
                )
            raise RuntimeError(f"Google AI returned no candidates: {data}")

        candidate = candidates_data[0]
        finish_reason = candidate.get("finishReason")
        if finish_reason in ("SAFETY", "BLOCKED", "PROHIBITED_CONTENT"):
            raise RuntimeError(f"Google AI generation blocked by safety filters: {finish_reason}")

        parts = candidate.get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

        self._record_success()
        elapsed = time.time() - t0
        log.info(
            "Google AI generated %d chars in %.1fs (model: %s)", len(text), elapsed, self.model
        )
        return text

    @staticmethod
    def _parse_sse_line(line: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse SSE line and return (token, safety_error)."""
        line = line.strip()
        if not line.startswith("data: "):
            return None, None
        try:
            data = json.loads(line[6:])
            candidates_data = data.get("candidates", [])
            if candidates_data:
                cand = candidates_data[0]
                finish_reason = cand.get("finishReason")
                if finish_reason in ("SAFETY", "BLOCKED", "PROHIBITED_CONTENT"):
                    return None, finish_reason
                parts = cand.get("content", {}).get("parts", [])
                tokens = [p.get("text", "") for p in parts if p.get("text")]
                if tokens:
                    return "".join(tokens), None
            block_reason = data.get("promptFeedback", {}).get("blockReason")
            if block_reason:
                return None, block_reason
        except json.JSONDecodeError:
            pass
        return None, None

    async def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream using Gemini API (streamGenerateContent) with header auth."""
        if self.disabled or not self._api_key:
            raise RuntimeError(
                "Gemini fallback unavailable: GOOGLE_AI_API_KEY not set or disabled."
            )

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        if "2." in self.model:
            payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            stream_url = f"{_API_BASE}/models/{self.model}:streamGenerateContent?alt=sse"

            async def _stream_with_url(url: str) -> AsyncIterator[str]:
                async with client.stream(
                    "POST",
                    url,
                    headers=self._get_headers(),
                    json=payload,
                ) as resp:
                    if resp.status_code == 429:
                        raise httpx.HTTPStatusError(
                            "Rate limited (429)", request=resp.request, response=resp
                        )
                    if resp.status_code == 404:
                        raise httpx.HTTPStatusError(
                            "Model not found (404)", request=resp.request, response=resp
                        )
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        token, error = self._parse_sse_line(line)
                        if error:
                            raise RuntimeError(
                                f"Google AI generation blocked by safety filters: {error}"
                            )
                        if token:
                            yield token

            try:
                async for token in _stream_with_url(stream_url):
                    self._record_success()
                    yield token
                return
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    log.warning(
                        "Google AI model '%s' returned HTTP 429 during stream. Retrying once...",
                        self.model,
                    )
                    if self.backoff_seconds > 0:
                        await asyncio.sleep(self.backoff_seconds)
                    try:
                        async for token in _stream_with_url(stream_url):
                            self._record_success()
                            yield token
                        return
                    except Exception as retry_err:
                        self._record_error(base_cooldown=60.0)
                        log.warning(
                            "Google AI model '%s' stream rate limited after retry (HTTP 429).",
                            self.model,
                        )
                        raise RuntimeError(
                            f"Google AI stream rate limit exceeded (HTTP 429) after retry: {retry_err}"
                        )
                elif e.response.status_code == 404:
                    log.warning(
                        "Google AI model '%s' returned HTTP 404 during stream. Attempting Flash fallback...",
                        self.model,
                    )
                    candidates = await self._get_flash_candidates(excluded={self.model})
                    for candidate in candidates:
                        self.model = candidate
                        new_url = f"{_API_BASE}/models/{self.model}:streamGenerateContent?alt=sse"
                        try:
                            async for token in _stream_with_url(new_url):
                                self._record_success()
                                yield token
                            return
                        except Exception as cand_err:
                            log.debug("Candidate stream failed for '%s': %s", candidate, cand_err)
                            continue
                    self._record_error(base_cooldown=300.0)
                    raise RuntimeError(
                        "Google AI model returned HTTP 404 and no available Flash-family fallback could be streamed."
                    )
                else:
                    self._record_error()
                    raise
            except Exception:
                self._record_error()
                raise
