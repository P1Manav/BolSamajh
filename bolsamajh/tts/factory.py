"""TTS adapter factory — constructs configured TTS adapter (Edge-TTS or Piper)."""

import logging

from bolsamajh.config import AppConfig
from bolsamajh.tts.base import TextToSpeech

log = logging.getLogger(__name__)


def create_tts_adapter(config: AppConfig) -> TextToSpeech:
    """Create configured TTS adapter based on config.tts.engine.

    Supports:
      - 'edge' / 'edge_tts': Microsoft Edge cloud TTS
      - 'piper': 100% offline Piper ONNX local TTS
    """
    engine = str(config.tts.engine).lower().strip()
    if engine in ("edge", "edge_tts"):
        from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter

        return EdgeTTSAdapter()
    elif engine == "piper":
        from bolsamajh.tts.piper_adapter import PiperTTSAdapter

        return PiperTTSAdapter(model_path=config.tts.piper_model_path)
    else:
        raise ValueError(
            f"Unknown TTS engine: '{config.tts.engine}'. Must be 'edge' (or 'edge_tts') or 'piper'."
        )
