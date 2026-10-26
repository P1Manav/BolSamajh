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
**2026-10-25** (verified by initial repository commit `82d10c1`).

### 4. What is the problem you are solving?
Over 500 million people across India speak fluid Hindi-English code-switching ("Hinglish"), yet mainstream speech recognition engines force an unnatural binary choice between pure English and formal Devanagari Hindi. Commercial dictation apps (e.g. Wispr Flow) are closed-source, require costly monthly subscriptions, send voice data to foreign cloud servers, and fail on colloquial code-switching like *"PR merge karke branch rebase kar lo"* or *"invoice pe 18% GST add karo"*. Furthermore, non-technical users struggle to digest complex PDFs, insurance policies, and legal notices without a conversational voice assistant that explains nuance in their own tongue with verifiable page citations.

### 5. How does your solution solve it?
BolSamajh provides a lightweight voice AI overlay (local STT/RAG; cloud TTS by default, offline TTS optional):
1. **Push-to-Talk Dictation in Any App (`Alt+Shift+Space`):** Real-time Hinglish dictation inserted at the cursor across Notepad, VS Code, Slack, Word, and Chrome with automatic currency (₹) and disfluency normalization.
2. **Talk-to-Document Intelligence (`Alt+Shift+D` to load, `Alt+Shift+A` to ask):** Long-context multilingual RAG (`intfloat/multilingual-e5-base`, 512-token context) that answers voice questions with exact page/section citations and sentence-streaming speech.
3. **In-Place Voice Editing (`Alt+Shift+C`):** Highlights text in any application, speaks instructions (*"make this email formal"*, *"translate to Hindi"*), and transforms text in-place.
4. **Bolna Agent Voice Gateway:** OpenAI-compatible TTS gateway for Bolna (not yet tested against a live agent). Exposes `/v1/audio/speech` (TTS endpoint proxying Microsoft Edge-TTS voices Swara/Neerja/Dhwani, plus local offline Piper voice) and `/v1/audio/transcriptions` (batch STT endpoint; realtime STT is not implemented).
5. **Interactive Web-Call Mode:** Full-featured browser UI with live audio waveform visualizers, document drag-and-drop, and SSE streaming.

### 6. What technologies and models did you use?
- **Speech-to-Text (STT):** `faster-whisper` (`medium`, `large-v3-turbo-ct2`, and `whisper-hinglish-swift-ct2` [third-party CT2 conversion of Oriserve Swift, unverified]) running on NVIDIA CUDA 12 via pip wheels with automatic CPU int8 fallback.
- **Phonetics & Script Normalization:** `aksharamukha` offline library for script transformation (Natural, Roman Latin with diacritic stripping, Devanagari) and canonical script-normalized benchmark scoring.
- **Document RAG:** `intfloat/multilingual-e5-base` (512 token context, passage/query prefixes), PyMuPDF with local OCR fallback for scanned PDFs, and FAISS vector index.
- **LLM Layer:** Local Ollama (`gemma3:4b`, `num_ctx: 8192`) with automatic fallback to Google AI Studio (`gemini-3.5-flash`, verified live 2026-10-26, with automatic Flash-family fallback on 404 via `x-goog-api-key` header).
- **Text-to-Speech (TTS):** Microsoft Edge-TTS (unofficial cloud endpoint: `hi-IN-SwaraNeural`, `en-IN-NeerjaNeural`, `gu-IN-DhwaniNeural`) and 100% offline local `piper-tts` (`hi_IN-pratham-medium` ONNX). Edge-TTS neural voices natively pronounce Roman Hinglish without destructive ISO transliteration.
- **Voice Interruption:** Silero VAD (`silero-vad`) for hands-free voice barge-in (exposed `is_active` state and warning logging); `Escape` key for immediate recording cancellation and audio stop.
- **Desktop & Web:** Python 3.11 & 3.12, Tkinter floating HUD with `WS_EX_NOACTIVATE` window style, `pystray`, `pynput`, `keyboard`, and FastAPI backend.

