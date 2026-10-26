# BolSamajh v0.1.3 — Release Notes

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
- Set default CUDA STT model to `large-v3-turbo` with empirical hardware performance: **<!-- NUM:hw.stt_real_mean_latency_ms -->575.5<!-- /NUM --> ms** real speech mean latency (RTF **<!-- NUM:hw.stt_real_rtf -->0.061<!-- /NUM -->x**, p95: **<!-- NUM:hw.stt_real_p95_latency_ms -->1301.6<!-- /NUM --> ms**) across <!-- NUM:hw.stt_real_count -->300<!-- /NUM --> clips, and **<!-- NUM:hw.stt_synth_latency_ms -->703.0<!-- /NUM --> ms** on synthetic sentences.
- True end-to-end Doc-QA Time-To-First-Audio measured at **<!-- NUM:hw.total_ttfa_ms -->1901.3<!-- /NUM --> ms** (< 2000 ms target).
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

1. **Spontaneous Code-Switching Accuracy:** While synthetic code-switched Hinglish achieves fast inference, real spontaneous accented speech from the HiACC corpus exhibits <!-- NUM:stt.medium.hiacc_wer -->50.2%<!-- /NUM --> WER on Whisper medium and <!-- NUM:stt.turbo.hiacc_wer -->38.52%<!-- /NUM --> on large-v3-turbo due to diverse Indian regional accents and colloquial loanwords.
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
