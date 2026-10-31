import asyncio
import os
import edge_tts
import subprocess

# Voice definitions
# NeerjaExpressiveNeural for articulate, natural Indian English narration
NARRATOR_VOICE = "en-IN-NeerjaExpressiveNeural"
HINDI_MALE = "hi-IN-MadhurNeural"
HINDI_FEMALE = "hi-IN-SwaraNeural"
GUJARATI_MALE = "gu-IN-NiranjanNeural"
GUJARATI_FEMALE = "gu-IN-DhwaniNeural"

# Target rate adjustments
AUDIO_SPECS = [
    # Chapter 1: Problem Hook (0 - 360f, narrator 15 - 330f = max 10.5s)
    {
        "id": "c1_hook_narrator",
        "voice": NARRATOR_VOICE,
        "rate": "+4%",
        "text": "500 million Indians speak fluid Hinglish every day. Yet commercial voice tools charge monthly subscriptions for dictation alone, while sensitive Indian documents cannot leave the device to foreign clouds."
    },

    # Chapter 2: Dictation Anywhere (360 - 1020f)
    # Part 1: Intro (375 - 515f = max 4.6s)
    {
        "id": "c2_dictate_intro",
        "voice": NARRATOR_VOICE,
        "rate": "+5%",
        "text": "With BolSamajh, push-to-talk dictation works in any desktop app. Hold Alt Shift Space."
    },
    # Part 2: User prompt (545 - 665f = max 4.0s)
    {
        "id": "c2_demo_prompt",
        "voice": HINDI_MALE,
        "rate": "+6%",
        "text": "Invoice pe 18 percent GST add karke total pandrah hazar kar do."
    },
    # Part 3: Formatting explanation (725 - 845f = max 4.0s)
    {
        "id": "c2_dictate_formatting",
        "voice": NARRATOR_VOICE,
        "rate": "+5%",
        "text": "Speech is cleaned of fillers, with automatic rupee and GST formatting."
    },
    # Part 4: Script control (875 - 985f = max 3.6s)
    {
        "id": "c2_dictate_script",
        "voice": NARRATOR_VOICE,
        "rate": "+5%",
        "text": "Plus explicit script control for Roman Hinglish or formal Devanagari."
    },

    # Chapter 3: Talk-to-Document Intelligence (1020 - 1920f)
    # Part 1: Intro (1030 - 1170f = max 4.6s)
    {
        "id": "c3_docqa_intro",
        "voice": NARRATOR_VOICE,
        "rate": "+5%",
        "text": "Here is the wedge: Talk-to-Document intelligence. Index any PDF, then hold Alt Shift A."
    },
    # Part 2: Question 1 (1205 - 1285f = max 2.6s)
    {
        "id": "c3_demo_q1",
        "voice": HINDI_MALE,
        "rate": "+5%",
        "text": "Kya ICU charges cover hote hain?"
    },
    # Part 2: Answer 1 (1300 - 1425f = max 4.1s)
    {
        "id": "c3_demo_a1",
        "voice": HINDI_FEMALE,
        "rate": "+2%",
        "text": "Page 1 ke mutabiq ICU charges 100 percent cover hote hain."
    },
    # Part 3: Barge-in user interrupt (1445 - 1505f = max 2.0s)
    {
        "id": "c3_bargein_user",
        "voice": HINDI_MALE,
        "rate": "+15%",
        "text": "Ruko! Ek minute."
    },
    # Part 3: Barge-in narrator explanation (1515 - 1605f = max 3.0s)
    {
        "id": "c3_bargein_narrator",
        "voice": NARRATOR_VOICE,
        "rate": "+6%",
        "text": "Interrupt anytime with hands-free voice barge-in in under 70 milliseconds."
    },
    # Part 4: Gujarati question (1625 - 1690f = max 2.1s)
    {
        "id": "c3_demo_q_guj",
        "voice": GUJARATI_MALE,
        "rate": "+8%",
        "text": "Maternity benefit ketlu male chhe?"
    },
    # Part 4: Gujarati answer (1695 - 1760f = max 2.1s)
    {
        "id": "c3_demo_a_guj",
        "voice": GUJARATI_FEMALE,
        "rate": "+8%",
        "text": "Page 2 mujab maternity benefit pachas hajaar sudhi male chhe."
    },
    # Part 5: Refusal answer (1775 - 1835f = max 2.0s)
    {
        "id": "c3_demo_a_refusal",
        "voice": HINDI_FEMALE,
        "rate": "+5%",
        "text": "Yeh document mein nahi hai."
    },
    # Part 5: Refusal narrator explanation (1840 - 1915f = max 2.5s)
    {
        "id": "c3_refusal_narrator",
        "voice": NARRATOR_VOICE,
        "rate": "+8%",
        "text": "And when something is not in the text, it refuses honestly."
    },

    # Chapter 4: Air-Gapped Offline Mode & Benchmark (1920 - 2340f)
    # Part 1: Offline mode (1930 - 2100f = max 5.6s)
    {
        "id": "c4_offline_narrator",
        "voice": NARRATOR_VOICE,
        "rate": "+5%",
        "text": "Turn off Wi-Fi completely: BolSamajh runs 100 percent air-gapped on-device with Faster-Whisper and Piper TTS."
    },
    # Part 2: Benchmark table (2130 - 2280f = max 5.0s)
    {
        "id": "c4_benchmark_narrator",
        "voice": NARRATOR_VOICE,
        "rate": "+6%",
        "text": "Our public benchmark publishes raw and normalized WER side-by-side with complete transparency."
    },

    # Chapter 5: Web Call, Android & Close (2340 - 2700f)
    # Part 1: Ecosystem (2345 - 2500f = max 5.1s)
    {
        "id": "c5_ecosystem_narrator",
        "voice": NARRATOR_VOICE,
        "rate": "+6%",
        "text": "Access browser Web-Call mode, pair with Android, or use as a free drop-in audio gateway for Bolna voice agents."
    },
    # Part 2: Download card (2525 - 2625f = max 3.3s)
    {
        "id": "c5_download_narrator",
        "voice": NARRATOR_VOICE,
        "rate": "+6%",
        "text": "Download the Windows installer on GitHub and try it in under 60 seconds."
    },
    # Part 3: Tagline (2645 - 2685f = max 1.3s)
    {
        "id": "c5_tagline",
        "voice": NARRATOR_VOICE,
        "rate": "-4%",
        "text": "BolSamajh. Bolo. Samjho."
    }
]

async def generate_all():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "public", "audio", "v2")
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Generating {len(AUDIO_SPECS)} calibrated audio files into {out_dir}...")
    for spec in AUDIO_SPECS:
        path = os.path.join(out_dir, f"{spec['id']}.mp3")
        communicate = edge_tts.Communicate(spec["text"], spec["voice"], rate=spec["rate"])
        await communicate.save(path)
        
        # Measure duration with ffprobe
        res = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path
        ]).decode().strip()
        sec = float(res)
        frames = int(round(sec * 30))
        print(f"[{spec['id']}] {sec:.2f}s ({frames} frames)")

if __name__ == "__main__":
    asyncio.run(generate_all())