### 7. What are your key measured metrics? (All backed by repository JSON files)
All metrics originate from reproducible scripts in `benchmark_data/`:
- **Inference Latency (`hardware_measurements.json`):** Measured on NVIDIA RTX 3060 Ti GPU (`cuda` `int8_float16`): **<!-- NUM:hw.stt_synth_latency_ms -->495.0<!-- /NUM --> ms mean** on a 3.82s sentence (RTF <!-- NUM:hw.stt_synth_rtf -->0.13<!-- /NUM -->x); real-speech latency across <!-- NUM:hw.stt_real_count -->300<!-- /NUM --> clips is **<!-- NUM:hw.stt_real_mean_latency_ms -->779.2<!-- /NUM --> ms** (RTF **<!-- NUM:hw.stt_real_rtf -->0.101<!-- /NUM -->x**, p95: **<!-- NUM:hw.stt_real_p95_latency_ms -->1492.6<!-- /NUM --> ms**) on `large-v3-turbo`.
- **VRAM Overhead (`hardware_measurements.json`):** **<!-- NUM:hw.vram_allocated_delta_mb -->1142.0<!-- /NUM --> MB** model allocation delta (fits comfortably in 8 GB VRAM alongside local Gemma 3 4B).
- **Document Retrieval (`retrieval_benchmark.json`):** **<!-- NUM:rag.hit_at_1 -->89.0%<!-- /NUM --> Hit@1, <!-- NUM:rag.hit_at_3 -->98.0%<!-- /NUM --> Hit@3, <!-- NUM:rag.hit_at_5 -->98.5%<!-- /NUM --> Hit@5** on Google XQuAD Hindi validation split with **<!-- NUM:rag.latency_ms -->22.31<!-- /NUM --> ms mean latency** and calibrated refusal threshold of **<!-- NUM:rag.refusal_threshold -->0.785<!-- /NUM -->** (F1: <!-- NUM:rag.f1 -->0.8685<!-- /NUM -->, Precision: <!-- NUM:rag.precision -->81.86%<!-- /NUM -->, Recall: <!-- NUM:rag.recall -->92.5%<!-- /NUM -->).
- **Time-To-First-Audio (`hardware_measurements.json`):** **<!-- NUM:hw.tts_first_packet_ms -->835.6<!-- /NUM --> ms** Edge-TTS first-packet latency; **<!-- NUM:hw.total_ttfa_ms -->1702.8<!-- /NUM --> ms** true end-to-end Doc-QA TTFA (question audio release → STT → RAG → LLM first sentence → audio playback).
- **Real Speech Benchmark (`benchmark_results.json`):**
  - Read Hindi (FLEURS `hi_in`): **<!-- NUM:stt.turbo.fleurs_hi_wer -->25.94%<!-- /NUM --> WER** on `large-v3-turbo`; **<!-- NUM:stt.medium.fleurs_hi_wer -->33.63%<!-- /NUM --> WER** on `medium`.
  - Spontaneous Hinglish Code-Switching (HiACC adult test eval): **<!-- NUM:stt.turbo.hiacc_wer -->38.52%<!-- /NUM --> WER** on `large-v3-turbo`; **<!-- NUM:stt.medium.hiacc_wer -->50.31%<!-- /NUM --> WER** on `medium`.
  - Read Gujarati (FLEURS `gu_in`): **<!-- NUM:stt.turbo.fleurs_gu_wer -->66.01%<!-- /NUM --> WER** on `large-v3-turbo`; **<!-- NUM:stt.medium.fleurs_gu_wer -->77.65%<!-- /NUM --> WER** on `medium`.
- **Synthetic Stress Benchmark (`benchmark_results.json`, 100 sentences with noise & 8kHz phone filter):**
  - Overall Synthetic Stress Set: **<!-- NUM:stt.swift.synth_wer -->31.02%<!-- /NUM --> WER** on `whisper-hinglish-swift` at **<!-- NUM:stt.swift.synth_latency_ms -->97.7<!-- /NUM --> ms latency** and **<!-- NUM:stt.swift.synth_rtf -->0.018<!-- /NUM -->x RTF**; **<!-- NUM:stt.turbo.synth_wer -->56.03%<!-- /NUM --> WER** on `large-v3-turbo`.

### 8. How does BolSamajh align with the Bolna ecosystem?
BolSamajh directly supports Bolna's vision of autonomous voice agents:
- Exposes standard OpenAI-compatible gateway endpoints:
  - `POST /v1/audio/speech`: TTS endpoint proxying Microsoft Edge-TTS (an unofficial cloud endpoint with Swara/Neerja/Dhwani voices) and local offline Piper ONNX voice (`hi_IN-pratham-medium`), supporting mp3/wav response formats and speech rate adjustment.
  - `POST /v1/audio/transcriptions`: Batch Hinglish STT endpoint; realtime WebSocket STT is not implemented.
- Status: Implemented and integration-tested against the OpenAI API specification; OpenAI-compatible TTS gateway for Bolna (not yet tested against a live agent; live testing instructions with a secure tunnel documented in [`docs/bolna_integration.md`](docs/bolna_integration.md)).
- When exposed via a secure tunnel (e.g. `cloudflared` or `ngrok`), a Bolna agent can configure `base_url="https://<tunnel>/v1"` to use BolSamajh for batch transcription and voice synthesis without per-minute cloud billing (a local server cannot be reached by Bolna cloud directly without a tunnel).

### 9. What is your commercialization / startup roadmap?
- **Target Market:** 500M+ Indian bilingual knowledge workers, healthcare professionals, legal practitioners, and educators.
- **B2C Model:** Free open-source local desktop client for developers and power users; premium cloud-synced mobile companion app.
- **B2B Enterprise Model:** Air-gapped, on-premise voice infrastructure for Indian hospitals (bilingual clinical note dictation) and legal firms (grounded voice Q&A over Indian Supreme Court case law and acts) where data privacy regulations prohibit public cloud data transfer.

### 10. Links & Verification
- **GitHub Repository:** https://github.com/P1Manav/BolSamajh
- **CI Status:** GitHub Actions multi-OS CPU matrix workflow (Ubuntu + Windows on Python 3.11 and 3.12) running 53 non-slow tests all passing green.
- **Dataset Licenses:** Detailed in [`benchmark_data/DATASETS.md`](benchmark_data/DATASETS.md)
- **Architectural Decision Records:** 17 ADRs documented in [`DECISIONS.md`](DECISIONS.md)
