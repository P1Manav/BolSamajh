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


def test_comparison_columns_use_identical_clip_sets():
    """Assert that every comparison column in documentation uses identical clip IDs across models shown."""
    import json
    from collections import defaultdict
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    results_jsonl = root / "benchmark_data" / "per_clip_results.jsonl"
    assert results_jsonl.exists(), "per_clip_results.jsonl missing"

    clips_by_model_and_split = defaultdict(lambda: defaultdict(set))
    with open(results_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            m = rec["model"]
            cid = rec["clip_id"]
            if cid.startswith("synth_"):
                clips_by_model_and_split[m]["synthetic"].add(cid)
            elif cid.startswith("hiacc_"):
                clips_by_model_and_split[m]["hiacc"].add(cid)
                clips_by_model_and_split[m]["real_all"].add(cid)
            else:
                clips_by_model_and_split[m]["real_all"].add(cid)

    # 1. Compare HiACC across all 3 models
    hiacc_medium = clips_by_model_and_split["medium"]["hiacc"]
    hiacc_turbo = clips_by_model_and_split["large-v3-turbo"]["hiacc"]
    hiacc_swift = clips_by_model_and_split["whisper-hinglish-swift"]["hiacc"]

    assert len(hiacc_medium) == 100
    assert hiacc_medium == hiacc_turbo == hiacc_swift, (
        "HiACC clip sets are not identical across all three models!"
    )

    # 2. Compare Synthetic Stress across all 3 models
    synth_medium = clips_by_model_and_split["medium"]["synthetic"]
    synth_turbo = clips_by_model_and_split["large-v3-turbo"]["synthetic"]
    synth_swift = clips_by_model_and_split["whisper-hinglish-swift"]["synthetic"]

    assert len(synth_medium) == 100
    assert synth_medium == synth_turbo == synth_swift, (
        "Synthetic stress clip sets are not identical across all three models!"
    )

    # 3. Compare All Real Speech (300 clips) between medium and large-v3-turbo
    real_medium = clips_by_model_and_split["medium"]["real_all"]
    real_turbo = clips_by_model_and_split["large-v3-turbo"]["real_all"]

    assert len(real_medium) == 300
    assert real_medium == real_turbo, (
        "All real speech (300 clips) sets differ between medium and large-v3-turbo!"
    )

    # 4. Assert whisper-hinglish-swift is NEVER shown with a score in any 300-clip column
    assert len(clips_by_model_and_split["whisper-hinglish-swift"]["real_all"]) == 100

    docs_to_check = [root / "README.md", root / "benchmark_data" / "BENCHMARK_RESULTS.md"]
    for doc in docs_to_check:
        lines = doc.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            if "All Real Speech" in line and idx + 2 < len(lines):
                headers = [c.strip() for c in line.split("|")[1:-1]]
                all_real_idx = None
                for c_i, h in enumerate(headers):
                    if "All Real Speech" in h:
                        all_real_idx = c_i
                        break
                if all_real_idx is not None:
                    for row_idx in range(idx + 2, min(idx + 8, len(lines))):
                        row = lines[row_idx]
                        if not row.strip().startswith("|"):
                            break
                        cols = [c.strip() for c in row.split("|")[1:-1]]
                        if len(cols) > all_real_idx and "swift" in cols[0].lower():
                            swift_score = cols[all_real_idx]
                            assert "N/A" in swift_score or "—" in swift_score, (
                                f"In {doc.name}, whisper-hinglish-swift has value '{swift_score}' "
                                f"in 300-clip column '{headers[all_real_idx]}'! Clip sets do not match."
                            )


def test_hardware_measurements_three_runs_and_median_p95():
    """Verify hardware_measurements.json contains 3 runs per model with required fields and README shows median/p95."""
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    hw_path = root / "benchmark_data" / "hardware_measurements.json"
    assert hw_path.exists(), "hardware_measurements.json missing"

    data = json.loads(hw_path.read_text(encoding="utf-8"))
    assert "models" in data, "models dict missing from hardware_measurements.json"

    expected_models = ["large-v3-turbo", "medium", "whisper-hinglish-swift"]
    for m in expected_models:
        assert m in data["models"], f"Model {m} missing from hardware_measurements.json models"
        m_data = data["models"][m]
        assert "runs" in m_data, f"runs missing for model {m}"
        assert len(m_data["runs"]) == 3, f"Expected 3 runs for {m}, got {len(m_data['runs'])}"
        for run in m_data["runs"]:
            assert "mean_latency_ms" in run
            assert "median_latency_ms" in run
            assert "p95_latency_ms" in run
        assert "gpu_name" in m_data
        assert "device_used" in m_data
        assert "nvidia_smi_output" in m_data
        assert "latency_ms" in m_data
        assert "median" in m_data["latency_ms"]
        assert "p95" in m_data["latency_ms"]

    readme_text = (root / "README.md").read_text(encoding="utf-8")
    assert "STT Latency (Synthetic Audio)" in readme_text
    assert "STT Latency (Real Speech)" in readme_text
    assert "p95:" in readme_text
    assert "Median over 300 real speech clips" in readme_text
