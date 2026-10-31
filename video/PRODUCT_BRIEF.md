# BolSamajh — Product Brief for Product Launch Film

> **Project:** BolSamajh (Bolo. Samjho.) 🇮🇳🎙️  
> **Event:** Bolna × Symphony Voice AI Buildathon (Deadline: 31 Oct 2026, 11:59 PM IST)  
> **Source Verification Status:** 100% verified against repository code, documentation, and benchmark datasets.  

---

## 1. What It Is

- **One-Sentence Technical Pitch:**  
  BolSamajh is an open-source, local-first voice AI system featuring push-to-talk Hinglish dictation across desktop applications, verifiable long-context document intelligence (RAG with page citations and live voice barge-in), and in-place voice editing—running on local consumer GPUs/CPUs with zero mandatory cloud spend. (`README.md:12-13`)
- **10-Second Plain-English Pitch (Non-Technical Judges):**  
  You talk naturally in Hinglish into any app and it types clean Indian text with rupee symbols; you give it a dense insurance or legal PDF and it speaks back simple answers with exact page numbers, letting you interrupt anytime you want.
- **Official Tagline:**  
  *"Bolo. Samjho."* — Speak to write and act in any app. Talk to any document to understand it in your own language. (`README.md:1-3`, `submission/demo_script.md:4`)

---

## 2. The Problem

- **Who Suffers:**  
  Over 500 million bilingual Indians who naturally think, speak, and code-switch between Hindi, Gujarati, English, and regional dialects, but work in software environments built exclusively for monolithic English or pure formal Hindi. (`README.md:12`, `submission/demo_script.md:15`)
- **What Breaks Today:**  
  1. **Forced Language Binary:** Commercial dictation forces users to choose between pure English or pure Devanagari Hindi. Real colloquial Hinglish (*"Invoice pe 18 percent GST add karke total pandrah hazar kar do"*) gets butchered into nonsense transliterations. (`docs/COMPETITIVE_NOTES.md:18`, `submission/JUDGES.md:31-33`)
  2. **Dense Document Gatekeeping:** Critical documents—health insurance terms, bank circulars, government schemes, employment policies—arrive in dense 15-page legal English that ordinary citizens cannot parse easily. (`submission/demo_script.md:15`, `samples/sample_policy.pdf`)
  3. **Cloud Lock-in & Privacy Risks:** Commercial tools like Wispr Flow require monthly subscriptions ($12–$15/mo) and transmit private microphone audio and documents to foreign cloud servers, violating air-gap requirements in sensitive healthcare, enterprise, and legal settings. (`README.md:35-37`, `docs/COMPETITIVE_NOTES.md:20-26, 38-42`)
- **Why Now:**  
  High-performance quantized local models (faster-whisper, multilingual-e5, Gemma 3 4B on Ollama, and Piper TTS) can finally run sub-second inference on accessible hardware (NVIDIA RTX 3060 Ti / 8GB VRAM or modern multi-core CPUs), making zero-cloud voice AI practical without recurring subscription costs. (`README.md:222-227, 279-290`)

---

## 3. The Fix (User Experience Flow)

1. **Voice IN (Push-to-Talk Dictation Everywhere):**  
   - Hold `Alt+Shift+Space` in any Windows application (VS Code, Notepad, Slack, WhatsApp Web, Word).  
   - Speak fluid Hinglish. Releasing the hotkey cleans hesitations (*umm, uhh, matlab*), normalizes Indian currency (`₹15,000`), percentages (`18%`), dates, and phone numbers.  
   - Explicit 3-way script toggle from the system tray: Natural (as spoken), Roman (clean Latin), or Devanagari. (`README.md:105-110`, `docs/evidence/e2e_dictation.txt`)
2. **Voice OUT (Talk to Any Document — The Wedge):**  
   - Press `Alt+Shift+D` to index any PDF (or DOCX/web page). Hold `Alt+Shift+A` to ask conversational questions in Hinglish or Gujarati.  
   - Streams grounded answers sentence-by-sentence with clickable page citations (e.g. `[Page 1]`, `[Pages 1–2]`).  
   - **Voice Barge-In:** Powered by Silero VAD, speaking or hitting `Escape` interrupts TTS audio within 74–140 ms without waiting for playback to finish.  
   - **Strict Grounding & Refusal:** Questions outside the document trigger an honest refusal (*"Yeh document mein nahi hai"* / refusal threshold 0.785) instead of hallucinating. (`README.md:112-118, 305`, `docs/evidence/doc_qa_e2e.txt`, `docs/evidence/bargein_check.txt`)
