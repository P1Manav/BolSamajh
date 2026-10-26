"""Unit tests for documentation synchronization and single source of truth verification."""
import pytest
from scripts.generate_readme_tables import sync_all_documentation, render_placeholders_in_text, get_metrics_dict
from bolsamajh.config import AppConfig, load_config
from bolsamajh.stt.faster_whisper_stt import FasterWhisperSTT
from bolsamajh.utils.cuda_setup import auto_detect_device


def test_documentation_in_sync_with_benchmark_truth():
    """Verify that all documentation files match the committed benchmark JSON results."""
    assert sync_all_documentation(check_only=True) is True, (
        "Documentation files differ from benchmark JSON results or contain un-rendered placeholders. "
        "Run 'python scripts/generate_readme_tables.py' to update them."
    )


def test_default_cuda_stt_model_is_large_v3_turbo():
    """Verify that large-v3-turbo is configured as default CUDA STT model everywhere."""
    cfg = AppConfig()
    assert cfg.stt.model_size == "large-v3-turbo"

    stt = FasterWhisperSTT()
    assert stt.model_size == "large-v3-turbo"


def test_placeholder_rendering_lifecycle():
    """Verify that {{key}} transforms to <!-- NUM:key -->val<!-- /NUM --> and updates idempotently."""
    metrics = {"stt.turbo.hiacc_wer": "38.52%"}

    # 1. First render: raw placeholder
    initial = "HiACC WER is {{stt.turbo.hiacc_wer}}."
    rendered = render_placeholders_in_text(initial, metrics)
    assert rendered == "HiACC WER is <!-- NUM:stt.turbo.hiacc_wer -->38.52%<!-- /NUM -->."

    # 2. Subsequent render: updates existing comment tag
    updated_metrics = {"stt.turbo.hiacc_wer": "37.50%"}
    re_rendered = render_placeholders_in_text(rendered, updated_metrics)
    assert re_rendered == "HiACC WER is <!-- NUM:stt.turbo.hiacc_wer -->37.50%<!-- /NUM -->."
