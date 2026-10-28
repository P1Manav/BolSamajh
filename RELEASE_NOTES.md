# BolSamajh — Release Notes

## BolSamajh v1.0.0-submission (Final Buildathon Submission)

> **Release Tag:** `v1.0.0-submission`  
> **Release Date:** 2026-10-26  
> **Buildathon:** Bolna × Symphony Voice AI Buildathon  
> **Status:** All 81 unit & integration tests passing locally in clean venvs across Python 3.11 and 3.12, and in multi-OS CI.

---

### 🚀 Overview
BolSamajh `v1.0.0-submission` represents the final, autonomous, end-to-end verified release for the Bolna × Symphony Voice AI Buildathon. Under strict empirical evidence and honesty guidelines, every benchmark number and hardware claim is derived from committed raw execution logs under `docs/evidence/` and verifiable JSON artifacts.

### 🌟 Verified Capabilities in v1.0.0-submission

1. **Automated Desktop Hotkeys & Insertion (Phase 5):**
   - Automated end-to-end Notepad launch, real `keybd_event` hotkey simulation (`Alt+Shift+Space`), audio transcription (WER 0.0000), modifier released check (`GetAsyncKeyState`), and 100% clipboard preservation.
   - Voice editing (`Alt+Shift+C`) tested with real text selection replacement in-place.
   - Evidence: [`docs/evidence/e2e_dictation.txt`](docs/evidence/e2e_dictation.txt).

2. **Automated Voice Barge-In & Interruption (Phase 5):**
   - Automated 10-minute continuous TTS playback test (93 sentences) with zero human intervention.
   - Speaker Mode: 0 false triggers (Threshold: $\le 3$), speech onset latency: Median 231.5 ms (P95: 231.6 ms).
   - Headphone Mode: 0 false triggers (Threshold: $\le 1$), speech onset latency: Median 66.2 ms (P95: 66.5 ms).
   - Evidence: [`docs/evidence/bargein_check.txt`](docs/evidence/bargein_check.txt), [`benchmark_data/bargein_measurements.json`](benchmark_data/bargein_measurements.json).

3. **100% Air-Gapped Offline Mode (Phase 5):**
   - Verified in an isolated process with all non-loopback network calls blocked at the socket level (`socket.socket.connect` monkeypatched, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).
   - All 7 pipeline components (audio capture, VAD, STT, embedding RAG, local Gemma 3 4B, Piper neural TTS, and text insertion) executed with zero internet connectivity.
   - Evidence: [`docs/evidence/offline_mode.txt`](docs/evidence/offline_mode.txt).

4. **Piper Local Offline Neural TTS (Phase 5):**
   - Pinned Rhasspy Hindi voice (`hi_IN-pratham-medium.onnx`) cryptographically verified against pinned SHA-256 hashes.
   - Real local ONNX synthesis executed and verified (199,212 bytes WAV output, duration 4.51s).
   - Evidence: [`docs/evidence/piper_check.txt`](docs/evidence/piper_check.txt).

5. **Document Intelligence Grounding & Citations (Phase 5):**
   - Real end-to-end evaluation across PDF, DOCX, and local HTTP web server documents.
   - 9/9 questions answered accurately with exact page citations for PDFs (*"Page 1"*, *"Page 2"*) and section citations for DOCX/Web (*"Section 1"*).
   - Evidence: [`docs/evidence/doc_qa_e2e.txt`](docs/evidence/doc_qa_e2e.txt).

6. **Bolna Framework Client Integration (Phase 6):**
   - Tested using **Bolna's own `OPENAISynthesizer` package client** against running BolSamajh gateway (`/v1/audio/speech`).
   - Verified returned audio stream is playable via PyAV for both Hindi (4.48s) and English (4.02s).
   - Tested batch STT endpoint (`/v1/audio/transcriptions`).
   - Implemented and verified minimal Realtime-compatible transcription WebSocket (`/v1/realtime?intent=transcription`) conforming to Bolna's streaming protocol (`session.update`, `input_audio_buffer.append` 24kHz linear16, `input_audio_buffer.commit`).
   - Evidence: [`docs/evidence/bolna_client_check.txt`](docs/evidence/bolna_client_check.txt).