3. **Voice ACT (In-Place Voice Editing):**  
   - Highlight any text in any application and hold `Alt+Shift+C`.  
   - Speak commands like *"Fix grammar and make it professional"* or *"Translate this paragraph to natural Hindi"*.  
   - Transforms text directly in-place via simulated clipboard operations, releasing keyboard modifiers cleanly and preserving the pre-existing clipboard. (`README.md:119-125`, `docs/evidence/e2e_dictation.txt:17-26`)

---

## 4. Architecture & Node Graph

### Node Graph
- **User Triggers:** Global Hotkeys (`Alt+Shift+Space`, `Alt+Shift+D`, `Alt+Shift+A`, `Alt+Shift+C`, `Escape`) | Browser Web Call (`/ws/call`) | Bolna Agent (`/v1/audio/*`)
- **Orchestration Pipelines:**  
  - `DictationPipeline` (`bolsamajh/pipelines/dictation.py`)
  - `DocQAPipeline` with Barge-in Controller (`bolsamajh/pipelines/doc_qa.py`)
  - `VoiceCommandsPipeline` (`bolsamajh/pipelines/voice_command.py`)
- **Speech-to-Text (STT):** `faster-whisper` (`large-v3-turbo` default on CUDA `int8_float16`; fallback to `MSpider3/whisper-hindi2hinglish-swift-ct2` on CPU).
- **Document RAG:** `intfloat/multilingual-e5-base` (512 token context, chunk size 500, overlap 80) + local FAISS index (`IndexFlatIP`).
- **LLM Reasoning:** Local Ollama (`gemma3:4b` at `localhost:11434`) with optional Google AI Studio Gemini free fallback.
- **Text-to-Speech (TTS):** Online default: `Edge-TTS` (`hi-IN-SwaraNeural`, `gu-IN-DhwaniNeural`, `en-IN-NeerjaNeural`); 100% Offline Air-Gapped mode: `Piper TTS` (ONNX `hi_IN-pratham-medium`).
- **Audio Output & VAD:** Local speaker playback (`sounddevice` / PyAV) + `Silero VAD` on-device background monitor for live barge-in.
- **Output Targets:** Any Active Windows Application | Floating HUD (`Tkinter` No-Activate) | Web Studio (`FastAPI` + HTML5) | Android Companion (WebSocket AudioRecord).
- **Bolna Gateway:** `/v1/audio/speech` (TTS proxy), `/v1/audio/transcriptions` (batch STT), `/v1/realtime` (WebSocket STT protocol).

---

## 5. Voice-AI Usage & Sponsor Truth

| Engine / Component | Model / Service | Execution Location | Config / File Path | Evidence Source |
|---|---|---|---|---|
| **STT Engine** | `faster-whisper` (`large-v3-turbo`) | Local GPU/CPU | `bolsamajh/stt/faster_whisper_engine.py` | `benchmark_data/hardware_measurements.json` |
| **STT Fallback / Fast** | `whisper-hinglish-swift-ct2` | Local CPU/GPU | `bolsamajh/stt/faster_whisper_engine.py` | `benchmark_data/benchmark_results.json` |
| **VAD & Barge-In** | `Silero VAD` (ONNX) | Local CPU | `bolsamajh/stt/vad.py` | `docs/evidence/bargein_check.txt` |
| **RAG Embeddings** | `intfloat/multilingual-e5-base` | Local CPU/GPU | `bolsamajh/documents/retriever.py` | `benchmark_data/retrieval_benchmark.json` |
| **Vector Database** | `FAISS` (`IndexFlatIP`) | Local RAM | `bolsamajh/documents/retriever.py` | `docs/evidence/doc_qa_e2e.txt` |
| **Local LLM** | Ollama (`gemma3:4b`) | Local `127.0.0.1:11434` | `bolsamajh/llm/ollama_adapter.py` | `docs/evidence/offline_mode.txt` |
| **Cloud LLM Fallback** | Google Gemini (`gemini-2.0-flash` free tier) | Cloud (Google AI Studio) | `bolsamajh/llm/gemini_adapter.py` | `docs/evidence/gemini_check.txt` |
| **Default Neural TTS** | Microsoft Edge-TTS | Cloud (HTTPS) | `bolsamajh/tts/edge_tts_engine.py` | `benchmark_data/hardware_measurements.json` |
| **Offline TTS** | Piper ONNX (`hi_IN-pratham-medium`) | Local CPU (ONNX Runtime) | `bolsamajh/tts/piper_engine.py` | `docs/evidence/offline_mode.txt` |
| **Bolna Voice Gateway** | OpenAI Audio Protocol `/v1` | Local FastAPI (`:8008`) | `bolsamajh/web/server.py` | `docs/evidence/bolna_client_check.txt` |

