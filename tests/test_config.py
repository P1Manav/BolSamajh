"""Unit tests for configuration loading, validation, and adapter factories."""

import sys

import pytest

from bolsamajh.config import AppConfig, load_config
from bolsamajh.llm.factory import create_llm_adapter
from bolsamajh.tts.factory import create_tts_adapter


def test_config_defaults():
    cfg = AppConfig()
    cfg.validate()
    assert cfg.stt.model_size == "large-v3-turbo"
    assert cfg.stt.device in ("cuda", "cpu")
    assert cfg.llm.engine == "ollama"
    assert cfg.llm.auto_fallback is True
    assert cfg.tts.engine == "edge_tts"
    assert cfg.dictation.script == "natural"


def test_config_invalid_llm_engine_raises(monkeypatch):
    monkeypatch.setenv("BOLSAMAJH_LLM_ENGINE", "invalid_engine")
    with pytest.raises(ValueError, match="Invalid BOLSAMAJH_LLM_ENGINE"):
        load_config()


def test_config_invalid_tts_engine_raises(monkeypatch):
    monkeypatch.setenv("BOLSAMAJH_TTS_ENGINE", "fake_tts")
    with pytest.raises(ValueError, match="Invalid BOLSAMAJH_TTS_ENGINE"):
        load_config()


def test_config_invalid_script_raises(monkeypatch):
    monkeypatch.setenv("BOLSAMAJH_SCRIPT", "cyrillic")
    with pytest.raises(ValueError, match="Invalid BOLSAMAJH_SCRIPT"):
        load_config()


def test_config_invalid_device_raises(monkeypatch):
    monkeypatch.setenv("BOLSAMAJH_STT_DEVICE", "tpu")
    with pytest.raises(ValueError, match="Invalid BOLSAMAJH_STT_DEVICE"):
        load_config()


def test_config_invalid_bool_raises(monkeypatch):
    monkeypatch.setenv("BOLSAMAJH_LLM_AUTO_FALLBACK", "not_a_bool")
    with pytest.raises(ValueError, match="Invalid boolean value"):
        load_config()


def test_config_valid_tts_engine_aliases(monkeypatch):
    monkeypatch.setenv("BOLSAMAJH_TTS_ENGINE", "edge")
    cfg = load_config()
    assert cfg.tts.engine == "edge_tts"

    monkeypatch.setenv("BOLSAMAJH_TTS_ENGINE", "piper")
    cfg = load_config()
    assert cfg.tts.engine == "piper"


def test_llm_factory_unknown_engine_raises():
    cfg = AppConfig()
    cfg.llm.engine = "unknown_engine"  # type: ignore
    with pytest.raises(ValueError, match="Unknown LLM engine"):
        create_llm_adapter(cfg)


def test_tts_factory_unknown_engine_raises():
    cfg = AppConfig()
    cfg.tts.engine = "unknown_tts"  # type: ignore
    with pytest.raises(ValueError, match="Unknown TTS engine"):
        create_tts_adapter(cfg)


def test_tts_factory_edge():
    cfg = AppConfig()
    cfg.tts.engine = "edge_tts"
    adapter = create_tts_adapter(cfg)
    assert adapter.name == "edge-tts"


def test_prompts_lightweight_isolation():
    """Verify that importing bolsamajh.prompts does not pull in heavy modules."""
    for mod in ["sounddevice", "torch", "tkinter"]:
        if mod in sys.modules:
            del sys.modules[mod]

    import bolsamajh.prompts as prompts

    assert hasattr(prompts, "_SYSTEM_PROMPT")
    assert hasattr(prompts, "_LANG_INSTRUCTIONS")
    assert "tkinter" not in sys.modules
    assert "sounddevice" not in sys.modules
