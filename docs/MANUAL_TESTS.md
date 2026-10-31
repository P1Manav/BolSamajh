# BolSamajh — Human-Only Manual Testing & Final Steps Guide

> **Target completion time for repository owner:** ≤ 45 minutes total.  
> All automated unit tests (146/146), integration pipelines, Playwright crawls, offline socket blockers, and RAG document tests are already **100% verified green** in [`docs/TEST_REPORT.md`](TEST_REPORT.md).  
> The tasks below require physical hardware transducers (microphone, room speakers), video capture, or user secrets (signing key).

---

## ⏱️ Human Verification Checklist Overview

| # | Task | Description | Est. Time | Script / Path |
|---|---|---|:---:|---|
| **1** | **Physical Mic & Speaker Test** | Verify desktop overlay, audio recording, and live voice playback | 5 mins | `python -m bolsamajh` |
| **2** | **100-Clip Human Hinglish Recording** | Record 100 sentences to publish verified human benchmark results | 20 mins | `python -m bolsamajh.benchmark.record_tool` |
| **3** | **Android APK Keystore Signing** | Generate keystore & configure release secret (or use debug APK) | 5 mins | `keytool` |
| **4** | **90-Second Demo Video Recording** | Screen record the live demo following the exact shot list | 15 mins | `submission/demo_script.md` |

**Total Estimated Human Time: ~45 Minutes**

---

## 1. Physical Microphone & Speaker Smoke Test (5 Mins)

1. Launch BolSamajh with local Ollama running:
   ```powershell
   ollama run gemma3:4b
   python -m bolsamajh
   ```
2. The Studio Web Dashboard will open automatically at `http://127.0.0.1:8000`.
3. Click **"Start Overlay"** in the top-right navbar. A compact glowing floating pill will appear on your desktop.
4. Open Notepad (`notepad.exe`).
5. Hold down `Alt + Shift + Space` and say:
   > *"Meeting kal subah 10 baje postpone ho gayi matlab 500 rupees extra lagenge"*
6. Release the keys. Verify:
   - Floating pill shows `thinking` -> `done`.
   - Notepad receives: `Meeting kal subah 10 baje postpone ho gayi matlab ₹500 extra lagenge`.
   - Your prior clipboard is untouched.
7. Switch to the Web Studio, click **"Web Call"** tab, load `sample_policy.pdf`, click **"Start Call"**, and ask:
   > *"What are the core collaboration hours?"*
8. Listen to the streaming spoken response with citation (`Page 1`), then speak to test live **barge-in** interruption.

---

## 2. 100-Clip Human Hinglish Recording Flow (20 Mins)

The competition requires distinguishing between synthetic TTS benchmark audio and real human speech. We have provided a streamlined recorder:

1. Connect your microphone and run:
   ```powershell
   python -m bolsamajh.benchmark.record_tool
   ```
2. The interactive terminal tool will present each of the 100 benchmark sentences one by one:
   - Press `[Space]` to start recording.
   - Read the sentence naturally at conversational pace.
   - Press `[Space]` to stop and preview.
   - Press `[Enter]` to save and advance to the next sentence (or `[R]` to re-record).
3. Once all 100 clips are saved into `benchmark_data/human_audio/`, run the auto-evaluator:
   ```powershell
   python -m bolsamajh.benchmark.evaluate_human
   python scripts/generate_readme_tables.py
   ```
4. This will calculate your personal human WER and CER metrics and update the benchmark tables with verified human empirical data.

---

## 3. Android APK Keystore Signing (5 Mins)

GitHub Actions builds `BolSamajh-Android.apk` automatically with debug signing. If you wish to release a production-signed APK:

1. Open PowerShell and generate a release keystore:
   ```powershell
   keytool -genkey -v -keystore bolsamajh-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias bolsamajh
   ```
   *(Enter a secure password when prompted and remember it).*
2. Convert the keystore to base64:
   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("bolsamajh-release.jks")) | Set-Clipboard
   ```
3. In your GitHub repository:
   - Go to **Settings → Secrets and variables → Actions**.
   - Add Secret `ANDROID_KEYSTORE_BASE64`: Paste from clipboard.
   - Add Secret `ANDROID_KEYSTORE_PASSWORD`: Keystore password.
   - Add Secret `ANDROID_KEY_ALIAS`: `bolsamajh`.
   - Add Secret `ANDROID_KEY_PASSWORD`: Key password.
4. Future git release tags will now build and sign `BolSamajh-Android.apk` automatically.

---

## 4. 90-Second Demo Video Recording (15 Mins)

Use OBS Studio or Windows Game Bar (`Win + G`):

1. Set resolution to **1920x1080** and microphone audio to clear voice.
2. Follow the exact time-coded shot list in [`submission/demo_script.md`](../submission/demo_script.md):
   - **0:00–0:10:** Problem hook: Show Wispr Flow pricing vs 500M Hinglish speakers.
   - **0:10–0:30:** Dictate into Notepad with `Alt+Shift+Space`: Show ₹ currency formatting & script switching.
   - **0:30–1:00:** Talk-to-Document: Ask question on `sample_policy.pdf`, show `[Page 1]` chip, interrupt with barge-in, ask in Gujarati, show refusal on ungrounded query.
   - **1:00–1:15:** Turn Wi-Fi off: Show 100% offline air-gapped badge in Web Studio and the benchmark table.
   - **1:15–1:30:** Web Call mode, Android companion pairing, and GitHub Release installer button.
3. Upload to YouTube (Unlisted) or Loom and paste the link into the buildathon submission form!
