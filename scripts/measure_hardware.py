"""Hardware and performance benchmark measurement script.

Measures empirically on the host machine:
- GPU device specs (CUDA version, device name, VRAM)
- Model load times (STT, embeddings)
- Peak VRAM allocated and reserved (via torch.cuda)
- STT inference latency (with warm-up run), RTF, min/mean/p95
- Vector retrieval latency (FAISS inner product search)
- Time-to-first-audio (TTFA) from streaming TTS

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

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from bolsamajh.utils.cuda_setup import setup_cuda_dlls
setup_cuda_dlls()


OUT_FILE = Path("benchmark_data/hardware_measurements.json")


def _read_wav_float32(wav_path: str) -> tuple[np.ndarray, float]:
    with wave.open(wav_path, "rb") as wf:
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        duration = len(audio) / float(sr)
        return audio, duration


def _get_nvidia_smi_memory() -> tuple[str, float, float]:
    """Query nvidia-smi for (device_name, total_mb, used_mb)."""
    import subprocess
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
        )
        line = res.stdout.strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]
        return parts[0], float(parts[1]), float(parts[2])
    except Exception:
        return "Unknown GPU", 0.0, 0.0


def measure_gpu_specs() -> Dict[str, Any]:
    gpu_name, total_vram, used_vram = _get_nvidia_smi_memory()
    cuda_available = torch.cuda.is_available() or total_vram > 0
    specs = {
        "cuda_available": cuda_available,
        "device_name": gpu_name if gpu_name != "Unknown GPU" else (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"),
        "total_vram_mb": total_vram if total_vram > 0 else (round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2), 1) if torch.cuda.is_available() else 0),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else "Direct CTranslate2 CUDA / cuBLAS",
    }
    return specs


def measure_stt_performance(model_size: str = "medium", device: str = "cuda", compute_type: str = "int8_float16", test_wav: str = "benchmark_data/audio/sentence_001.wav") -> Dict[str, Any]:
    from faster_whisper import WhisperModel

    _, _, baseline_vram = _get_nvidia_smi_memory()

    print(f"Loading faster-whisper '{model_size}' on {device} ({compute_type})...")
    t0 = time.perf_counter()
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    load_time_sec = round(time.perf_counter() - t0, 3)

    _, _, loaded_vram = _get_nvidia_smi_memory()

    audio_np, duration_sec = _read_wav_float32(test_wav)

    # 1. Warm-up run (excluded from latency stats)
    print("Running STT warm-up...")
    _ = list(model.transcribe(audio_np, language="hi"))

    # 2. Timed runs
    runs = 5
    latencies_ms = []
    print(f"Running {runs} timed transcription runs...")
    peak_used_vram = loaded_vram
    for _ in range(runs):
        t_start = time.perf_counter()
        segments, info = model.transcribe(audio_np, language="hi")
        _ = " ".join(s.text for s in segments)
        lat = (time.perf_counter() - t_start) * 1000.0
        latencies_ms.append(lat)
        _, _, current_vram = _get_nvidia_smi_memory()
        if current_vram > peak_used_vram:
            peak_used_vram = current_vram

    model_allocated_vram = max(0.0, loaded_vram - baseline_vram)


    mean_lat = round(float(np.mean(latencies_ms)), 1)
    median_lat = round(float(np.median(latencies_ms)), 1)
    p95_lat = round(float(np.percentile(latencies_ms, 95)), 1)
    min_lat = round(float(np.min(latencies_ms)), 1)
    rtf = round((mean_lat / 1000.0) / duration_sec, 3)

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {
        "model": f"faster-whisper-{model_size}",
        "device": device,
        "compute_type": compute_type,
        "model_load_time_sec": load_time_sec,
        "test_clip_duration_sec": round(duration_sec, 2),
        "warmup_excluded": True,
        "runs": runs,
        "latency_ms": {
            "mean": mean_lat,
            "median": median_lat,
            "min": min_lat,
            "p95": p95_lat,
        },
        "real_time_factor_rtf": rtf,
        "vram_mb": {
            "baseline_system_used": round(baseline_vram, 1),
            "model_allocated_delta": round(model_allocated_vram, 1),
            "peak_total_used": round(peak_used_vram, 1),
        }

    }


def measure_retrieval_performance() -> Dict[str, Any]:
    from bolsamajh.documents.loader import Document, DocumentPage
    from bolsamajh.documents.retriever import DocumentRetriever

    # Create mock 20-page document for retrieval benchmarking
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

    retriever = DocumentRetriever()
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
        }
    }


async def measure_ttfa_performance() -> Dict[str, Any]:
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
        "time_to_first_audio_chunk_ms": round((first_chunk_time or 0) * 1000, 1),
        "total_tts_time_ms": round(total_time * 1000, 1),
        "audio_chunks_received": total_chunks,
        "audio_bytes": total_bytes,
    }


def main():
    print("=" * 65)
    print("  BolSamajh — Empirical Hardware & Performance Measurement")
    print("=" * 65)

    gpu_specs = measure_gpu_specs()
    print(f"Device: {gpu_specs['device_name']} (Total VRAM: {gpu_specs['total_vram_mb']} MB)")

    stt_perf = measure_stt_performance()
    print(f"STT: Mean Latency: {stt_perf['latency_ms']['mean']} ms | Model VRAM Delta: {stt_perf['vram_mb']['model_allocated_delta']} MB | Peak Used: {stt_perf['vram_mb']['peak_total_used']} MB")


    retrieval_perf = measure_retrieval_performance()
    print(f"RAG: Mean Retrieval Latency: {retrieval_perf['query_latency_ms']['mean']} ms across {retrieval_perf['indexed_chunks']} chunks")

    ttfa_perf = asyncio.run(measure_ttfa_performance())
    print(f"TTS: Time To First Audio (TTFA): {ttfa_perf['time_to_first_audio_chunk_ms']} ms | Total: {ttfa_perf['total_tts_time_ms']} ms")

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gpu_specs": gpu_specs,
        "stt_performance": stt_perf,
        "retrieval_performance": retrieval_perf,
        "tts_ttfa_performance": ttfa_perf,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✓ Saved hardware measurements to {OUT_FILE}")


if __name__ == "__main__":
    main()
