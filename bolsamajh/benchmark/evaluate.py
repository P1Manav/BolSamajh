"""BolSamajh Benchmark v2 Evaluator — Real Speech & Synthetic Stress Evaluation.

Adheres strictly to Tier 1 Guidelines:
- Compares at least 3 verified open-source models:
  1. faster-whisper medium (baseline)
  2. faster-whisper large-v3-turbo (deepdml/faster-whisper-large-v3-turbo-ct2)
  3. Whisper-Hindi2Hinglish-Swift (MSpider3/whisper-hindi2hinglish-swift-ct2)
- Evaluates REAL speech and SYNTHETIC stress sets separately:
  * Real Speech: Google FLEURS (hi_in, gu_in) & HiACC (Hindi-English code-switched)
  * Synthetic Stress: 100 sentences with multi-voice and open-source DSP degradations
- Canonical scoring via script-normalized transliteration (Aksharamukha) & Devanagari normalization
  (drops unprincipled 'best of two' trick).
- Outputs comprehensive benchmark JSON to benchmark_data/benchmark_results.json.
"""

import os
import sys
import json
import time
import wave
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from faster_whisper import WhisperModel

from bolsamajh.benchmark.normalization import compute_normalized_wer_cer
from bolsamajh.utils.cuda_setup import setup_cuda_dlls

setup_cuda_dlls()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REAL_MANIFEST = ROOT_DIR / "benchmark_data" / "real_speech_manifest.json"
SYNTH_METADATA = ROOT_DIR / "benchmark_data" / "metadata.json"
RESULTS_JSON = ROOT_DIR / "benchmark_data" / "benchmark_results.json"
RESULTS_MD = ROOT_DIR / "benchmark_data" / "BENCHMARK_RESULTS.md"
PER_CLIP_JSONL = ROOT_DIR / "benchmark_data" / "per_clip_results.jsonl"

MODEL_MAP = {
    "medium": "medium",
    "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
    "whisper-hinglish-swift": "MSpider3/whisper-hindi2hinglish-swift-ct2",
    "whisper-hindi2hinglish-prime": "models/whisper-hindi2hinglish-prime-ct2",
}


def compute_bootstrap_ci(data: List[float], n_bootstrap: int = 1000, ci: float = 0.95, seed: int = 42) -> List[float]:
    """Calculate non-parametric bootstrap 95% confidence interval for mean metric (percentage)."""
    if not data:
        return [0.0, 0.0]
    rng = np.random.default_rng(seed)
    n = len(data)
    indices = rng.integers(0, n, size=(n_bootstrap, n))
    boot_means = np.mean(np.array(data)[indices], axis=1) * 100.0
    alpha = (1.0 - ci) / 2.0
    low = float(np.percentile(boot_means, alpha * 100.0))
    high = float(np.percentile(boot_means, (1.0 - alpha) * 100.0))
    return [round(low, 2), round(high, 2)]


def load_audio_array(wav_path: Path) -> np.ndarray:
    """Read WAV file directly into float32 numpy array."""
    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    return audio_np


def evaluate_clip(
    model: WhisperModel,
    audio_np: np.ndarray,
    reference: str,
    duration_sec: float,
    lang_hint: Optional[str] = None
) -> Dict[str, Any]:
    """Transcribe a single audio clip with anti-repetition guards and compute script-normalized metrics."""
    t_start = time.perf_counter()

    # Guarded transcription parameters to prevent hallucination loops and Urdu misclassification
    transcribe_kwargs = {
        "beam_size": 5,
        "vad_filter": True,
        "vad_parameters": dict(min_silence_duration_ms=500),
        "condition_on_previous_text": False,
        "compression_ratio_threshold": 2.4,
        "no_speech_threshold": 0.6,
        "repetition_penalty": 1.1,
    }
    if lang_hint:
        transcribe_kwargs["language"] = lang_hint

    segments, info = model.transcribe(audio_np, **transcribe_kwargs)
    hyp_text = " ".join(seg.text for seg in segments).strip()
    t_end = time.perf_counter()

    latency_ms = (t_end - t_start) * 1000.0
    rtf = (latency_ms / 1000.0) / duration_sec if duration_sec > 0 else 0.0

    wer, cer, canon_ref, canon_hyp = compute_normalized_wer_cer(reference, hyp_text)

    return {
        "reference": reference,
        "hypothesis": hyp_text,
        "canonical_ref": canon_ref,
        "canonical_hyp": canon_hyp,
        "duration_sec": round(duration_sec, 2),
        "latency_ms": round(latency_ms, 1),
        "rtf": round(rtf, 3),
        "wer": wer,
        "cer": cer,
    }


