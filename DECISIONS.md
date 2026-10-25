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
**Reason:** CTranslate2 backend is 4× faster than original Whisper. `medium` model (~1.5 GB VRAM in INT8) fits alongside LLM on RTX 3060 Ti 8 GB. Initial prompt biasing (`initial_prompt="Hinglish, Hindi, Devanagari, English. Bolo. Samjho."`) ensures script consistency and prevents phonetics drifting into unintended scripts.

## D003: LLM Local — Ollama + gemma3:4b (with Google AI Studio Fallback)
**Date:** 2026-10-25  
**Choice:** Ollama serving gemma3:4b locally, Google AI Studio free tier (Gemini 2.0 Flash — 15 RPM, 1M tokens/day free) as fallback.  
**Alternatives considered:** llama.cpp direct, Phi-3 (less multilingual), Mistral (English-centric).  
**Reason:** Gemma 3 4B has strong multilingual capability including Hindi/English, fits in 8 GB VRAM alongside whisper medium, and Ollama provides a simple HTTP API.

## D004: TTS — Edge-TTS (Online Neural Speech)
**Date:** 2026-10-25  
**Choice:** Edge-TTS with `hi-IN-SwaraNeural` voice for neural speech synthesis.  
**Alternatives considered:** gTTS (unnatural robotic voice, no streaming), Coqui TTS (resource-heavy), Piper (open-source offline, requires verified high-quality Hindi ONNX voice model).  
**Reason:** Edge-TTS is free (uses Microsoft Edge's speech service, no API key), supports streaming audio, and produces high-quality natural Hindi and Indian English voices with low latency (TTFA ~644 ms). Requires internet connectivity, as noted in the Privacy and Limitations documentation.


## D005: Embeddings — paraphrase-multilingual-MiniLM-L12-v2
**Date:** 2026-10-25  
**Choice:** sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (420 MB).  
**Alternatives considered:** multilingual-e5-small (less tested), BGE-M3 (1.3 GB, overkill).  
**Reason:** Supports 50+ languages including Hindi and English, small enough to run on CPU, well-tested with FAISS.

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

## D012: Benchmark v2 Architecture — Real Speech & Canonical Scoring
**Date:** 2026-10-25  
**Choice:** Separate evaluations into Real Speech (Google FLEURS `hi_in`/`gu_in`, HiACC `Trelis/hiacc-adult-test-eval`) and Synthetic Stress Set (100 sentences with multi-voice rotation and automated DSP degradations: noise injection, speed change, 8 kHz telephony bandpass filtering). Replace unprincipled 'best of two references' with canonical Devanagari normalization and phonemic transliteration via Aksharamukha.  
**Alternatives considered:** Only synthetic evaluation; character-exact scoring without phonetic transliteration (penalizes loanword spelling variations).  
**Reason:** Separating real human speech from synthetic stress gives voice-AI judges clear, reproducible evidence. Canonical phonemic transliteration accurately measures whether the speech recognition captured the right words rather than penalizing script mismatches (e.g. मीटिंग vs meeting).