7. **Code Quality & Thread Lifecycle Sweep (Phase 7):**
   - Physical modifier restoration in `ModifierGuard` using `GetAsyncKeyState` so held keys are never stuck released.
   - Sentence splitter enhancements: initials (`A.`, `M.`) and trailing closing brackets/quotes support.
   - Unconditional reset of `_processing` in `cancel()` and worker threads to prevent deadlock.
   - Device and compute_type configuration consistency across CPU and CUDA.
   - Clean `ruff` validation on chosen ruleset (`F`, `E9`).

8. **Latency Reconciliation & Grammar Normalizer (Phases 2 & 3):**
   - Shared timing harness in `bolsamajh/benchmark/timing.py` eliminating measurement discrepancies between scripts.
   - Strict grammar number normalizer ensuring only valid numeric sequences are converted; ambiguous words (`do`, `so`, etc.) protected. Full 1,000-clip benchmark rerun with normalizer on/off WER reported.
   - Dynamic stamps for date and CUDA version generated directly from JSON.

---

### ⚠️ Honest Known Limitations (from `docs/UNVERIFIED.md`)

1. **Bolna Cloud Telephony Call:** The gateway was tested locally with Bolna's official client library; live telephony call from the Bolna cloud orchestrator was not performed as it requires a paid Bolna cloud account and outbound telephony trunk.
2. **Google Gemini Live API Check:** `GOOGLE_AI_API_KEY` was not configured in the host environment. The fail-soft adapter was fully verified using mock HTTP unit tests (startup warning, 404 Flash discovery, 429 rate limit backoff, `/api/status` fail-soft).
3. **Scanned PDF OCR via Tesseract:** Evaluated using local system presence. Tesseract OCR engine binary is not installed on this host machine; text-based PDFs and DOCX are parsed natively via PyMuPDF and python-docx.

---

## BolSamajh v0.1.3 — Release Notes

> **Release Tag:** `v0.1.3`  
> **Release Date:** 2026-10-26  
> **Buildathon:** Bolna × Symphony Voice AI Buildathon  
> **Status:** All acceptance tests passing (75 non-slow, non-network unit & integration tests passing locally and in automated multi-OS CI across Python 3.11 and 3.12)

---

## 🚀 Overview

BolSamajh v0.1.3 is an audited, empirical release of the open-source voice AI companion (local STT/RAG; cloud TTS by default, offline TTS optional) built for 500 million Hinglish and Indian-language speakers. It combines push-to-talk dictation in any desktop application, document intelligence with verifiable citations, in-place voice editing, and standard OpenAI-compatible audio gateway endpoints for Bolna agents.

---

## 🌟 Key Highlights & Fixes in v0.1.3 (Prompt v5 Audit)

### 1. Grammar-Based Number Normalizer Rewrite (Tier 1)
- Purged all test-set transliteration artifacts (`dasamla`, `pacasa`, `karoda`, `eka`, `tina`, `cara`, `pamca`, `atha`, `nava`, `sunya`, `hajara`, `lakha`) from `bolsamajh/benchmark/normalization.py`.
- Replaced heuristic mappings with strict, grammar-justified rules for Devanagari, Gujarati, English, and Roman Hindi numbers.
- Implemented an Ambiguity Guard: everyday Roman Hindi words (`do`, `so`, `sat`, `ath`, `nau`) are never converted unless part of a run $\ge 3$ or adjacent to scale words forming valid numbers (e.g. "I do so like it" and "mujhe do teen din chahiye" remain untouched).
- Added `normalize_number_words` ablation flag and published a full Normalizer Disclosure in `benchmark_data/BENCHMARK_RESULTS.md`.

### 2. Fair Summary Tables & Disjoint Test Set Prevention (Tier 2)
- Fixed summary tables so disparate test splits are never averaged into one misleading column.
- Added explicit clip counts in headers: `FLEURS Hindi (100 clips)`, `FLEURS Gujarati (100 clips)`, `HiACC Hinglish (100 clips, comparable across all 3)`, and `All Real Speech (300 clips)`.
- Enforced that Hinglish-only model (`whisper-hinglish-swift`) is marked `— *(N/A: Hinglish-only)*` in 300-clip columns.
- Added regression test `test_comparison_columns_use_identical_clip_sets` asserting identical clip IDs across models in every comparison column.
- Stated model recommendation (`large-v3-turbo`) using only comparable numbers.

### 3. Latency Honesty & Multi-Run Empirical Benchmarking (Tier 3)
- Updated `scripts/measure_hardware.py` and `evaluate.py` to benchmark 3 separate runs per model with warmup, recording per-run mean, median, p95, GPU name, and `nvidia-smi` state.
- Reported median and p95 in README and documentation tables instead of single-run mean.
- Deleted speculative explanations of latency variance. Added regression test `test_hardware_measurements_three_runs_and_median_p95`.

