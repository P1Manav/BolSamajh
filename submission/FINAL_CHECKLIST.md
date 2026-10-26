# BolSamajh — Final Submission Checklist

> **Buildathon:** Bolna × Symphony Voice AI Buildathon (October 2026)  
> **Repository:** [https://github.com/P1Manav/BolSamajh](https://github.com/P1Manav/BolSamajh)  
> **Builder:** Manav (Solo Builder, Ahmedabad, India)  
> **License:** [MIT License](file:///d:/Projects/BolSamajh/LICENSE) (100% Free and Open Source)

---

## 1. Quick Verification & Execution

### One-Command Launch (Desktop Overlay)
```powershell
python -m bolsamajh
```
*HUD overlay docks in system tray with hotkeys: `Alt+Shift+Space` (dictate), `Alt+Shift+D` (load doc), `Alt+Shift+A` (ask doc), `Alt+Shift+C` (voice command).*

### One-Command Launch (Web UI & Bolna Gateway)
```powershell
python -m uvicorn bolsamajh.web.server:app --port 8000
```
*Access browser interface at `http://localhost:8000` or target OpenAI-compatible voice gateway at `http://localhost:8000/v1`.*

### Run All Unit & Integration Tests (Locally on Clean Venvs)
```powershell
pytest -v -m "not slow and not network" tests/
```
*81 tests passing green across both Python 3.11 and 3.12.*

---

## 2. Benchmark Reproduction

All benchmark data, real-speech audio manifests, synthetic audio generation, and evaluations are 100% deterministic and script-driven using public, ungated CC-BY-4.0 datasets (Google FLEURS `hi_in`/`gu_in`, HiACC Adult Test Eval):

```powershell
# Step 1: Download public benchmark datasets and generate synthetic test set
python scripts/fetch_benchmark_data.py

# Step 2: Run evaluation across models (large-v3-turbo, medium, whisper-hinglish-swift)
python -m bolsamajh.benchmark.evaluate --models medium large-v3-turbo whisper-hinglish-swift --suite all --device cuda --compute_type int8_float16

# Step 3: Measure hardware latencies and document retrieval speeds
python scripts/measure_hardware.py

# Step 4: Validate documentation tables against generated JSON files
python scripts/generate_readme_tables.py --check
```

---

## 3. Verified Features & Empirical Evidence Links

Every claimed feature is verified on this Windows machine (NVIDIA GeForce RTX 3060 Ti) with raw output committed under `docs/evidence/`:

| Feature | Verification Method | Evidence Link |
|:---|:---|:---|
| **CI & Test Suite** | 81 tests passing on Python 3.11 & 3.12 in clean venvs | [docs/evidence/ci_health.txt](file:///d:/Projects/BolSamajh/docs/evidence/ci_health.txt) |
| **Dictation & Text Insertion** | Automated Notepad launch, real `keybd_event` (Alt+Shift+Space), WER 0.0000, modifier released check (`GetAsyncKeyState`), clipboard restored | [docs/evidence/e2e_dictation.txt](file:///d:/Projects/BolSamajh/docs/evidence/e2e_dictation.txt) |
| **In-Place Voice Commands** | Automated Notepad launch with selection, Alt+Shift+C, in-place text rewrite | [docs/evidence/e2e_dictation.txt](file:///d:/Projects/BolSamajh/docs/evidence/e2e_dictation.txt) |
| **Voice Barge-In** | 10 min continuous TTS playback (93 sentences, 0 false triggers in speaker mode and 0 in headphone mode; median latency 231.5ms speaker / 66.2ms headphones) | [docs/evidence/bargein_check.txt](file:///d:/Projects/BolSamajh/docs/evidence/bargein_check.txt)<br>[benchmark_data/bargein_measurements.json](file:///d:/Projects/BolSamajh/benchmark_data/bargein_measurements.json) |
| **100% Offline Air-Gapped Mode** | Outbound network socket blocker, all 7 pipeline components executed with zero internet | [docs/evidence/offline_mode.txt](file:///d:/Projects/BolSamajh/docs/evidence/offline_mode.txt) |
| **Piper Local Neural TTS** | Real synthesis, SHA-256 verified against official Rhasspy pins | [docs/evidence/piper_check.txt](file:///d:/Projects/BolSamajh/docs/evidence/piper_check.txt) |
| **Document Intelligence (Doc-QA)** | Real PDF, DOCX, and local web page indexing; 9/9 questions answered with exact page/section citations | [docs/evidence/doc_qa_e2e.txt](file:///d:/Projects/BolSamajh/docs/evidence/doc_qa_e2e.txt) |
| **Bolna Synthesizer Integration** | Tested locally using Bolna package `OPENAISynthesizer` client code; verified Hindi & English synthesis playable via PyAV (>0.5s duration) | [docs/evidence/bolna_client_check.txt](file:///d:/Projects/BolSamajh/docs/evidence/bolna_client_check.txt) |
| **Bolna Realtime WebSocket STT** | Implemented & verified `/v1/realtime?intent=transcription` with Bolna protocol message shapes (`session.update`, `input_audio_buffer.append` 24kHz linear16, `input_audio_buffer.commit`) | [docs/evidence/bolna_client_check.txt](file:///d:/Projects/BolSamajh/docs/evidence/bolna_client_check.txt) |

---

## 4. Unverified Items & Limitations

In accordance with our strict honesty policy, features not verified on hardware are catalogued in [`docs/UNVERIFIED.md`](file:///d:/Projects/BolSamajh/docs/UNVERIFIED.md):

1. **Bolna Cloud Telephony Call:** Tested locally using Bolna's client library; live call from Bolna cloud orchestrator was not performed as it requires an active Bolna cloud subscription and telephone telephony trunk.
2. **Google Gemini Live API Check:** `GOOGLE_AI_API_KEY` was not configured in the host environment. The fail-soft adapter was fully verified using mock HTTP unit tests (startup warning, 404 Flash discovery, 429 rate limit backoff, `/api/status` fail-soft).
3. **Scanned PDF OCR via Tesseract:** Evaluated using local system presence. Tesseract OCR engine binary is not installed on this host machine; text-based PDFs and DOCX are parsed natively via PyMuPDF and python-docx.
