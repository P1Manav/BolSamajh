# BolSamajh — Progress Tracker

> Updated after each milestone. Carry this file across sessions.

## Current Status: 🎯 Phase 14 Complete — Supervisor Architecture & Resilient Web-Call Core

---

### ✅ Completed Milestones

#### Phase 14 — Supervisor Architecture, Auto Port Fallback, /healthz & --selftest
- [x] **Supervisor Engine (`bolsamajh/web/supervisor.py`):** Built supervisor with:
  - Dynamic port fallback (`find_available_port` testing 8000..8025 with socket bind).
  - Single-instance detection (`check_existing_instance`): second double-clicks activate the existing running dashboard and exit 0 cleanly without port conflicts.
  - Runtime state tracking (`write_runtime_info` to `%LOCALAPPDATA%\BolSamajh\runtime.json`).
  - Rotating file logger (`setup_rotating_file_logger` to `%LOCALAPPDATA%\BolSamajh\logs\bolsamajh.log`, 5 MB, 3 backups) eliminating invisible errors in windowless mode.
  - Active `/healthz` HTTP probe with timeout coordination.
- [x] **Core Server Endpoints:** Added `/healthz` liveness/readiness probe and `/call` route to `bolsamajh/web/server.py`.
- [x] **Robust Startup & Error Dialog:** Updated `bolsamajh/main.py` to poll `/healthz` before launching the browser. On failure, presents a friendly message box with log file paths and diagnostics instead of an Edge connection refused error.
- [x] **Automated `--selftest` Flag:** Implemented `python -m bolsamajh --selftest` testing CUDA STT on sample Hinglish audio, SentenceTransformers multilingual embedding retriever, and core web server on an isolated port. Verified exiting code 0 in CI and local test harnesses.
- [x] **Removed Redundant Server Instructions:** Cleaned up duplicate `uvicorn` commands from `README.md`, `submission/FINAL_CHECKLIST.md`, and `docs/` so users never start competing servers.
- [x] **Unit & Integration Test Suite Expanded:** Added 10 tests across `tests/test_supervisor.py` and `tests/test_server.py`. All 139 non-slow tests passing green.

#### Phase 13 — Truth Pass, Competitor Scrub & Sourced Competitive Grounding
- [x] **Competitor Branding Scrubbed:** Removed all occurrences of competitor names ("Wispr Flow") from tray icon menu, web studio HTML, JavaScript, CSS, and docstrings.
- [x] **Personal Paths Sanitized:** Scrubbed user paths (`Maxpr`, `d:\Projects\BolSamajh`) from `docs/FINAL_REPORT.md`, `docs/MANUAL_VERIFICATION.md`, and `PROGRESS.md`.
- [x] **Fake Hero Image Removed:** Deleted AI-generated macOS mockup (`assets/bolsamajh_app_demo.jpg`) and removed reference from `README.md`.
- [x] **Ideation History Archived:** Moved `docs/ideation_transcript.md` (101 KB) into `docs/archive/` to keep root docs clean.
- [x] **Sourced Competitive Grounding (`docs/COMPETITIVE_NOTES.md`):** Formally analyzed Wispr Flow capabilities from official vendor pages (retrieved 2026-10-31), documenting verified free tier, 100+ languages, Hinglish support, script selection, Command Mode, SignPath Foundation OSS program, and genuine BolSamajh differentiators (built-in voice Doc Q&A with citations, local air-gap offline mode, open reproducible benchmarks, Bolna gateway).
- [x] **Application Answers Cleaned:** Deleted unverified claim regarding code-switching failure from `submission/application_answers.md` and updated problem statement with verified, sourced claims.

#### Phase 12 — Windows GUI Double-Click Crash Resolution & Welcoming Explainer Dashboard
- [x] **Windows GUI `NoneType.isatty` Crash Resolved:** Identified root cause of unhandled exception dialog on double-click: Windows `--noconsole` launches with `sys.stdout = None` and `sys.stderr = None`, causing `uvicorn.logging.DefaultFormatter` to crash on `sys.stdout.isatty()`. Implemented `_SafeNullStream` wrappers in `bolsamajh/__main__.py`, `bolsamajh/main.py`, and `bolsamajh/web/server.py`, and configured `uvicorn.Config` with `log_config=None`.
- [x] **Welcoming Explainer & Setup Dashboard Redesign:** Transformed main interface into an intuitive onboarding and explainer dashboard (`#view-dashboard`):
  - Welcome hero banner with clear product pitch and zero-cloud-spend privacy guarantee.
  - Prominent **"🚀 Activate Floating Overlay"** central call-to-action button with real-time status indicators.
  - 3 Core Pillar Interactive Cards (Voice IN push-to-talk with live mic tester, Voice OUT talk-to-docs with quick dropzone, Voice Actions with sample transformation sandbox).
  - Hardware & system diagnostics summary grid (STT, LLM, TTS, Privacy).
  - Visual keyboard shortcuts cheatsheet.
