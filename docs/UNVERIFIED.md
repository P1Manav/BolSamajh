# BolSamajh — Unverified Items & Limitations Log

> Under the strict honesty policy of BolSamajh, any capability, integration, external credential, or environment feature that has not been empirically verified with committed raw evidence on this machine is catalogued here.

## 1. Google Gemini AI Studio (`GOOGLE_AI_API_KEY`)
- **Status:** Unverified (no API key configured in environment).
- **What was attempted:** Ran `python scripts/check_gemini.py`. The environment variable `GOOGLE_AI_API_KEY` is not set.
- **Safety / Default:** BolSamajh automatically disables cloud LLM fallback, logs a single clear warning at startup, and runs 100% locally on Ollama (`gemma3:4b`). `/api/status` reports `"LLM fallback unavailable"`. All mock error paths (missing key, 404 live model fallback, 429 rate limit backoff) are covered by automated unit tests.
- **How to verify personally:** Set `GOOGLE_AI_API_KEY=your_key` in `.env` and run `python scripts/check_gemini.py`.

## 2. Bolna Cloud End-to-End Live Call
- **Status:** Unverified on Bolna Cloud (no Bolna cloud account / outbound telephony credits).
- **What was verified:** Verified locally using Bolna's official client library (`bolna` package) against BolSamajh's OpenAI-compatible Speech synthesis endpoint (`/v1/audio/speech`). Synthesized both Hindi and English sentences, verified playable audio (>0.5s duration and 24kHz sample rate).
- **Limitation:** Bolna's cloud voice agents interact via WebSocket. BolSamajh supports OpenAI-compatible HTTP speech synthesis and transcription; live deployment on Bolna cloud requires an active Bolna cloud agent and outbound telephony trunk.

## 3. Scanned PDF OCR via Tesseract
- **Status:** Evaluated based on local system presence.
- **What was attempted:** Checked system PATH for `tesseract.exe`.
- **Safety / Default:** If Tesseract is not installed on the host machine, text-based PDFs and DOCX are parsed via PyMuPDF and python-docx. Scanned OCR fallback is marked as optional/untested on environments without system Tesseract binary.

## 4. Hardware Discrepancy Reconciliation
- **Status:** Resolved in Phase 2 with unified measurement benchmark.