### Sponsor Policy:
- **Bolna:** Verified integration with Bolna package source code (`OPENAISynthesizer` client against local gateway `/v1/audio/speech` and `/v1/audio/transcriptions`, plus Realtime WebSocket `/v1/realtime`). We do NOT claim a live PSTN telephony call because that requires a public tunnel and paid Bolna cloud account. (`docs/evidence/bolna_client_check.txt:41-47`)
- **Sarvam / Deepgram:** Mentioned in competitive analysis documentation as alternative Indic STT APIs, but the default runtime is 100% self-hosted open-source models (zero external API fee).

---

## 6. Tech Stack (Actually in Repository)

- **Language & Runtime:** Python 3.10 / 3.11 / 3.12, PyInstaller on Windows x64.
- **Audio & ML Libraries:** `faster-whisper`, `ctranslate2`, `onnxruntime`, `silero-vad`, `faiss-cpu`, `sounddevice`, `edge-tts`, `piper-tts`, `PyAV` (av).
- **Document Ingestion:** `PyMuPDF` (fitz), `python-docx`, `beautifulsoup4`, `tesseract` fallback.
- **Web & Desktop UI:** `FastAPI`, `uvicorn`, `websockets`, `pystray`, `keyboard`, `pynput`, vanilla HTML5/ES6/CSS3 web studio, Kotlin native Android companion.

---

## 7. Honest Differentiators vs Wispr Flow

| Capability | Wispr Flow | BolSamajh | Source & Retrieval Date |
|---|---|---|---|
| **License & Auditability** | Proprietary closed-source | **100% Open Source (MIT)** | `wisprflow.ai`, 2026-10-31 / `LICENSE` |
| **Pricing** | Free (~2,000 words/wk) / **$12–$15/mo** | **$0.00 / Zero mandatory spend** | `wisprflow.ai`, 2026-10-31 / `README.md:36` |
| **Air-Gapped / Offline** | Cloud-dependent (voice audio sent to cloud) | **100% Offline Mode** (Faster-Whisper + Piper + Ollama) | `docs/COMPETITIVE_NOTES.md:63`, `docs/evidence/offline_mode.txt` |
| **Talk to Documents (RAG)**| None (requires external tools) | **Built-in Voice Doc Q&A** with page citations & refusal | `docs/COMPETITIVE_NOTES.md:39`, `docs/evidence/doc_qa_e2e.txt` |
| **Voice Barge-In** | N/A | **Silero VAD Voice Interruption** during speech playback | `docs/COMPETITIVE_NOTES.md:65`, `docs/evidence/bargein_check.txt` |
| **Script Control** | Implicit (Hindi vs Hinglish) | **Explicit 3-way toggle** (Natural / Roman / Devanagari) | `docs/COMPETITIVE_NOTES.md:66`, `submission/JUDGES.md:34` |
| **Indian Normalization** | General formatting | **Targeted ₹ currency, GST %, Lakh/Crore, Indian dates** | `docs/COMPETITIVE_NOTES.md:67`, `submission/JUDGES.md:33` |
| **Voice Agent Gateway** | None | **Drop-in OpenAI-compatible gateway** for Bolna agents | `docs/COMPETITIVE_NOTES.md:68`, `docs/evidence/bolna_client_check.txt` |
| **Benchmark Transparency** | Proprietary benchmarks | **Public, reproducible benchmark** with raw + norm WER | `docs/COMPETITIVE_NOTES.md:69`, `benchmark_data/BENCHMARK_RESULTS.md` |

---

## 8. Real Proof Points (Exact Repo Metrics)

All numbers verified from committed benchmark JSON files:
- **Speech Recognition (HiACC Hinglish Corpus, 100 clips):**  
  - `large-v3-turbo`: **38.52% WER** [32.71–44.56% 95% CI] | **573.0 ms** mean latency | **0.079x RTF** (over 12x faster than realtime) (`benchmark_data/benchmark_results.json`)
  - `medium`: **50.73% WER** [44.89–56.69% 95% CI] | **1370.9 ms** mean latency | **0.176x RTF** (`benchmark_data/benchmark_results.json`)
  - `whisper-hinglish-swift`: **52.70% WER** [48.41–57.86% 95% CI] | **100.0 ms** mean latency | **0.026x RTF** (`benchmark_data/benchmark_results.json`)
