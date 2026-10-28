"""Deterministic benchmark data downloader and synthetic audio generator.

Adheres to Tier 2 Requirements:
- Downloads and extracts public datasets (CC-BY-4.0):
  * 100 clips of Google FLEURS Hindi (hi_in)
  * 100 clips of Google FLEURS Gujarati (gu_in)
  * 100 clips of HiACC Hindi-English code-switched speech
- Generates 100 synthetic benchmark sentences deterministically using fixed random seeds:
  * 3+ Edge-TTS neural voices (Swara, Madhur, Neerja, Dhwani)
  * Noise degradations at 20 dB, 10 dB, and 5 dB SNR
  * 8 kHz telephone band-limit (300-3400 Hz) + G.711 mu-law companding
  * Speed variations at ±10% (0.90x and 1.10x)
- Records exact per-clip metadata in metadata.json and real_speech_manifest.json.
"""

import argparse
import asyncio
import io
import json
import random
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pyarrow.parquet as pq
import scipy.signal
import soundfile as sf
from huggingface_hub import hf_hub_download

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
REAL_DIR = ROOT_DIR / "benchmark_data" / "real_speech"
SYNTH_DIR = ROOT_DIR / "benchmark_data" / "audio"
REAL_MANIFEST = ROOT_DIR / "benchmark_data" / "real_speech_manifest.json"
SYNTH_METADATA = ROOT_DIR / "benchmark_data" / "metadata.json"

EDGE_VOICES = [
    "hi-IN-SwaraNeural",  # Female Hindi
    "hi-IN-MadhurNeural",  # Male Hindi
    "en-IN-NeerjaNeural",  # Female Indian English
    "gu-IN-DhwaniNeural",  # Female Gujarati
]


def set_fixed_seeds(seed: int = 42):
    """Seed Python and NumPy random number generators for exact reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def save_audio_bytes_as_wav(audio_bytes: bytes, out_path: Path, target_sr: int = 16000) -> float:
    """Read audio bytes and save as clean 16kHz mono 16-bit PCM WAV."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.BytesIO(audio_bytes) as bio:
        data, sr = sf.read(bio)

    if data.ndim > 1:
        data = data.mean(axis=1)

    if sr != target_sr:
        num_target_samples = int(len(data) * target_sr / sr)
        data = np.interp(
            np.linspace(0, len(data), num_target_samples, endpoint=False),
            np.arange(len(data)),
            data,
        )

    duration_sec = len(data) / target_sr
    data_int16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(target_sr)
        wf.writeframes(data_int16.tobytes())

    return duration_sec


def apply_audio_degradations(
    audio: np.ndarray,
    sr: int = 16000,
    speed_factor: float = 1.0,
    snr_db: Optional[float] = None,
    phone_filter: bool = False,
    apply_mu_law: bool = False,
) -> np.ndarray:
    """Apply calibrated digital signal processing degradations."""
    out = audio.copy()

    # 1. Speed factor variation via linear interpolation resampling
    if speed_factor != 1.0 and len(out) > 0:
        new_length = int(len(out) / speed_factor)
        out = np.interp(
            np.linspace(0, len(out), new_length, endpoint=False),
            np.arange(len(out)),
            out,
        ).astype(np.float32)

    # 2. 8 kHz Telephony bandpass filter (300 Hz - 3400 Hz passband)
    if phone_filter and len(out) > 0:
        nyquist = sr / 2.0
        low = 300.0 / nyquist
        high = 3400.0 / nyquist
        sos = scipy.signal.butter(4, [low, high], btype="bandpass", output="sos")
        out = scipy.signal.sosfilt(sos, out).astype(np.float32)

        # Downsample to 8kHz then back to 16kHz
        half_len = int(len(out) * 8000 / sr)
        down = np.interp(
            np.linspace(0, len(out), half_len, endpoint=False),
            np.arange(len(out)),
            out,
        )
        out = np.interp(
            np.linspace(0, half_len, len(out), endpoint=False),
            np.arange(half_len),
            down,
        ).astype(np.float32)

    # 3. G.711 standard mu-law companding simulation (mu=255)
    if apply_mu_law and len(out) > 0:
        mu = 255.0
        # Compress
        compressed = np.sign(out) * np.log(1.0 + mu * np.abs(out)) / np.log(1.0 + mu)
        # 8-bit quantization
        quantized = np.round((compressed + 1.0) * 127.5) / 127.5 - 1.0
        # Expand
        out = np.sign(quantized) * (1.0 / mu) * ((1.0 + mu) ** np.abs(quantized) - 1.0)
        out = out.astype(np.float32)

    # 4. Additive Gaussian noise at specified SNR
    if snr_db is not None and len(out) > 0:
        signal_power = np.mean(out**2)
        if signal_power > 1e-8:
            snr_linear = 10.0 ** (snr_db / 10.0)
            noise_power = signal_power / snr_linear
            noise = np.random.normal(0, np.sqrt(noise_power), len(out)).astype(np.float32)
            out = out + noise

    return np.clip(out, -1.0, 1.0)


