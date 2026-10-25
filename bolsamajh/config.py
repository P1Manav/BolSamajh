"""BolSamajh configuration — hotkeys, adapter selection, model paths."""

import os
from dataclasses import dataclass, field
from typing import Literal
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)


@dataclass
class HotkeyConfig:
    """Global hotkey bindings."""
    dictation: str = "ctrl+shift+space"       # Push-to-talk dictation
    doc_load: str = "ctrl+shift+d"            # Load document
    doc_ask: str = "ctrl+shift+a"             # Ask question about document
    command: str = "ctrl+shift+c"             # Voice command on selection
    stop: str = "escape"                      # Stop TTS / cancel


@dataclass
class STTConfig:
    """Speech-to-text settings."""
    engine: Literal["faster_whisper", "ai4bharat"] = "faster_whisper"
    model_size: str = "medium"                # faster-whisper model size
    language: str = "hi"                      # Language hint for Hinglish
    device: str = "cuda"                      # cuda or cpu
    compute_type: str = "int8_float16"         # int8 weights + fp16 compute (fast on RTX 3060 Ti)


@dataclass
class LLMConfig:
    """LLM adapter settings."""
    engine: Literal["ollama", "google_ai"] = "ollama"
    ollama_model: str = "gemma3:4b"
    ollama_base_url: str = "http://localhost:11434"
    google_ai_model: str = "gemini-2.0-flash"
    # API key read from env var GOOGLE_AI_API_KEY
    temperature: float = 0.3
    max_tokens: int = 1024


@dataclass
class TTSConfig:
    """Text-to-speech settings."""
    engine: Literal["edge_tts", "piper"] = "edge_tts"
    edge_voice_hi: str = "hi-IN-SwaraNeural"
    edge_voice_en: str = "en-IN-NeerjaNeural"
    edge_voice_gu: str = "gu-IN-DhwaniNeural"
    piper_model_path: str = ""
    output_sample_rate: int = 24000


@dataclass
class DictationConfig:
    """Dictation pipeline settings."""
    script: Literal["roman", "devanagari", "natural"] = "natural"
    remove_fillers: bool = True
    auto_punctuate: bool = True


@dataclass
class DocQAConfig:
    """Document Q&A settings."""
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: int = 500       # tokens
    chunk_overlap: int = 50     # tokens
    top_k: int = 5              # retrieval results
    response_language: Literal["hinglish", "hindi", "gujarati", "english"] = "hinglish"


@dataclass
class AppConfig:
    """Top-level application configuration."""
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    dictation: DictationConfig = field(default_factory=DictationConfig)
    doc_qa: DocQAConfig = field(default_factory=DocQAConfig)
    debug: bool = False


def load_config() -> AppConfig:
    """Load configuration with environment variable overrides."""
    config = AppConfig()

    # Override from env vars where useful
    if os.getenv("BOLSAMAJH_STT_ENGINE"):
        config.stt.engine = os.getenv("BOLSAMAJH_STT_ENGINE")
    if os.getenv("BOLSAMAJH_STT_DEVICE"):
        config.stt.device = os.getenv("BOLSAMAJH_STT_DEVICE")
    if os.getenv("BOLSAMAJH_LLM_ENGINE"):
        config.llm.engine = os.getenv("BOLSAMAJH_LLM_ENGINE")
    if os.getenv("BOLSAMAJH_SCRIPT"):
        config.dictation.script = os.getenv("BOLSAMAJH_SCRIPT")
    if os.getenv("BOLSAMAJH_DEBUG"):
        config.debug = os.getenv("BOLSAMAJH_DEBUG", "").lower() in ("1", "true")

    return config
