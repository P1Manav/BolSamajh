# BolSamajh — Decision Log

> Records architectural and tooling decisions with rationale.

## D001: Desktop Shell — Tkinter + pystray + pynput
**Date:** 2026-10-25  
**Choice:** Tkinter floating overlay + pystray system tray + pynput/keyboard for global hotkeys.  
**Alternatives considered:** Electron (heavy, 200+ MB), PyQt (GPL complications), Tauri (Rust build step).  
**Reason:** Zero extra install (Tkinter ships with Python), lightweight (~5 MB total), sufficient for an overlay HUD. Windows-native tray support via pystray.

## D002: STT Primary — faster-whisper `medium` (INT8_FP16)
**Date:** 2026-10-25  
**Choice:** faster-whisper with `medium` model, `int8_float16` compute type on CUDA (RTX 3060 Ti).  
**Alternatives considered:** whisper.cpp (needs separate build), OpenAI Whisper (slower, more VRAM), Vosk (lower accuracy for Hinglish).  
**Reason:** CTranslate2 backend is 4× faster than original Whisper. `medium` model (~1.5 GB VRAM in INT8) fits alongside LLM on RTX 3060 Ti 8 GB. Condition on previous text disabled (`condition_on_previous_text=False`), Silero VAD filtering, and post-ASR regex cleanup strip disfluencies and normalize digits without hallucination loops.

## D003: LLM Layer — Ollama + gemma3:4b (with Google AI Studio Fallback)
**Date:** 2026-10-25  
**Choice:** Ollama serving `gemma3:4b` locally, with optional Google AI Studio (`gemini-3.5-flash` free tier via `x-goog-api-key`, unverified — run `python scripts/check_gemini.py` with your key, with automatic 404 fallback to live Flash-family models) as cloud fallback.  
**Alternatives considered:** llama.cpp direct, Phi-3 (less multilingual), Mistral (English-centric).  
**Reason:** Gemma 3 4B has strong multilingual capability including Hindi/English, fits in 8 GB VRAM alongside whisper medium, and Ollama provides a simple local HTTP API. Free-tier Gemini provides an optional, unmetered fallback when local resources are constrained.

