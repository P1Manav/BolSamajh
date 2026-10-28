"""LLM adapter factory — constructs primary or auto-fallback LLM adapter."""

import logging
from bolsamajh.config import AppConfig
from bolsamajh.llm.base import LLMAdapter
from bolsamajh.llm.ollama_adapter import OllamaAdapter
from bolsamajh.llm.google_ai import GoogleAIAdapter
from bolsamajh.llm.fallback import FallbackLLMAdapter

log = logging.getLogger(__name__)


def create_llm_adapter(config: AppConfig) -> LLMAdapter:
    """Create configured LLM adapter with optional auto-fallback."""
    engine = str(config.llm.engine).lower().strip()
    if engine not in ("ollama", "google_ai"):
        raise ValueError(
            f"Unknown LLM engine: '{config.llm.engine}'. Must be 'ollama' or 'google_ai'."
        )

    ollama = OllamaAdapter(
        model=config.llm.ollama_model,
        base_url=config.llm.ollama_base_url,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        num_ctx=getattr(config.llm, "ollama_num_ctx", 8192),
    )
    google_ai = GoogleAIAdapter(
        model=config.llm.google_ai_model,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
    )

    if config.llm.auto_fallback:
        if engine == "ollama":
            return FallbackLLMAdapter(primary=ollama, secondary=google_ai)
        else:
            return FallbackLLMAdapter(primary=google_ai, secondary=ollama)

    if engine == "google_ai":
        return google_ai
    return ollama
