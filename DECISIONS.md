# BolSamajh — Decision Log

> Records architectural and tooling decisions with rationale.

## D001: Desktop Shell — Tkinter + pystray + pynput
**Date:** 2026-10-25
**Choice:** Tkinter floating overlay + pystray system tray + pynput/keyboard for global hotkeys.
**Alternatives considered:** Electron (heavy, 200+ MB), PyQt (GPL complications), Tauri (Rust build step).
**Reason:** Zero extra install (Tkinter ships with Python), lightweight (~5 MB total), sufficient for an overlay HUD. Windows-native tray support via pystray.

## D002: STT Primary — faster-whisper `medium`
**Date:** 2026-10-25
**Choice:** faster-whisper with `medium` model, INT8 compute, CUDA device.
**Alternatives considered:** whisper.cpp (needs separate build), OpenAI Whisper (slower, more VRAM), Vosk (lower accuracy for Hinglish).
**Reason:** CTranslate2 backend is 4× faster than original Whisper. `medium` model (~1.5 GB VRAM in INT8) fits alongside LLM on RTX 3060 Ti 8 GB. Language hint `hi` helps with Hinglish. Will benchmark against `large-v3` and AI4Bharat.

## D003: LLM Local — Ollama + gemma3:4b
**Date:** 2026-10-25
**Choice:** Ollama serving gemma3:4b locally.
**Alternatives considered:** llama.cpp direct, Phi-3 (less multilingual), Mistral (English-centric).
**Reason:** Gemma 3 4B has strong multilingual capability including Hindi/English, fits in 8 GB VRAM alongside whisper medium, and Ollama provides a simple HTTP API. Google AI Studio free tier (Gemini 2.0 Flash — 15 RPM, 1M tokens/day free as of Oct 2026) serves as a fallback.

## D004: TTS — Edge-TTS (online) + Piper (offline fallback)
**Date:** 2026-10-25
**Choice:** Edge-TTS with `hi-IN-SwaraNeural` voice as primary, Piper as offline fallback.
**Alternatives considered:** gTTS (no streaming), Coqui TTS (resource-heavy).
**Reason:** Edge-TTS is free (uses MS Edge's speech service, no API key), supports streaming, and has high-quality Hindi voices. Piper provides fully offline capability with lighter resource usage.

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
