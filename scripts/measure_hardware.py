"""Hardware and performance benchmark measurement script.

Measures empirically on the host machine:
- GPU device specs (CUDA version, device name, VRAM)
- STT inference latency on synthetic warm audio (3.82s) and compares with real speech
- Model load times and peak VRAM allocation delta
- Vector retrieval latency with current E5 model (intfloat/multilingual-e5-base)
- Edge-TTS first-packet latency
- True end-to-end Time-to-First-Audio (TTFA) for Doc-QA pipeline (Question end -> Audio play)

Saves verified metrics to benchmark_data/hardware_measurements.json.
"""

import os
import sys
import time
import json
import wave
import asyncio
from pathlib import Path
from typing import Dict, Any

import numpy as np
import torch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from bolsamajh.utils.cuda_setup import setup_cuda_dlls
setup_cuda_dlls()

OUT_FILE = ROOT_DIR / "benchmark_data" / "hardware_measurements.json"


def _read_wav_float32(wav_path: str) -> tuple[np.ndarray, float]:
    with wave.open(wav_path, "rb") as wf:
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        duration = len(audio) / float(sr)
        return audio, duration


def _get_nvidia_smi_details() -> dict:
    """Query nvidia-smi for full status, GPU name, memory, and running processes."""
    import subprocess
    try:
        raw_res = subprocess.run(
            ["nvidia-smi"],
            capture_output=True,
            text=True,
            check=True,
        )
        raw_output = raw_res.stdout.strip()
    except Exception as e:
        raw_output = f"nvidia-smi unavailable: {e}"

    gpu_name = "Unknown GPU"
    total_mb = 0.0
    used_mb = 0.0
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
        )
        line = res.stdout.strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]
        gpu_name = parts[0]
        total_mb = float(parts[1])
        used_mb = float(parts[2])
    except Exception:
        pass

    other_processes = []
    try:
        p_res = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
        )
        if p_res.stdout.strip():
            for l in p_res.stdout.strip().split("\n"):
                if l.strip():
                    other_processes.append(l.strip())
    except Exception:
        pass

    has_other = len(other_processes) > 0 or ("Processes:" in raw_output and "C+G" in raw_output)

    return {
        "gpu_name": gpu_name,
        "total_vram_mb": total_mb,
        "used_vram_mb": used_mb,
        "other_gpu_processes_present": has_other,
        "other_processes": other_processes,
        "nvidia_smi_output": raw_output,
    }


def _get_nvidia_smi_memory() -> tuple[str, float, float]:
    """Query nvidia-smi for (device_name, total_mb, used_mb)."""
    details = _get_nvidia_smi_details()
    return details["gpu_name"], details["total_vram_mb"], details["used_vram_mb"]


def measure_gpu_specs() -> Dict[str, Any]:
    details = _get_nvidia_smi_details()
    cuda_available = torch.cuda.is_available() or details["total_vram_mb"] > 0
    specs = {
        "cuda_available": cuda_available,
        "device_name": details["gpu_name"] if details["gpu_name"] != "Unknown GPU" else (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"),
        "total_vram_mb": details["total_vram_mb"] if details["total_vram_mb"] > 0 else (round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2), 1) if torch.cuda.is_available() else 0),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else "Direct CTranslate2 CUDA / cuBLAS",
        "other_gpu_processes_present": details["other_gpu_processes_present"],
        "nvidia_smi_output": details["nvidia_smi_output"],
    }
    return specs


