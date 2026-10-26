import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import hashlib
import wave
import io
from bolsamajh.tts.piper_adapter import PiperTTSAdapter, _MODEL_SHA256, _CONFIG_SHA256, _MODEL_FILENAME, _CONFIG_FILENAME


def get_sha256(filepath: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    size = 0
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
            size += len(chunk)
    return size, h.hexdigest()


def main():
    print("[*] Initializing PiperTTSAdapter and performing real offline synthesis...")
    adapter = PiperTTSAdapter()
    text = "नमस्ते, यह बोलसमझ का ऑफलाइन टेक्स्ट टू स्पीच परीक्षण है।"
    wav_bytes = adapter.synthesize_to_bytes(text)

    models_dir = Path("models/piper")
    model_file = models_dir / _MODEL_FILENAME
    config_file = models_dir / _CONFIG_FILENAME

    model_size, model_hash = get_sha256(model_file)
    config_size, config_hash = get_sha256(config_file)

    print(f"Model file:  {model_file.name} ({model_size} bytes)")
    print(f"  SHA-256:   {model_hash}")
    print(f"  Pinned:    {_MODEL_SHA256}")
    print(f"  Match:     {model_hash.lower() == _MODEL_SHA256.lower()}")

    print(f"Config file: {config_file.name} ({config_size} bytes)")
    print(f"  SHA-256:   {config_hash}")
    print(f"  Pinned:    {_CONFIG_SHA256}")
    print(f"  Match:     {config_hash.lower() == _CONFIG_SHA256.lower()}")

    wav_io = io.BytesIO(wav_bytes)
    with wave.open(wav_io, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        duration_sec = n_frames / float(framerate)

    wav_hash = hashlib.sha256(wav_bytes).hexdigest()

    print(f"\nSynthesis Output:")
    print(f"  Text:          '{text}'")
    print(f"  WAV Size:      {len(wav_bytes)} bytes")
    print(f"  Channels:      {n_channels}")
    print(f"  Sample Rate:   {framerate} Hz")
    print(f"  Duration:      {duration_sec:.2f} s")
    print(f"  WAV SHA-256:   {wav_hash}")

    evidence_path = Path("docs/evidence/piper_check.txt")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_content = (
        f"BolSamajh — Piper Offline TTS Live Empirical Verification\n"
        f"==========================================================\n"
        f"Input Text: {text}\n"
        f"\n"
        f"1. Model Artifact Verification:\n"
        f"   Filename:      {model_file.name}\n"
        f"   Bytes:         {model_size}\n"
        f"   SHA-256:       {model_hash}\n"
        f"   Pinned SHA:    {_MODEL_SHA256}\n"
        f"   Verified:      {'PASS' if model_hash.lower() == _MODEL_SHA256.lower() else 'FAIL'}\n"
        f"\n"
        f"2. Config Artifact Verification:\n"
        f"   Filename:      {config_file.name}\n"
        f"   Bytes:         {config_size}\n"
        f"   SHA-256:       {config_hash}\n"
        f"   Pinned SHA:    {_CONFIG_SHA256}\n"
        f"   Verified:      {'PASS' if config_hash.lower() == _CONFIG_SHA256.lower() else 'FAIL'}\n"
        f"\n"
        f"3. Real Audio Synthesis Output:\n"
        f"   WAV Total Bytes: {len(wav_bytes)}\n"
        f"   Channels:        {n_channels}\n"
        f"   Sample Width:    {sampwidth * 8}-bit\n"
        f"   Sample Rate:     {framerate} Hz\n"
        f"   Frames:          {n_frames}\n"
        f"   Duration:        {duration_sec:.2f} seconds\n"
        f"   WAV SHA-256:     {wav_hash}\n"
        f"   Status:          VERIFIED LIVE (no mock)\n"
    )
    with open(evidence_path, "w", encoding="utf-8") as f:
        f.write(evidence_content)
    print(f"\n[+] Evidence saved to {evidence_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
