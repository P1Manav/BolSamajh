CHECK buildathon rules on pre-existing work before submitting Q3.

# Bolna x Symphony Voice AI Buildathon — Official Application Form Answers

> **Submission Deadline:** 31 October 2026, 11:59 PM IST  
> **Repository:** https://github.com/P1Manav/BolSamajh  
> **Builder:** Manav (Solo, Ahmedabad, India)  
> **License:** MIT License (100% Open Source; local STT/RAG; cloud TTS by default, offline TTS optional)

---

### 1. Project Name
**BolSamajh**

### 2. Tagline / One-Line Pitch
**Bolo. Samjho.** — Open-source voice AI companion (local STT/RAG; cloud TTS by default, offline TTS optional) for 500 million Hinglish speakers: dictation anywhere, talk-to-document with verifiable citations, and in-place voice editing.

### 3. Since when have you been working on this project?
this repository started on 2026-10-25; the first prototype overlay predates it.

### 4. What is the problem you are solving?
Over 500 million people across India speak fluid Hindi-English code-switching ("Hinglish"), yet mainstream speech recognition engines force an unnatural binary choice between pure English and formal Devanagari Hindi. Commercial dictation apps (e.g. Wispr Flow) are closed-source, require costly monthly subscriptions, send voice data to foreign cloud servers, and fail on colloquial code-switching like *"PR merge karke branch rebase kar lo"* or *"invoice pe 18% GST add karo"*. Furthermore, non-technical users struggle to digest complex PDFs, insurance policies, and legal notices without a conversational voice assistant that explains nuance in their own tongue with verifiable page citations.

### 5. How does your solution solve it?
BolSamajh provides a lightweight voice AI overlay (local STT/RAG; cloud TTS by default, offline TTS optional):
1. **Push-to-Talk Dictation in Any App (`Alt+Shift+Space`):** Real-time Hinglish dictation inserted at the cursor across Notepad, VS Code, Slack, Word, and Chrome with automatic currency (₹), percentages, phone numbers, and disfluency normalization.
2. **Talk-to-Document Intelligence (`Alt+Shift+D` to load, `Alt+Shift+A` to ask):** Long-context multilingual RAG (`intfloat/multilingual-e5-base`, 512-token context) that answers voice questions with exact page/section citations and sentence-streaming speech.
3. **In-Place Voice Editing (`Alt+Shift+C`):** Highlights text in any application, speaks instructions (*"make this email formal"*, *"translate to Hindi"*), and transforms text in-place.
4. **Bolna Agent Voice Gateway:** OpenAI-compatible voice gateway verified locally using Bolna's own package client code (`OPENAISynthesizer`) and Realtime WebSocket protocol (evidence: `docs/evidence/bolna_client_check.txt`). Exposes `/v1/audio/speech` (TTS endpoint proxying Edge-TTS and local offline Piper voice), `/v1/audio/transcriptions` (batch STT), and `/v1/realtime?intent=transcription` (minimal streaming transcription WebSocket). Not tested on Bolna cloud.
5. **Interactive Web-Call Mode:** Full-featured browser UI with live audio waveform visualizers, document drag-and-drop, and SSE streaming.

### 6. What technologies and models did you use?
- **Speech-to-Text (STT):** `faster-whisper` (`large-v3-turbo-ct2` by default, `medium`, and `whisper-hinglish-swift-ct2` [third-party CT2 conversion of Oriserve Swift, unverified]) running on NVIDIA CUDA 12 via pip wheels with automatic CPU int8 fallback (`MSpider3/whisper-hindi2hinglish-swift-ct2`).
- **Phonetics & Script Normalization:** `aksharamukha` offline library for script transformation (Natural, Roman Latin with diacritic stripping, Devanagari) and canonical script-normalized benchmark scoring.
- **Document RAG:** `intfloat/multilingual-e5-base` (512 token context, passage/query prefixes), PyMuPDF with local OCR fallback for scanned PDFs, and FAISS vector index.
- **LLM Layer:** Local Ollama (`gemma3:4b`, `num_ctx: 8192`) with automatic fallback to Google AI Studio (`gemini-3.5-flash`, unverified — run `python scripts/check_gemini.py` with your key, with automatic Flash-family fallback on 404 via `x-goog-api-key` header).
- **Text-to-Speech (TTS):** Microsoft Edge-TTS (unofficial cloud endpoint: `hi-IN-SwaraNeural`, `en-IN-NeerjaNeural`, `gu-IN-DhwaniNeural`; Roman Hinglish voice pending listening test) and 100% offline local `piper-tts` (`hi_IN-pratham-medium` ONNX). Text is synthesized as-is without destructive ISO transliteration.
- **Voice Interruption:** Silero VAD (`silero-vad`) for hands-free voice barge-in (exposed `is_active` state and warning logging; verified 10-minute automated test with 0 false triggers); `Escape` key for immediate recording cancellation and audio stop.
- **Desktop & Web:** Python 3.11 & 3.12, Tkinter floating HUD with `WS_EX_NOACTIVATE` window style, `pystray`, `pynput`, `keyboard`, and FastAPI backend.