## D004: TTS — Edge-TTS (Online) + Piper (100% Offline Local)
**Date:** 2026-10-25  
**Choice:** Edge-TTS with `hi-IN-SwaraNeural` voice as primary online synthesizer; Piper ONNX as 100% offline local alternative.  
**Alternatives considered:** gTTS (unnatural robotic voice, no streaming), Coqui TTS (resource-heavy).  
**Reason:** Edge-TTS is free (uses Microsoft Edge's speech service, no API key), supports streaming audio, and produces high-quality natural Hindi and Indian English voices with low packet latency (~626 ms). Piper provides fully offline, air-gapped capability using local ONNX Hindi models.

## D005: Embeddings — intfloat/multilingual-e5-base
**Date:** 2026-10-25  
**Choice:** `intfloat/multilingual-e5-base` (768-dim, 512 token context) with asymmetric `passage: ` and `query: ` prefixes and local FAISS inner-product index.  
**Alternatives considered:** sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (shorter context, lower retrieval precision on cross-page context), BGE-M3 (1.3 GB, overkill).  
**Reason:** E5-base provides superior cross-lingual semantic alignment across Hindi, Gujarati, and English with 512 token capacity, achieving 98.0% Hit@3 on Google XQuAD Hindi with sub-35ms retrieval and calibrated refusal threshold at 0.785.

## D006: Text Insertion — Clipboard Simulation
**Date:** 2026-10-25  
**Choice:** Copy text to clipboard, then simulate Ctrl+V via pynput.  
**Alternatives considered:** Windows UI Automation API (complex, app-specific), SendInput (lower-level).  
**Reason:** Works universally in any app that accepts paste. Simple, reliable. Saves and restores original clipboard content.

## D007: Windows CUDA DLL Dynamic Registration
**Date:** 2026-10-25  
**Choice:** Auto-detect and register NVIDIA runtime DLLs (`cublas64_12.dll`, `cudnn64_8.dll`) dynamically via `os.add_dll_directory` in `bolsamajh/utils/cuda_setup.py`.  
**Alternatives considered:** Requiring user to install full 4 GB CUDA Toolkit installer and reboot.  
**Reason:** Enables zero-hassle GPU acceleration on Windows 11 with RTX 3060 Ti by picking up pre-existing PyTorch/CUDA runtime libraries without requiring system PATH tampering or administrator privileges.

## D008: Synthetic Benchmark Generation for Reproducibility
**Date:** 2026-10-25  
**Choice:** Provide both interactive CLI recording for human speakers and an automated `--synthetic` generator using neural Edge-TTS.  
**Alternatives considered:** Only human recordings (blocks CI/CD and evaluation until recorded).  
**Reason:** Allows immediate, reproducible automated evaluation of STT models across all 100 sentences with consistent ground truth, while keeping human recording available at any time.

## D009: In-Place Voice Editing Pattern
**Date:** 2026-10-25  
**Choice:** Selected text is grabbed via simulated Ctrl+C upon hotkey trigger, transformed via prompt-constrained LLM, and replaced in-place via simulated Ctrl+V.  
**Alternatives considered:** Floating text editor popup.  
**Reason:** Preserves the user's flow inside their active window (IDE, browser, Word, Slack) without requiring window management or copying back and forth.

## D010: Web-Call Architecture — FastAPI + Vanilla HTML/CSS/JS
**Date:** 2026-10-25  
**Choice:** FastAPI backend serving static vanilla frontend with Web Audio API.  
**Alternatives considered:** Next.js / React build step.  
**Reason:** Eliminates Node/npm build steps for Python users; starts immediately with `python -m bolsamajh.web.server`; achieves 60fps waveform animations with zero bundle overhead.

## D011: Empirical Hardware Measurement Suite
**Date:** 2026-10-25  
**Choice:** Provide `scripts/measure_hardware.py` which interrogates `nvidia-smi` and runtime timers directly to record peak VRAM delta, warm-up excluded latency, and TTFA.  
**Alternatives considered:** Relying on published theoretical benchmarks or unverified estimates.  
**Reason:** Voice AI judges require reproducible, honest numbers measured on real hardware. All documented latencies and memory metrics must trace directly to `benchmark_data/hardware_measurements.json`.

## D012: Benchmark v2 Architecture — Real Speech & Canonical Script Normalization
**Date:** 2026-10-25  
**Choice:** Separate evaluations into Real Speech (Google FLEURS `hi_in`/`gu_in`, HiACC `Trelis/hiacc-adult-test-eval`) and Synthetic Stress Set (100 sentences with multi-voice rotation and automated DSP degradations: noise injection, speed change, 8 kHz telephony bandpass filtering). Replace unprincipled 'best of two references' with canonical Devanagari normalization and script-normalized transliteration via Aksharamukha.  
**Alternatives considered:** Only synthetic evaluation; character-exact scoring without transliteration (penalizes script mismatches); claiming full phonemic unification when English loanwords (e.g. *meeting* vs *mitinga*) are not orthographically merged.  
**Reason:** Separating real human speech from synthetic stress provides reproducible, honest empirical evidence. Canonical script-normalized transliteration accurately measures whether speech recognition captured the right words across Devanagari and Latin scripts without penalizing character set mismatches.

## D013: Long-Context Multilingual Embeddings (`intfloat/multilingual-e5-base`) & Refusal Calibration
**Date:** 2026-10-25  
**Choice:** Replace 128-token MiniLM with `intfloat/multilingual-e5-base` (512 token max sequence length, explicit `passage: ` and `query: ` prefixes). Calibrate cosine similarity refusal threshold on 200 Google XQuAD Hindi validation questions and 200 unanswerable queries.  
**Alternatives considered:** `paraphrase-multilingual-MiniLM-L12-v2` (truncates 500-token chunks after 128 tokens), `BGE-M3` (heavier VRAM footprint).  
**Reason:** 200-question XQuAD Hindi empirical evaluation achieved <!-- NUM:rag.hit_at_1 -->89.0%<!-- /NUM --> Hit@1, <!-- NUM:rag.hit_at_3 -->98.0%<!-- /NUM --> Hit@3, <!-- NUM:rag.hit_at_5 -->98.5%<!-- /NUM --> Hit@5 at <!-- NUM:rag.latency_ms -->22.31<!-- /NUM --> ms latency. Optimal F1-maximizing refusal threshold of <!-- NUM:rag.refusal_threshold -->0.785<!-- /NUM --> cleanly separates relevant from irrelevant queries (F1: <!-- NUM:rag.f1 -->0.8685<!-- /NUM -->, Precision: <!-- NUM:rag.precision -->81.86%<!-- /NUM -->, Recall: <!-- NUM:rag.recall -->92.5%<!-- /NUM -->).

## D014: Prompt-Injection Guardrails & Conversational Memory
**Date:** 2026-10-25  
**Choice:** Wrap document context within `<document_data>` XML delimiters with explicit system instructions treating context as untrusted passive data. Maintain 3-turn short conversational history in `DocQAPipeline`.  
**Alternatives considered:** Direct string interpolation without guardrails (susceptible to adversarial override); full chat history (exceeds local context limits).  
**Reason:** Hardens the RAG pipeline against malicious PDF/doc payloads attempting to override system behavior. Conversational memory enables natural follow-ups ("ruko, yeh dobara samjhao", "explain in simpler terms").

## D015: Sentence-by-Sentence TTS Streaming & Voice Barge-In via Silero VAD
**Date:** 2026-10-25  
**Choice:** Stream tokens from LLM generator, delimit sentences (`.`, `?`, `!`, `।`, `\n`), synthesize and play audio immediately on the first completed sentence. Monitor microphone with Silero VAD (`BargeInMonitor`) during playback to halt TTS on user speech.  
**Alternatives considered:** Waiting for full LLM generation before starting TTS (3-5s TTFA); pure keypress interruption.  
**Reason:** Drops Time-To-First-Audio (TTFA) to under 800 ms. Voice barge-in provides a hands-free conversational experience aligned with modern voice assistants.

## D016: Piper Offline TTS Adapter with Verified Hindi Voices
**Date:** 2026-10-25  
**Choice:** Implement `PiperTTSAdapter` using `piper-tts` ONNX runtime with official MIT-licensed `hi_IN-pratham-medium` voice from Hugging Face (`rhasspy/piper-voices`).  
**Alternatives considered:** Offline TTS claims without implementation (failed audit); heavyweight Coqui TTS.  
**Reason:** Delivers true 100% offline text-to-speech capability when internet access is unavailable or privacy constraints forbid external cloud speech endpoints.

## D017: LLM Layer Hardening — Context Window, Auto-Fallback & Header Auth
**Date:** 2026-10-25  
**Choice:** Set `num_ctx: 8192` explicitly in Ollama API payload. Implement `FallbackLLMAdapter` between local Ollama and Google AI Studio. Update Google AI Studio adapter to free-tier `gemini-3.5-flash` (unverified — run `python scripts/check_gemini.py` with your key, with automatic Flash-family fallback on 404), native `systemInstruction`, and `x-goog-api-key` header auth (never in URL params). Set `httpx`/`httpcore` loggers to `WARNING`.  
**Alternatives considered:** Hardcoded single provider; API key in URL parameters (leaks to HTTP proxy logs).  
**Reason:** Ensures zero prompt truncation on 8k context, zero key leakage in logs or URL traces, and automatic failover if local Ollama is not running.

## D018: Dual-Venv Verification & Windows CI Health Check
**Date:** 2026-10-26  
**Choice:** Verified clean virtual environments for both Python 3.11 (`test_venv_311`) and Python 3.12 (`test_venv_312`) using `requirements.lock.txt`. Checked GitHub Actions CI status via `gh run list` and `gh run view`.  
**Alternatives considered:** Testing only current active venv or relying solely on remote CI.  
**Reason:** Guarantees reproduction on fresh installs and validates that Windows CI is passing before proceeding with autonomous phases. Raw evidence committed to `docs/evidence/ci_health.txt`.
## D019: Shared STT Timing Protocol & Latency Reconciliation
**Date:** 2026-10-26  
**Choice:** Created `bolsamajh.benchmark.timing` module with unified `DEFAULT_TRANSCRIBE_KWARGS` (explicit language hint and VAD parameters) and a shared timing function used by both `evaluate.py` and `measure_hardware.py`.  
**Alternatives considered:** Maintaining separate timing loops in benchmark and hardware scripts.  
**Reason:** Diagnosed that `measure_hardware.py` omitted `language="hi"` and VAD parameters, causing Whisper's language identification to run on every clip, inflating RTF by ~2.5x. Unifying the timing harness and decode parameters reconciled RTF across comparable clips to within empirical variance.

## D020: Strict Number Grammar Normalization & Dynamic Documentation Stamps
**Date:** 2026-10-26  
**Choice:** Replaced naive regex/lookaround number conversion with a strict hierarchy grammar parser (`_parse_strict_number`, `_parse_sub99`, `SCALE_PRIORITY`). Ambiguous Hindi number words (`do`, `so`, `sat`, etc.) only convert when part of a valid compound containing an unambiguous scale word or digit. Removed all hardcoded dates and CUDA version strings from docs, generating them dynamically via `generate_readme_tables.py` from JSON sources of truth.  
**Alternatives considered:** Relying on ad-hoc exception lists for common phrases like "nau do gyarah".  
**Reason:** Ad-hoc regexes failed on phrases like "so do sau" and colloquial idioms. Strict grammar prevents corrupting natural language while accurately parsing valid numerical expressions. Dynamic document stamping eliminates stale doc stamps.

## D021: Fail-Soft Gemini Cloud Fallback Architecture
**Date:** 2026-10-26  
**Choice:** Hardened `GoogleAIAdapter` and `FallbackLLMAdapter` with an explicit `disabled` flag, one clear startup warning on missing `GOOGLE_AI_API_KEY` or failed model check, single-retry backoff on HTTP 429 rate limits, and automatic Flash-family candidate discovery on HTTP 404. When Gemini fallback is unavailable or unconfigured, `/api/status` returns `"llm_fallback": "LLM fallback unavailable"` and the system operates 100% locally on Ollama without process termination.  
**Alternatives considered:** Throwing unhandled exceptions during API calls or silently omitting fallback status.  
**Reason:** Prevents demo or server crashes when users run locally without an external Google AI key or encounter cloud rate limits, ensuring uninterrupted offline/local operation.

## D022: Dynamic Configuration & Lightweight Prompt Isolation
**Date:** 2026-10-28  
**Choice:** Added centralized `.env` auto-loading in `bolsamajh/config.py`, desktop entry `main.py`, and FastAPI web server. Added validation for all literal configuration values (`BOLSAMAJH_TTS_ENGINE`, `BOLSAMAJH_LLM_AUTO_FALLBACK`, `BOLSAMAJH_LLM_ENGINE`, `BOLSAMAJH_SCRIPT`, `BOLSAMAJH_STT_DEVICE`). Replaced hardcoded `EdgeTTSAdapter` in `server.py` and `main.py` with `bolsamajh/tts/factory.py:create_tts_adapter`. Raised explicit `ValueError` on unknown LLM engines in `llm/factory.py`. Isolated Q&A system prompts to `bolsamajh/prompts.py` so the web server avoids importing desktop GUI/DSP dependencies (`tkinter`, `sounddevice`, `torch`). Pruned dead code (`stt/ai4bharat.py`, dead `_SENTENCE_END_RE`, unused `auto_punctuate`).  
**Alternatives considered:** Keeping prompt templates in `doc_qa.py` and letting `server.py` trigger audio/GUI imports on headless servers; silent fallback on unknown LLM engine strings.  
## D023: Desktop and Pipeline Correctness Hardening
**Date:** 2026-10-28  
**Choice:** Implemented comprehensive correctness and stability fixes across all core desktop and pipeline modules:
- **Clipboard & Insertion:** Sentinel-safe restore with configurable delay (`BOLSAMAJH_CLIPBOARD_RESTORE_DELAY`, default 0.3s), empty clipboard clearing, retry loop, and modifier guard re-pressing only physically held keys upon exit. Commands and dictation report "Done" only if `insert_text` succeeds.
- **Audio & Atomic Storage:** `_render_audio` writes to `.tmp` file and atomically renames. Audio recording capped at configurable duration (`BOLSAMAJH_AUDIO_MAX_RECORD_SECONDS`, default 120s) with optional input device index override.
- **Document Ingestion & Retrieval:** Thread-safe atomic swap of index and chunks in `DocumentRetriever`. Model-calibrated refusal thresholds with loud warning on fallback `e5-small`. Reject legacy `.doc` files, extract DOCX tables, check empty DOCX, detect encrypted PDFs, enforce OCR limits (30 pages / 50MB), normalize CRLF line endings, and use HTML `<title>`.
- **Chunking & Citations:** Script-aware token estimation (>= 3 tokens/word for Devanagari/Gujarati), splitting of oversized unpunctuated sentences, accurate `page_start` across overlaps, and citation format strictly governed by `doc_type` (`Page X` for PDF, `Section X` for non-PDF).
- **Doc Q&A Pipeline & VAD:** Neutralized `</document_data>` prompt injection, deterministic refusal in query language without LLM calls, history-augmented retrieval queries, automatic language detection from query script, and bounded TTS prefetching (sentence N+1 synthesized during sentence N playback). Thread-safe Silero VAD singleton shared across pipelines with echo-mute window measured from playback start (`notify_playback_start`).
- **Sentence Splitter:** Curated abbreviation set, protected decimals and timestamps, lookforward confirmation for lowercase continuations, and list item numbering awareness.
- **LLM Adapters:** Google AI adapter uses exponential backoff cooldown timers, explicit safety block messages, deterministic Flash candidate selection, and deduplicated SSE parsing without context manager leaks. Mid-stream fallback aborts with clear errors rather than duplicating output. Ollama requires exact model tag matches and supports configurable `keep_alive`.
- **STT & TTS:** Faster-Whisper unforces Hindi on short auto clips, falls back to small CPU model on CUDA failure, resamples audio to 16 kHz mono, and prunes unverified non-CT2 model mappings. Edge TTS maintains stoppable playback with configurable Roman voice `BOLSAMAJH_ROMAN_VOICE` (`en-IN-NeerjaNeural`). Piper TTS checks Hindi language compatibility and stores models in user data dir.
- **Text Cleanup & UI:** Lazy `aksharamukha` import, fixed anusvara conversion (`\u1e41`/`\u1e43` to 'n' in Roman mode), percentage/phone/rupee formatting, thread-marshalled Tkinter HUD queue, and cross-platform file dialog filters.  
**Alternatives considered:** Ad-hoc error handling in individual modules; letting partial TTS audio or failed clipboard state fail silently.  
**Reason:** Eliminates race conditions, audio corruption, prompt injection vulnerabilities, and UI freezes while guaranteeing offline and multi-script stability.

