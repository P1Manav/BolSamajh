"""Ollama LLM adapter — local LLM via Ollama HTTP API."""

import os
import json
import time
import logging
from typing import AsyncIterator

import httpx

from bolsamajh.llm.base import LLMAdapter

log = logging.getLogger(__name__)


class OllamaAdapter(LLMAdapter):
    """LLM adapter for Ollama (local inference server)."""

    def __init__(
        self,
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        max_tokens: int = 1024,
        num_ctx: int = 8192,
        keep_alive: str | None = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.num_ctx = num_ctx
        if keep_alive is None:
            keep_alive = os.getenv("BOLSAMAJH_OLLAMA_KEEP_ALIVE", "30m")
        self.keep_alive = keep_alive

    @property
    def name(self) -> str:
        return f"ollama/{self.model}"

    async def check_status(self) -> tuple[bool, str]:
        """Check detailed status of Ollama server and verify exact model tag."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code != 200:
                    return False, f"Ollama HTTP error {resp.status_code}"
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]

                # Check exact configured model tag (e.g. 'gemma3:4b' or 'gemma3:latest')
                expected_tag = self.model if ":" in self.model else f"{self.model}:latest"

                def _matches_exact(tag_name: str) -> bool:
                    norm_tag = tag_name if ":" in tag_name else f"{tag_name}:latest"
                    # Match exact name or path suffix like 'library/gemma3:4b'
                    return norm_tag == expected_tag or norm_tag.endswith(f"/{expected_tag}")

                has_model = any(_matches_exact(n) for n in model_names)
                if has_model:
                    return True, f"Ollama ready ({self.model})"
                return False, f"Model '{self.model}' not found in Ollama. Run: ollama run {self.model}"
        except httpx.ConnectError:
            return False, "Ollama is not running. Start with: ollama serve"
        except Exception as e:
            return False, f"Ollama connection error: {e}"

    async def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        ready, msg = await self.check_status()
        if not ready:
            log.warning("Ollama status: %s", msg)
        return ready

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate a complete response from Ollama."""
        t0 = time.time()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "num_ctx": self.num_ctx,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        if "error" in data:
            raise RuntimeError(f"Ollama error: {data['error']}")

        text = data.get("response", "")
        elapsed = time.time() - t0
        log.info("Ollama generated %d chars in %.1fs", len(text), elapsed)
        return text

    async def generate_stream(self, prompt: str, system: str = "") -> AsyncIterator[str]:
        """Stream a response from Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "num_ctx": self.num_ctx,
            },
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "error" in data:
                                raise RuntimeError(f"Ollama stream error: {data['error']}")
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                return
                        except json.JSONDecodeError:
                            continue