### 4. Server Security & Piper Gateway Singleton (Tier 4)
- **Gzip/Deflate Bomb Defense:** Rewrote `safe_fetch_url` to stream chunk-by-chunk using `zlib.decompressobj()`, enforcing the 5 MB limit on decompressed output without allocating full uncompressed buffers. Added bomb defense unit test.
- **Piper Gateway Singleton:** Implemented lazy, thread-safe module-level cache `get_piper_adapter()` in `/v1/audio/speech`, eliminating ONNX model reloads per request. Added regression test asserting `_load_voice` is called once across multiple requests.
- **Pinned HF Commit:** Pinned Piper Hugging Face repository URL to immutable commit SHA `5041a7a49ae5b3a0f30e6837769eb03fdbb231bd` with verified live SHA-256 hashes for both ONNX model and config.
- **Eliminated Test Warnings:** Fixed async generator in Edge-TTS error test, passing `pytest -W error::ResourceWarning`.

### 5. Honest External Claims (Tier 5)
- Added `scripts/check_gemini.py` for live model verification; changed unbacked claims to "unverified — run `python scripts/check_gemini.py` with your key".
- Replaced unbacked CI text with GitHub Actions CI status badge in README.
- Clarified application timeline: this repository started on 2026-10-25; the first prototype overlay predates it.

---

## 🌟 Previous Highlights & Fixes in v0.1.2

### 1. CI & Environment Integrity (Tier 0)
- Multi-OS CPU matrix workflow (Ubuntu + Windows across Python 3.11 and 3.12) running clean test suites from pinned `requirements.lock.txt`.
- Headless Linux CI handles missing X11 display and stubs `pynput` keyboard listeners safely.
- Fast, deterministic CI runs without network calls via `fake_edge_tts` and mock LLM fixtures (`pytest -m "not slow and not network"`).

### 2. Live Gemini Fallback & Key Security (Tier 1)
- Switched default Google AI fallback model to `gemini-3.5-flash` (unverified — run `python scripts/check_gemini.py` with your key).
- Implemented automatic Flash-family fallback on HTTP 404 from live Google AI models endpoint.
- Secured API key handling: transmitted strictly via `x-goog-api-key` header (never in URL), with `httpx` logging suppressed to prevent terminal key leaks.

### 3. Web UI Security & Authenticated Audio Playback (Tier 2)
- Added in-memory API key input in the Web UI navigation bar with clear `✓ Set` status. The key is never persisted to `localStorage`, `sessionStorage`, or cookies.
- Implemented authenticated audio playback (`fetchWithAuth` returning `URL.createObjectURL(blob)`) to eliminate HTTP 401 Unauthorized errors in standard HTML `<audio>` elements.

### 4. Benchmark Normalization Repair (Tier 3)
- Fixed fused decimals: preserved real decimal points (`3.5`, `36.6`, `2.5 crore`) between digits and edge punctuation.
- Normalized spaced and hyphenated digit sequences (`3 5 0` → `350`), spoken decimal words, and compound Hindi number words (`एक सौ पचास` / `ek sau pachaas` → `150`).
- Added regression test `test_no_fused_decimals_in_per_clip_results` and re-evaluated all <!-- NUM:benchmark.total_clips -->1,000<!-- /NUM --> clips on NVIDIA RTX 3060 Ti GPU, eliminating all 12 fused decimals.

### 5. Single Set of Numbers & Large-v3-Turbo Default (Tier 4)
- Set default CUDA STT model to `large-v3-turbo` with empirical hardware performance: **<!-- NUM:hw.stt_real_mean_latency_ms -->575.5<!-- /NUM --> ms** real speech mean latency (RTF **<!-- NUM:hw.stt_real_rtf -->0.061<!-- /NUM -->x**, p95: **<!-- NUM:hw.stt_real_p95_latency_ms -->1301.6<!-- /NUM --> ms**) across <!-- NUM:hw.stt_real_count -->300<!-- /NUM --> clips, and **<!-- NUM:hw.stt_synth_latency_ms -->475.9<!-- /NUM --> ms** on synthetic sentences.
- True end-to-end Doc-QA Time-To-First-Audio measured at **<!-- NUM:hw.total_ttfa_ms -->1592.6<!-- /NUM --> ms** (< 2000 ms target).
- Automated synchronization of numbers across all files via `scripts/generate_readme_tables.py --check` and unit test `test_docs_sync.py` to prevent numbers drift.

