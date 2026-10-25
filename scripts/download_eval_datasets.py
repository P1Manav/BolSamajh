"""Download and prepare real speech evaluation datasets from public sources.

Datasets used:
1. Google FLEURS Hindi (hi_in) - Read Hindi speech (CC-BY-4.0)
2. Google FLEURS Gujarati (gu_in) - Read Gujarati speech (CC-BY-4.0)
3. HiACC Adult Test Eval - Real Hindi-English Code-Switched speech (CC-BY-4.0)

Extracts balanced evaluation subsets and saves them with verified references to:
  benchmark_data/real_speech/
  benchmark_data/real_speech_manifest.json
"""

import io
import sys
import json
import wave
from pathlib import Path

from huggingface_hub import hf_hub_download
import pyarrow.parquet as pq
import soundfile as sf
import numpy as np

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "benchmark_data" / "real_speech"
MANIFEST_PATH = ROOT_DIR / "benchmark_data" / "real_speech_manifest.json"


def save_audio_bytes_as_wav(audio_bytes: bytes, out_path: Path, target_sr: int = 16000) -> float:
    """Read audio bytes (wav/mp3/flac) and save as 16kHz mono 16-bit PCM WAV."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.BytesIO(audio_bytes) as bio:
        data, sr = sf.read(bio)
    
    # Convert stereo to mono if necessary
    if data.ndim > 1:
        data = data.mean(axis=1)
    
    # Resample to 16kHz if needed
    if sr != target_sr:
        num_target_samples = int(len(data) * target_sr / sr)
        data = np.interp(
            np.linspace(0, len(data), num_target_samples, endpoint=False),
            np.arange(len(data)),
            data
        )
    
    duration_sec = len(data) / target_sr
    
    # Save as 16-bit PCM
    data_int16 = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(target_sr)
        wf.writeframes(data_int16.tobytes())
        
    return duration_sec


def process_hiacc(num_clips: int = 20) -> list:
    """Extract code-switched Hindi-English samples from HiACC."""
    print("Downloading HiACC Adult Test Eval parquet...")
    parquet_path = hf_hub_download(
        repo_id="Trelis/hiacc-adult-test-eval",
        filename="data/adult_test-00000-of-00001.parquet",
        repo_type="dataset"
    )
    table = pq.read_table(parquet_path)
    records = []
    
    count = 0
    for i in range(len(table)):
        cs_count = table["code_switch_count"][i].as_py()
        if cs_count and cs_count >= 2:  # Strong code-switching
            transcript = table["transcription"][i].as_py()
            audio_dict = table["audio"][i].as_py()
            audio_bytes = audio_dict["bytes"]
            
            clip_name = f"hiacc_cs_{count+1:03d}.wav"
            out_file = OUTPUT_DIR / clip_name
            dur = save_audio_bytes_as_wav(audio_bytes, out_file)
            
            records.append({
                "id": f"hiacc_{count+1:03d}",
                "dataset": "HiACC (Trelis/hiacc-adult-test-eval)",
                "split": "code_switched_hinglish",
                "wav_file": f"benchmark_data/real_speech/{clip_name}",
                "reference": transcript,
                "duration_sec": round(dur, 2),
                "code_switch_points": cs_count,
                "license": "CC-BY-4.0"
            })
            count += 1
            if count >= num_clips:
                break
                
    print(f"Extracted {len(records)} code-switched clips from HiACC.")
    return records


def process_fleurs(lang_code: str, split_name: str, num_clips: int = 20) -> list:
    """Extract read speech samples from Google FLEURS."""
    print(f"Downloading FLEURS {lang_code} validation parquet...")
    parquet_path = hf_hub_download(
        repo_id="google/fleurs",
        filename=f"parquet-data/{lang_code}/validation-00000-of-00001.parquet",
        repo_type="dataset"
    )
    table = pq.read_table(parquet_path)
    records = []
    
    for i in range(min(num_clips, len(table))):
        transcript = table["transcription"][i].as_py()
        audio_dict = table["audio"][i].as_py()
        audio_bytes = audio_dict["bytes"]
        
        clip_name = f"fleurs_{lang_code}_{i+1:03d}.wav"
        out_file = OUTPUT_DIR / clip_name
        dur = save_audio_bytes_as_wav(audio_bytes, out_file)
        
        records.append({
            "id": f"fleurs_{lang_code}_{i+1:03d}",
            "dataset": f"Google FLEURS ({lang_code})",
            "split": split_name,
            "wav_file": f"benchmark_data/real_speech/{clip_name}",
            "reference": transcript,
            "duration_sec": round(dur, 2),
            "license": "CC-BY-4.0"
        })
        
    print(f"Extracted {len(records)} clips from FLEURS {lang_code}.")
    return records


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_manifest = []
    
    # 1. HiACC Hindi-English Code-Switched
    hiacc_records = process_hiacc(num_clips=20)
    all_manifest.extend(hiacc_records)
    
    # 2. FLEURS Hindi
    fleurs_hi = process_fleurs("hi_in", "read_hindi", num_clips=20)
    all_manifest.extend(fleurs_hi)
    
    # 3. FLEURS Gujarati
    fleurs_gu = process_fleurs("gu_in", "read_gujarati", num_clips=20)
    all_manifest.extend(fleurs_gu)
    
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(all_manifest, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccessfully created Real Speech Manifest at {MANIFEST_PATH}")
    print(f"Total real speech clips: {len(all_manifest)}")


if __name__ == "__main__":
    main()
