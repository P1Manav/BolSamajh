# Bolna x Symphony Voice AI Buildathon — Official Application Form Answers

> **Submission Deadline:** 31 October 2026, 11:59 PM IST  
> **Repository:** https://github.com/P1Manav/BolSamajh  
> **Builder:** Manav (Solo, Ahmedabad, India)  
> **License:** MIT License (100% Open Source, Zero Cloud Spend)

---

### 1. Project Name
**BolSamajh**

### 2. Tagline / One-Line Pitch
**Bolo. Samjho.** — Open-source, local-first Voice AI for 500 million Hinglish speakers: dictation anywhere, talk-to-document with verifiable citations, and in-place voice editing.

### 3. Since when have you been working on this project?
**2026-10-25** (verified by initial repository commit `82d10c1`).

### 4. What is the problem you are solving?
Over 500 million people across India speak fluid Hindi-English code-switching ("Hinglish"), yet mainstream speech recognition engines force an unnatural binary choice between pure English and formal Devanagari Hindi. Commercial dictation apps (e.g. Wispr Flow) are closed-source, require costly monthly subscriptions, send voice data to foreign cloud servers, and fail on colloquial code-switching like *"PR merge karke branch rebase kar lo"* or *"invoice pe 18% GST add karo"*. Furthermore, non-technical users struggle to digest complex PDFs, insurance policies, and legal notices without a conversational voice assistant that explains nuance in their own tongue with verifiable page citations.

### 5. How does your solution solve it?
BolSamajh provides a lightweight, local-first voice AI overlay with zero cloud spend:
1. **Push-to-Talk Dictation in Any App (`Alt+Shift+Space`):** Real-time Hinglish dictation inserted at the cursor across Notepad, VS Code, Slack, Word, and Chrome with automatic currency (₹) and disfluency normalization.
2. **Talk-to-Document Intelligence (`Alt+Shift+D` to load, `Alt+Shift+A` to ask):** Long-context multilingual RAG (`intfloat/multilingual-e5-base`, 512-token context) that answers voice questions with exact page/section citations and sentence-streaming speech.
3. **In-Place Voice Editing (`Alt+Shift+C`):** Highlights text in any application, speaks instructions (*"make this email formal"*, *"translate to Hindi"*), and transforms text in-place.
4. **Bolna Agent Voice Gateway:** Exposes OpenAI-compatible `/v1/audio/transcriptions` and `/v1/audio/speech` endpoints so any Bolna voice agent can use BolSamajh as a local speech provider.
5. **Interactive Web-Call Mode:** Full-featured browser UI with live audio waveform visualizers, document drag-and-drop, and SSE streaming.

### 6. What technologies and models did you use?
- **Speech-to-Text (STT):** `faster-whisper` (`medium`, `large-v3-turbo-ct2`, and `whisper-hinglish-swift-ct2` CTranslate2 INT8/FP16 models) running on NVIDIA CUDA 12 via pip wheels with automatic CPU int8 fallback.
- **Phonetics & Script Normalization:** `aksharamukha` offline library for script transformation (Natural, Roman Latin with diacritic stripping, Devanagari) and canonical phonemic benchmark scoring.
- **Document RAG:** `intfloat/multilingual-e5-base` (512 token context, passage/query prefixes), PyMuPDF with local OCR fallback for scanned PDFs, and FAISS vector index.
- **LLM Layer:** Local Ollama (`gemma3:4b`, `num_ctx: 8192`) with automatic fallback to Google AI Studio (`gemini-1.5-flash` free tier via `x-goog-api-key` header).
- **Text-to-Speech (TTS):** Microsoft Edge-TTS (`hi-IN-SwaraNeural`, `en-IN-NeerjaNeural`, `gu-IN-DhwaniNeural`) and 100% offline local `piper-tts` (`hi_IN-pratham-medium` ONNX).
- **Voice Interruption:** Silero VAD (`silero-vad`) for hands-free voice barge-in; `Escape` key for immediate recording cancellation and audio stop.
- **Desktop & Web:** Python 3.12, Tkinter floating HUD with `WS_EX_NOACTIVATE` window style, `pystray`, `pynput`, `keyboard`, and FastAPI backend.

### 7. What are your key measured metrics? (All backed by repository JSON files)
All metrics originate from reproducible scripts in `benchmark_data/`:
- **Inference Latency (`hardware_measurements.json`):** **686.2 ms mean** on a 3.82s sentence on NVIDIA RTX 3060 Ti (**0.180x Real-Time Factor**, running 5.5× faster than real-time).
- **VRAM Overhead (`hardware_measurements.json`):** **1,076 MB** model allocation delta (fits comfortably in 8 GB VRAM alongside local Gemma 3 4B).
- **Document Retrieval (`retrieval_benchmark.json`):** **93.33% Hit@1, 100.0% Hit@3, 100.0% Hit@5** on Google XQuAD Hindi validation split with **21.38 ms mean latency** and empirical refusal threshold of 0.76.
- **Time-To-First-Audio (`hardware_measurements.json`):** **644.6 ms** via streaming neural speech.
- **Real Speech Benchmark (`benchmark_results.json`):**
  - Read Hindi (FLEURS `hi_in`): **24.15% WER** (large-v3-turbo), **27.39% WER** (medium).
  - Spontaneous Hinglish Code-Switching (HiACC adult test eval): **52.84% WER** (medium).
- **Synthetic Stress Benchmark (100 sentences with noise & 8kHz phone filter):**
  - Rapid Code-switching: **12.48% WER** (`whisper-hinglish-swift`), **23.52% WER** (`large-v3-turbo`).
  - Overall Synthetic Stress Set: **33.43% WER** (`whisper-hinglish-swift`).

### 8. How does BolSamajh align with the Bolna ecosystem?
BolSamajh directly supports Bolna's vision of autonomous voice agents:
- Exposes standard OpenAI-compatible endpoints:
  - `POST /v1/audio/transcriptions` (Hinglish STT)
  - `POST /v1/audio/speech` (Natural Indian TTS)
- A Bolna agent deployed locally or via cloud tunnel can configure `base_url="http://localhost:8000/v1"` to gain free, unlimited, low-latency Hinglish transcription and Indian-language voice synthesis without per-minute cloud billing.
- Complete documentation and tested curl examples are provided in [`docs/bolna_integration.md`](docs/bolna_integration.md).

### 9. What is your commercialization / startup roadmap?
- **Target Market:** 500M+ Indian bilingual knowledge workers, healthcare professionals, legal practitioners, and educators.
- **B2C Model:** Free open-source local desktop client for developers and power users; premium cloud-synced mobile companion app.
- **B2B Enterprise Model:** Air-gapped, on-premise voice infrastructure for Indian hospitals (bilingual clinical note dictation) and legal firms (grounded voice Q&A over Indian Supreme Court case law and acts) where data privacy regulations prohibit public cloud data transfer.

### 10. Links & Verification
- **GitHub Repository:** https://github.com/P1Manav/BolSamajh
- **CI Status:** GitHub Actions CPU workflow passes 23/23 tests (`.github/workflows/ci.yml`)
- **Dataset Licenses:** Detailed in [`benchmark_data/DATASETS.md`](benchmark_data/DATASETS.md)
- **Architectural Decision Records:** 17 ADRs documented in [`DECISIONS.md`](DECISIONS.md)
