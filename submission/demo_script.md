# BolSamajh — 90-Second Demo Video Script & Shot List

> **Event:** Bolna x Symphony Voice AI Buildathon  
> **Tagline:** *"Bolo. Samjho."* — Speak to write and act in any app, talk to any document in your language.  
> **Target Duration:** Exactly 90 seconds (1 min 30 sec)  
> **Presenter:** Manav (Solo Builder, Ahmedabad)

---

## Shot List & Narrative Flow

| Timecode | Visual / Screen Action | Spoken Voiceover (Script) | Key On-Screen Callout |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:12** *(12s)* | **Screen:** BolSamajh HUD overlay glowing on desktop. Quick demonstration of everyday code-switched speech ("Chai peene chalte hain, meeting 3:45 baje hai") typed out cleanly. | *"500 million Indians speak Hinglish every single day — mixing Hindi grammar with English vocabulary. Yet standard voice tools either force pure English or output phonetic garble. Meet BolSamajh: Bolo. Samjho — speech intelligence engineered for Indian language workflows."* | **500M+ Hinglish Speakers Need Grounded Voice AI** |
| **0:12 – 0:32** *(20s)* | **Screen:** Open Notepad or VS Code. Hold **Alt+Shift+Space**. Overlay turns green with 🎤 "Listening...". Speak naturally: *"Yaar client presentation review karni hai, kal subah 10:30 AM par meeting schedule kar do."* Release key. Instant text insertion at cursor. | *"Feature 1: Push-to-Talk Dictation in ANY desktop app. Hold Alt+Shift+Space, speak fluid Hinglish. BolSamajh uses local faster-whisper on an RTX 3060 Ti with intelligent filler removal and script flexibility. Dictated text inserts right at your cursor with 2,262 ms latency on a 15.5s real speech clip (RTF 0.146x, running 6.8x faster than real-time) on Whisper medium, or 997 ms on large-v3-turbo — completely local STT on your hardware, zero API bill."* | **Local GPU STT: 0.146x RTF (Medium) • 997ms (Turbo) • Zero Cloud Cost** |
| **0:32 – 0:54** *(22s)* | **Screen:** Press **Alt+Shift+D**, load a sample PDF document (e.g. *Insurance Policy / Tax Guidelines*). Press **Alt+Shift+A** and ask via mic: *"Is policy me health checkup aur claim reimbursement ka kya rule hai?"* BolSamajh streams sentence-by-sentence audio with page citation pill. Speak over audio or hit **Escape** to demonstrate voice barge-in / instant stop. | *"Feature 2: Talk-to-Document Intelligence. Load any PDF, Word doc, or webpage. Press Alt+Shift+A to ask questions in voice. Our multilingual vector retriever indexes context with 22.3 ms retrieval latency. BolSamajh cites the exact page number, explains it in conversational Hinglish, and streams audio sentence-by-sentence with 673 ms Edge-TTS first-packet latency (~2.5s true end-to-end TTFA) and voice barge-in. Hit Escape or speak over to interrupt anytime."* | **Grounded RAG: 22ms Search • 673ms TTS Packet • 2.5s E2E TTFA • VAD Barge-In** |
| **0:54 – 1:12** *(18s)* | **Screen:** Highlight rough text in an email or Slack. Press **Alt+Shift+C**, speak: *"Make this email formal and concise."* The highlighted text immediately rewrites in-place to polished professional English/Hinglish. | *"Feature 3: In-App Voice Commands. Select text anywhere, hold Alt+Shift+C, and speak your intent — rewrite, shorten, translate to Hindi or Gujarati. The LLM modifies your selection directly inside your active window without touching a browser tab."* | **In-Place Voice Editing in Any Application** |
| **1:12 – 1:30** *(18s)* | **Screen:** Switch to BolSamajh Web-Call UI (`localhost:8000`) showing glowing audio visualizer, interactive chat cards, OpenAI-compatible `/v1` gateway for Bolna agents, and the real-speech + synthetic stress benchmark tables. | *"We didn't just build a wrapper — we evaluated 1,200 real speech and synthetic stress clips across three models on an RTX 3060 Ti GPU, committed every per-clip result to per_clip_results.jsonl, and connected directly to Bolna voice agents. BolSamajh: Bolo. Samjho. Thank you!"* | **1,200 Benchmark Clips • Per-Clip JSONL Logs • Bolna Compatible • 100% Free** |

---

## Recording Tips for Manav

1. **Audio Setup:** Use a clean USB or headset mic in a quiet room.
2. **Screen Resolution:** Record at 1920x1080 (1080p 60fps) with OBS Studio.
3. **Cursor Visibility:** Enable cursor highlight or large pointer so hotkeys and text insertion are clear.
4. **App Sequence:**
   - Notepad (Dictation demo)
   - BolSamajh Document Q&A (PDF loaded)
   - Browser / Email draft (Voice Command demo)
   - BolSamajh Web UI (`http://localhost:8000`)