- **Speech Recognition (FLEURS Real Read Speech):**  
  - FLEURS Hindi (100 clips): **25.98% WER** (large-v3-turbo) (`benchmark_data/benchmark_results.json`)
  - FLEURS Gujarati (100 clips): **66.01% WER** (large-v3-turbo) (`benchmark_data/benchmark_results.json`)
- **Hardware Latency (RTX 3060 Ti GPU, 8GB VRAM):**  
  - STT Median Latency: **461.7 ms** (p95: **562.9 ms**, RTF: **0.121x**) (`benchmark_data/hardware_measurements.json:45-49`)
  - STT Real Speech Median: **510.1 ms** (p95: **1301.6 ms**, RTF: **0.061x**) (`README.md:285`)
  - STT GPU VRAM Allocation Delta: **1192.0 MB** (fits easily in 8GB) (`README.md:286`)
  - E5 Vector Retrieval Latency: **22.31 ms** mean (p95: **26.56 ms**) (`benchmark_data/retrieval_benchmark.json:11-12`)
  - Edge-TTS First-Packet Latency: **732.7 ms** (`README.md:288`)
  - Doc-QA True End-to-End TTFA (question end to audio play): **1592.6 ms** (< 2.0s target) (`README.md:289`)
- **Document Intelligence (Google XQuAD Hindi, 400 test queries):**  
  - Retrieval **Hit@1: 89.0%** | **Hit@3: 98.0%** | **Hit@5: 98.5%** (`benchmark_data/retrieval_benchmark.json:8-10`)
  - Calibrated Refusal Threshold: **0.785** (F1: **0.8685**, Precision: **81.86%**, Recall: **92.5%**) (`benchmark_data/retrieval_benchmark.json:13-16`)
- **Voice Barge-In Interruption:**  
  - Headphone Mode Interruption Latency: **66.2 ms** median (p95: **66.5 ms**) (`docs/evidence/bargein_check.txt:23`)
  - Replay Simulation Latency: **74.2 ms** median (p95: **78.8 ms**) (`benchmark_data/bargein_measurements.json:19-20`)
  - False Trigger Rate in 10-minute continuous background noise: **0.0 / min (0 false triggers)** (`benchmark_data/bargein_measurements.json:13-14`)

---

## 9. Where BolSamajh Loses / Known Limitations

We deliberately display these in the film to establish total engineering credibility:
1. **Language Breadth:** Wispr Flow supports **100+ production languages**; BolSamajh focuses on Hinglish, Hindi, Gujarati, and English. (`docs/COMPETITIVE_NOTES.md:46`)
2. **Gujarati ASR Accuracy:** Whisper error rate on Gujarati is **66.01%** on FLEURS vs 25.98% on Hindi. (`README.md:261, 382`)
3. **Cross-Platform Maturity:** Wispr Flow has native apps across macOS, Windows, iOS, and Android with cloud sync. BolSamajh's desktop app is Windows-only (Linux/macOS via Web UI). (`README.md:47, 387`)
4. **Offline Voice Coverage:** Local Piper TTS (`hi_IN-pratham-medium`) is Hindi-only; Gujarati and English in full air-gap mode lack native offline models and warn. (`README.md:384`)
5. **No Hardware Echo Cancellation:** Silero VAD runs without AEC; laptop speakers at maximum volume can trigger false barge-ins without headphones. (`README.md:385`)

---

## 10. Brand Identity & Styling

- **Name:** BolSamajh (बोलसमझ)
- **Colors:**
  - Base Dark: `#0a0d14` (card: `#121724`, border: `rgba(255, 255, 255, 0.08)`)
  - Accent Primary: `#6366f1` (Indigo)
  - Accent Secondary: `#8b5cf6` (Purple)
  - Accent Cyan: `#06b6d4`
  - Accent Green (Hero / Verified / Citations): `#10b981` (Emerald)
  - Glow: `0 0 25px rgba(99, 102, 241, 0.35)`
- **Typography:** Inter / system display font for UI, JetBrains Mono for chips/code, Noto Sans Devanagari for Hindi, Noto Sans Gujarati for Gujarati.
- **Tone:** Authoritative, clean, transparent, developer-first, zero hype.

