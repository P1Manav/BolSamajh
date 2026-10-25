# BolSamajh — Progress Tracker

> Updated after each milestone. Carry this file across sessions.

## Current Status: 🎯 Tier 1 Complete — Benchmark v2 on Real Speech & Canonical Scoring

---

### ✅ Completed Milestones

#### Tier 1 — Benchmark v2 on Real Speech & Canonical Normalization
- [x] **Zero Manual Recording & Verified Permissive Licenses:**
  - Evaluated on real public datasets: Google FLEURS (`hi_in`, `gu_in`) and HiACC Adult Test Eval (`Trelis/hiacc-adult-test-eval`) under **CC-BY-4.0** license.
  - Documented sources, access terms, and license verification in `benchmark_data/DATASETS.md`.
  - Extracted 60 real audio clips (20 HiACC code-switched Hinglish, 20 FLEURS read Hindi, 20 FLEURS read Gujarati) via `scripts/download_eval_datasets.py`.
- [x] **Automated Synthetic Stress Test Generation (`bolsamajh/benchmark/record_tool.py`):**
  - Explicitly labelled as Synthetic Stress Set.
  - Multi-voice neural rotation (`hi-IN-SwaraNeural`, `hi-IN-MadhurNeural`, `gu-IN-DhwaniNeural`, `en-IN-NeerjaNeural`).
  - Open-source DSP degradations implemented via `scipy.signal` and `numpy`:
    * Speed variations (0.90x to 1.15x)
    * Additive Gaussian noise (20–22 dB SNR)
    * 8 kHz telephony phone-codec simulation (300 Hz – 3,400 Hz 4th order Butterworth bandpass filter).
- [x] **Canonical Phonemic Normalization (`bolsamajh/benchmark/normalization.py`):**
  - Unicode NFC normalization.
  - Indic digit replacement (`०-९`, `૦-૯` -> ASCII `0-9`).
  - Danda (`।`, `॥`) and punctuation stripping.
  - Chandrabindu (`\u0901`, `\u0a81`) -> Anusvara (`\u0902`, `\u0a82`).
  - Nukta stripping (`\u093c`, `\u0abc`) and zero-width character removal (ZWJ/ZWNJ).
  - Transliteration to canonical Latin representation via `Aksharamukha` to prevent penalizing English loanword spelling variants.
  - Dropped the unprincipled "best of two references" trick.
- [x] **Multi-Engine Empirical Comparison on NVIDIA RTX 3060 Ti:**
  - **Real Speech:**
    * `medium`: 52.79% Mean WER, 23.67% CER, 5,307 ms latency (HiACC CS: 52.84%, FLEURS HI: 27.39%, FLEURS GU: 78.13%)
    * `large-v3-turbo`: 71.89% Mean WER, 52.89% CER, 610.3 ms latency, 0.076x RTF (FLEURS HI: 24.15%, FLEURS GU: 70.01%)
    * `whisper-hinglish-swift`: 103.88% Mean WER, 173.1 ms latency, 0.020x RTF
  - **Synthetic Stress Set:**
    * `whisper-hinglish-swift`: **33.43% Overall WER**, **18.77% CER**, **108.5 ms Latency**, **0.019x RTF** (Code-switching: **12.48% WER**, Everyday: **23.79% WER**)
    * `large-v3-turbo`: 58.99% Overall WER, 26.43% CER, 486.2 ms Latency, 0.089x RTF (Code-switching: 23.52% WER)
    * `medium`: 66.12% Overall WER, 32.97% CER, 800.4 ms Latency, 0.142x RTF (Code-switching: 37.06% WER)
- [x] **Automated README Table Generation (`scripts/generate_readme_tables.py`):**
  - Generated README tables directly from `benchmark_data/benchmark_results.json` and `hardware_measurements.json`.

#### Tier 0 — Truth, Reproducibility & Performance Profile
- [x] Conducted exhaustive audit across `README.md`, `PROGRESS.md`, `DECISIONS.md`, and `submission/*.md`.
- [x] Removed or corrected all unsupported claims:
  - Latency claims updated to measured numbers (`hardware_measurements.json`).
  - Removed unmeasured `base` row from README benchmark table.
  - Removed claims of Piper offline fallback (Edge-TTS documented as online neural TTS).
  - Clarified AI4Bharat status (standalone prototype adapter, not yet integrated into primary pipeline).
  - Corrected `Escape` key description (stops TTS audio playback).
  - Replaced "flawless" code-switching claims with empirical observations.
  - Replaced privacy blanket claims with an explicit data boundary matrix (Edge-TTS sends text to Microsoft; Gemini sends prompts to Google; STT and vector search remain strictly local).
  - Fixed `bolna.dev` -> `bolna.ai`.
- [x] Added `scripts/measure_hardware.py`:
  - Peak GPU VRAM measured via `nvidia-smi` (1,076 MB model delta, 2,437 MB peak total on RTX 3060 Ti).
  - STT inference latency measured with warm-up exclusion (mean 686.2 ms, min 584.0 ms, p95 806.9 ms on a 3.82s test clip, RTF 0.180x).
  - Document retrieval latency measured across 20 chunks (mean 13.98 ms).
  - Time-To-First-Audio (TTFA) measured on streaming Edge-TTS (644.6 ms).
  - Results saved to `benchmark_data/hardware_measurements.json`.
