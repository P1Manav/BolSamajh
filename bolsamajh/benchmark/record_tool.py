"""Synthetic generation and interactive recording tool for Hinglish benchmark sentences.

Adheres to Tier 1 Requirement 5:
- 100 sentences clearly labelled as SYNTHETIC stress set.
- Multiple TTS neural voices (Hindi male/female, Gujarati female, Indian English female).
- Automated open-source audio degradations via numpy and scipy.signal:
  * Speed variation (0.90x – 1.15x)
  * Additive Gaussian noise (15 – 25 dB SNR)
  * 8 kHz telephony phone-codec simulation (300 Hz – 3,400 Hz bandpass filter)
"""

import json
import time
import io
import wave
import asyncio
from pathlib import Path
from typing import Optional

import numpy as np
import scipy.signal

from bolsamajh.benchmark.sentences import SENTENCES

AUDIO_DIR = Path("benchmark_data/audio")
METADATA_FILE = Path("benchmark_data/metadata.json")

VOICES = [
    "hi-IN-SwaraNeural",    # Female Hindi
    "hi-IN-MadhurNeural",   # Male Hindi
    "gu-IN-DhwaniNeural",   # Female Gujarati
    "en-IN-NeerjaNeural",   # Female Indian English
]


def _save_wav(filepath: Path, audio: np.ndarray, sample_rate: int = 16000):
    """Save float32 numpy array as 16-bit PCM WAV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


def apply_audio_degradations(
    audio: np.ndarray,
    sr: int = 16000,
    speed_factor: float = 1.0,
    snr_db: Optional[float] = None,
    phone_filter: bool = False,
) -> np.ndarray:
    """Apply automated degradations to clean audio: speed change, noise, and 8kHz phone filter."""
    out = audio.copy()
    
    # 1. Speed factor variation via linear interpolation resampling
    if speed_factor != 1.0 and len(out) > 0:
        new_length = int(len(out) / speed_factor)
        out = np.interp(
            np.linspace(0, len(out), new_length, endpoint=False),
            np.arange(len(out)),
            out
        ).astype(np.float32)

    # 2. 8 kHz Telephony simulation (G.711 standard passband 300 Hz - 3400 Hz)
    if phone_filter and len(out) > 0:
        nyquist = sr / 2.0
        low = 300.0 / nyquist
        high = 3400.0 / nyquist
        sos = scipy.signal.butter(4, [low, high], btype='bandpass', output='sos')
        out = scipy.signal.sosfilt(sos, out).astype(np.float32)
        
        # Downsample to 8kHz then back to 16kHz to simulate telephone quantization
        half_len = int(len(out) * 8000 / sr)
        down = np.interp(
            np.linspace(0, len(out), half_len, endpoint=False),
            np.arange(len(out)),
            out
        )
        out = np.interp(
            np.linspace(0, half_len, len(out), endpoint=False),
            np.arange(half_len),
            down
        ).astype(np.float32)

    # 3. Additive Gaussian ambient noise
    if snr_db is not None and len(out) > 0:
        signal_power = np.mean(out ** 2)
        if signal_power > 1e-8:
            snr_linear = 10.0 ** (snr_db / 10.0)
            noise_power = signal_power / snr_linear
            noise = np.random.normal(0, np.sqrt(noise_power), len(out)).astype(np.float32)
            out = out + noise

    # Clip to prevent clipping distortion
    return np.clip(out, -1.0, 1.0)


async def generate_synthetic_dataset():
    """Generate audio for all 100 sentences with multi-voice rotation and automated degradations."""
    import edge_tts
    import av

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    metadata = []
    sample_rate = 16000

    print("=" * 70)
    print("  Generating Synthetic Benchmark Stress Set (100 Sentences)")
    print(f"  Voices: {', '.join(VOICES)}")
    print("  Automated Degradations: Speed variation, 8 kHz Telephony, Noise injection")
    print("=" * 70)

    for i, s in enumerate(SENTENCES, 1):
        wav_path = AUDIO_DIR / f"sentence_{s.id:03d}.wav"
        
        # Multi-voice rotation
        voice = VOICES[(s.id - 1) % len(VOICES)]
        
        # Determine degradation profile based on index
        if 1 <= s.id <= 20:
            deg_profile = "clean"
            speed = 1.0
            snr = None
            phone = False
        elif 21 <= s.id <= 40:
            deg_profile = "speed_variation"
            speed = 0.90 if s.id % 2 == 0 else 1.15
            snr = None
            phone = False
        elif 41 <= s.id <= 60:
            deg_profile = "noise_injection"
            speed = 1.0
            snr = 20.0
            phone = False
        elif 61 <= s.id <= 80:
            deg_profile = "8khz_telephony_codec"
            speed = 1.0
            snr = None
            phone = True
        else:
            deg_profile = "combined_stress"
            speed = 1.10
            snr = 22.0
            phone = True

        print(f"[{i:03d}/100] ({s.category:10s} | {voice.split('-')[2][:5]} | {deg_profile}): {s.reference_roman[:35]}...")

        # Select appropriate script according to TTS voice locale
        if voice.startswith("hi-IN"):
            text = s.reference_devanagari
        elif voice.startswith("gu-IN"):
            from aksharamukha import transliterate
            text = transliterate.process("Devanagari", "Gujarati", s.reference_devanagari)
        else:
            text = s.reference_roman

        comm = edge_tts.Communicate(text, voice)
        mp3_data = io.BytesIO()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                mp3_data.write(chunk["data"])

        # Decode MP3 to float32
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

        # Resample to 16000
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

        # Apply automated degradations
        degraded_audio = apply_audio_degradations(
            audio_16k,
            sr=sample_rate,
            speed_factor=speed,
            snr_db=snr,
            phone_filter=phone
        )

        _save_wav(wav_path, degraded_audio, sample_rate)
        duration = len(degraded_audio) / sample_rate

        metadata.append({
            "id": s.id,
            "category": s.category,
            "reference_roman": s.reference_roman,
            "reference_devanagari": s.reference_devanagari,
            "wav_path": str(wav_path).replace("\\", "/"),
            "duration_sec": round(duration, 2),
            "voice": voice,
            "degradation": deg_profile,
            "dataset_type": "synthetic_stress_test",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Generated {len(metadata)} synthetic stress audio files in {AUDIO_DIR}/")


if __name__ == "__main__":
    asyncio.run(generate_synthetic_dataset())
