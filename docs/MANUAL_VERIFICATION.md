# BolSamajh — Hardware & Live Verification Guide

> **Important Rule:** To maintain strict empirical honesty, features requiring physical microphone input, physical hotkey presses, air-gapped physical disconnection, or live third-party cloud agents are marked as **`Implemented, untested on hardware`** in the README until you complete these checklists and paste the results back.

---

## 📋 Instructions for Manav

Please execute the following 4 verification workflows on your machine (NVIDIA RTX 3060 Ti GPU, Windows 11). Once completed, fill in the **[Verification Results Template](#-verification-results-template)** at the bottom of this file and paste it into the conversation.

---

### Test 1: Hands-Free Voice Barge-In (Speakers & Headphones)

Measure whether microphone echo cancellation and Silero VAD reliably prevent false interruptions while allowing deliberate speech barge-in.

#### 1.1 Headphone Mode (10 Minutes)
1. Plug in and wear your headphones (ensure playback goes through headphones).
2. Sit in your normal workspace (remain silent during playback to measure false triggers).
3. Run the automated measurement script:
   ```powershell
   .\venv\Scripts\python scripts/measure_bargein.py --mode headphones --duration 600
   ```
4. Confirm `benchmark_data/bargein_measurements.json` is generated.
5. Acceptance threshold: $\le 1$ false trigger across 10 minutes.

#### 1.2 Speaker Mode (10 Minutes)
1. Unplug headphones or switch playback to laptop / desktop speakers at normal listening volume (~60%).
2. Run the measurement script in speaker mode:
   ```powershell
   .\venv\Scripts\python scripts/measure_bargein.py --mode speakers --duration 600
   ```
3. During playback, deliberately speak over sentence #5 (*"Wait, explain that again"*).
4. Verify playback immediately cuts off when you speak.
5. Acceptance threshold: $\le 3$ false triggers across 10 minutes; intentional speech interrupts within 500 ms.

---

### Test 2: Global Hotkeys & Desktop Selection Editing

Verify that hotkeys trigger without collisions, text inserts cleanly at the cursor, and keyboard modifiers (Alt, Shift, Ctrl) do not get stuck.

#### 2.1 Push-to-Talk Dictation (`Alt+Shift+Space`)
1. Launch BolSamajh desktop app:
   ```powershell
   .\venv\Scripts\python -m bolsamajh
   ```
2. Wait for HUD notification: **"BolSamajh Ready ✓"**.
3. **Notepad Test:**
   - Open Notepad. Focus cursor on a blank line.
   - Hold `Alt+Shift+Space`. Verify overlay turns green with 🎤 *"Listening..."*.
   - Speak: *"Yaar kal presentation 10:30 AM par review karni hai, 5000 rupaye budget finalize kar do."*
   - Release hotkey.
   - Verify text inserts at cursor with currency symbol: `₹5,000`.
4. **VS Code Test:**
   - Open VS Code. In an open code file or markdown scratchpad, hold `Alt+Shift+Space`.
   - Speak a technical sentence: *"Function me try except block add karo aur error log print karo."*
   - Release hotkey. Verify text inserts cleanly without opening VS Code command palette or keybinding conflicts.
5. **Chrome / Browser Test:**
   - Open Google Chrome. Focus on any input box (e.g. search box or email draft).
   - Hold `Alt+Shift+Space`, speak, and release.
   - Confirm text inserts without triggering Chrome DevTools (Ctrl+Shift+I or Shift collision).
6. **Modifier Check:** Press regular typing keys (A, B, C, Enter). Confirm `Alt` or `Shift` is NOT stuck in active state.

#### 2.2 In-Place Voice Selection Edit (`Alt+Shift+C`)
1. In Notepad or an email draft, write:
   `i am writing to say we cannot accept the terms because price too high`
2. Select the sentence with your mouse.
3. Hold `Alt+Shift+C`, overlay turns blue: ✏️ *"Listening for command..."*.
4. Speak: *"Make this polite, concise, and professional."*
5. Release hotkey.
6. Verify the selected text is replaced in-place with polished text.
7. Confirm previous clipboard contents or sentinels do not leak.

---

### Test 3: 100% Offline Air-Gapped Mode

Verify that BolSamajh functions completely offline without any internet connection.

#### 3.1 Setup
1. Ensure Ollama is running locally with Gemma 3:
   ```powershell
   ollama run gemma3:4b
   ```
2. Configure `.env` for strict offline mode:
   ```ini
   BOLSAMAJH_TTS_ENGINE=piper
   BOLSAMAJH_LLM_ENGINE=ollama
   BOLSAMAJH_LLM_AUTO_FALLBACK=false
   ```
3. Disconnect Wi-Fi / unplug Ethernet cable (turn off all internet access).

#### 3.2 Offline Verification
1. Launch the app:
   ```powershell
   .\venv\Scripts\python -m bolsamajh
   ```
2. **Offline Dictation:** Hold `Alt+Shift+Space`, speak a sentence in Hinglish. Confirm text appears at cursor using local `faster-whisper`.
3. **Offline Document Q&A:**
   - Press `Alt+Shift+D`, select a sample PDF (e.g. `docs/sample_policy.pdf` or any text document).
   - Press `Alt+Shift+A`, speak: *"Is document ka main topic kya hai?"*
   - Verify local FAISS retrieval finds relevant chunks, Ollama generates the answer, and local Piper TTS synthesizes speech without throwing network errors.
4. Reconnect network after test.

---

### Test 4: Live Bolna Cloud Agent Integration

Verify that a live voice agent running on the Bolna platform can use BolSamajh's OpenAI-compatible TTS gateway via a secure tunnel.

#### 4.1 Launch BolSamajh Gateway
```powershell
# In Terminal 1:
$env:BOLSAMAJH_API_KEY="test-bolna-key-2026"
.\venv\Scripts\python -m uvicorn bolsamajh.web.server:app --host 127.0.0.1 --port 8000
```

#### 4.2 Expose via Cloudflare Tunnel
```powershell
# In Terminal 2:
cloudflared tunnel --url http://127.0.0.1:8000
```
*Note the public HTTPS URL generated (e.g. `https://random-slug.trycloudflare.com`).*

#### 4.3 Configure Bolna Agent
1. Open your Bolna Dashboard (or local Bolna orchestrator).
2. Under Agent **Synthesizer** settings, choose **Custom OpenAI Provider**:
   - **Base URL:** `https://<YOUR-TUNNEL-URL>/v1`
   - **API Key:** `test-bolna-key-2026`
   - **Model:** `tts-1`
   - **Voice:** `swara` (or `neerja` / `piper`)
3. Place a test call using the web call simulator or phone number.
4. Verify:
   - Terminal 1 logs show `POST /v1/audio/speech 200 OK`.
   - Voice agent speaks with natural Indian pronunciation.

---

## 📝 Verification Results Template

Copy and paste this section into the chat with your measured numbers:

```markdown
### BolSamajh Manual Verification Results

| Test Area | Hardware / Environment | Result (PASS / FAIL) | Notes / Measured Figures |
| :--- | :--- | :---: | :--- |
| **1.1 Barge-In (Headphones)** | USB Headset, Quiet room | [PASS / FAIL] | False triggers: __ / 10 min (target <= 1) |
| **1.2 Barge-In (Speakers)** | Laptop / Monitor speakers | [PASS / FAIL] | False triggers: __ / 10 min (target <= 3), Interrupt latency: __ ms |
| **2.1 Dictation in Notepad** | Windows 11 Notepad | [PASS / FAIL] | Currency normalization (₹) verified: [Yes / No] |
| **2.2 Dictation in VS Code** | VS Code 1.90+ | [PASS / FAIL] | No hotkey collisions observed: [Yes / No] |
| **2.3 Dictation in Chrome** | Google Chrome | [PASS / FAIL] | DevTools not triggered; modifiers clean: [Yes / No] |
| **2.4 In-Place Voice Edit** | Notepad selection edit | [PASS / FAIL] | Text rewritten in-place without cursor jump: [Yes / No] |
| **3. Offline Air-Gapped Mode**| Wi-Fi disconnected | [PASS / FAIL] | Dictation + Doc QA worked with Piper + Ollama: [Yes / No] |
| **4. Live Bolna Agent Test**  | Cloudflare tunnel | [PASS / FAIL] | Live agent synthesized speech via /v1/audio/speech: [Yes / No] |
```