- [x] **Windows Installer Wizard (`Install-BolSamajh.bat`):** Created a 1-click Windows installer script that installs the application to `%LOCALAPPDATA%\Programs\BolSamajh`, configures Start Menu and Desktop shortcuts with custom multi-size icons, and starts the app.
- [x] **In-App Shortcut Creation Endpoint:** Added `POST /api/install-shortcuts` to create/refresh Windows shortcuts directly from the Web UI with one click.
- [x] **Recompiled Standalone Executable & Package:** Rebuilt `dist/BolSamajh/BolSamajh.exe` and `dist/BolSamajh-v1.1.0-windows-x64.zip` (451.5 MB), verified double-click execution with 0 errors, and uploaded to GitHub Release v1.1.0.

#### Phase 11 — Standalone Executable Runtime Robustness & Live Verification
- [x] **PyInstaller Frozen Path Resolution:** Updated `bolsamajh/web/server.py` (`_resolve_static_dir`), `bolsamajh/documents/retriever.py`, and `bolsamajh/tts/piper_adapter.py` to resolve static web assets, thresholds, and ONNX models from `sys._MEIPASS` and `_internal/` when running as a compiled binary.
- [x] **Active Socket Polling for Edge App Mode:** Eliminated `ERR_CONNECTION_REFUSED` race condition in `bolsamajh/main.py` by polling the server port via socket connection up to 6.0s before launching Microsoft Edge borderless application window.
- [x] **Persistent Glass Overlay HUD:** Hardened `bolsamajh/overlay/hud.py` so pinned state (`/api/overlay/toggle`) keeps a persistent pill (` 🎙️ BolSamajh  Ready`) on top of all windows instead of auto-withdrawing.
- [x] **Standalone Executable Compilation:** Recompiled `dist/BolSamajh/BolSamajh.exe` and packaged `dist/BolSamajh-v1.1.0-windows-x64.zip` (451.5 MB) containing PyTorch runtime, CT2 CUDA DLLs, PyAV, SentenceTransformers, and all web assets.
- [x] **Live Binary Empirical Verification:** Automated tests verified that running `dist/BolSamajh/BolSamajh.exe` starts Uvicorn, serves the Studio UI (`GET /`, HTTP 200, 24,983 bytes), serves PWA manifest, and handles HUD overlay controls (`/api/overlay`, `/api/overlay/toggle`).
- [x] **Direct Desktop Shortcut:** Updated `scripts/create_desktop_shortcut.py` and regenerated `%USERPROFILE%\Desktop\BolSamajh.lnk` pointing directly to `dist\BolSamajh\BolSamajh.exe`.
- [x] **GitHub Release Asset Clobber:** Uploaded updated 451.5 MB standalone archive to GitHub Release v1.1.0 (`https://github.com/P1Manav/BolSamajh/releases/tag/v1.1.0`).

#### Phase 10 — Standalone Application Release & CI Matrix Resolution (v1.1.0)
- [x] **CI Dependency Conflict Resolved:** Pinned pytest-asyncio==1.4.1 for clean pip resolution with pytest==9.1.1 across Ubuntu and Windows runners.
- [x] **Platform Test Isolation:** Hardened 	est_modifier_guard_releases_and_restores_only_held and 	est_google_ai_exponential_cooldown for headless Linux and Windows environments where GOOGLE_AI_API_KEY is not present.
- [x] **Direct Windows Desktop Launchers:** Created BolSamajh.vbs (silent windowless launcher) and BolSamajh.bat (batch runner) for zero-terminal startup.
- [x] **Windows Desktop Shortcut Creator:** Built scripts/create_desktop_shortcut.py and scripts/generate_icon.py to create a 1-click desktop icon with multi-size ICO/PNG assets.
- [x] **Standalone Executable Compiler:** Built scripts/build_executable.py using PyInstaller to package Python runtime, C++ DLLs, models, static web frontend, and assets into dist/BolSamajh/BolSamajh.exe and dist/BolSamajh-windows-x64.zip.
- [x] **Automated GitHub Release Pipeline:** Added .github/workflows/release.yml to automatically compile and release Windows executables upon tag push.
- [x] **System Tray Enhancements:** Added direct 'Open Web-Call Interface' browser launcher and 'Headphone Mode' toggle to the tray menu.
- [x] **RAG Warmup:** Added background preloading of intfloat/multilingual-e5-base alongside STT so the first document query is instantaneous.