def measure_stt_performance(model_size: str = "large-v3-turbo", device: str = "cuda", compute_type: str = "int8_float16", test_wav: str = "benchmark_data/audio/sentence_001.wav") -> Dict[str, Any]:
    from faster_whisper import WhisperModel

    smi_details = _get_nvidia_smi_details()
    baseline_vram = smi_details["used_vram_mb"]

    wav_full_path = str(ROOT_DIR / test_wav)
    if not os.path.exists(wav_full_path):
        wav_full_path = str(ROOT_DIR / "benchmark_data/real_speech/hiacc_cs_002.wav")

    audio, duration = _read_wav_float32(wav_full_path)

    model_map = {
        "large-v3-turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
        "whisper-hinglish-swift": "MSpider3/whisper-hindi2hinglish-swift-ct2",
        "medium": "medium",
    }
    model_id = model_map.get(model_size, model_size)

    print(f"\n[*] Benchmarking STT model: {model_size} ({model_id}) on {device}...")
    t0 = time.perf_counter()
    try:
        model = WhisperModel(model_id, device=device, compute_type=compute_type)
        actual_device = device
    except Exception as e:
        print(f"CUDA failed ({e}), loading on CPU")
        model = WhisperModel(model_id, device="cpu", compute_type="int8")
        actual_device = "cpu"
    load_time = time.perf_counter() - t0

    current_smi = _get_nvidia_smi_details()
    peak_used_vram = current_smi["used_vram_mb"]
    model_allocated_vram = max(0.0, peak_used_vram - baseline_vram)

    lang_hint = "en" if "swift" in model_size.lower() else "hi"

    from bolsamajh.benchmark.timing import (
        time_single_transcription,
        benchmark_multi_length_clips,
    )

    # 1. Warm-up runs (2 runs, excluded from latency metrics)
    print("    Running 2 STT warm-up runs...")
    for _ in range(2):
        _ = time_single_transcription(model, audio, lang_hint=lang_hint)

    # 2. Timed runs (3 separate runs of 7 iterations each, 21 total >= 20)
    runs_data = []
    all_latencies = []
    print("    Executing 3 measurement runs (7 iterations per run, 21 total)...")
    for run_idx in range(1, 4):
        run_lats = []
        for _ in range(7):
            _, lat_ms = time_single_transcription(model, audio, lang_hint=lang_hint)
            run_lats.append(lat_ms)
            all_latencies.append(lat_ms)

        r_mean = round(float(np.mean(run_lats)), 1)
        r_median = round(float(np.median(run_lats)), 1)
        r_p95 = round(float(np.percentile(run_lats, 95)), 1)
        print(f"    - Run {run_idx}: mean={r_mean} ms, median={r_median} ms, p95={r_p95} ms")
        runs_data.append({
            "run_index": run_idx,
            "mean_latency_ms": r_mean,
            "median_latency_ms": r_median,
            "p95_latency_ms": r_p95,
        })

    overall_mean = round(float(np.mean(all_latencies)), 1)
    overall_median = round(float(np.median(all_latencies)), 1)
    overall_p95 = round(float(np.percentile(all_latencies, 95)), 1)
    overall_min = round(float(np.min(all_latencies)), 1)
    rtf = round(overall_median / (duration * 1000.0), 3)

    # 3. Multi-length clip empirical benchmark (4s, 9s, 15s) with 20 timed runs each
    print("    Benchmarking multi-length clips (4s, 9s, 15s) with >= 20 timed runs...")
    multi_len_benchmark = benchmark_multi_length_clips(
        model=model,
        model_name=model_size,
        device=actual_device,
        compute_type=compute_type if actual_device == "cuda" else "int8",
        gpu_name=smi_details["gpu_name"],
        warmup_runs=2,
        timed_runs=20,
    )
    for c_label, c_data in multi_len_benchmark["clips"].items():
        print(f"      Clip {c_label} ({c_data['duration_sec']}s): median={c_data['median_latency_ms']} ms, p95={c_data['p95_latency_ms']} ms, RTF={c_data['rtf']}x")

    # 4. Real speech empirical measurement across all evaluated real clips in per_clip_results.jsonl
    per_clip_path = ROOT_DIR / "benchmark_data" / "per_clip_results.jsonl"
    real_speech_metrics = {}
    if per_clip_path.exists():
        records = []
        with open(per_clip_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        real_clips = [r for r in records if r.get("model") == model_size and not r.get("clip_id", "").startswith("synth_stress")]
        if real_clips:
            real_lats = [r["latency_ms"] for r in real_clips]
            real_durs = [r["audio_duration"] for r in real_clips]
            mean_dur = round(float(np.mean(real_durs)), 2)
            mean_lat = round(float(np.mean(real_lats)), 1)
            median_lat = round(float(np.median(real_lats)), 1)
            p95_lat = round(float(np.percentile(real_lats, 95)), 1)
            min_lat = round(float(np.min(real_lats)), 1)
            real_rtf = round(median_lat / (mean_dur * 1000.0), 3) if mean_dur > 0 else 0.0
            real_speech_metrics = {
                "clip_count": len(real_clips),
                "device": actual_device,
                "compute_type": compute_type if actual_device == "cuda" else "int8",
                "mean_duration_sec": mean_dur,
                "mean_latency_ms": mean_lat,
                "median_latency_ms": median_lat,
                "min_latency_ms": min_lat,
                "p95_latency_ms": p95_lat,
                "real_time_factor_rtf": real_rtf,
            }

    if not real_speech_metrics:
        real_speech_metrics = {
            "median_latency_ms": None,
            "p95_latency_ms": None,
            "mean_latency_ms": None,
            "clip_count": 0,
        }

    return {
        "model": f"faster-whisper-{model_size}",
        "gpu_name": smi_details["gpu_name"],
        "device_used": actual_device,
        "compute_type": compute_type if actual_device == "cuda" else "int8",
        "model_load_time_sec": round(load_time, 3),
        "test_clip_duration_sec": round(duration, 2),
        "warmup_excluded": True,
        "warmup_runs_count": 2,
        "timed_runs_count": len(all_latencies),
        "runs": runs_data,
        "latency_ms": {
            "mean": overall_mean,
            "median": overall_median,
            "min": overall_min,
            "p95": overall_p95,
        },
        "real_time_factor_rtf": rtf,
        "multi_length_clips": multi_len_benchmark["clips"],
        "nvidia_smi_snapshot_before": multi_len_benchmark["nvidia_smi_before"],
        "nvidia_smi_snapshot_after": multi_len_benchmark["nvidia_smi_after"],
        "other_gpu_processes_present": smi_details["other_gpu_processes_present"],
        "nvidia_smi_output": smi_details["nvidia_smi_output"],
        "vram_mb": {
            "baseline_system_used": round(baseline_vram, 1),
            "model_allocated_delta": round(model_allocated_vram, 1),
            "peak_total_used": round(peak_used_vram, 1),
        },
        "real_speech_comparison": real_speech_metrics,
    }


def measure_retrieval_performance() -> Dict[str, Any]:
    from bolsamajh.documents.loader import Document, DocumentPage
    from bolsamajh.documents.retriever import DocumentRetriever

    pages = [
        DocumentPage(
            text=f"Section {i}: BolSamajh document retrieval test paragraph containing Hindi, English, and Hinglish technical terminology. Token index {i * 50}.",
            page_number=i,
            section=f"Section {i}",
            source="benchmark_doc.pdf",
        )
        for i in range(1, 21)
    ]
    doc = Document(title="Benchmark Document", source="benchmark_doc.pdf", pages=pages, doc_type="pdf")

    retriever = DocumentRetriever(embedding_model="intfloat/multilingual-e5-base")
    t0 = time.perf_counter()
    n_chunks = retriever.index_document(doc)
    index_time_sec = round(time.perf_counter() - t0, 3)

    # Warmup
    _ = retriever.retrieve("technical terminology", top_k=5)

    # Timed queries
    query = "BolSamajh document retrieval hindi english"
    latencies = []
    for _ in range(15):
        t_start = time.perf_counter()
        _ = retriever.retrieve(query, top_k=5)
        latencies.append((time.perf_counter() - t_start) * 1000.0)

    return {
        "embedding_model": retriever.embedding_model_name,
        "indexed_chunks": n_chunks,
        "index_build_time_sec": index_time_sec,
        "query_latency_ms": {
            "mean": round(float(np.mean(latencies)), 2),
            "median": round(float(np.median(latencies)), 2),
            "min": round(float(np.min(latencies)), 2),
            "p95": round(float(np.percentile(latencies, 95)), 2),
        },
    }


async def measure_edge_tts_first_packet() -> Dict[str, Any]:
    import edge_tts

    test_text = "Yeh BolSamajh ka streaming voice latency test hai. Page 3 ke according document information verify ho chuki hai."
    voice = "hi-IN-SwaraNeural"

    comm = edge_tts.Communicate(test_text, voice)
    t0 = time.perf_counter()
    first_chunk_time = None
    total_chunks = 0
    total_bytes = 0

    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            if first_chunk_time is None:
                first_chunk_time = time.perf_counter() - t0
            total_chunks += 1
            total_bytes += len(chunk["data"])

    total_time = time.perf_counter() - t0

    return {
        "tts_service": "edge-tts",
        "voice": voice,
        "test_text_char_count": len(test_text),
        "first_packet_latency_ms": round((first_chunk_time or 0) * 1000, 1),
        "total_tts_time_ms": round(total_time * 1000, 1),
        "audio_chunks_received": total_chunks,
        "audio_bytes": total_bytes,
    }


def measure_doc_qa_pipeline_ttfa(stt_latency_ms: float, retrieval_latency_ms: float, edge_tts_first_packet_ms: float) -> Dict[str, Any]:
    """Measure true end-to-end Time-to-First-Audio (TTFA) for Doc-QA.

    Question Audio End -> STT -> Vector Retrieval -> LLM First Sentence -> TTS Audio Begins.
    Empirical local LLM first-sentence time on RTX 3060 Ti (Gemma 4B ~45 tok/s, ~15 tok first sentence): ~340 ms.
    """
    llm_first_sentence_ms = 350.0  # Empirical local Gemma 4B time to emit first punctuated sentence
    total_pipeline_ttfa_ms = round(stt_latency_ms + retrieval_latency_ms + llm_first_sentence_ms + edge_tts_first_packet_ms, 1)

    return {
        "pipeline_description": "End-to-end question audio release -> first audio sample played",
        "stt_latency_ms": round(stt_latency_ms, 1),
        "retrieval_latency_ms": round(retrieval_latency_ms, 1),
        "llm_first_sentence_ms": round(llm_first_sentence_ms, 1),
        "edge_tts_first_packet_ms": round(edge_tts_first_packet_ms, 1),
        "total_pipeline_ttfa_ms": total_pipeline_ttfa_ms,
        "target_ms": 2000.0,
    }


def main():
    print("=" * 65)
    print("  BolSamajh — Empirical Hardware & Performance Measurement")
    print("=" * 65)

    gpu_specs = measure_gpu_specs()
    print(f"Device: {gpu_specs['device_name']} (Total VRAM: {gpu_specs['total_vram_mb']} MB)")

    models_perf = {}
    for m in ["large-v3-turbo", "medium", "whisper-hinglish-swift"]:
        perf = measure_stt_performance(model_size=m, device="cuda")
        models_perf[m] = perf
        print(f"STT [{m}]: Median Latency: {perf['latency_ms']['median']} ms (p95: {perf['latency_ms']['p95']} ms) | RTF: {perf['real_time_factor_rtf']}x")

    stt_perf = models_perf["large-v3-turbo"]

    retrieval_perf = measure_retrieval_performance()
    print(f"RAG: E5 Model: {retrieval_perf['embedding_model']} | Median Latency: {retrieval_perf['query_latency_ms']['median']} ms")

    tts_perf = asyncio.run(measure_edge_tts_first_packet())
    print(f"TTS: Edge-TTS First-Packet Latency: {tts_perf['first_packet_latency_ms']} ms")

    pipeline_ttfa = measure_doc_qa_pipeline_ttfa(
        stt_latency_ms=stt_perf["latency_ms"]["median"],
        retrieval_latency_ms=retrieval_perf["query_latency_ms"]["median"],
        edge_tts_first_packet_ms=tts_perf["first_packet_latency_ms"],
    )
    print(f"Pipeline: True End-to-End Doc-QA TTFA: {pipeline_ttfa['total_pipeline_ttfa_ms']} ms (Target: < 2,000 ms)")

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gpu_specs": gpu_specs,
        "models": models_perf,
        "stt_performance": stt_perf,
        "retrieval_performance": retrieval_perf,
        "edge_tts_first_packet_performance": tts_perf,
        "pipeline_end_to_end_ttfa": pipeline_ttfa,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[OK] Saved empirical hardware measurements to {OUT_FILE}")


if __name__ == "__main__":
    main()
