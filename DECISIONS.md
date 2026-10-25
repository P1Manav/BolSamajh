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

## D004: TTS — Edge-TTS (online) + Piper (offline fallback)
**Date:** 2026-10-25  
**Choice:** Edge-TTS with `hi-IN-SwaraNeural` voice as primary, Piper as offline fallback.  
**Alternatives considered:** gTTS (no streaming), Coqui TTS (resource-heavy).  
**Reason:** Edge-TTS is free (uses MS Edge's speech service, no API key), supports streaming, and has high-quality Hindi and Indian English voices. Piper provides fully offline capability with lighter resource usage.

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
