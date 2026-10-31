import asyncio
import os
import json
import subprocess
import edge_tts

NARRATOR = "en-IN-NeerjaExpressiveNeural"

TUNED_SPECS = [
    # C3 Refusal narrator
    {
        "id": "c3_refusal_narrator",
        "voice": NARRATOR,
        "rate": "+22%",
        "text": "And it refuses out-of-document queries honestly."
    },
    # C4 Offline narrator
    {
        "id": "c4_offline_narrator",
        "voice": NARRATOR,
        "rate": "+24%",
        "text": "Turn off Wi-Fi: BolSamajh runs 100 percent air-gapped on-device with Faster-Whisper and Piper TTS."
    },
    # C4 Benchmark narrator
    {
        "id": "c4_benchmark_narrator",
        "voice": NARRATOR,
        "rate": "+22%",
        "text": "Our public benchmark publishes raw and normalized WER side-by-side with complete transparency."
    },
    # C5 Unified Close Narration
    {
        "id": "c5_close_unified",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "Access browser Web-Call mode, pair with Android, or use as a free Bolna gateway. Download the Windows installer on GitHub. Bolo. Samjho."
    }
]

async def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "public", "audio", "final")
    for item in TUNED_SPECS:
        path = os.path.join(out_dir, f"{item['id']}.mp3")
        communicate = edge_tts.Communicate(item["text"], item["voice"], rate=item["rate"])
        await communicate.save(path)
        
        res = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path
        ]).decode().strip()
        sec = float(res)
        frames = int(round(sec * 30))
        print(f"  [OK] {item['id']}: {sec:.2f}s ({frames} frames)")

if __name__ == "__main__":
    asyncio.run(main())