---

### ✅ Completed Milestones

#### Phase 1–9 Final Master Execution & Buildathon Submission (v1.0.0-submission)
- [x] **Phase 1 — CI & Repo Health:** Test suites run on Python 3.11 and 3.12 cleanly; `scripts/generate_readme_tables.py --check` passing. Evidence: `docs/evidence/ci_health.txt`.
- [x] **Phase 2 — Latency Reconciliation:** Shared decode/timing harness in `bolsamajh/benchmark/timing.py` across both measurement scripts with identical warmup, clip lengths, and reporting.
- [x] **Phase 3 — Strict Grammar Number Normalizer:** Grammar-based parsing in `bolsamajh/benchmark/normalization.py`; whole-run valid number parsing; ambiguous words (`do`, `so`, etc.) guarded; normalizer on/off WER reported; dynamic date/CUDA stamps.
- [x] **Phase 4 — Fail-Soft Gemini Fallback:** Startup warning, 404 Flash discovery, 429 single-retry with backoff, `/api/status` fail-soft status; 100% pipeline stability with no key.
- [x] **Phase 5 — Host Automated Verifications:**
  - Automated desktop dictation in Notepad (WER 0.0000, modifier released check via `GetAsyncKeyState`, 100% clipboard restoration).
  - Voice editing (`Alt+Shift+C`) tested with real text selection replacement in-place.
  - Automated 10-minute barge-in continuous test (93 sentences, 0 false triggers in speaker and headphone modes, speech onset latency 231.5ms / 66.2ms).
  - 100% offline air-gapped mode verified with socket-level outbound blocker across all 7 pipeline components.
  - Piper local neural TTS verified with SHA-256 cryptographic check and live synthesis.
  - Document Q&A tested on real PDF, DOCX, and local web page (9/9 questions answered with exact citations).
- [x] **Phase 6 — Bolna Package Integration:** Verified using Bolna's own `OPENAISynthesizer` package client code against local server (Hindi 4.48s & English 4.02s playable audio via PyAV); batch STT verified; minimal Realtime WebSocket `/v1/realtime` verified. Evidence: `docs/evidence/bolna_client_check.txt`.
- [x] **Phase 7 — Code Quality Sweep:** Modifier restore after Ctrl+C/V; sentence splitter initials & quotes edge cases; cancel thread lifecycle deadlock resolved; device/compute_type consistency; clean `ruff` validation on pyflakes ruleset.
- [x] **Phase 8 — Submission Package:** Rewritten application answers and demo script; created `submission/FINAL_CHECKLIST.md`; fresh-clone smoke test passed in isolated temp dir; tagged `v1.0.0-submission`.
- [x] **Phase 9 — Final Execution Report:** Comprehensive final report in `docs/FINAL_REPORT.md` and pushed to remote master.
- [x] **Complete Test Suite:** 40/40 non-slow unit tests passing in automated CI (`pytest -v -m "not slow" tests/`), with full 41/41 unit tests passing locally and in dedicated workflow, covering sentence splitting, barge-in echo, interrupt generation ID, worker lifecycle, text cleanup, transliteration, DocumentRetriever, LLM fallback, clipboard sentinel logic, and web server endpoints with SSRF protection.
- [x] **GitHub Actions Workflow (`.github/workflows/ci.yml`):** Multi-OS (Ubuntu + Windows) and multi-version (Python 3.11, 3.12) CPU test runner.
- [x] **Pinned & Split Dependencies:** Clean separation into `requirements.txt` (CPU / platform independent) and `requirements-gpu.txt` (NVIDIA CUDA 12 runtime wheels).
- [x] **README Rewrite (`README.md`):** Step-by-step setup instructions for Ollama, GPU vs CPU execution, model download notes (~1.5 GB cached locally), and automated results tables.
- [x] **Restructured Submission Answers (`submission/application_answers.md`):** Mapped to actual Buildathon application form fields, first commit date `2026-10-25`, aligned with JSON metrics.
- [x] **Demo Script Polish (`submission/demo_script.md`):** Updated with conflict-free `Alt+Shift+...` hotkeys and streaming TTFA.

