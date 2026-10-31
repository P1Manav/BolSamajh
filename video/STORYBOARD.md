# BolSamajh Product Video — Storyboard

> **Duration:** 88.0 seconds = 2640 frames @ 30 fps (Hard cap: 90s / 2700 frames)  
> **Resolution:** 1920 × 1080 Landscape, 30 fps  
> **Visual Identity:** Cinematic Dark Theme (`#0a0d14`), Indigo Hero (`#6366f1`), Emerald Verified (`#10b981`), JetBrains Mono HUD  

---

## Timeline & Scene Beat Breakdown

```
|---- Beat 1: Hook ----|-- Beat 2: Problem --|-- Beat 3: Solution --|-- Beat 4: Architecture --|
0s                    5s                    15s                    24s                        33s
[0 - 150f]            [150 - 450f]          [450 - 720f]           [720 - 990f]

|------------------- Beat 5: Live Product (Dictate -> Doc QA -> Offline) -------------------|
33s                                                                                          63s
[990 - 1890f]  (Dictate: 990-1230f | Doc QA: 1230-1650f | Offline: 1650-1890f)

|-- Beat 6: Different --|-- Beat 7: Tech & Numbers --|-- Beat 8: Close --|
63s                     72s                          83s                 88s
[1890 - 2160f]          [2160 - 2490f]               [2490 - 2640f]
```

---

### Beat 1: The Hook (0.0s – 5.0s / Frames 0 – 150)
- **Visual:** Deep matte black background (`#07080a`). Dynamic typography rises with staggered spring:
  `"We speak Hinglish."`
  `"Software doesn't."`
- **Animation:** Staggered word reveal with subtle chromatic aura. Frame 75: High-speed flash transition cuts to the official BolSamajh logomark with glowing cyan-indigo accent + tagline:
  **BolSamajh** — *"Bolo. Samjho."*
- **Persistent HUD Enters:** Top-left brand mark + chip `[01 // HOOK]`, top-right `#BolnaBuildathon`, bottom timeline progress bar.
- **Voiceover:** *"We speak Hinglish. Software doesn't."* (Hold stillness 15 frames).

---

### Beat 2: The Problem (5.0s – 15.0s / Frames 150 – 450)
- **Visual:** Smooth transition into light/high-contrast editorial view (`#f8fafc`). A dense 12-page legal insurance policy PDF (`sample_policy.pdf`) floats with subtle perspective tilt.
- **HUD Chip:** `[02 // THE PROBLEM]`
- **Motion:** 3 punchy problem statements slide in with subtle red warnings:
  1. *"500 million Indians think and speak in code-switched Hinglish."*
  2. *"Crucial health policies and notices arrive in impenetrable English."*
  3. *"Traditional voice tools force a choice: pure English or robotic formal Hindi."*
- **Camera:** Slow Ken Burns drift (scale 1.0 -> 1.06) over the dense legalese text.
- **Voiceover:** *"Over 500 million people talk like this every day. But when important policies arrive, they are trapped in dense English legalese, and voice tools force you into pure English or formal Hindi."*

---

### Beat 3: The Solution (15.0s – 24.0s / Frames 450 – 720)
- **Visual:** Dark theme re-emerges with deep ambient radial glow (`#6366f1`). The BolSamajh Studio application window reveals with a smooth spring scale (0.94 -> 1.0) and macOS-style window chrome.
- **HUD Chip:** `[03 // THE SOLUTION]`
- **Motion:** Headline reveals: *"One unified companion for voice in, out, and action."*  
  Three interactive feature pills scale into view staggered by 4 frames:
  - Pill 1: `[ 🎤 Speak to write ]` (Dictate in any app)
  - Pill 2: `[ 📄 Talk to any document ]` (Grounded RAG with page citations)
  - Pill 3: `[ ⚡ Speak to edit ]` (In-place clipboard transforms)
- **Voiceover:** *"Meet BolSamajh. One open-source voice AI companion that lets you dictate anywhere, talk to any document, and edit text with your voice."*

---

### Beat 4: How It Works — Architecture (24.0s – 33.0s / Frames 720 – 990)
- **Visual:** Interactive animated node graph showing data packets flowing seamlessly:
  `Mic Hotkey` ➔ `faster-whisper (STT)` ➔ `multilingual-e5 + FAISS (RAG)` ➔ `Ollama Gemma 3 (LLM)` ➔ `Piper / Edge-TTS (TTS)`
- **HUD Chip:** `[04 // HOW IT WORKS]`
- **Motion:** An emerald illuminated boundary line draws itself around the STT, RAG, and LLM nodes with badge: `🟢 RUNS LOCALLY ON YOUR DEVICE (Zero External API Fees)`.
- **Packet Animation:** Glowing pulses travel along the paths into the active desktop application.
- **Voiceover:** *"Hotkeys trigger local faster-whisper STT, multilingual-e5 embeddings, and local Ollama reasoning. Your voice audio never leaves your workstation."*

---

### Beat 5: Live Product in Action (33.0s – 63.0s / Frames 990 – 1890)
**HUD Chip:** `[05 // IN ACTION]`

