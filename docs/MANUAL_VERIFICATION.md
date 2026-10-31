# BolSamajh — Final Manual Verification & Hardware Checklist

> **Buildathon Honesty Policy:** Features requiring physical audio transducers (microphone, speakers, headphones), physical user hotkey presses, third-party cloud keys (Gemini), physical air-gap disconnection, or telephony trunks are pending manual verification by the repository owner. This document is the complete, single-source-of-truth checklist to execute on the host machine (NVIDIA RTX 3060 Ti GPU, Windows 11).

---

## 🚀 Pre-Flight Setup & Environment Check

1. **Activate Virtual Environment & Check `.env`:**
   ```powershell
   cd <path-to-repo>\BolSamajh
   .\venv\Scripts\activate
   # Ensure .env exists with any desired overrides:
   cp .env.example .env  # if not already present
   ```
2. **Start Local Ollama Engine:**
   ```powershell
   # In a separate terminal:
   ollama run gemma3:4b
   ```
3. **Verify CUDA Setup:**
   ```powershell
   python -c "from bolsamajh.utils.cuda_setup import auto_detect_device; print(auto_detect_device())"
   # Should output: ('cuda', 'int8_float16', 'large-v3-turbo')
   ```

---

## 📊 Phase A: Re-Running Automated Evidence Scripts on Host Hardware

Execute each script to regenerate empirical logs in `docs/evidence/`:

### 1. Hardware Latency, TTFA & RTF
```powershell
python scripts/measure_hardware.py
```
- **What it checks:** GPU specs, synthetic audio STT latency, VRAM allocation delta, E5 retrieval latency, Edge-TTS first packet, and true end-to-end TTFA (question end → first audio sample played).
- **Target Output:** Updates `benchmark_data/hardware_measurements.json`.

### 2. Voice Barge-In Acoustic Measurement
```powershell
# Headphone mode:
python scripts/measure_bargein.py --mode headphones --duration 600
# Speaker mode:
python scripts/measure_bargein.py --mode speakers --duration 600
```
- **What it checks:** Measures false interruption triggers during continuous TTS playback.
- **Target Output:** Generated `benchmark_data/bargein_measurements.json` and `docs/evidence/bargein_check.txt`. Target: $\le 1$ false trigger (headphones), $\le 3$ (speakers).

### 3. Desktop Dictation & Win32 Clipboard Verification
```powershell
python scripts/e2e_dictation_test.py
```
- **What it checks:** Automated Notepad launch, real `keybd_event` hotkey injection (`Alt+Shift+Space`), WER against threshold (< 0.25), modifier release check via `GetAsyncKeyState`, and 100% clipboard restoration.
- **Target Output:** Updates `docs/evidence/e2e_dictation.txt`.

### 4. 100% Offline Mode with Network Blocker
```powershell
python scripts/test_offline_mode.py
```
- **What it checks:** Configures offline mode via `load_config()`, activates outbound socket blocker, and drives Piper TTS factory, Faster-Whisper, Ollama LLM, FAISS retriever, and real `DictationPipeline` / `DocQAPipeline`.
- **Target Output:** Updates `docs/evidence/offline_mode.txt` with count of exercised components.

### 5. Multi-Chunk Document QA Pipeline
```powershell
python scripts/e2e_doc_qa_test.py
```
- **What it checks:** Multi-chunk documents (>= 10 chunks each for PDF, DOCX, Web page), production retrieval threshold (0.785), production prompt, page citations, and keyword presence.
- **Target Output:** Updates `docs/evidence/doc_qa_e2e.txt`.

### 6. Table Generation & Verification
```powershell
python scripts/generate_readme_tables.py
python scripts/generate_readme_tables.py --check
```
- **What it checks:** Verifies all tables and numbers in `README.md`, `PROGRESS.md`, `RELEASE_NOTES.md`, and `submission/application_answers.md` match JSON metrics, and generates clean `submission/application_answers_RENDERED.md`.

---

## 🎧 Phase B: Physical Interactive Checks (Human-in-the-Loop)

Launch the desktop application for interactive testing:
```powershell
python -m bolsamajh
```
*(Wait until the HUD displays **"BolSamajh Ready ✓"**)*