def extract_hiacc(num_clips: int = 100) -> List[Dict[str, Any]]:
    """Extract clean code-switched Hindi-English samples from HiACC."""
    print(f"Extracting {num_clips} code-switched clips from HiACC...")
    parquet_path = hf_hub_download(
        repo_id="Trelis/hiacc-adult-test-eval",
        filename="data/adult_test-00000-of-00001.parquet",
        repo_type="dataset",
    )
    table = pq.read_table(parquet_path)
    records = []

    count = 0
    for i in range(len(table)):
        cs_count = table["code_switch_count"][i].as_py()
        transcript = (table["transcription"][i].as_py() or "").strip()
        words = len(transcript.split())

        # Quality guard: require active code-switching (>= 1 point) and non-truncated references (>= 4 words)
        if cs_count and cs_count >= 1 and words >= 4:
            audio_dict = table["audio"][i].as_py()
            audio_bytes = audio_dict["bytes"]

            clip_name = f"hiacc_cs_{count + 1:03d}.wav"
            out_file = REAL_DIR / clip_name
            dur = save_audio_bytes_as_wav(audio_bytes, out_file)

            # Extra guard: discard if audio is long (> 5s) but transcript is excessively brief (< 3 words)
            if dur > 5.0 and words < 3:
                continue

            records.append(
                {
                    "id": f"hiacc_{count + 1:03d}",
                    "dataset": "HiACC (Trelis/hiacc-adult-test-eval)",
                    "split": "code_switched_hinglish",
                    "wav_file": f"benchmark_data/real_speech/{clip_name}",
                    "reference": transcript,
                    "duration_sec": round(dur, 2),
                    "code_switch_points": cs_count,
                    "license": "CC-BY-4.0",
                }
            )
            count += 1
            if count >= num_clips:
                break

    print(f"✓ Saved {len(records)} HiACC clips to {REAL_DIR}")
    return records


def extract_fleurs(lang_code: str, split_name: str, num_clips: int = 100) -> List[Dict[str, Any]]:
    """Extract speech samples from Google FLEURS."""
    print(f"Extracting {num_clips} clips from FLEURS {lang_code} ({split_name})...")
    parquet_path = hf_hub_download(
        repo_id="google/fleurs",
        filename=f"parquet-data/{lang_code}/validation-00000-of-00001.parquet",
        repo_type="dataset",
    )
    table = pq.read_table(parquet_path)
    records = []

    for i in range(min(num_clips, len(table))):
        transcript = table["transcription"][i].as_py()
        audio_dict = table["audio"][i].as_py()
        audio_bytes = audio_dict["bytes"]

        clip_name = f"fleurs_{lang_code}_{i + 1:03d}.wav"
        out_file = REAL_DIR / clip_name
        dur = save_audio_bytes_as_wav(audio_bytes, out_file)

        records.append(
            {
                "id": f"fleurs_{lang_code}_{i + 1:03d}",
                "dataset": f"Google FLEURS ({lang_code})",
                "split": split_name,
                "wav_file": f"benchmark_data/real_speech/{clip_name}",
                "reference": transcript,
                "duration_sec": round(dur, 2),
                "license": "CC-BY-4.0",
            }
        )

    print(f"✓ Saved {len(records)} FLEURS {lang_code} clips to {REAL_DIR}")
    return records