#### Beat 5a: Dictate Anywhere (33.0s – 41.0s / Frames 990 – 1230)
- **Visual:** Real Notepad window. BolSamajh floating HUD pill displays `Alt+Shift+Space` active waveform.
- **Audio:** Real spoken Hinglish: *"Invoice pe 18 percent GST add karke total pandrah hazar kar do."*
- **Typing Animation:** Types into Notepad: `Invoice pe 18% GST add karke total ₹15,000 kar do.`
- **Callout Chips:** `✓ Filler words removed` • `✓ ₹15,000 currency formatted` • `✓ 18% GST normalized`.
- **Script Toggle:** Tray switch toggles to Devanagari: `मीटिंग पोस्टपोन हो गई`.
- **Voiceover:** *"Hold Alt+Shift+Space in any app. It removes fillers, formats rupees and GST automatically, with instant script switching."*

#### Beat 5b: Talk to a PDF with Citations & Interruption (41.0s – 55.0s / Frames 1230 – 1650)
- **Visual:** `sample_policy.pdf` open in BolSamajh Studio. User asks in Hinglish:  
  *"Kya ICU charges cover hote hain?"*
- **Answer Streaming:** Audio streams sentence-by-sentence. A clickable green citation pill **`[Page 1]`** appears and highlights Section 1.2 on the PDF page.
- **Barge-In Demonstration:** While voice speaks, user speaks: *"Ruko!"* — Silero VAD detects speech in **66 ms**, waveform cuts cleanly, audio stops instantly.
- **Gujarati Voice Demo:** Question: *"Maternity benefit ketlu male chhe?"* Spoken Gujarati audio plays with **`[Page 2]`** citation.
- **Refusal Gating:** Question: *"Space travel cover chhe?"* System displays calibrated refusal: *"Yeh document mein nahi hai"* (Threshold: 0.785).
- **Voiceover:** *"Load any policy and ask in Hinglish or Gujarati. Answers stream with verifiable page citations. Interrupt hands-free with voice barge-in, and trust calibrated out-of-document refusal."*

#### Beat 5c: 100% Air-Gapped Offline Mode (55.0s – 63.0s / Frames 1650 – 1890)
- **Visual:** Network disconnected / airplane mode badge triggers. BolSamajh Studio status switches to:  
  `🟢 100% AIR-GAPPED OFFLINE MODE`.
- **Verification Checklist:**
  - `[✓] faster-whisper local CT2`
  - `[✓] Ollama gemma3:4b (localhost:11434)`
  - `[✓] Piper ONNX TTS`
  - `[✓] FAISS local vector search`
- **Voiceover:** *"Disconnect the internet completely. BolSamajh runs 100% air-gapped on your GPU or CPU with Piper TTS and local Ollama."*

---

### Beat 6: Different by Design (63.0s – 72.0s / Frames 1890 – 2160)
- **Visual:** High-contrast side-by-side comparison matrix with Wispr Flow (sourced 2026-10-31 from `wisprflow.ai`).
- **HUD Chip:** `[06 // DIFFERENT BY DESIGN]`
- **Table Rows:**
  1. **License & Cost:** Closed-source ($12–$15/mo) vs **100% Open Source (MIT) / $0.00**
  2. **Offline Mode:** Cloud-dependent vs **100% Offline Air-Gapped**
  3. **Document Intelligence:** None vs **Built-in Voice RAG with Page Citations**
  4. **Voice Barge-In:** N/A vs **Silero VAD Live Interruption (66 ms)**
- **Honest Engineering Reality Footnote:**  
  *"Where Wispr Flow is stronger: 100+ production languages, mature cross-platform sync, zero local GPU footprint."*
- **Voiceover:** *"Unlike closed cloud tools costing $15 a month, BolSamajh is open source, air-gapped, and reads your documents. We respect what others do well—Wispr has 100+ languages—but BolSamajh is built for privacy and Indic depth."*

---

### Beat 7: The Voice-AI Tech & The Numbers (72.0s – 83.0s / Frames 2160 – 2490)
- **Visual:** Real benchmark card and code adapter snippet.
- **HUD Chip:** `[07 // THE TECH & NUMBERS]`
- **Real Verified Metrics Display:**
  - `38.52% WER` on HiACC Hinglish (large-v3-turbo) vs `50.73%` (medium)
  - `510 ms` real speech median latency (0.061x RTF on RTX 3060 Ti)
  - `98.0% Hit@3` on Google XQuAD Hindi document retrieval
  - `1592 ms` true end-to-end question-to-speech TTFA
- **Honest Limitation Callout:**  
  `Gujarati ASR error rate: 66.01% WER on FLEURS (Whisper multilingual boundary)`
- **Code Block:** Live Bolna gateway `/v1/audio/speech` and `/v1/audio/transcriptions` adapter interface.
- **Voiceover:** *"Backed by 1,000 evaluated benchmark clips on public CC-BY datasets. Sub-second latency, 98% retrieval accuracy, and drop-in gateway compatibility for Bolna voice agents."*

---

### Beat 8: Close & Call to Action (83.0s – 88.0s / Frames 2490 – 2640)
- **Visual:** Launch card with Windows Setup installer badge, portable ZIP, Android companion APK, and GitHub repository.
- **HUD Chip:** `[08 // GET STARTED]`
- **Hero Title:** **BolSamajh** — *"Bolo. Samjho."*
- **Subline:** `github.com/P1Manav/BolSamajh` • Built for the Bolna × Symphony Voice AI Buildathon.
- **Last Frame Hold:** 2.0s stillness (frames 2580–2640).
- **Voiceover:** *"Download the Windows installer or clone the code on GitHub. BolSamajh. Bolo. Samjho."*