- [x] Added explicit Limitations and Privacy sections to `README.md`.

#### Milestone 0 — Scaffolding & Environment Setup
- [x] Initialized Git repository, `.gitignore`, MIT `LICENSE`.
- [x] Created clean virtual environment with CUDA runtime library linking (`bolsamajh/utils/cuda_setup.py`).
- [x] Established modular architecture: `stt`, `llm`, `tts`, `documents`, `pipeline`, `overlay`, `utils`, `benchmark`, `web`.
- [x] Built system tray indicator (`pystray`) and global configuration manager (`bolsamajh/config.py`).

#### Milestone 1 — Push-to-Talk Dictation in Any App
- [x] Implemented `MicRecorder` with `sounddevice` for low-latency 16kHz PCM capture.
- [x] Created `FasterWhisperSTT` adapter using CTranslate2 with INT8-FP16 mixed precision on RTX 3060 Ti GPU.
- [x] Built `text_cleanup.py`: filler stripping, currency and date formatting, script control framework.
- [x] Built universal clipboard paste simulation (`utils/clipboard.py`) for in-place text typing into any application.
- [x] Built lightweight floating Tkinter HUD with states (`listening`, `processing`, `done`, `error`).
- [x] Wired global hotkey `Ctrl+Shift+Space` for push-to-talk.

#### Milestone 2 — Document Ingestion & Multilingual RAG
- [x] Multi-format document parser (`documents/loader.py`): PDF (`PyMuPDF`), Word (`python-docx`), Webpages (`trafilatura`), plain text & Markdown.
- [x] Sentence-aware chunker (`documents/chunker.py`) with metadata tracking (page numbers, section titles, source path).
- [x] Local multilingual vector retrieval (`documents/retriever.py`): `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` + FAISS inner product index.
- [x] Benchmarked retrieval: cosine similarity search completes in ~14 ms.

#### Milestone 3 — Talk-to-Document Voice Q&A with Citations
- [x] Abstract LLM adapter interface (`llm/base.py`) with streaming support.
- [x] Local Ollama adapter (`llm/ollama_adapter.py`) with `gemma3:4b`.
- [x] Google AI Studio free tier adapter (`llm/google_ai.py`).
- [x] Edge-TTS adapter (`tts/edge_tts_adapter.py`) supporting Hindi (`hi-IN-SwaraNeural`), English, and Gujarati neural voices with zero API spend.
- [x] Grounded prompt engineering: enforces page citations, strict context-only answers, and professional disclaimer.
- [x] Audio playback and voice interruption via `Escape` key (`tts.stop()`).
- [x] Hotkeys wired: `Ctrl+Shift+D` (load document dialog), `Ctrl+Shift+A` (voice ask).

#### Milestone 4 — 100-Sentence Hinglish Benchmark Suite
- [x] Curated 100 realistic Hinglish sentences (`benchmark/sentences.py`) across 5 domains.
- [x] Built interactive CLI recording tool (`benchmark/record_tool.py`) with metadata checkpointing.
- [x] Built synthetic dataset generator for reproducible baselines using neural TTS.
- [x] Built automated benchmark evaluator (`benchmark/evaluate.py`) calculating WER, CER, RTF, latency, and per-category breakdowns.

#### Milestone 5 — In-App Voice Commands on Selection
- [x] Implemented `VoiceCommandsPipeline` (`pipeline/commands.py`): user highlights text in any desktop app, presses `Ctrl+Shift+C`, speaks instruction.
- [x] LLM transforms selected text in-place (rewrite, formalize, shorten, bullet points, translate).
- [x] Output replaces selection cleanly via simulated clipboard operations.

#### Milestone 6 — Browser Web-Call Mode
- [x] Built FastAPI web server (`bolsamajh/web/server.py`) exposing REST endpoints for status, document ingestion, text & voice Q&A, and in-app commands.
- [x] Designed responsive, dark-mode web application (`bolsamajh/web/static/`):
  - Glassmorphism design system (`style.css`)
  - Live HTML5 Canvas audio waveform visualizer (`app.js`)
  - Browser microphone streaming via MediaRecorder API
  - Interactive source citation cards and audio response playback

---

### 📊 Empirically Verified Metrics (`benchmark_data/hardware_measurements.json`)

| Metric | Measured Value | Target | Status |
| :--- | :--- | :--- | :--- |
| **STT Latency (single sentence, warm)** | **686.2 ms (min: 584.0 ms, p95: 806.9 ms)** | < 1000 ms | 🟢 Verified |
| **Synthetic Stress Set Mean Latency** | **1,288 ms (across 100 clips)** | < 2000 ms | 🟢 Verified |
| **Real-Time Factor (RTF)** | **0.180x (single) / 0.234x (batch)** | < 0.50x | 🟢 Verified |
| **GPU VRAM Model Allocation** | **1,076 MB (faster-whisper medium)** | < 4,000 MB | 🟢 Verified |
| **Peak Total VRAM Used** | **2,437 MB (System + Whisper)** | < 8,192 MB | 🟢 Verified |
| **Document Retrieval Latency** | **13.98 ms across 20 chunks** | < 50 ms | 🟢 Verified |
| **Time-To-First-Audio (TTFA)** | **644.6 ms (Edge-TTS)** | < 1500 ms | 🟢 Verified |
| **Cloud API Spend** | **$0.00 (Zero spend rule)** | $0.00 | 🟢 100% Free |
