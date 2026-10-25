# BolSamajh v0.1.0 — Release Notes

> **Release Tag:** `v0.1.0`  
> **Release Date:** 2026-10-25  
> **Buildathon:** Bolna × Symphony Voice AI Buildathon  
> **Status:** All acceptance tests passing (41/41 unit tests, green CI on Ubuntu and Windows)

---

## 🚀 Overview

BolSamajh v0.1.0 is the first production-ready release of the open-source, local-first voice AI companion built for 500 million Hinglish and Indian-language speakers. It combines push-to-talk dictation in any desktop application, document intelligence with verifiable citations, in-place voice editing, and standard OpenAI-compatible audio gateway endpoints for Bolna agents.

---

## 🌟 Key Highlights & Fixes

### 1. Robustness & Voice Desktop Engine (Tier 5)
- **Acoustic Echo Suppression & Barge-In:** Mutes detection for the first ~300 ms of sentence playback; requires an elevated VAD threshold (0.80) and longer sustained run (~200 ms) in speaker mode to prevent speaker audio reflection; supports `headphone_mode` via config flag.
- **Answer Interruption Generation ID:** When interrupted via voice barge-in or keypress, the active generation ID advances immediately, ensuring that queued and future streamed sentence chunks are discarded.
- **Worker Cancellation Lifecycle:** Worker threads are joined cleanly on `cancel()`, guaranteeing that `_processing` flags are cleared only when workers fully exit.
- **Modifier Release for Hotkeys:** Releases physical Shift, Alt, and Ctrl modifiers before simulating `Ctrl+C` or `Ctrl+V` to prevent hotkey conflicts (e.g. `Alt+Shift+C`), and safely restores them.
- **Multilingual Sentence Splitter:** Intelligent boundary detection that prevents premature splitting on decimals (`15.50`), English abbreviations (`Dr.`, `Mr.`, `Mrs.`, `Rs.`), and Hindi abbreviations (`डॉ.`, `पं.`, `रु.`), while properly splitting on Hindi dandas (`।`, `॥`) and question marks.
- **Document Citations & Chunk Spans:** Tracks exact cross-page merged chunk page spans (`Pages 1–2` for PDFs) and formats DOCX/web citations strictly as `Section: ...` (never `Page`).

### 2. Empirical Benchmark & Credibility Audit (Tiers 1 & 2)
- **Dataset Validation & Script Routing:** Added reference validation filters in `scripts/fetch_benchmark_data.py` requiring `len(words) >= 4` and duration consistency to prevent truncated upstream references, language routing for Indic/English scripts, and repetition penalty + VAD filtering.
- **400 Audio Clip Benchmark Evaluation:**
  - 300 Real Speech Clips: 100 HiACC Hinglish code-switching, 100 Google FLEURS Hindi, 100 Google FLEURS Gujarati.
  - 100 Synthetic Degraded Stress Clips: 4 Edge-TTS voices across 5 categories and automated DSP degradations (speed ±10%, additive noise at 20/10/5 dB SNR, 8 kHz telephony bandpass + mu-law).
- **Bootstrap 95% Confidence Intervals:** Computed non-parametric bootstrap CIs (1,000 resamples) for all WER metrics in `benchmark_results.json` and README tables.
- **Deterministic Fetch Script:** Added `scripts/fetch_benchmark_data.py` with fixed random seeds for 100% reproducible benchmark data generation.
- **Calibrated Refusal Threshold:** Empirically calibrated cosine similarity refusal threshold to **0.785** across 200 Google XQuAD Hindi questions, maximizing F1 to **0.8685** (Precision: 81.86%, Recall: 92.5%).

### 3. Web Gateway & Security Hardening (Tiers 3 & 4)
- **Bolna Voice Gateway:** Standard OpenAI-compatible `/v1/audio/transcriptions` and `/v1/audio/speech` endpoints verified against live running server instances.
- **Path Traversal Protection:** Validates that audio file requests strictly resolve within the audio cache directory using `Path.resolve().is_relative_to`.
- **Bearer Token Authentication:** Enforces `Authorization: Bearer <BOLSAMAJH_API_KEY>` for all gateway endpoints.
- **Binding Security:** Refuses to bind on external or non-localhost interfaces unless `BOLSAMAJH_API_KEY` is set.
- **Single-Hop SSRF Defense:** Manually resolves and re-validates each redirect hop, blocking all private, loopback, link-local, and reserved IPv4/IPv6 ranges.
- **Streaming Upload Limit:** Aborts oversized audio file uploads in 64 KB streaming chunks with HTTP 413, preventing memory exhaustion.

---

## 🧪 Test Suite Status

- **Total Test Cases:** 41 passed (40 non-slow in automated CI, 1 slow in local/manual workflow).
- **Test Execution Time:** ~24.5 seconds on Windows / Ubuntu.
- **Verified Python Environments:** Python 3.11, Python 3.12.