def evaluate_real_speech(
    model: WhisperModel,
    model_key: str = "medium",
    device: str = "cuda",
    max_clips: Optional[int] = None,
    per_clip_records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Run evaluation on real-speech manifest (FLEURS hi/gu, HiACC) with bootstrap confidence intervals."""
    if not REAL_MANIFEST.exists():
        print(f"Warning: {REAL_MANIFEST} not found. Run scripts/fetch_benchmark_data.py first.")
        return {}

    with open(REAL_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    if max_clips:
        manifest = manifest[:max_clips]

    print(f"\n--- Evaluating Real Speech ({len(manifest)} clips) for {model_key} ---")
    splits_data: Dict[str, List[Dict[str, Any]]] = {}

    for i, item in enumerate(manifest, 1):
        wav_path = ROOT_DIR / item["wav_file"]
        if not wav_path.exists():
            continue

        audio_np = load_audio_array(wav_path)
        dur = item.get("duration_sec", len(audio_np) / 16000.0)
        split = item.get("split", "general")

        # Swift model was trained to emit Roman Hinglish when language='en'
        if model_key == "whisper-hinglish-swift":
            hint = "en"
        else:
            hint = "gu" if "gujarati" in split else ("hi" if ("hindi" in split or "code_switched" in split) else None)

        res = evaluate_clip(model, audio_np, item["reference"], dur, lang_hint=hint)
        splits_data.setdefault(split, []).append(res)

        if per_clip_records is not None:
            per_clip_records.append({
                "model": model_key,
                "clip_id": item.get("id", Path(item.get("wav_file", "")).stem),
                "reference": item["reference"],
                "raw_hypothesis": res["hypothesis"],
                "canonical_ref": res["canonical_ref"],
                "canonical_hyp": res["canonical_hyp"],
                "wer": res["wer"],
                "latency_ms": res["latency_ms"],
                "audio_duration": res["duration_sec"],
                "device": device,
            })

        if i % 25 == 0 or i == len(manifest):
            all_so_far = [c for s in splits_data.values() for c in s]
            cur_wer = np.mean([c["wer"] for c in all_so_far]) * 100
            print(f"[{i:03d}/{len(manifest)}] Real Speech Running Mean WER: {cur_wer:.1f}%")

    all_clips = [c for s in splits_data.values() for c in s]
    if not all_clips:
        return {}

    all_wers = [c["wer"] for c in all_clips]

    return {
        "total_clips": len(all_clips),
        "mean_wer_pct": round(float(np.mean(all_wers) * 100), 2),
        "mean_wer_ci_95": compute_bootstrap_ci(all_wers),
        "mean_cer_pct": round(float(np.mean([c["cer"] for c in all_clips]) * 100), 2),
        "mean_latency_ms": round(float(np.mean([c["latency_ms"] for c in all_clips])), 1),
        "mean_rtf": round(float(np.mean([c["rtf"] for c in all_clips])), 3),
        "splits": {
            split: {
                "count": len(clips),
                "wer_pct": round(float(np.mean([c["wer"] for c in clips]) * 100), 2),
                "wer_ci_95": compute_bootstrap_ci([c["wer"] for c in clips]),
                "cer_pct": round(float(np.mean([c["cer"] for c in clips]) * 100), 2),
                "mean_latency_ms": round(float(np.mean([c["latency_ms"] for c in clips])), 1),
            }
            for split, clips in splits_data.items()
        }
    }


def evaluate_synthetic_stress(
    model: WhisperModel,
    model_key: str = "medium",
    device: str = "cuda",
    max_clips: Optional[int] = None,
    per_clip_records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Run evaluation on 100 synthetic degraded stress sentences with bootstrap confidence intervals."""
    if not SYNTH_METADATA.exists():
        print(f"Warning: {SYNTH_METADATA} not found. Run scripts/fetch_benchmark_data.py first.")
        return {}

    with open(SYNTH_METADATA, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if max_clips:
        metadata = metadata[:max_clips]

    print(f"\n--- Evaluating Synthetic Stress Set ({len(metadata)} clips) for {model_key} ---")
    category_data: Dict[str, List[Dict[str, Any]]] = {}
    degradation_data: Dict[str, List[Dict[str, Any]]] = {}

    hint = "en" if model_key == "whisper-hinglish-swift" else "hi"

    for i, item in enumerate(metadata, 1):
        wav_path = ROOT_DIR / item["wav_path"]
        if not wav_path.exists():
            continue

        audio_np = load_audio_array(wav_path)
        dur = item.get("duration_sec", len(audio_np) / 16000.0)
        cat = item.get("category", "everyday")
        deg = item.get("degradation", "clean")

        # Evaluate against Roman reference as ground truth
        res = evaluate_clip(model, audio_np, item["reference_roman"], dur, lang_hint=hint)
        category_data.setdefault(cat, []).append(res)
        degradation_data.setdefault(deg, []).append(res)

        if per_clip_records is not None:
            per_clip_records.append({
                "model": model_key,
                "clip_id": f"synth_stress_{item.get('id', i):03d}",
                "reference": item["reference_roman"],
                "raw_hypothesis": res["hypothesis"],
                "canonical_ref": res["canonical_ref"],
                "canonical_hyp": res["canonical_hyp"],
                "wer": res["wer"],
                "latency_ms": res["latency_ms"],
                "audio_duration": res["duration_sec"],
                "device": device,
            })

        if i % 25 == 0 or i == len(metadata):
            all_so_far = [c for s in category_data.values() for c in s]
            cur_wer = np.mean([c["wer"] for c in all_so_far]) * 100
            print(f"[{i:03d}/{len(metadata)}] Synthetic Stress Running Mean WER: {cur_wer:.1f}%")

    all_clips = [c for s in category_data.values() for c in s]
    if not all_clips:
        return {}

    all_wers = [c["wer"] for c in all_clips]

    return {
        "total_clips": len(all_clips),
        "mean_wer_pct": round(float(np.mean(all_wers) * 100), 2),
        "mean_wer_ci_95": compute_bootstrap_ci(all_wers),
        "mean_cer_pct": round(float(np.mean([c["cer"] for c in all_clips]) * 100), 2),
        "mean_latency_ms": round(float(np.mean([c["latency_ms"] for c in all_clips])), 1),
        "mean_rtf": round(float(np.mean([c["rtf"] for c in all_clips])), 3),
        "categories": {
            cat: {
                "count": len(clips),
                "mean_wer_pct": round(float(np.mean([c["wer"] for c in clips]) * 100), 2),
                "wer_ci_95": compute_bootstrap_ci([c["wer"] for c in clips]),
                "mean_cer_pct": round(float(np.mean([c["cer"] for c in clips]) * 100), 2),
                "mean_latency_ms": round(float(np.mean([c["latency_ms"] for c in clips])), 1),
            }
            for cat, clips in category_data.items()
        },
        "degradations": {
            deg: {
                "count": len(clips),
                "mean_wer_pct": round(float(np.mean([c["wer"] for c in clips]) * 100), 2),
                "wer_ci_95": compute_bootstrap_ci([c["wer"] for c in clips]),
                "mean_latency_ms": round(float(np.mean([c["latency_ms"] for c in clips])), 1),
            }
            for deg, clips in degradation_data.items()
        }
    }


def main():
    parser = argparse.ArgumentParser(description="BolSamajh Benchmark v2 Evaluator")
    parser.add_argument("--models", nargs="+", default=["medium", "large-v3-turbo", "whisper-hinglish-swift"], help="Models to evaluate")
    parser.add_argument("--suite", choices=["real", "synthetic", "all"], default="all", help="Test suite to run")
    parser.add_argument("--device", default="cuda", help="Inference device (cuda or cpu)")
    parser.add_argument("--compute_type", default="int8_float16", help="Precision (int8_float16, int8, float16)")
    parser.add_argument("--max_clips", type=int, default=None, help="Limit number of clips for fast smoke test")
    args = parser.parse_args()

    results = {
        "benchmark_version": "v2.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": {
            "device": args.device,
            "compute_type": args.compute_type
        },
        "real_speech": {},
        "synthetic_stress": {}
    }

    all_per_clip_records: List[Dict[str, Any]] = []

    for model_key in args.models:
        model_id = MODEL_MAP.get(model_key, model_key)
        print(f"\n==================================================================")
        print(f" Loading Engine: {model_key} ({model_id}) on {args.device} ({args.compute_type})")
        print(f"==================================================================")

        actual_device = args.device
        actual_compute = args.compute_type
        try:
            model = WhisperModel(model_id, device=args.device, compute_type=args.compute_type)
        except Exception as e:
            print("\n" + "!" * 72)
            print(f"LOUD WARNING: Requested device '{args.device}' with precision '{args.compute_type}' FAILED!")
            print(f"Exception: {e}")
            print(f"FALLING BACK TO CPU (compute_type='int8').")
            print(f"Latency and Real-Time Factor (RTF) will be severely degraded on CPU.")
            print("!" * 72 + "\n")
            actual_device = "cpu"
            actual_compute = "int8"
            model = WhisperModel(model_id, device="cpu", compute_type="int8")

        # 1. Real Speech
        if args.suite in ["real", "all"]:
            real_res = evaluate_real_speech(
                model, model_key=model_key, device=actual_device,
                max_clips=args.max_clips, per_clip_records=all_per_clip_records
            )
            if real_res:
                real_res["device"] = actual_device
                real_res["compute_type"] = actual_compute
                results["real_speech"][model_key] = real_res

        # 2. Synthetic Stress
        if args.suite in ["synthetic", "all"]:
            synth_res = evaluate_synthetic_stress(
                model, model_key=model_key, device=actual_device,
                max_clips=args.max_clips, per_clip_records=all_per_clip_records
            )
            if synth_res:
                synth_res["device"] = actual_device
                synth_res["compute_type"] = actual_compute
                results["synthetic_stress"][model_key] = synth_res

        # Free GPU memory between model evaluations
        del model

    # Save to JSON
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Saved empirical benchmark results to {RESULTS_JSON}")

    # Save per-clip results file
    PER_CLIP_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(PER_CLIP_JSONL, "w", encoding="utf-8") as f:
        for rec in all_per_clip_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[OK] Saved {len(all_per_clip_records)} per-clip records to {PER_CLIP_JSONL}")

    # Generate Markdown report and update README
    from scripts.generate_readme_tables import update_readme
    update_readme()
    print("[OK] Updated README.md and benchmark tables from results JSON.")


if __name__ == "__main__":
    main()
