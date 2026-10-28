# BolSamajh — 90-Second Demo Video Script & Shot List

> **Event:** Bolna x Symphony Voice AI Buildathon  
> **Tagline:** *"Bolo. Samjho."* — Speak to write and act in any app, talk to any document in your language.  
> **Target Duration:** Exactly 90 seconds (189 spoken words, pace ~125 wpm)  
> **Presenter:** Manav (Solo Builder, Ahmedabad)  
> **Note:** Video recording is a MANUAL task for the repository owner; follow the shot list and script below.

---

## Shot List & Narrative Flow

| Timecode | Visual / Screen Action | Spoken Voiceover (Script) | Key On-Screen Callout |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:15** *(15s)* | **Screen:** Desktop view with floating BolSamajh HUD docked in system tray. Show title card and prompt overlay. | *"Over 500 million Indians speak Hinglish every day, but existing voice tools force an unnatural choice between pure English and formal Hindi. Meet BolSamajh: Bolo. Samjho — open-source, private voice intelligence built for Indian language workflows."* | **500M+ Hinglish Speakers • Open-Source & Private** |
| **0:15 – 0:35** *(20s)* | **Screen:** Open Notepad. Hold **`Alt+Shift+Space`**. HUD glows green (🎤 *Listening*). Speak: *"Yaar client review ke liye kal subah 10:30 par meeting schedule kar do."* Release key. Clean text inserts at cursor. | *"First, Push-to-Talk Dictation in any application. Hold Alt+Shift+Space and speak naturally. Release, and it types instantly at your cursor. Running locally with Whisper turbo at under 0.1 Real-Time Factor — fast, private, and zero cloud API cost."* | **Local GPU STT: ~0.06x RTF • Alt+Shift+Space Dictation** |
| **0:35 – 0:55** *(20s)* | **Screen:** Press **`Alt+Shift+D`** to open file dialog and select a sample PDF policy. Press **`Alt+Shift+A`**, speak: *"Health checkup reimbursement ka kya rule hai?"* Audio streams back with green `Page 2` citation pill. Press **`Escape`** to interrupt. | *"Second, Talk-to-Document. Press Alt+Shift+D to load any PDF or policy, then hold Alt+Shift+A to ask voice questions. BolSamajh answers in natural Hinglish with exact page citations, streaming audio sentence-by-sentence. Hit Escape or speak over to interrupt anytime."* | **Grounded RAG • Exact Page Citations • Silero Barge-In** |
| **0:55 – 1:12** *(17s)* | **Screen:** Highlight rough text in an email draft. Hold **`Alt+Shift+C`**, speak: *"Make this email formal and concise."* Selection updates in-place to polished text. | *"Third, in-place voice editing. Highlight text in an email or Slack, press Alt+Shift+C, and speak your intent. The LLM rewrites your text directly in-place without switching windows or compromising your clipboard."* | **Alt+Shift+C • In-Place Voice Editing Anywhere** |
| **1:12 – 1:30** *(18s)* | **Screen:** Switch to Web UI (`http://localhost:8000`) showing audio waveforms and chat history. Show `.env` setting `BOLSAMAJH_TTS_ENGINE=piper` for air-gapped mode. | *"Finally, a strictly 100% offline air-gapped mode with local Piper TTS and Ollama, plus an OpenAI-compatible audio gateway for Bolna voice agents. BolSamajh: Bolo. Samjho. 100% free and open-source. Thank you!"* | **100% Offline Air-Gapped Mode • Bolna Voice Gateway** |

---

## Step-by-Step Recording Checklist (Manual Task)

1. **Hardware & Microphone:** Use a USB or headset mic; select default recording device in Windows sound settings.
2. **Screen Capture:** Open OBS Studio (1920x1080 @ 60fps), capture main display, enable cursor capture.
3. **App Windows Pre-arranged:**
   - Left half: Notepad with empty document.
   - Right half: Sample multi-page PDF (`scratch/doc_qa_e2e/sample_policy.pdf`).
   - Browser tab ready on `http://localhost:8000`.
4. **Hotkey Practice:**
   - `Alt+Shift+Space` (Dictate)
   - `Alt+Shift+D` (Load Doc)
   - `Alt+Shift+A` (Ask Doc)
   - `Alt+Shift+C` (Voice Edit Selection)
   - `Escape` (Interrupt Audio)
5. **Upload:** Upload video to YouTube or Loom as Unlisted (90 seconds max), copy link into submission form.