### 1. Real-Mic Dictation in Notepad, VS Code & Chrome (`Alt+Shift+Space`)
- **Notepad:** Open Notepad, hold `Alt+Shift+Space`, speak: *"Client presentation kal subah 10:30 baje hai, aur 5000 rupaye advance dena hai."* Release.
  - Verify text inserts at cursor with currency symbol `₹5,000` or `Rs 5,000`.
- **VS Code:** Open a code or markdown file, hold `Alt+Shift+Space`, speak: *"Function me try except block add karo aur error log print karo."* Release.
  - Verify clean insertion without opening command palette or triggering hotkey conflicts.
- **Chrome:** Focus on an input box or address bar, hold `Alt+Shift+Space`, speak, and release.
  - Verify text inserts without opening Chrome DevTools (Ctrl+Shift+I).
- **Modifier Cleanliness:** Type normally (A, B, C, Enter) to ensure `Alt` or `Shift` did not remain stuck down.

### 2. In-Place Voice Selection Editing (`Alt+Shift+C`)
- Write: `i am writing to say we cannot accept the terms because price too high`
- Select the sentence with your mouse.
- Hold `Alt+Shift+C` (HUD shows ✏️ *Processing command*).
- Speak: *"Make this polite, concise, and professional."* Release.
- Verify text is transformed in-place without cursor jumps, and clipboard contents are preserved.

### 3. Talk-to-Document Voice Q&A (`Alt+Shift+D` to load, `Alt+Shift+A` to ask)
- Press `Alt+Shift+D`. Select a sample PDF (`scratch/doc_qa_e2e/sample_policy.pdf`).
- HUD shows *Document Loaded ✓*.
- Hold `Alt+Shift+A`, speak: *"Health checkup aur insurance claim ka kya rule hai?"* Release.
- Verify: Audio response streams back in natural Hinglish citing exact page numbers (e.g. *"Page 3 ke according..."*).
- **Barge-in test:** Speak while audio is playing (or press `Escape`). Audio should stop immediately.

### 4. Listening Test: Roman Hinglish Voice Comparison (Swara vs. Neerja)
- In `.env`, test both voices for Roman Hinglish:
  - Option 1: `BOLSAMAJH_ROMAN_VOICE=en-IN-NeerjaNeural`
  - Option 2: `BOLSAMAJH_ROMAN_VOICE=hi-IN-SwaraNeural`
- Ask: *"Explain policy in Hinglish"*. Perform a by-ear check:
  - Does Neerja pronounce English technical terms better?
  - Does Swara pronounce Hindi grammar better?
  - Record the preferred choice in your submission notes.

### 5. Gujarati Sanity Check
- Set `BOLSAMAJH_DOC_QA_RESPONSE_LANGUAGE=gujarati` in `.env`.
- Ask a Gujarati question about an indexed document or general query: *"ગુજરાતનું પાટનગર કયું છે?"*
- Verify audio plays in Gujarati via `gu-IN-DhwaniNeural`.

### 6. Live Google Gemini API Key Check
```powershell
# Set your Gemini API key in .env or pass via CLI:
python scripts/check_gemini.py --api-key "AIzaSy..."
```
- **What it checks:** Paginates models endpoint (`pageSize=1000` + `nextPageToken`), verifies configured model is present, and runs a live `generateContent` call. Exits 0 on success.

### 7. Tesseract OCR on Scanned Hindi PDF
- Install Tesseract OCR:
  - Download Windows installer from UB-Mannheim: https://github.com/UB-Mannheim/tesseract/wiki
  - During setup, check **Additional script data → Devanagari script** and **Additional language data → Hindi (`hin`)**.
  - Add `C:\Program Files\Tesseract-OCR` to system PATH.
- Test loading a scanned Hindi PDF in BolSamajh (`Alt+Shift+D`).
- Verify text is extracted and indexed for Q&A.

### 8. Strict Physical Air-Gap Disconnection Test
- In `.env`, set:
  ```ini
  BOLSAMAJH_TTS_ENGINE=piper
  BOLSAMAJH_LLM_ENGINE=ollama
  BOLSAMAJH_LLM_AUTO_FALLBACK=false
  ```
