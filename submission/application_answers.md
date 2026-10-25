# Bolna x Symphony Voice AI Buildathon — Official Submission Application

> **Project Name:** BolSamajh  
> **Tagline:** *"Bolo. Samjho."* — Speak to write and act in any app, talk to any document in your language.  
> **Builder:** Manav (Solo Builder, Ahmedabad, India)  
> **License:** MIT Open Source License  
> **GitHub Repository:** https://github.com/P1Manav/BolSamajh  
> **Codebase:** Fully functional desktop client + Web-Call mode + 100-sentence benchmark suite  

---

### 1. One-Line Pitch
**BolSamajh** is an open-source, zero-cloud-spend Voice AI companion for the desktop that enables 500 million Hinglish and Indian-language speakers to dictate in any application, converse with complex documents via grounded voice RAG, and execute in-place voice editing.

---

### 2. The Problem
- **The Hinglish Void:** 500M+ Indians communicate daily via a fluid mix of Hindi grammar and English terminology (code-switching). Existing speech engines (Whisper defaults, standard phone dictation) force an unnatural binary choice: either pure English or formal Devanagari Hindi. They struggle on hybrid sentences like *"PR merge karke branch rebase kar lo"* or *"₹4,500 invoice amount pe 18% GST add karo"*.
- **Walled-Garden Dictation:** Existing commercial AI dictation tools (e.g. Wispr Flow) are closed-source, require monthly subscriptions, send user audio to remote servers, and lack tuning for Indian accents and everyday code-switching.
- **Document Literacy & Voice Accessibility:** Millions of professionals, students, and citizens deal with complex PDFs, legal notices, and technical documentation without a conversational voice interface that can explain nuance in their own spoken idiom with verifiable page citations.

---

### 3. The Solution & Features
BolSamajh solves these problems natively through a lightweight desktop architecture with three primary capabilities:

1. **Push-to-Talk Dictation in Any App (`Ctrl+Shift+Space`):**
   - Press and hold global hotkey in Notepad, VS Code, Slack, WhatsApp Web, Word, or Chrome.
   - Speaks naturally in Hinglish, Hindi, Gujarati, or English.
   - Text is transcribed via local `faster-whisper` on GPU with smart filler removal (strips *umm*, *uhh*, *hmm*, *ahh*) and currency/date formatting.
   - Inserts text directly at cursor via clipboard simulation with **~580–800 ms per-sentence inference on RTX 3060 Ti** (RTF 0.180x).

2. **Talk-to-Document Intelligence with Citations (`Ctrl+Shift+D` to load, `Ctrl+Shift+A` to ask):**
   - Ingests PDFs, Word (.docx), text/markdown files, or live web URLs.
   - Indexes text chunks using a local multilingual sentence-transformer embedding model (`paraphrase-multilingual-MiniLM-L12-v2`) and FAISS vector index (measured ~14 ms retrieval latency).
   - User asks voice questions in their own tongue; the pipeline retrieves grounded context, generates concise answers, and speaks aloud via neural TTS.
   - Enforces strict groundedness: answers cite exact page/section numbers and decline out-of-context hallucinations.
   - Halts TTS playback immediately on `Escape`.

3. **In-App Voice Commands on Selection (`Ctrl+Shift+C`):**
   - Select text in any window, speak instructions like *"make this email formal"*, *"translate to Hindi"*, *"summarize in 2 bullet points"*.
   - The LLM transforms the selected text directly in-place without context-switching.

4. **Browser Web-Call Mode:**
   - Standalone FastAPI web application featuring an interactive dark-themed UI, live audio waveform visualizer, document drag-and-drop, and spoken response player.

---

### 4. Technical Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                      BolSamajh Architecture                     │
│                                                                 │
│  [Global Hotkeys: pynput] ──► [Overlay HUD: Tkinter floating]   │
│                                                                 │
│  [Speech-to-Text]        [RAG Engine]        [LLM & TTS]       │
│  • faster-whisper         • PyMuPDF / docx    • Ollama (local   │
│    (medium, INT8/FP16)    • Multilingual        gemma3:4b)      │
│  • CTranslate2 CUDA         Sentence-         • Google AI       │
│    (RTX 3060 Ti)            Transformers        (Gemini 2.5     │
│                           • FAISS vector db     Flash Free)     │
│                                               • Edge-TTS        │
│                                                 (SwaraNeural)   │
│                                                                 │
│  [In-App Text Insertion] ──► Direct into active window (Ctrl+V) │
│  [Web-Call Interface]    ──► FastAPI + Vanilla HTML5/CSS3/JS    │
└─────────────────────────────────────────────────────────────────┘
```

- **Runtime:** Python 3.12, Windows 11 x64, NVIDIA CUDA 12 (tested on RTX 3060 Ti 8GB VRAM).
- **Hard Zero-Spend Rule:** 100% free and open-source models; zero subscription fees, zero cloud credit card requirements.

---

### 5. Measured Performance & Benchmark
All metrics are verified from direct script execution (`benchmark_data/hardware_measurements.json` and `benchmark_data/benchmark_summary.json`):

#### Empirical Hardware Profile (RTX 3060 Ti):
- **STT Engine:** `faster-whisper medium` with INT8-FP16 mixed precision
- **STT Latency (Single sentence, warm):** **686.2 ms mean** (min: 584.0 ms, p95: 806.9 ms)
- **Real-Time Factor (RTF):** **0.180x** (processes audio ~5.5× faster than real-time)
- **VRAM Footprint:** **1,076 MB model allocation** (peak total system used: 2,437 MB, leaving >5.7 GB free for local LLM)
- **Multilingual RAG Retrieval Latency:** **13.98 ms mean** across 20 indexed chunks via FAISS
- **Time To First Audio (TTFA):** **644.6 ms** via streaming Edge-TTS

#### 100-Sentence Hinglish Synthetic Stress Benchmark:
- **Overall Mean WER:** 40.79% | **Mean CER:** 20.83% | **Batch Latency:** 1,288 ms
- **Everyday Conversation (30 clips):** 26.95% WER
- **Mid-sentence Code-switching (15 clips):** 29.10% WER
- **Indian Names & Brands (15 clips):** 36.92% WER

---

### 6. Commercialization & Startup Roadmap
- **Market Size:** India has 700M+ smartphone and PC users, with Hinglish being the de facto corporate and personal communication medium.
- **B2C Model:** Freemium desktop productivity tool (free local tier for power users; optional cloud sync for mobile).
- **B2B Enterprise Model:** On-premise air-gapped deployment for Indian healthcare (bilingual doctor dictation), legal/judiciary (talk to case law PDFs), and banking operations where data cannot leave India.
