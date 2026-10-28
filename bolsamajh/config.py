"""BolSamajh configuration — hotkeys, adapter selection, model paths."""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv

log = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Load .env automatically at startup
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()


def _parse_bool(name: str, val: str) -> bool:
    """Parse a boolean environment variable or raise ValueError."""
    v = val.strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"Invalid boolean value for {name}: '{val}'. Must be true or false.")


@dataclass
class HotkeyConfig:
    """Global hotkey bindings with low-conflict defaults."""

    dictation: str = "alt+shift+space"  # Push-to-talk dictation (avoids VS Code Ctrl+Shift+Space)
    doc_load: str = "alt+shift+d"  # Load document (avoids VS Code Ctrl+Shift+D debug)
    doc_ask: str = "alt+shift+a"  # Ask question about document (avoids Chrome Ctrl+Shift+A)
    command: str = "alt+shift+c"  # Voice command on selection (avoids Chrome Ctrl+Shift+C inspect)
    stop: str = "escape"  # Stop TTS / cancel recording
    suppress: bool = False  # Whether keyboard hook suppresses key propagation


@dataclass
class STTConfig:
    """Speech-to-text settings."""

    engine: str = "faster_whisper"
    model_size: str = (
        "large-v3-turbo"  # Default CUDA model (large-v3-turbo); medium supported as fallback
    )
    language: str = "auto"  # Auto-detect language or specify 'hi', 'en', 'gu'
    device: Literal["cuda", "cpu"] = "cuda"  # cuda or cpu
    compute_type: str = "int8_float16"  # int8 weights + fp16 compute


@dataclass
class LLMConfig:
    """LLM adapter settings."""

    engine: Literal["ollama", "google_ai"] = "ollama"
    ollama_model: str = "gemma3:4b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_ctx: int = 8192  # 8k context window to prevent prompt truncation
    ollama_keep_alive: str = "30m"  # Configurable Ollama model retention in memory
    auto_fallback: bool = True  # Automatically fallback between Ollama and Gemini
    google_ai_model: str = "gemini-3.5-flash"  # Configurable via GOOGLE_AI_MODEL
    temperature: float = 0.3
    max_tokens: int = 1024


@dataclass
class TTSConfig:
    """Text-to-speech settings."""

    engine: Literal["edge_tts", "piper", "edge"] = "edge_tts"
    edge_voice_hi: str = "hi-IN-SwaraNeural"
    edge_voice_en: str = "en-IN-NeerjaNeural"
    edge_voice_gu: str = "gu-IN-DhwaniNeural"
    roman_voice: str = "en-IN-NeerjaNeural"  # Voice for Roman Hinglish text
    piper_model_path: str = ""
    output_sample_rate: int = 24000


@dataclass
class DictationConfig:
    """Dictation pipeline settings."""

    script: Literal["roman", "devanagari", "natural"] = "natural"
    remove_fillers: bool = True
    clipboard_restore_delay: float = 0.3  # Configurable clipboard restore delay in seconds


@dataclass
class DocQAConfig:
    """Document Q&A settings."""

    embedding_model: str = "intfloat/multilingual-e5-base"  # 512 token context limit
    chunk_size: int = 380  # tokens (aligned with embedder context)
    chunk_overlap: int = 40  # tokens
    top_k: int = 5  # retrieval results
    refusal_threshold: float = (
        0.785  # Calibrated on 200 XQuAD Hindi QA pairs (F1=0.8685, Precision=81.86%, Recall=92.5%)
    )
    response_language: Literal["hinglish", "hindi", "gujarati", "english", "auto"] = "hinglish"


@dataclass
class AppConfig:
    """Top-level application configuration."""

    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    dictation: DictationConfig = field(default_factory=DictationConfig)
    doc_qa: DocQAConfig = field(default_factory=DocQAConfig)
    headphone_mode: bool = False  # False = speaker mode (echo gate active); True = headphone mode
    audio_max_record_seconds: int = 120  # Maximum recording duration cap
    audio_input_device: Optional[str] = None  # Audio input device index or name
    allowed_hosts: str = "localhost,127.0.0.1"  # Allowed Host header values
    api_key: str = ""  # Optional web API key
    debug: bool = False

    def validate(self) -> None:
        """Validate Literal-typed and constrained fields; raise ValueError on invalid values."""
        # STT device
        if self.stt.device not in ("cuda", "cpu"):
            raise ValueError(f"Invalid STT device: '{self.stt.device}'. Must be 'cuda' or 'cpu'.")

        # LLM engine
        if self.llm.engine not in ("ollama", "google_ai"):
            raise ValueError(
                f"Invalid LLM engine: '{self.llm.engine}'. Must be 'ollama' or 'google_ai'."
            )

        # TTS engine
        if self.tts.engine in ("edge", "edge_tts"):
            self.tts.engine = "edge_tts"
        elif self.tts.engine != "piper":
            raise ValueError(
                f"Invalid TTS engine: '{self.tts.engine}'. Must be 'edge' (or 'edge_tts') or 'piper'."
            )

        # Dictation script
        if self.dictation.script not in ("roman", "devanagari", "natural"):
            raise ValueError(
                f"Invalid dictation script: '{self.dictation.script}'. Must be 'roman', 'devanagari', or 'natural'."
            )

        # Doc QA response language
        if self.doc_qa.response_language not in (
            "hinglish",
            "hindi",
            "gujarati",
            "english",
            "auto",
        ):
            raise ValueError(
                f"Invalid doc_qa response_language: '{self.doc_qa.response_language}'. "
                "Must be 'hinglish', 'hindi', 'gujarati', 'english', or 'auto'."
            )