### 7. What are your key measured metrics? (All backed by repository JSON files)
All metrics originate from reproducible scripts in `benchmark_data/`:
- **Inference Latency (`hardware_measurements.json`):** Measured on NVIDIA RTX 3060 Ti GPU (`cuda` `int8_float16`): **475.9 ms mean** on a 3.82s sentence (RTF 0.121x); real-speech latency across 300 clips is **575.5 ms** (RTF **0.061x**, p95: **1301.6 ms**) on `large-v3-turbo`.
- **VRAM Overhead (`hardware_measurements.json`):** **1192.0 MB** model allocation delta (fits comfortably in 8 GB VRAM alongside local Gemma 3 4B).
- **Document Retrieval (`retrieval_benchmark.json`):** **89.0% Hit@1, 98.0% Hit@3, 98.5% Hit@5** on Google XQuAD Hindi validation split with **22.31 ms mean latency** and calibrated refusal threshold of **0.785** (F1: 0.8685, Precision: 81.86%, Recall: 92.5%).
- **Time-To-First-Audio (`hardware_measurements.json`):** **732.7 ms** Edge-TTS first-packet latency; **1592.6 ms** true end-to-end Doc-QA TTFA (question audio release → STT → RAG → LLM first sentence → audio playback).
- **Real Speech Benchmark (`benchmark_results.json`):**
  - Read Hindi (FLEURS `hi_in`): **25.98% WER** on `large-v3-turbo`; **33.59% WER** on `medium`.
  - Spontaneous Hinglish Code-Switching (HiACC adult test eval): **38.52% WER** on `large-v3-turbo`; **50.73% WER** on `medium`.
  - Read Gujarati (FLEURS `gu_in`): **66.01% WER** on `large-v3-turbo`; **77.6% WER** on `medium`.
- **Synthetic Stress Benchmark (`benchmark_results.json`, 100 sentences with noise & 8kHz phone filter):**
  - Overall Synthetic Stress Set: **31.39% WER** on `whisper-hinglish-swift` at **93.6 ms latency** and **0.017x RTF**; **55.93% WER** on `large-v3-turbo`.

### 8. How does BolSamajh align with the Bolna ecosystem?
BolSamajh directly supports Bolna's vision of autonomous voice agents:
- Exposes standard OpenAI-compatible gateway endpoints:
  - `POST /v1/audio/speech`: TTS endpoint proxying Microsoft Edge-TTS voices and local offline Piper ONNX voice (`hi_IN-pratham-medium`), supporting mp3/wav response formats. Tested and verified directly with Bolna's `OPENAISynthesizer` package client (evidence: `docs/evidence/bolna_client_check.txt`).
  - `POST /v1/audio/transcriptions`: Batch Hinglish STT endpoint.
  - `WS /v1/realtime?intent=transcription`: Realtime WebSocket endpoint supporting Bolna transcriber message shapes (`session.update`, `input_audio_buffer.append`, `input_audio_buffer.commit`).
- Status: Tested locally using Bolna's package source code; live deployment on Bolna cloud requires an active Bolna cloud subscription and telephone telephony trunk (documented in [`docs/bolna_integration.md`](docs/bolna_integration.md)). Provider schema in agent config is unverified against Bolna cloud's current API schema.
- When exposed via a secure tunnel (e.g. `cloudflared` or `ngrok`), a Bolna agent can configure `base_url="https://<tunnel>/v1"` to use BolSamajh for transcription and voice synthesis without per-minute cloud billing.

### 9. What is your commercialization / startup roadmap?
- **Target Market:** 500M+ Indian bilingual knowledge workers, healthcare professionals, legal practitioners, and educators.
- **B2C Model:** Free open-source local desktop client for developers and power users; premium cloud-synced mobile companion app.
- **B2B Enterprise Model:** Air-gapped, on-premise voice infrastructure for Indian hospitals (bilingual clinical note dictation) and legal firms (grounded voice Q&A over Indian Supreme Court case law and acts) where data privacy regulations prohibit public cloud data transfer.

### 10. Links & Verification
- **GitHub Repository:** https://github.com/P1Manav/BolSamajh
- **CI Status:** GitHub Actions multi-OS CPU matrix workflow (Ubuntu + Windows on Python 3.11 and 3.12) running 116 non-slow tests all passing green.
- **Dataset Licenses:** Detailed in [`benchmark_data/DATASETS.md`](benchmark_data/DATASETS.md)
- **Architectural Decision Records:** 26 ADRs (D001–D026) documented in [`DECISIONS.md`](DECISIONS.md)
- **Final Submission Checklist:** [`submission/FINAL_CHECKLIST.md`](submission/FINAL_CHECKLIST.md)
