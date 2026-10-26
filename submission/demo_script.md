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
| **0:12 – 0:32** *(20s)* | **Screen:** Open Notepad or VS Code. Hold **Alt+Shift+Space**. Overlay turns green with 🎤 "Listening...". Speak naturally: *"Yaar client presentation review karni hai, kal subah 10:30 AM par meeting schedule kar do."* Release key. Instant text insertion at cursor. | *"Feature 1: Push-to-Talk Dictation in ANY desktop app. Hold Alt+Shift+Space, speak fluid Hinglish. BolSamajh uses local faster-whisper on an RTX 3060 Ti with intelligent filler removal and script flexibility. Dictated text inserts right at your cursor with <!-- NUM:hw.stt_real_mean_latency_ms -->779.2<!-- /NUM --> ms mean latency (RTF <!-- NUM:hw.stt_real_rtf -->0.101<!-- /NUM -->x, p95: <!-- NUM:hw.stt_real_p95_latency_ms -->1492.6<!-- /NUM --> ms) across <!-- NUM:hw.stt_real_count -->300<!-- /NUM --> real speech clips on large-v3-turbo, or <!-- NUM:hw.stt_synth_latency_ms -->495.0<!-- /NUM --> ms on synthetic sentences — completely local STT on your hardware, zero API bill."* | **Local GPU STT: <!-- NUM:hw.stt_real_rtf -->0.101<!-- /NUM -->x RTF • <!-- NUM:hw.stt_synth_latency_ms -->495.0<!-- /NUM -->ms Synth • Zero Cloud Cost** |
| **0:32 – 0:54** *(22s)* | **Screen:** Press **Alt+Shift+D**, load a sample PDF document (e.g. *Insurance Policy / Tax Guidelines*). Press **Alt+Shift+A** and ask via mic: *"Is policy me health checkup aur claim reimbursement ka kya rule hai?"* BolSamajh streams sentence-by-sentence audio with page citation pill. Speak over audio or hit **Escape** to demonstrate voice barge-in / instant stop. | *"Feature 2: Talk-to-Document Intelligence. Load any PDF, Word doc, or webpage. Press Alt+Shift+A to ask questions in voice. Our multilingual vector retriever indexes context with <!-- NUM:rag.latency_ms -->22.31<!-- /NUM --> ms retrieval latency. BolSamajh cites the exact page number, explains it in conversational Hinglish, and streams audio sentence-by-sentence with <!-- NUM:hw.tts_first_packet_ms -->835.6<!-- /NUM --> ms Edge-TTS first-packet latency (~<!-- NUM:hw.total_ttfa_ms -->1702.8<!-- /NUM --> ms true end-to-end TTFA) and voice barge-in. Hit Escape or speak over to interrupt anytime."* | **Grounded RAG: <!-- NUM:rag.latency_ms -->22.31<!-- /NUM -->ms Search • <!-- NUM:hw.tts_first_packet_ms -->835.6<!-- /NUM -->ms TTS Packet • <!-- NUM:hw.total_ttfa_ms -->1702.8<!-- /NUM -->ms E2E TTFA • VAD Barge-In** |
| **0:54 – 1:12** *(18s)* | **Screen:** Highlight rough text in an email or Slack. Press **Alt+Shift+C**, speak: *"Make this email formal and concise."* The highlighted text immediately rewrites in-place to polished professional English/Hinglish. | *"Feature 3: In-App Voice Commands. Select text anywhere, hold Alt+Shift+C, and speak your intent — rewrite, shorten, translate to Hindi or Gujarati. The LLM modifies your selection directly inside your active window without touching a browser tab."* | **In-Place Voice Editing in Any Application** |
| **1:12 – 1:30** *(18s)* | **Screen:** Switch to BolSamajh Web-Call UI (`localhost:8000`) showing glowing audio visualizer, interactive chat cards, OpenAI-compatible `/v1` gateway for Bolna agents, and the real-speech + synthetic stress benchmark tables. | *"We didn't just build a wrapper — we evaluated <!-- NUM:benchmark.total_clips -->1,000<!-- /NUM --> real speech and synthetic stress clips across three models on an RTX 3060 Ti GPU, committed every per-clip result to per_clip_results.jsonl, and built an OpenAI-compatible TTS gateway for Bolna (not yet tested against a live agent). BolSamajh: Bolo. Samjho. Thank you!"* | **<!-- NUM:benchmark.total_clips -->1,000<!-- /NUM --> Benchmark Clips • Per-Clip JSONL Logs • Bolna Gateway • 100% Free** |

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
