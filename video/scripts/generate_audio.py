import asyncio
import os
import json
import edge_tts

DEMO_VOICES = {
    "hindi_male": "hi-IN-MadhurNeural",
    "hindi_female": "hi-IN-SwaraNeural",
    "gujarati_male": "gu-IN-NiranjanNeural",
    "gujarati_female": "gu-IN-DhwaniNeural",
    "narrator": "en-IN-PrabhatNeural",
}

DEMO_AUDIO_ITEMS = [
    {
        "filename": "dictation_prompt.mp3",
        "voice": DEMO_VOICES["hindi_male"],
        "rate": "+0%",
        "text": "Invoice pe 18 percent GST add karke total pandrah hazar kar do."
    },
    {
        "filename": "doc_qa_question.mp3",
        "voice": DEMO_VOICES["hindi_male"],
        "rate": "+0%",
        "text": "Kya ICU charges cover hote hain?"
    },
    {
        "filename": "doc_qa_answer.mp3",
        "voice": DEMO_VOICES["hindi_female"],
        "rate": "-4%",
        "text": "Page 1 ke mutabiq ICU charges 100 percent cover hote hain."
    },
    {
        "filename": "doc_qa_gujarati_q.mp3",
        "voice": DEMO_VOICES["gujarati_male"],
        "rate": "+0%",
        "text": "Maternity benefit ketlu male chhe?"
    },
    {
        "filename": "doc_qa_gujarati_a.mp3",
        "voice": DEMO_VOICES["gujarati_female"],
        "rate": "-4%",
        "text": "Page 2 mujab maternity benefit pachas hajaar sudhi male chhe."
    },
    {
        "filename": "doc_qa_refusal.mp3",
        "voice": DEMO_VOICES["hindi_female"],
        "rate": "-4%",
        "text": "Yeh document mein nahi hai."
    },
    {
        "filename": "bargein_user.mp3",
        "voice": DEMO_VOICES["hindi_male"],
        "rate": "+10%",
        "text": "Ruko! Ek minute."
    }
]

VO_ITEMS = [
    {
        "filename": "vo_01_hook.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "We speak Hinglish. Software doesn't."
    },
    {
        "filename": "vo_02_problem_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Over 500 million people talk like this every day."
    },
    {
        "filename": "vo_02_problem_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Yet critical policies and contracts arrive in dense legal English."
    },
    {
        "filename": "vo_02_problem_3.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Voice software forces you into pure English or formal Hindi."
    },
    {
        "filename": "vo_03_solution_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Meet BolSamajh. One local companion for voice in, out, and action."
    },
    {
        "filename": "vo_03_solution_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Dictate anywhere, talk to any document, and edit with your voice."
    },
    {
        "filename": "vo_04_arch_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Global hotkeys trigger local Whisper STT, multilingual-e5 embeddings, and local Ollama."
    },
    {
        "filename": "vo_04_arch_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Your voice audio stays on your machine. Zero cloud fees."
    },
    {
        "filename": "vo_05a_dictate_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Hold Alt Shift Space in any application."
    },
    {
        "filename": "vo_05a_dictate_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "It strips fillers and formats rupees and GST automatically."
    },
    {
        "filename": "vo_05b_docqa_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Press Alt Shift D to index any PDF, then hold Alt Shift A."
    },
    {
        "filename": "vo_05b_docqa_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Answers stream sentence by sentence with verifiable page citations."
    },
    {
        "filename": "vo_05b_docqa_3.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Interrupt hands-free with voice barge-in anytime."
    },
    {
        "filename": "vo_05b_docqa_4.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "And when something is not in the text, it refuses honestly."
    },
    {
        "filename": "vo_05c_offline_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Turn off the internet completely."
    },
    {
        "filename": "vo_05c_offline_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "BolSamajh runs 100 percent air-gapped on your GPU or CPU with Piper TTS."
    },
    {
        "filename": "vo_06_diff_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Unlike closed cloud tools costing fifteen dollars a month, BolSamajh is open source."
    },
    {
        "filename": "vo_06_diff_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Wispr Flow has 100-plus languages, but BolSamajh gives you offline privacy and citations."
    },
    {
        "filename": "vo_07_tech_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Backed by 1,000 real speech benchmark clips on public open datasets."
    },
    {
        "filename": "vo_07_tech_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Sub-second latency, 98 percent retrieval accuracy, and drop-in Bolna gateway support."
    },
    {
        "filename": "vo_08_close_1.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-2%",
        "text": "Download the Windows installer or clone the code on GitHub."
    },
    {
        "filename": "vo_08_close_2.mp3",
        "voice": DEMO_VOICES["narrator"],
        "rate": "-4%",
        "text": "BolSamajh. Bolo. Samjho."
    }
]

async def generate_file(item, output_dir):
    out_path = os.path.join(output_dir, item["filename"])
    communicate = edge_tts.Communicate(item["text"], item["voice"], rate=item["rate"])
    await communicate.save(out_path)
    print(f"Generated {out_path} ({os.path.getsize(out_path)} bytes)")

async def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    public_dir = os.path.join(base_dir, "..", "public")
    demo_dir = os.path.join(public_dir, "audio", "demo")
    vo_dir = os.path.join(public_dir, "audio", "vo")

    os.makedirs(demo_dir, exist_ok=True)
    os.makedirs(vo_dir, exist_ok=True)

    print("--- Generating Demo Audio ---")
    for item in DEMO_AUDIO_ITEMS:
        await generate_file(item, demo_dir)

    print("--- Generating Voiceover Segments ---")
    for item in VO_ITEMS:
        await generate_file(item, vo_dir)

    print("All audio generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())