#### Tier 4 — Sponsor Alignment (Bolna Voice Gateway)
- [x] **OpenAI-Compatible STT & TTS Endpoints (`bolsamajh/web/server.py`):**
  - `POST /v1/audio/transcriptions` (Hinglish speech-to-text with auto-resampling).
  - `POST /v1/audio/speech` (TTS gateway proxying Edge-TTS Swara/Neerja/Dhwani, plus local offline Piper voice).
- [x] **Bolna Integration Guide (`docs/bolna_integration.md`):** Complete walkthrough showing how Bolna agents can configure `base_url="http://localhost:8000/v1"` (or a secure tunnel) to use BolSamajh as an OpenAI-compatible TTS gateway (not yet tested against a live agent).

#### Tier 3 — Desktop & Web Robustness
- [x] **Single-Threaded Tkinter Safety (`bolsamajh/overlay/hud.py`, `bolsamajh/main.py`):**
  - Eliminated secondary `tk.Tk()` root on background thread by routing document file dialogs directly through `OverlayHUD.prompt_open_file()`.
  - Added Windows `WS_EX_NOACTIVATE (0x08000000)` window style so floating HUD never steals focus from active applications.
  - Auto-hides error states after 3,000 ms.
  - Background model preloading thread displays "BolSamajh Ready ✓" only after STT and LLM models are loaded.