def load_config() -> AppConfig:
    """Load configuration with environment variable overrides and device auto-detection."""
    # Ensure latest .env is loaded
    if _env_path.exists():
        load_dotenv(_env_path, override=False)
    else:
        load_dotenv(override=False)

    config = AppConfig()

    # Hotkey overrides
    if os.getenv("BOLSAMAJH_HOTKEY_DICTATION"):
        config.hotkeys.dictation = os.getenv("BOLSAMAJH_HOTKEY_DICTATION").strip()
    if os.getenv("BOLSAMAJH_HOTKEY_DOC_LOAD"):
        config.hotkeys.doc_load = os.getenv("BOLSAMAJH_HOTKEY_DOC_LOAD").strip()
    if os.getenv("BOLSAMAJH_HOTKEY_DOC_ASK"):
        config.hotkeys.doc_ask = os.getenv("BOLSAMAJH_HOTKEY_DOC_ASK").strip()
    if os.getenv("BOLSAMAJH_HOTKEY_COMMAND"):
        config.hotkeys.command = os.getenv("BOLSAMAJH_HOTKEY_COMMAND").strip()
    if os.getenv("BOLSAMAJH_HOTKEY_STOP"):
        config.hotkeys.stop = os.getenv("BOLSAMAJH_HOTKEY_STOP").strip()
    if os.getenv("BOLSAMAJH_HOTKEY_SUPPRESS"):
        config.hotkeys.suppress = _parse_bool(
            "BOLSAMAJH_HOTKEY_SUPPRESS", os.getenv("BOLSAMAJH_HOTKEY_SUPPRESS")
        )

    # STT engine and device overrides
    if os.getenv("BOLSAMAJH_STT_ENGINE"):
        config.stt.engine = os.getenv("BOLSAMAJH_STT_ENGINE").strip()
    if os.getenv("BOLSAMAJH_STT_MODEL"):
        config.stt.model_size = os.getenv("BOLSAMAJH_STT_MODEL").strip()
    if os.getenv("BOLSAMAJH_STT_LANGUAGE"):
        config.stt.language = os.getenv("BOLSAMAJH_STT_LANGUAGE").strip().lower()

    if os.getenv("BOLSAMAJH_STT_DEVICE"):
        dev = os.getenv("BOLSAMAJH_STT_DEVICE").strip().lower()
        if dev not in ("cuda", "cpu"):
            raise ValueError(f"Invalid BOLSAMAJH_STT_DEVICE: '{dev}'. Must be 'cuda' or 'cpu'.")
        config.stt.device = dev
        if config.stt.device == "cpu" and config.stt.compute_type in ("int8_float16", "float16"):
            config.stt.compute_type = "int8"
    else:
        # Auto-detect optimal device, compute type, and model
        try:
            from bolsamajh.utils.cuda_setup import auto_detect_device

            dev, comp, model = auto_detect_device()
            config.stt.device = dev
            config.stt.compute_type = comp
            if not os.getenv("BOLSAMAJH_STT_MODEL"):
                config.stt.model_size = model
        except Exception as e:
            log.warning("Device auto-detection failed, defaulting to CPU: %s", e)
            config.stt.device = "cpu"
            config.stt.compute_type = "int8"

    # LLM overrides
    if os.getenv("BOLSAMAJH_LLM_ENGINE"):
        llm_engine = os.getenv("BOLSAMAJH_LLM_ENGINE").strip().lower()
        if llm_engine not in ("ollama", "google_ai"):
            raise ValueError(
                f"Invalid BOLSAMAJH_LLM_ENGINE: '{llm_engine}'. Must be 'ollama' or 'google_ai'."
            )
        config.llm.engine = llm_engine

    if os.getenv("BOLSAMAJH_LLM_AUTO_FALLBACK") is not None:
        config.llm.auto_fallback = _parse_bool(
            "BOLSAMAJH_LLM_AUTO_FALLBACK", os.getenv("BOLSAMAJH_LLM_AUTO_FALLBACK")
        )

    if os.getenv("BOLSAMAJH_OLLAMA_MODEL"):
        config.llm.ollama_model = os.getenv("BOLSAMAJH_OLLAMA_MODEL").strip()
    if os.getenv("BOLSAMAJH_OLLAMA_BASE_URL"):
        config.llm.ollama_base_url = os.getenv("BOLSAMAJH_OLLAMA_BASE_URL").strip()
    if os.getenv("BOLSAMAJH_OLLAMA_KEEP_ALIVE"):
        config.llm.ollama_keep_alive = os.getenv("BOLSAMAJH_OLLAMA_KEEP_ALIVE").strip()

    if os.getenv("BOLSAMAJH_GOOGLE_AI_MODEL"):
        config.llm.google_ai_model = os.getenv("BOLSAMAJH_GOOGLE_AI_MODEL").strip()
    elif os.getenv("GOOGLE_AI_MODEL"):
        config.llm.google_ai_model = os.getenv("GOOGLE_AI_MODEL").strip()

    # TTS overrides
    if os.getenv("BOLSAMAJH_TTS_ENGINE"):
        tts_engine = os.getenv("BOLSAMAJH_TTS_ENGINE").strip().lower()
        if tts_engine in ("edge", "edge_tts"):
            config.tts.engine = "edge_tts"
        elif tts_engine == "piper":
            config.tts.engine = "piper"
        else:
            raise ValueError(
                f"Invalid BOLSAMAJH_TTS_ENGINE: '{tts_engine}'. Must be 'edge' or 'piper'."
            )

    if os.getenv("BOLSAMAJH_EDGE_VOICE_HI"):
        config.tts.edge_voice_hi = os.getenv("BOLSAMAJH_EDGE_VOICE_HI").strip()
    if os.getenv("BOLSAMAJH_EDGE_VOICE_EN"):
        config.tts.edge_voice_en = os.getenv("BOLSAMAJH_EDGE_VOICE_EN").strip()
    if os.getenv("BOLSAMAJH_EDGE_VOICE_GU"):
        config.tts.edge_voice_gu = os.getenv("BOLSAMAJH_EDGE_VOICE_GU").strip()
    if os.getenv("BOLSAMAJH_ROMAN_VOICE"):
        config.tts.roman_voice = os.getenv("BOLSAMAJH_ROMAN_VOICE").strip()
    if os.getenv("BOLSAMAJH_PIPER_MODEL_PATH"):
        config.tts.piper_model_path = os.getenv("BOLSAMAJH_PIPER_MODEL_PATH").strip()

    # Dictation overrides
    if os.getenv("BOLSAMAJH_SCRIPT"):
        script = os.getenv("BOLSAMAJH_SCRIPT").strip().lower()
        if script not in ("roman", "devanagari", "natural"):
            raise ValueError(
                f"Invalid BOLSAMAJH_SCRIPT: '{script}'. Must be 'roman', 'devanagari', or 'natural'."
            )
        config.dictation.script = script

    if os.getenv("BOLSAMAJH_CLIPBOARD_RESTORE_DELAY"):
        try:
            config.dictation.clipboard_restore_delay = float(
                os.getenv("BOLSAMAJH_CLIPBOARD_RESTORE_DELAY")
            )
        except ValueError:
            raise ValueError(
                f"Invalid BOLSAMAJH_CLIPBOARD_RESTORE_DELAY: '{os.getenv('BOLSAMAJH_CLIPBOARD_RESTORE_DELAY')}'. Must be a float."
            )

    # Doc QA overrides
    if os.getenv("BOLSAMAJH_DOC_QA_RESPONSE_LANGUAGE"):
        resp_lang = os.getenv("BOLSAMAJH_DOC_QA_RESPONSE_LANGUAGE").strip().lower()
        if resp_lang not in ("hinglish", "hindi", "gujarati", "english", "auto"):
            raise ValueError(
                f"Invalid BOLSAMAJH_DOC_QA_RESPONSE_LANGUAGE: '{resp_lang}'. "
                "Must be 'hinglish', 'hindi', 'gujarati', 'english', or 'auto'."
            )
        config.doc_qa.response_language = resp_lang

    # App overrides
    if os.getenv("BOLSAMAJH_HEADPHONE_MODE"):
        config.headphone_mode = _parse_bool(
            "BOLSAMAJH_HEADPHONE_MODE", os.getenv("BOLSAMAJH_HEADPHONE_MODE")
        )
    if os.getenv("BOLSAMAJH_DEBUG"):
        config.debug = _parse_bool("BOLSAMAJH_DEBUG", os.getenv("BOLSAMAJH_DEBUG"))
    if os.getenv("BOLSAMAJH_AUDIO_MAX_RECORD_SECONDS"):
        try:
            config.audio_max_record_seconds = int(os.getenv("BOLSAMAJH_AUDIO_MAX_RECORD_SECONDS"))
        except ValueError:
            raise ValueError(
                f"Invalid BOLSAMAJH_AUDIO_MAX_RECORD_SECONDS: '{os.getenv('BOLSAMAJH_AUDIO_MAX_RECORD_SECONDS')}'. Must be an integer."
            )
    if os.getenv("BOLSAMAJH_AUDIO_INPUT_DEVICE"):
        config.audio_input_device = os.getenv("BOLSAMAJH_AUDIO_INPUT_DEVICE").strip()
    if os.getenv("BOLSAMAJH_ALLOWED_HOSTS"):
        config.allowed_hosts = os.getenv("BOLSAMAJH_ALLOWED_HOSTS").strip()
    if os.getenv("BOLSAMAJH_API_KEY"):
        config.api_key = os.getenv("BOLSAMAJH_API_KEY").strip()

    config.validate()
    return config