- **Physically disconnect Wi-Fi / Ethernet** (turn off network adapter).
- Run `python -m bolsamajh`.
- Dictate a sentence (`Alt+Shift+Space`) and ask a document question (`Alt+Shift+A`).
- Verify 100% on-device speech synthesis via Piper ONNX and Ollama Gemma 3.
- Reconnect network after test.

### 9. Live Bolna Cloud Agent Integration via Tunnel
- Launch BolSamajh web gateway:
  ```powershell
  $env:BOLSAMAJH_API_KEY="test-bolna-key-2026"
  python -m bolsamajh.web.server --port 8000
  ```
- Expose via Cloudflare tunnel (free, no account needed):
  ```powershell
  cloudflared tunnel --url http://127.0.0.1:8000
  ```
- In Bolna Agent settings:
  - Provider: `openai`
  - Base URL: `https://<YOUR-TUNNEL-URL>/v1`
  - API Key: `test-bolna-key-2026`
  - Model: `tts-1`, Voice: `swara` (or `neerja` / `piper`)
- Make a test call from Bolna dashboard web-call simulator and observe gateway logs.

### 10. 90-Second Demo Video Recording
- Follow `submission/demo_script.md` shot-by-shot (~189 spoken words).
- Record in OBS Studio (1920x1080 @ 60fps).
- Upload to YouTube/Loom as Unlisted, copy link to submission form.

---

## 📝 One-Page Verification Results Template

Copy and paste this section into the chat or your submission records upon completion:

```markdown
### BolSamajh Manual Verification Results (RTX 3060 Ti, Windows 11)

| Check | Test Description | Status (PASS / FAIL) | Notes / Measured Value |
| :--- | :--- | :---: | :--- |
| **A.1** | `python scripts/measure_hardware.py` | [PASS / FAIL] | TTFA: ___ ms, RTF: ___x |
| **A.2** | `python scripts/measure_bargein.py` (headphones) | [PASS / FAIL] | False triggers: ___ / 10 min |
| **A.3** | `python scripts/measure_bargein.py` (speakers) | [PASS / FAIL] | False triggers: ___ / 10 min |
| **A.4** | `python scripts/e2e_dictation_test.py` | [PASS / FAIL] | Automated keystroke WER: ___ |
| **A.5** | `python scripts/test_offline_mode.py` | [PASS / FAIL] | Exercised components: ___/7 |
| **A.6** | `python scripts/e2e_doc_qa_test.py` | [PASS / FAIL] | Multi-chunk queries passed: ___/9 |
| **B.1** | Real-mic Dictation (Notepad / VS Code / Chrome) | [PASS / FAIL] | ₹ currency and % formatted cleanly |
| **B.2** | In-Place Voice Selection Edit (`Alt+Shift+C`) | [PASS / FAIL] | In-place text transformation verified |
| **B.3** | Talk-to-Document Intelligence (`Alt+Shift+A`) | [PASS / FAIL] | Grounded answer with page citation |
| **B.4** | Voice Barge-In & Escape Audio Interruption | [PASS / FAIL] | Immediate audio cutoff verified |
| **B.5** | Roman Voice Listening Test (Swara vs Neerja) | [PASS / FAIL] | Preferred voice: [Swara / Neerja] |
| **B.6** | Gujarati Sanity Check (`gu-IN-DhwaniNeural`) | [PASS / FAIL] | Gujarati Q&A audible and clear |
| **B.7** | Gemini Live Key Check (`scripts/check_gemini.py`) | [PASS / FAIL] | Model discovery and generateContent OK |
| **B.8** | Tesseract OCR on Scanned Hindi PDF | [PASS / FAIL] | Scanned PDF text extracted and indexed |
| **B.9** | Physical Air-Gap Disconnection Test | [PASS / FAIL] | Piper + Ollama operated with Wi-Fi off |
| **B.10**| Live Bolna Agent via Tunnel | [PASS / FAIL] | /v1/audio/speech called by Bolna agent |
| **B.11**| 90-Second Demo Video Recorded | [PASS / FAIL] | Link: https://... |
```
