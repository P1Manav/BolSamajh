import asyncio
import os
import json
import subprocess
import edge_tts

NARRATOR = "en-IN-NeerjaExpressiveNeural"
HINDI_MALE = "hi-IN-MadhurNeural"
HINDI_FEMALE = "hi-IN-SwaraNeural"
GUJARATI_MALE = "gu-IN-NiranjanNeural"
GUJARATI_FEMALE = "gu-IN-DhwaniNeural"

# Refined audio items with exact word counts & rates for tight sync
REFINED_SPECS = [
    # C1: Hook (0 - 360)
    {
        "id": "c1_hook_narrator",
        "voice": NARRATOR,
        "rate": "+22%",
        "text": "500 million Indians speak fluid Hinglish every day. Yet commercial voice tools charge monthly subscriptions, while sensitive Indian documents cannot leave the device."
    },

    # C2: Dictation (360 - 1020)
    {
        "id": "c2_dictate_intro",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "With BolSamajh, push-to-talk dictation works in any desktop app. Hold Alt Shift Space."
    },
    {
        "id": "c2_demo_prompt",
        "voice": HINDI_MALE,
        "rate": "+18%",
        "text": "Invoice pe 18 percent GST add karke total pandrah hazar kar do."
    },
    {
        "id": "c2_dictate_formatting",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "Speech is cleaned of fillers, with automatic rupee formatting and explicit script control for Roman or Devanagari."
    },

    # C3: Doc QA (1020 - 1920)
    {
        "id": "c3_docqa_intro",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "Here is the wedge: Talk-to-Document intelligence. Index any PDF, then hold Alt Shift A."
    },
    {
        "id": "c3_demo_q1",
        "voice": HINDI_MALE,
        "rate": "+16%",
        "text": "Kya ICU charges cover hote hain?"
    },
    {
        "id": "c3_demo_a1",
        "voice": HINDI_FEMALE,
        "rate": "+16%",
        "text": "Page 1 ke mutabiq ICU charges 100 percent cover hote hain."
    },
    {
        "id": "c3_bargein_user",
        "voice": HINDI_MALE,
        "rate": "+24%",
        "text": "Ruko! Ek minute."
    },
    {
        "id": "c3_bargein_narrator",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "Interrupt anytime with hands-free voice barge-in in under 70 milliseconds."
    },
    {
        "id": "c3_demo_a_refusal",
        "voice": HINDI_FEMALE,
        "rate": "+16%",
        "text": "Yeh document mein nahi hai."
    },
    {
        "id": "c3_refusal_narrator",
        "voice": NARRATOR,
        "rate": "+20%",
        "text": "And when something is not in the text, it refuses honestly."
    },

    # C4: Offline & Benchmark (1920 - 2340)
    {
        "id": "c4_offline_narrator",
        "voice": NARRATOR,
        "rate": "+20%",
        "text": "Turn off Wi-Fi completely. BolSamajh runs 100 percent air-gapped on-device with Faster-Whisper and Piper TTS."
    },
    {
        "id": "c4_benchmark_narrator",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "Our public benchmark publishes raw and normalized WER side-by-side with complete transparency."
    },

    # C5: Ecosystem & Close (2340 - 2700)
    {
        "id": "c5_ecosystem_narrator",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "Access browser Web-Call mode, pair with Android, or use as a free Bolna gateway."
    },
    {
        "id": "c5_download_narrator",
        "voice": NARRATOR,
        "rate": "+18%",
        "text": "Download the Windows installer on GitHub and try it in under 60 seconds."
    },
    {
        "id": "c5_tagline",
        "voice": NARRATOR,
        "rate": "+10%",
        "text": "Bolo. Samjho."
    }
]

async def main():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "public", "audio", "final")
    os.makedirs(out_dir, exist_ok=True)
    
    measurements = {}
    print("Generating refined tracks...")
    for item in REFINED_SPECS:
        path = os.path.join(out_dir, f"{item['id']}.mp3")
        communicate = edge_tts.Communicate(item["text"], item["voice"], rate=item["rate"])
        await communicate.save(path)
        
        res = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path
        ]).decode().strip()
        sec = float(res)
        frames = int(round(sec * 30))
        measurements[item["id"]] = {
            "sec": round(sec, 2),
            "frames": frames,
            "file": f"audio/final/{item['id']}.mp3"
        }
        print(f"  [OK] {item['id']}: {sec:.2f}s ({frames} frames)")
    
    json_path = os.path.join(os.path.dirname(__file__), "..", "src", "audio_measurements.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(measurements, f, indent=2)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