### 6. Pitch Honesty & Local Piper Gateway (Tier 5)
- Clarified that the TTS gateway proxies Microsoft Edge-TTS (an unofficial cloud endpoint) by default.
- Wired local offline Piper TTS (`hi_IN-pratham-medium` ONNX) directly into `/v1/audio/speech` via `voice="piper"` or `model="piper"` with automatic WAV and MP3 formatting.
- Replaced blanket "zero cloud / local-first" pitch claims with "local STT/RAG; cloud TTS by default, offline TTS optional".
- Deleted "connected directly to Bolna agents" claims in favor of "OpenAI-compatible TTS gateway for Bolna (not yet tested against a live agent)".

### 7. Server Hardening Leftovers (Tier 6)
- Capped URL fetch response bodies to 5 MB while streaming in `safe_fetch_url` to prevent memory exhaustion.
- Implemented charset detection from `Content-Type` header and HTML `<meta charset>`, falling back to UTF-8 with `errors="replace"`.
- Included non-default ports in the `Host` header (e.g. `example.com:8080`).
- Cleanly reported HTTP 4xx/5xx upstream errors as `"Failed to fetch URL (HTTP X)"` rather than SSRF protection errors.
- Handled IPv6 wildcards (`::`, `[::]`) in `check_bind_security` and added a `__main__` entrypoint with security enforcement.

### 8. Hardware Verification Workflows (Tier 7)
- Created `docs/MANUAL_VERIFICATION.md` with copy-paste step-by-step checklists for barge-in, hotkeys/clipboard, offline air-gapped mode, and Bolna live tunnel testing.
- Built automated barge-in test script `scripts/measure_bargein.py` that plays continuous speech while monitoring false-trigger rates.

---

## ⚠️ Honest Known Limitations

1. **Spontaneous Code-Switching Accuracy:** While synthetic code-switched Hinglish achieves fast inference, real spontaneous accented speech from the HiACC corpus exhibits <!-- NUM:stt.medium.hiacc_wer -->50.73%<!-- /NUM --> WER on Whisper medium and <!-- NUM:stt.turbo.hiacc_wer -->38.52%<!-- /NUM --> on large-v3-turbo due to diverse Indian regional accents and colloquial loanwords.
2. **Swift Model Conversion:** The model `MSpider3/whisper-hindi2hinglish-swift-ct2` is an unverified third-party CT2 conversion of Oriserve's Swift model.
3. **Physical Hardware Execution:** Features such as physical microphone hotkey dictation, in-place OS clipboard pasting, and 100% offline air-gapped mode with physical network disconnection are implemented and verified via unit/integration tests with synthetic audio and stubs, but are marked **Implemented, untested on hardware** in README tables until manually verified via `docs/MANUAL_VERIFICATION.md`.
4. **Bolna Live Integration:** The Bolna audio gateway endpoints (`/v1/audio/transcriptions` and `/v1/audio/speech`) are implemented and pass all integration tests against the OpenAI specification, but have not yet been tested against a live Bolna agent in production. Cloud agents require a tunnel (e.g. `cloudflared`) to reach localhost.
5. **Real-time Bolna WebSocket STT:** Full-duplex streaming WebSocket transcriber (`REALTIME_TRANSCRIBER_URL`) is not implemented; Bolna uses standard `/v1/audio/transcriptions`.
6. **Edge-TTS Unofficial Cloud Service:** Default speech synthesis relies on Microsoft Edge's Read Aloud service. For strictly air-gapped deployments, users must configure `BOLSAMAJH_TTS_ENGINE=piper`.
7. **Numerical Digit Variations:** ASR output alternates between written Hindi words (*"पंद्रह"*) and ASCII digits (*"15"*), which increases raw word error rates on numerical test sets.

---

## 🧪 Test Suite Status

- **Total Test Cases:** 75 passed, 2 deselected slow (100% passing across 11 test modules).
- **Verified Python Environments:** Python 3.11, Python 3.12 (clean venvs created from `requirements.lock.txt`).
- **Platforms:** Ubuntu (CI), Windows (Local & CI).
- **Documentation Verification:** `python scripts/generate_readme_tables.py --check` passing green.