- [x] **Dynamic CUDA Discovery & CPU Fallback (`bolsamajh/utils/cuda_setup.py`):**
  - Removed all hardcoded ChatRTX paths.
  - Dynamically registers `site-packages/nvidia/*/bin` wheels (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`, `nvidia-cuda-nvrtc-cu12`) via `os.add_dll_directory` and `PATH`.
  - Added `auto_detect_device()`: automatically selects `cuda:int8_float16` if GPU is detected, falling back to `cpu:int8` with lightweight swift model on CPU machines.
- [x] **Hotkeys & Selection Conflict Hardening (`bolsamajh/config.py`, `bolsamajh/utils/clipboard.py`, `bolsamajh/pipeline/commands.py`):**
  - Migrated default hotkeys to low-conflict `Alt+Shift+...` bindings (`Alt+Shift+Space`, `Alt+Shift+D`, `Alt+Shift+A`, `Alt+Shift+C`) to avoid collisions with VS Code and Chrome. Made configurable via `.env`.
  - In voice command flow, microphone recording starts **immediately** without waiting for selection copy, eliminating opening syllable clipping. Selection is captured in parallel.
  - Implemented unique UUID clipboard sentinel so highlighting text that matches existing clipboard content is recognized as a valid selection.
  - Temporarily releases physical Shift modifier prior to sending Ctrl+C to prevent Chrome DevTools activation.
- [x] **Web Server Robustness (`bolsamajh/web/server.py`):**
  - Built PyAV `AudioResampler` converting arbitrary 48 kHz/44.1 kHz browser audio to 16 kHz mono PCM.
  - Offloaded STT, document chunking/indexing, and URL fetching via `asyncio.to_thread`.
  - Restricted CORS to localhost without credentials.
  - Added SSRF protection blocking loopback and private/internal IP address ranges on `/api/documents/url`.
  - Enforced 25 MB upload limit.
  - Preserved real document filename in `doc.title`.
  - Mapped language to Gujarati voice (`gu-IN-DhwaniNeural`).
  - Unified with desktop app's grounded QA system prompt.
  - Added Server-Sent Events (SSE) streaming endpoint (`/api/qa/stream`).
  - Added dynamic hardware status endpoint (`/api/status`) and removed hardcoded "RTX 3060 Ti" frontend label.
  - Automated cleanup of expired temporary audio cache files.

#### Tier 2 — Core Product Correctness & Robust Voice Pipelines
- [x] **Dictation Output & Hallucination Prevention (`bolsamajh/stt/faster_whisper_stt.py`):**
  - Default `language="auto"` enables organic code-switched Hindi-English transcription without forced Hindi phonetics.
  - Stripped hardcoded initial prompt (`Bolo. Samjho.`) that leaked into silent or background noise clips.
  - Added dual silence gating: audio duration gate (<0.4s) and RMS energy threshold (<0.003) to prevent silence hallucination.
  - Added regex post-filtering to reject repetitive hallucination loops (e.g. `[Applause]`, `Thank you for watching`, `Subtitles by...`).
- [x] **Accurate Script Control & Tray Integration (`bolsamajh/utils/text_cleanup.py`, `bolsamajh/overlay/tray.py`):**
  - Replaced naive character map with `aksharamukha` offline transliteration library.
  - Fully supports `natural` (mixed as transcribed), `roman` (clean Latin with diacritic stripping), and `devanagari` scripts.
  - Exposed live script selection in system tray menu.
- [x] **Text Cleanup & Currency Disfluency Hardening (`bolsamajh/utils/text_cleanup.py`):**
  - Fixed currency regex with strict word boundaries `\b` (`doctors 5` is untouched; `Rs 500` -> `₹500`).
  - Removed aggressive fillers that deleted real Hindi/English words (`like`, `so`, `sun`, `actually`, `matlab`, `accha`, `dekho`, `toh` preserved).
  - Isolated true disfluencies (`umm`, `uhh`, `hmm`, `अम्म`, `उहह`, `हम्म`).
  - Verified with 4 unit tests in `tests/test_cleanup.py`.
- [x] **Long-Context Multilingual RAG & Refusal Calibration (`bolsamajh/documents/`):**
  - Replaced 128-token MiniLM with `intfloat/multilingual-e5-base` (512 token context limit, `passage: ` and `query: ` prefixes).
  - Implemented cross-page paragraph chunking (`bolsamajh/documents/chunker.py`) with format-specific citations (`Page N` only for PDFs, `Section: X` / `Paragraph N` for Web/DOCX/TXT).
  - Evaluated on Google XQuAD Hindi validation split (`scripts/evaluate_retrieval_xquad.py`):
    * **Hit@1:** 93.33%
    * **Hit@3:** 100.0%
    * **Hit@5:** 100.0%
    * **Mean Latency:** 21.38 ms
    * **Relevant Mean Score:** 0.809 vs **Irrelevant Max Score:** 0.756.
  - Set empirical refusal threshold to **0.76** based on benchmark results.
- [x] **LLM Layer Robustness & Seamless Auto-Fallback (`bolsamajh/llm/`):**
  - Set `num_ctx: 8192` in `OllamaAdapter` options so long document prompts are never truncated.
  - Added `check_status()` to verify server connectivity and model pull status.
  - Created `FallbackLLMAdapter` (`bolsamajh/llm/fallback.py`) and `create_llm_adapter` factory.
  - Updated `GoogleAIAdapter`: default to active free-tier `gemini-3.5-flash` (unverified — run `python scripts/check_gemini.py` with your key), automatic 404 fallback to select available Flash-family models from live models endpoint, `x-goog-api-key` header authentication, top-level `systemInstruction`, and suppressed `httpx`/`httpcore` loggers to `WARNING`.
- [x] **Document Handling & Prompt Injection Hardening (`bolsamajh/documents/loader.py`, `bolsamajh/pipeline/doc_qa.py`):**
  - Added OCR fallback for scanned PDFs via PyMuPDF native OCR and `pytesseract` with clear logging for unreadable pages.
  - Wrapped retrieved context inside `<document_data>` XML tags with explicit instruction to treat content strictly as passive data.
  - Implemented 3-turn short conversational memory in `DocQAPipeline` to enable natural follow-ups (*"ruko, yeh dobara samjhao"*).
- [x] **Voice Latency, Offline TTS & Voice Barge-In (`bolsamajh/pipeline/doc_qa.py`, `bolsamajh/tts/`, `bolsamajh/utils/vad.py`):**
  - Implemented sentence-by-sentence streaming from LLM generator into TTS, reporting Time-To-First-Audio (TTFA).
  - Routes Roman Hinglish directly to neural voice (`en-IN-NeerjaNeural` or `hi-IN-SwaraNeural`) as-is without destructive ISO transliteration.
  - Implemented `PiperTTSAdapter` (`bolsamajh/tts/piper_adapter.py`) supporting 100% offline local TTS with verified MIT-licensed Piper Hindi voices (`hi_IN-pratham-medium`).
  - Added voice barge-in with Silero VAD (`BargeInMonitor` in `bolsamajh/utils/vad.py`) to stop TTS immediately when user speaks.
  - Wired `Escape` key to abort active microphone recording across all pipelines in addition to halting TTS.
- [x] **Unit Test Suite:**
  - 15/15 unit tests passing in `pytest tests/` (cleanup, llm, normalization, retriever).

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
- [x] **Canonical Script Normalization (`bolsamajh/benchmark/normalization.py`):**
  - Unicode NFC normalization.
  - Indic digit replacement (`०-९`, `૦-૯` -> ASCII `0-9`).
  - Danda (`।`, `॥`) and punctuation stripping.
  - Chandrabindu (`\u0901`, `\u0a81`) -> Anusvara (`\u0902`, `\u0a82`).
  - Nukta stripping (`\u093c`, `\u0abc`) and zero-width character removal (ZWJ/ZWNJ).
  - Transliteration to canonical Latin representation via `Aksharamukha` (script-normalized evaluation across Devanagari and Latin scripts).
  - Dropped the unprincipled "best of two references" trick.
- [x] **Multi-Engine Empirical Comparison on NVIDIA RTX 3060 Ti:**
  - **Real Speech:**
    * `medium`: <!-- NUM:stt.medium.real_mean_wer -->53.97%<!-- /NUM --> Mean WER, <!-- NUM:stt.medium.real_mean_cer -->20.47%<!-- /NUM --> CER, <!-- NUM:stt.medium.real_latency_ms -->1370.9<!-- /NUM --> ms latency on CUDA int8_float16 (HiACC CS: <!-- NUM:stt.medium.hiacc_wer -->50.73%<!-- /NUM -->, FLEURS HI: <!-- NUM:stt.medium.fleurs_hi_wer -->33.59%<!-- /NUM -->, FLEURS GU: <!-- NUM:stt.medium.fleurs_gu_wer -->77.6%<!-- /NUM -->)
    * `large-v3-turbo`: <!-- NUM:stt.turbo.real_mean_wer -->43.5%<!-- /NUM --> Mean WER, <!-- NUM:stt.turbo.real_mean_cer -->18.2%<!-- /NUM --> CER, <!-- NUM:stt.turbo.real_latency_ms -->573.0<!-- /NUM --> ms latency, <!-- NUM:stt.turbo.real_rtf -->0.079<!-- /NUM -->x RTF (FLEURS HI: <!-- NUM:stt.turbo.fleurs_hi_wer -->25.98%<!-- /NUM -->, FLEURS GU: <!-- NUM:stt.turbo.fleurs_gu_wer -->66.01%<!-- /NUM -->, HiACC CS: <!-- NUM:stt.turbo.hiacc_wer -->38.52%<!-- /NUM -->)
    * `whisper-hinglish-swift`: <!-- NUM:stt.swift.real_mean_wer -->52.7%<!-- /NUM --> Mean WER (Hinglish-only), <!-- NUM:stt.swift.real_latency_ms -->100.0<!-- /NUM --> ms latency, <!-- NUM:stt.swift.real_rtf -->0.026<!-- /NUM -->x RTF
  - **Synthetic Stress Set:**
    * `whisper-hinglish-swift`: **<!-- NUM:stt.swift.synth_wer -->31.39%<!-- /NUM --> Overall WER**, **<!-- NUM:stt.swift.synth_latency_ms -->93.6<!-- /NUM --> ms Latency**, **<!-- NUM:stt.swift.synth_rtf -->0.017<!-- /NUM -->x RTF**
    * `large-v3-turbo`: <!-- NUM:stt.turbo.synth_wer -->55.93%<!-- /NUM --> Overall WER, <!-- NUM:stt.turbo.synth_latency_ms -->310.7<!-- /NUM --> ms Latency, <!-- NUM:stt.turbo.synth_rtf -->0.058<!-- /NUM -->x RTF
    * `medium`: <!-- NUM:stt.medium.synth_wer -->61.01%<!-- /NUM --> Overall WER, <!-- NUM:stt.medium.synth_latency_ms -->630.9<!-- /NUM --> ms Latency, <!-- NUM:stt.medium.synth_rtf -->0.12<!-- /NUM -->x RTF
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

#### Milestone 10 — Standalone Application Release & Green CI Across All Runners
- [x] Standalone Direct Launchers:
  - `BolSamajh.vbs`: 100% silent windowless background desktop launcher (0 CMD flash).
  - `BolSamajh.bat`: Interactive batch runner with automated virtual environment detection and recovery.
  - Windows Desktop Shortcut (`BolSamajh.lnk`) created on user desktop with custom multi-resolution microphone icon (`assets/bolsamajh.ico`).
  - Standalone executable compiler (`scripts/build_executable.py`) producing `dist/BolSamajh/BolSamajh.exe` and `dist/BolSamajh-v1.1.0-windows-x64.zip` (zero Python installation required).
  - Automated release pipeline (`.github/workflows/release.yml`) for continuous Windows standalone packaging.
- [x] System Tray & Startup Enhancements:
  - "Open Web-Call Interface" one-click browser launch (`webbrowser.open("http://localhost:8000")`).
  - Dynamic "Headphone Mode" toggle directly in tray menu.
  - Live script mode selector (Roman / Devanagari / Natural Mix).
  - Non-blocking background preloading of multilingual embeddings (`intfloat/multilingual-e5-base`).
  - Graceful OS shutdown signal handlers (`signal.SIGINT`, `signal.SIGTERM`).
- [x] CI/CD Green Across All 4 Matrix Runners:
  - Resolved `pytest-asyncio` 1.4.1 compatibility with `pytest` 9.1.1 across all runners.
  - Fixed headless modifier guard OS mocking and Google AI cooldown test fixtures.
  - Verified 55/55 unit tests passing on Windows py3.11, Windows py3.12, Ubuntu py3.11, Ubuntu py3.12.
  - Ruff lint & format checks completely clean across all 89 files.

#### Milestone 11 — Wispr Flow Studio Interface, Built-in Background Web Server, and Android PWA Companion
- [x] **Built-in Background Web Server in `main.py`:**
  - Integrated Uvicorn runner in a background daemon thread upon app launch, permanently eliminating connection refused / "site cant be reached" errors on `http://127.0.0.1:8000`.
  - Added native borderless window launcher (`msedge.exe --app=http://127.0.0.1:8000`) for a true desktop application feel without Electron bloat.
  - Connected floating HUD pill click and tray icon double-click directly to toggle the Studio interface.
- [x] **Wispr Flow Studio Interface (`index.html`, `style.css`, `app.js`):**
  - Designed 5-tab glassmorphic dashboard: Dictation Studio, Doc Intelligence, Voice Actions, Android Companion, System & Hotkeys.
  - Big glowing hero mic button with concentric ripple animations and live audio waveform canvas.
  - Instant script switcher (Natural Mixed, Roman Hinglish, Devanagari) with automatic filler cleanup count and latency badge.
  - "Inject into Active Window" (`/api/inject`) and "Copy to Clipboard" one-click action buttons.
  - Real-time transcription history feed with per-item copy and inject controls.
  - Mid-answer audio interruption support for Talk-to-Document voice Q&A.
- [x] **Android Companion & PWA App:**
  - Added `manifest.json` and service worker `sw.js` for 1-click "Add to Home screen" Android installation.
  - Generated multi-resolution PWA icons (`icon-192.png`, `icon-512.png`).
  - Added dynamic LAN IP detection and offline pure-JS QR code generator for 1-second mobile camera pairing.
  - Allowed private LAN subnet binding (`192.168.x.x`, `10.x.x.x`) so Android companion phones can stream mic audio directly to the desktop backend over local Wi-Fi.
- [x] **Verification & Release:**
  - 134/134 unit and integration tests passing cleanly.
  - Standalone release package published with standalone binary asset `BolSamajh-v1.1.0-windows-x64.zip`.

#### Milestone 12 — Studio Overlay Launcher & Wispr Flow Uniqueness Verification
- [x] **Claude Ideation Analysis (`docs/ideation_transcript.md`):**
  - Extracted 47 conversation messages from user's Claude session.
  - Formulated and verified the 5 core differentiators separating BolSamajh from Wispr Flow: Voice IN (script control + Indian context formatting + vocal pause removal), Voice OUT (Talk-to-Document grounded Q&A with multi-page citations and refusal gating), In-App Commands (text transformation in active app), Overlay Launcher (web studio primary UI with pill overlay controller), and Android Companion (offline QR pairing & PWA).
- [x] **Studio App Interface as Primary Controller with Overlay Toggle:**
  - Added `@property state`, `@property is_pinned`, `show_pill()`, and `toggle_pin()` to `bolsamajh/overlay/hud.py`.
  - Exposed `/api/overlay`, `/api/overlay/toggle`, `/api/overlay/start`, and `/api/overlay/stop` in `bolsamajh/web/server.py`.
  - Added `#toggleOverlayBtn` in the web studio navigation header and hero banner callout card in `bolsamajh/web/static/index.html` and `style.css`.
  - Wired live polling and one-click toggle in `bolsamajh/web/static/app.js`.
- [x] **Empirical Uniqueness Verification Suite (`scripts/verify_uniqueness_and_functionality.py`):**
  - Validated all 5 differentiators against live model pipelines in 35.49s.
  - Voice IN: Filtered `umm/uhh`, preserved `matlab/actually`, formatted `₹500`, converted to Roman, Natural, and Devanagari scripts.
  - Voice OUT: Indexed multi-page document into `DocumentRetriever`, scored 0.841 with `Pages 1–2` citation on valid query, refused out-of-domain query with score 0.000 (< 0.785), and synthesized 46,512 bytes of natural speech via Edge-TTS.
  - In-App Voice Actions: Transformed informal Hinglish to executive text via Gemini 2.5 Flash fallback and injected into active window.
  - Studio Overlay Control: Verified HUD state reporting and pin toggle.
  - Android Companion: Verified PWA manifest and service worker delivery.
- [x] **100% Green CI & Linting:**
  - `ruff check .` and `ruff format --check .` 100% clean across 91 files.
  - Pytest full suite: 135/135 passed (100%).


---

### 📊 Empirically Verified Metrics (`benchmark_data/hardware_measurements.json`)

| Metric | Measured Value | Target | Status |
| :--- | :--- | :--- | :--- |
| **STT Latency (single sentence, warm)** | **<!-- NUM:hw.stt_synth_latency_ms -->475.9<!-- /NUM --> ms (large-v3-turbo)** | < 1000 ms | 🟢 Verified (GPU) |
| **STT Latency (Real Speech)** | **<!-- NUM:hw.stt_real_mean_latency_ms -->575.5<!-- /NUM --> ms (mean over <!-- NUM:hw.stt_real_count -->300<!-- /NUM --> clips, RTF <!-- NUM:hw.stt_real_rtf -->0.061<!-- /NUM -->x, p95: <!-- NUM:hw.stt_real_p95_latency_ms -->1301.6<!-- /NUM --> ms)** | < 2000 ms | 🟢 Verified (GPU) |
| **Real-Time Factor (RTF)** | **<!-- NUM:hw.stt_real_rtf -->0.061<!-- /NUM -->x (real speech)** | < 0.25x | 🟢 Verified |
| **GPU VRAM Model Allocation** | **<!-- NUM:hw.vram_allocated_delta_mb -->1192.0<!-- /NUM --> MB (faster-whisper large-v3-turbo)** | < 2,048 MB | 🟢 Verified |
| **Peak Total VRAM Used** | **<!-- NUM:hw.vram_peak_used_mb -->2627.0<!-- /NUM --> MB (System + Whisper)** | < 8,192 MB | 🟢 Verified |
| **Document Retrieval Latency** | **<!-- NUM:hw.retrieval_latency_ms -->48.23<!-- /NUM --> ms across 20 chunks (E5 Base)** | < 50 ms | 🟢 Verified |
| **Edge-TTS First-Packet Latency** | **<!-- NUM:hw.tts_first_packet_ms -->732.7<!-- /NUM --> ms (Edge-TTS)** | < 1,000 ms | 🟢 Verified |
| **Doc-QA True End-to-End TTFA** | **<!-- NUM:hw.total_ttfa_ms -->1592.6<!-- /NUM --> ms (Question end → Audio play)** | < 2000 ms | 🟢 Verified |
| **Cloud API Spend** | **$0.00 (Zero spend rule)** | $0.00 | 🟢 100% Free |
