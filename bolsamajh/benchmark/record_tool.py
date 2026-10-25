"""Interactive recording and synthetic generation tool for Hinglish benchmark sentences.

Features:
- Interactive CLI recording for human speaker (shows Roman + Devanagari, records WAV).
- Resumes where left off (saves metadata index).
- Synthetic mode (--synthetic) generates reference WAVs using Edge-TTS so the benchmark
  can run immediately and establish baseline measurements.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
import sounddevice as sd
import numpy as np

from bolsamajh.benchmark.sentences import SENTENCES, BenchmarkSentence

AUDIO_DIR = Path("benchmark_data/audio")
METADATA_FILE = Path("benchmark_data/metadata.json")


def _save_wav(filepath: Path, audio: np.ndarray, sample_rate: int = 16000):
    """Save float32 numpy array as 16-bit PCM WAV."""
    import wave
    filepath.parent.mkdir(parents=True, exist_ok=True)
    # Clip and convert to int16
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


def record_interactive():
    """Interactive recording session for human speaker."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    completed_ids = set()
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                completed_ids = {item["id"] for item in data}
        except Exception:
            pass

    print("=" * 65)
    print("  BolSamajh Hinglish Benchmark — Recording Tool")
    print(f"  Total sentences: {len(SENTENCES)} | Completed: {len(completed_ids)}")
    print("  Press Enter to start recording, then Enter to stop.")
    print("  Type 'q' to save & exit, 's' to skip.")
    print("=" * 65)

    sample_rate = 16000
    metadata = []
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = []

    for s in SENTENCES:
        wav_path = AUDIO_DIR / f"sentence_{s.id:03d}.wav"
        if s.id in completed_ids and wav_path.exists():
            continue

        print(f"\n[{s.id}/100] Category: {s.category.upper()}")
        print(f"  Roman:      {s.reference_roman}")
        print(f"  Devanagari: {s.reference_devanagari}")
        if s.notes:
            print(f"  Note:       {s.notes}")

        cmd = input("\n[Enter to record, 's' to skip, 'q' to quit]: ").strip().lower()
        if cmd == "q":
            break
        if cmd == "s":
            continue

        print("🎤 RECORDING... (Speak clearly, then press Enter to stop)")
        recording_frames = []
        is_recording = True

        def callback(indata, frames, time_info, status):
            if is_recording:
                recording_frames.append(indata.copy())

        stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32", callback=callback)
        with stream:
            input()  # Wait for user Enter
            is_recording = False

        if not recording_frames:
            print("No audio captured. Skipping.")
            continue

        audio = np.concatenate(recording_frames, axis=0).flatten()
        duration = len(audio) / sample_rate
        print(f"✓ Recorded {duration:.2f} seconds.")

        # Save WAV
        _save_wav(wav_path, audio, sample_rate)

        # Update metadata
        record_entry = {
            "id": s.id,
            "category": s.category,
            "reference_roman": s.reference_roman,
            "reference_devanagari": s.reference_devanagari,
            "wav_path": str(wav_path).replace("\\", "/"),
            "duration_sec": round(duration, 2),
            "source": "human",
            "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        metadata = [m for m in metadata if m["id"] != s.id]
        metadata.append(record_entry)
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        completed_ids.add(s.id)

    print(f"\nRecording session ended. {len(completed_ids)}/{len(SENTENCES)} sentences ready.")


async def generate_synthetic_dataset(voice: str = "hi-IN-SwaraNeural"):
    """Generate audio for all 100 sentences using Edge-TTS for synthetic baseline."""
    import edge_tts
    import av
    import io

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    metadata = []
    sample_rate = 16000

    print("=" * 65)
    print("  Generating Synthetic Benchmark Dataset via Edge-TTS")
    print(f"  Voice: {voice} | Sentences: {len(SENTENCES)}")
    print("=" * 65)

    for i, s in enumerate(SENTENCES, 1):
        wav_path = AUDIO_DIR / f"sentence_{s.id:03d}.wav"
        print(f"[{i:03d}/100] ({s.category:10s}) Generating: {s.reference_roman[:45]}...")

        # Use natural Devanagari text for Indian TTS neural voice
        text = s.reference_devanagari
        comm = edge_tts.Communicate(text, voice)
        mp3_data = io.BytesIO()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                mp3_data.write(chunk["data"])

        # Decode MP3 to 16kHz mono float32
        mp3_data.seek(0)
        container = av.open(mp3_data)
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

        # Resample to 16000 if needed
        in_sr = audio_stream.rate or 24000
        if in_sr != sample_rate:
            # Simple linear interpolation resampling
            in_len = len(raw_audio)
            out_len = int(in_len * sample_rate / in_sr)
            audio_resampled = np.interp(
                np.linspace(0, in_len, out_len, endpoint=False),
                np.arange(in_len),
                raw_audio,
            ).astype(np.float32)
        else:
            audio_resampled = raw_audio

        _save_wav(wav_path, audio_resampled, sample_rate)
        duration = len(audio_resampled) / sample_rate

        metadata.append({
            "id": s.id,
            "category": s.category,
            "reference_roman": s.reference_roman,
            "reference_devanagari": s.reference_devanagari,
            "wav_path": str(wav_path).replace("\\", "/"),
            "duration_sec": round(duration, 2),
            "source": f"edge_tts_{voice}",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Generated {len(metadata)} audio files in {AUDIO_DIR}/")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--synthetic":
        asyncio.run(generate_synthetic_dataset())
    else:
        record_interactive()
