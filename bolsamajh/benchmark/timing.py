"""Shared timing and transcription benchmarking module for BolSamajh.

Provides identical decode options, timing boundaries, warmup protocols,
and multi-clip duration evaluations across benchmark evaluators and hardware scripts.
"""

import subprocess
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from faster_whisper import WhisperModel

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Shared, identical decode options across all evaluation & hardware benchmarks
DEFAULT_TRANSCRIBE_KWARGS = {
    "beam_size": 5,
    "vad_filter": True,
    "vad_parameters": dict(min_silence_duration_ms=500),
    "condition_on_previous_text": False,
    "compression_ratio_threshold": 2.4,
    "no_speech_threshold": 0.6,
    "repetition_penalty": 1.1,
}

# Standard multi-duration clips for empirical RTF agreement testing (~4s, ~9s, ~15s)
STANDARD_TIMING_CLIPS = [
    {
        "label": "4s",
        "relative_path": "benchmark_data/audio/sentence_001.wav",
        "default_lang": "hi",
    },
    {
        "label": "9s",
        "relative_path": "benchmark_data/real_speech/fleurs_hi_in_068.wav",
        "default_lang": "hi",
    },
    {
        "label": "15s",
        "relative_path": "benchmark_data/real_speech/fleurs_hi_in_026.wav",
        "default_lang": "hi",
    },
]


def load_audio_array(wav_path: Path | str) -> Tuple[np.ndarray, float]:
    """Read WAV file directly into float32 numpy array and return (audio_np, duration_sec)."""
    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        duration_sec = len(audio_np) / float(sr)
    return audio_np, duration_sec


def get_nvidia_smi_snapshot() -> str:
    """Capture raw nvidia-smi output snapshot."""
    try:
        res = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception as e:
        return f"nvidia-smi unavailable: {e}"


def time_single_transcription(
    model: WhisperModel,
    audio_np: np.ndarray,
    lang_hint: Optional[str] = None,
    extra_kwargs: Optional[Dict[str, Any]] = None,
) -> Tuple[str, float]:
    """Time only model.transcribe(...) including consumption of segment generator.

    Returns (hyp_text, latency_ms).
    """
    kwargs = dict(DEFAULT_TRANSCRIBE_KWARGS)
    if lang_hint:
        kwargs["language"] = lang_hint
    if extra_kwargs:
        kwargs.update(extra_kwargs)

    t_start = time.perf_counter()
    segments, info = model.transcribe(audio_np, **kwargs)
    hyp_text = " ".join(seg.text for seg in segments).strip()
    t_end = time.perf_counter()

    latency_ms = (t_end - t_start) * 1000.0
    return hyp_text, latency_ms


def run_stt_timing_protocol(
    model: WhisperModel,
    audio_np: np.ndarray,
    duration_sec: float,
    lang_hint: Optional[str] = None,
    warmup_runs: int = 2,
    timed_runs: int = 20,
) -> Dict[str, Any]:
    """Execute standard STT timing protocol:

    - 2 warmup runs (excluded from measurements)
    - >= 20 timed runs
    - Records per-run latency, median, p95, RTF, min, max.
    """
    # Warmup runs
    for _ in range(warmup_runs):
        _ = time_single_transcription(model, audio_np, lang_hint=lang_hint)

    # Timed runs
    latencies = []
    sample_hyp = ""
    for _ in range(timed_runs):
        hyp, lat_ms = time_single_transcription(model, audio_np, lang_hint=lang_hint)
        latencies.append(lat_ms)
        sample_hyp = hyp

    latencies_arr = np.array(latencies)
    median_lat = round(float(np.median(latencies_arr)), 1)
    p95_lat = round(float(np.percentile(latencies_arr, 95)), 1)
    mean_lat = round(float(np.mean(latencies_arr)), 1)
    min_lat = round(float(np.min(latencies_arr)), 1)
    max_lat = round(float(np.max(latencies_arr)), 1)
    rtf = round((median_lat / 1000.0) / duration_sec, 4) if duration_sec > 0 else 0.0

    return {
        "duration_sec": round(duration_sec, 2),
        "timed_runs_count": timed_runs,
        "warmup_runs_count": warmup_runs,
        "per_run_latencies_ms": [round(lat, 1) for lat in latencies],
        "mean_latency_ms": mean_lat,
        "median_latency_ms": median_lat,
        "p95_latency_ms": p95_lat,
        "min_latency_ms": min_lat,
        "max_latency_ms": max_lat,
        "rtf": rtf,
        "sample_hypothesis": sample_hyp,
    }


def benchmark_multi_length_clips(
    model: WhisperModel,
    model_name: str,
    device: str,
    compute_type: str,
    gpu_name: str,
    clips_config: Optional[List[Dict[str, str]]] = None,
    warmup_runs: int = 2,
    timed_runs: int = 20,
) -> Dict[str, Any]:
    """Measure STT latency across 3 clips of different lengths (~4s, ~9s, ~15s).

    Includes nvidia-smi snapshots before and after.
    """
    if clips_config is None:
        clips_config = STANDARD_TIMING_CLIPS

    smi_before = get_nvidia_smi_snapshot()

    clips_results = {}
    for clip_info in clips_config:
        wav_path = ROOT_DIR / clip_info["relative_path"]
        if not wav_path.exists():
            continue

        audio_np, dur = load_audio_array(wav_path)
        hint = "en" if "swift" in model_name.lower() else clip_info.get("default_lang", "hi")

        res = run_stt_timing_protocol(
            model=model,
            audio_np=audio_np,
            duration_sec=dur,
            lang_hint=hint,
            warmup_runs=warmup_runs,
            timed_runs=timed_runs,
        )
        clips_results[clip_info["label"]] = {
            "relative_path": clip_info["relative_path"],
            "language_hint": hint,
            **res,
        }

    smi_after = get_nvidia_smi_snapshot()

    return {
        "model": model_name,
        "device": device,
        "compute_type": compute_type,
        "gpu_name": gpu_name,
        "clips": clips_results,
        "nvidia_smi_before": smi_before,
        "nvidia_smi_after": smi_after,
    }
