# BolSamajh — 2-Minute Judge Evaluation Guide 🇮🇳🎙️

> **Buildathon:** Bolna × Symphony Voice AI Buildathon (October 2026)  
> **Builder:** Manav (Solo Builder, Ahmedabad, India)  
> **Repository:** [https://github.com/P1Manav/BolSamajh](https://github.com/P1Manav/BolSamajh)  
> **License:** MIT License (100% Free & Open Source)  

---

## ⚡ The 2-Minute Live Evaluation Path

You can evaluate BolSamajh in **under 2 minutes** using either the pre-compiled binary or a single command:

### Option 1: Standalone Windows App (Zero Setup)
1. Download **`BolSamajh-windows-x64.zip`** from [GitHub Releases](https://github.com/P1Manav/BolSamajh/releases/tag/v1.1.0).
2. Unzip and double-click **`BolSamajh.exe`**.
3. The Studio Dashboard opens automatically in your browser (with automatic port fallback and health check), and the floating glass pill docks in your system tray.

### Option 2: Run from Cloned Repo
```powershell
python -m bolsamajh
```
*(Automatically tests `/healthz`, starts the server, and launches `http://localhost:8000`)*

---

## 🧪 3 Live Tests in 90 Seconds

### Test 1: Push-to-Talk Dictation (Voice IN)
- On the **Welcome & Setup** tab, click **"Test Speaking Here"** (or hold `Alt+Shift+Space` in Notepad).
- Speak naturally in Hinglish:  
  *"Invoice pe 18 percent GST add karke total pandrah hazar kar do."*
- **Verify:** Transcribed instantaneously with smart filler cleanup and automatic currency formatting (`"Invoice pe 18% GST add karke total ₹15,000 kar do"`).
- Toggle script mode in tray: switch to **Devanagari** for formal Hindi output, or **Roman** for Latin-script Hinglish.

### Test 2: Talk to a PDF with Citations & Barge-In (Voice OUT — The Wedge)
- Drag & drop **`samples/sample_policy.pdf`** into the dropzone (or press `Alt+Shift+D`).
- Ask via microphone or text:  
  *"Kya ICU charges cover hote hain?"*
- **Verify:**  
  1. Spoken Hinglish answer streams back.
  2. Clickable green citation chip **`[Page 1]`** highlights the exact source clause.
  3. Speak aloud while it answers: hands-free voice barge-in cancels speech within 140 ms.
- Ask in Gujarati: *"Maternity benefit ketlu male chhe?"*  
  **Verify:** Spoken Gujarati voice answer with **`[Page 2]`** citation.
- Ask an out-of-document question: *"Space travel cover chhe?"*  
  **Verify:** Clear, honest refusal: *"Yeh document mein nahi hai."*

### Test 3: Sourced Competitor Comparison & Privacy Honesty
- Click the **"Why BolSamajh"** tab in the UI:
  - Review the sourced capability comparison matrix against Wispr Flow (sourced from official vendor docs, retrieved 2026-10-31).
  - Review the transparent **"Where Wispr Flow is Stronger"** section (100+ languages, mature mobile apps, zero GPU footprint).
- Check the **System Architecture Banner**:
  - Shows green **"100% Air-Gapped Offline Mode"** when using Faster-Whisper + Ollama + Piper.
  - Shows amber **"Hybrid Mode"** when using Edge-TTS cloud synthesis.

---

## 📊 Key Verified Metrics (100% Backed by Repo JSON Files)

| Metric | Measured Result | Source Benchmark File |
| :--- | :--- | :--- |
| **Real Speech Hinglish WER** | **38.52%** (large-v3-turbo) / **50.73%** (medium) | `benchmark_data/benchmark_results.json` |
| **Real Speech Hindi WER** | **25.98%** (FLEURS `hi_in`) | `benchmark_data/benchmark_results.json` |
| **Inference Latency** | **573.0 ms** mean / **0.079x RTF** (RTX 3060 Ti) | `benchmark_data/hardware_measurements.json` |
| **Document Retrieval Hit@1** | **89.0%** (98.0% Hit@3, 22.3 ms latency) | `benchmark_data/retrieval_benchmark.json` |
| **Calibrated Refusal Threshold** | **0.785** (F1: 0.8685, Precision: 81.9%) | `benchmark_data/retrieval_benchmark.json` |
| **Voice Barge-In Stop Latency** | **140 ms** (0 false triggers in 10-min noise) | `benchmark_data/bargein_measurements.json` |
| **Mandatory Cloud Spend** | **$0.00** (Zero spend, 100% MIT open source) | Fully self-hosted |

---

## 🤖 Bolna Agent Gateway Integration

BolSamajh serves as a drop-in OpenAI-compatible audio gateway for Bolna agents:
- `POST /v1/audio/transcriptions`: Batch Hinglish STT
- `POST /v1/audio/speech`: TTS proxying Edge-TTS and offline Piper ONNX
- `WS /v1/realtime`: Realtime audio WebSocket protocol

Expose locally via Cloudflare tunnel: `cloudflared tunnel --url http://127.0.0.1:8000` and set base URL in your Bolna agent configuration.