async def generate_synthetic_stress_dataset(num_clips: int = 100):
    """Generate 100 synthetic degraded stress clips deterministically with Edge-TTS."""
    import av
    import edge_tts

    from bolsamajh.benchmark.sentences import SENTENCES

    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    metadata = []
    sample_rate = 16000

    print("\n" + "=" * 70)
    print("  Generating 100 Synthetic Degraded Stress Clips (Edge-TTS)")
    print(f"  Voices: {', '.join(EDGE_VOICES)}")
    print("  Degradations: Noise (20/10/5 dB SNR), 8kHz Phone + Mu-Law, Speed (±10%)")
    print("=" * 70)

    for i, s in enumerate(SENTENCES[:num_clips], 1):
        wav_path = SYNTH_DIR / f"sentence_{s.id:03d}.wav"
        voice = EDGE_VOICES[(s.id - 1) % len(EDGE_VOICES)]

        # Multi-tier degradation schedule
        if 1 <= s.id <= 20:
            deg_profile = "clean"
            speed = 1.0
            snr = None
            phone = False
            mu_law = False
        elif 21 <= s.id <= 40:
            deg_profile = "speed_variation"
            speed = 0.90 if s.id % 2 == 0 else 1.10
            snr = None
            phone = False
            mu_law = False
        elif 41 <= s.id <= 60:
            # 20 dB (mild), 10 dB (moderate), 5 dB (severe)
            snr_choice = 20.0 if s.id <= 48 else (10.0 if s.id <= 55 else 5.0)
            deg_profile = f"noise_{int(snr_choice)}db_snr"
            speed = 1.0
            snr = snr_choice
            phone = False
            mu_law = False
        elif 61 <= s.id <= 80:
            deg_profile = "8khz_telephone_mulaw"
            speed = 1.0
            snr = None
            phone = True
            mu_law = True
        else:
            deg_profile = "combined_stress"
            speed = 1.10
            snr = 10.0
            phone = True
            mu_law = True

        # Render TTS audio in target script
        if voice.startswith("hi-IN"):
            text = s.reference_devanagari
        elif voice.startswith("gu-IN"):
            from aksharamukha import transliterate

            text = transliterate.process("Devanagari", "Gujarati", s.reference_devanagari)
        else:
            text = s.reference_roman

        comm = edge_tts.Communicate(text, voice)
        mp3_buf = io.BytesIO()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                mp3_buf.write(chunk["data"])

        # Decode MP3 frames to numpy array
        mp3_buf.seek(0)
        container = av.open(mp3_buf)
        audio_stream = container.streams.audio[0]
        frames = []
        for frame in container.decode(audio_stream):
            arr = frame.to_ndarray()
            if arr.ndim > 1:
                arr = arr.mean(axis=0)
            frames.append(arr)

        if not frames:
            continue

        raw_audio = np.concatenate(frames).astype(np.float32)
        if raw_audio.max() > 1.0:
            raw_audio = raw_audio / 32768.0

        # Resample to 16 kHz
        in_sr = audio_stream.rate or 24000
        if in_sr != sample_rate:
            in_len = len(raw_audio)
            out_len = int(in_len * sample_rate / in_sr)
            audio_16k = np.interp(
                np.linspace(0, in_len, out_len, endpoint=False),
                np.arange(in_len),
                raw_audio,
            ).astype(np.float32)
        else:
            audio_16k = raw_audio

        # Apply deterministic degradations
        degraded = apply_audio_degradations(
            audio_16k,
            sr=sample_rate,
            speed_factor=speed,
            snr_db=snr,
            phone_filter=phone,
            apply_mu_law=mu_law,
        )

        # Save to disk
        out_int16 = (np.clip(degraded, -1.0, 1.0) * 32767).astype(np.int16)
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(out_int16.tobytes())

        dur = len(degraded) / sample_rate
        metadata.append(
            {
                "id": s.id,
                "category": s.category,
                "reference_roman": s.reference_roman,
                "reference_devanagari": s.reference_devanagari,
                "wav_path": str(wav_path.relative_to(ROOT_DIR)).replace("\\", "/"),
                "duration_sec": round(dur, 2),
                "voice": voice,
                "degradation": deg_profile,
                "degradation_params": {
                    "speed_factor": speed,
                    "snr_db": snr,
                    "phone_filter": phone,
                    "mu_law": mu_law,
                },
                "dataset_type": "synthetic_stress_test",
            }
        )

        if i % 20 == 0 or i == num_clips:
            print(f"[{i:03d}/{num_clips}] Generated ({deg_profile}): {s.reference_roman[:35]}...")

    with open(SYNTH_METADATA, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(
        f"✓ Saved {len(metadata)} synthetic stress clips to {SYNTH_DIR} (metadata in {SYNTH_METADATA})"
    )


def main():
    parser = argparse.ArgumentParser(description="Fetch and build benchmark datasets")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducible generation"
    )
    parser.add_argument(
        "--real-clips", type=int, default=100, help="Clips per real speech split (default: 100)"
    )
    parser.add_argument(
        "--synth-clips",
        type=int,
        default=100,
        help="Number of synthetic stress clips (default: 100)",
    )
    parser.add_argument("--skip-synth", action="store_true", help="Skip synthetic generation")
    parser.add_argument("--skip-real", action="store_true", help="Skip real dataset extraction")
    args = parser.parse_args()

    set_fixed_seeds(args.seed)
    REAL_DIR.mkdir(parents=True, exist_ok=True)
    SYNTH_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Real Speech extraction (100 per split = 300 total)
    if not args.skip_real:
        print("\n=== 1. Extracting Real Speech Datasets (300 clips) ===")
        manifest = []
        hiacc_clips = extract_hiacc(num_clips=args.real_clips)
        manifest.extend(hiacc_clips)

        fleurs_hi_clips = extract_fleurs("hi_in", "read_hindi", num_clips=args.real_clips)
        manifest.extend(fleurs_hi_clips)

        fleurs_gu_clips = extract_fleurs("gu_in", "read_gujarati", num_clips=args.real_clips)
        manifest.extend(fleurs_gu_clips)

        with open(REAL_MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"✓ Real Speech Manifest saved to {REAL_MANIFEST} (Total: {len(manifest)} clips)")

    # 2. Synthetic dataset generation
    if not args.skip_synth:
        print("\n=== 2. Generating Synthetic Stress Dataset ===")
        asyncio.run(generate_synthetic_stress_dataset(num_clips=args.synth_clips))

    print("\n[OK] Benchmark data successfully prepared.")


if __name__ == "__main__":
    main()
