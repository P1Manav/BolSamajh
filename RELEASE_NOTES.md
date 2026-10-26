# BolSamajh v0.1.1 — Release Notes

> **Release Tag:** `v0.1.1`  
> **Release Date:** 2026-10-26  
> **Buildathon:** Bolna × Symphony Voice AI Buildathon  
> **Status:** All acceptance tests passing (53/53 unit tests, green CI on Ubuntu and Windows across Python 3.11 and 3.12)

---

## 🚀 Overview

BolSamajh v0.1.1 is an audited, empirical release of the open-source, local-first voice AI companion built for 500 million Hinglish and Indian-language speakers. It combines push-to-talk dictation in any desktop application, document intelligence with verifiable citations, in-place voice editing, and standard OpenAI-compatible audio gateway endpoints for Bolna agents.

---

## 🌟 Key Highlights & Fixes in v0.1.1

### 1. CI & Environment Integrity (Tier 0)
- Fixed headless Linux CI failure in clipboard handling by stubbing `Key` and providing a null keyboard fallback when pynput cannot initialize.
- Added offline `fake_edge_tts` fixture in `tests/conftest.py` so CI runs without network dependencies (`pytest -m "not slow and not network"`).
- Pinned exact dependency versions in `requirements.lock.txt` for both Python 3.11 and 3.12 across Ubuntu and Windows.

### 2. Empirical Benchmark & Latency Truth (Tier 1)
- Evaluated 1,200 real speech and synthetic stress clips across three models on an NVIDIA GeForce RTX 3060 Ti GPU.
- Committed complete per-clip results in `benchmark_data/per_clip_results.jsonl` (model, clip ID, reference, raw hypothesis, normalized texts, WER, latency, audio duration, device).
- Generated Section 3 worst clips automatically via `scripts/dump_worst_clips.py` with zero hand edits.
- Re-measured real speech latency on GPU: **2,262.2 ms** (RTF **0.146x**, running 6.8× faster than real-time) on a 15.45s clip (`hiacc_cs_001.wav`), replacing fabricated latency claims.
- Clarified that `MSpider3/whisper-hindi2hinglish-swift-ct2` is an unverified third-party CT2 conversion of Oriserve Swift.

### 3. Gemini Fallback & Speech Gateway (Tier 2)
- Updated Google AI default from retired `gemini-2.0-flash` to active `gemini-3.5-flash` (verified live on 2026-10-26 with `generateContent`, configurable via `GOOGLE_AI_MODEL`), added automatic Flash-family fallback on HTTP 404 from live models endpoint, and added regression tests.
- Enhanced `/v1/audio/speech` endpoint to honor `response_format` (`mp3`, `wav`), `speed` (rate adjustment), and return clean HTTP 502 JSON error on Edge-TTS upstream failure (no bare 500s).
- Clarified Bolna gateway documentation as implemented and integration-tested, with clear live testing steps.

### 4. Server Security Hardening (Tier 3)
- Protected `/api/*` endpoints with HMAC Bearer token auth (`hmac.compare_digest`) when `BOLSAMAJH_API_KEY` is configured, while keeping `/`, `/static`, and `/api/status` exempt.
- Hardened `safe_fetch_url` against DNS rebinding attacks by connecting sockets directly to the vetted, resolved IP address (preserving Host header and TLS SNI).
- Wrapped `/api/qa/stream` in error handling that emits an `error` SSE event before `[DONE]`.
- Enforced HTTP 400 with "unsupported audio" on `/api/qa/voice` if audio resampling fails, rather than passing raw bytes to STT.
- Corrected Indic TTS transliteration: ceased running destructive ISO transliteration on Roman Hinglish; transliteration is only applied cross-script between Indic scripts (e.g. Gujarati to Devanagari).
- Documented 60-second TTL cache for the `/api/status` LLM readiness check.

### 5. Voice & Desktop Honesty (Tier 4)
- Added `is_active` property and WARNING log capture on mic stream errors in `BargeInMonitor`.
- Added end-to-end integration tests exercising real sentence splitting, generation ID tracking, cleanup pipeline, and BargeInMonitor.
- Re-labeled README capabilities table using strictly allowed statuses: **Verified**, **Implemented, untested on hardware**, or **Not implemented**.

---

## ⚠️ Honest Known Limitations

1. **Spontaneous Code-Switching Accuracy:** While synthetic code-switched Hinglish achieves 12.48% WER on fast models, real spontaneous accented speech from the HiACC corpus exhibits 50.41% WER on Whisper medium and 38.59% on large-v3-turbo due to diverse Indian regional accents and colloquial loanwords.
2. **Orthographic vs. Phonetic Variants:** Hinglish English loanwords lack a single standardized spelling (e.g., *"meeting"* vs *"miting"* vs *"मीटिंग"*). While BolSamajh uses canonical script-normalized transliteration to bridge Devanagari and Latin scripts without penalizing alphabet mismatches, it does not phonemically collapse loanword spelling variants.
3. **Physical Hardware Execution:** Features such as physical microphone hotkey dictation, in-place OS clipboard pasting, and 100% offline air-gapped mode with physical network disconnection are implemented and verified via unit/integration tests with synthetic audio and stubs, but are marked **Implemented, untested on hardware** for this automated session.
4. **Swift Model Conversion:** The model `MSpider3/whisper-hindi2hinglish-swift-ct2` is an unverified third-party CT2 conversion of Oriserve's Swift model.
5. **Bolna Live Integration:** The Bolna audio gateway endpoints (`/v1/audio/transcriptions` and `/v1/audio/speech`) are implemented and pass all integration tests against the OpenAI specification, but have not yet been tested against a live Bolna agent in production.
6. **Numerical Digit Variations:** ASR output alternates between written Hindi words (*"पंद्रह"*) and ASCII digits (*"15"*), which increases raw word error rates on numerical test sets.

---

## 🧪 Test Suite Status

- **Total Test Cases:** 53 passed (53 non-slow in automated CI, 2 deselected slow).
- **Verified Python Environments:** Python 3.11, Python 3.12 (clean venvs created from `requirements.lock.txt`).
- **Platforms:** Ubuntu (CI), Windows (Local & CI).
