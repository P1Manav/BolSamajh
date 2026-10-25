# Bolna Agent Integration with BolSamajh

This guide explains how to connect an autonomous voice agent built on [Bolna](https://bolna.ai) to **BolSamajh**'s open-source Hinglish STT and natural Indian TTS gateway.

---

## Architecture Overview

Bolna agents support OpenAI-compatible audio protocol endpoints for custom speech-to-text and text-to-speech providers.

BolSamajh exposes OpenAI-standard endpoints at:
- **STT (Speech-to-Text):** `POST http://localhost:8000/v1/audio/transcriptions`
- **TTS (Text-to-Speech):** `POST http://localhost:8000/v1/audio/speech`

```
┌─────────────────────────────────┐        OpenAI Audio Protocol         ┌─────────────────────────────────┐
│           Bolna Agent           │ ───────────────────────────────────> │        BolSamajh Gateway        │
│          (bolna.ai)             │ <─────────────────────────────────── │      (localhost:8000/v1)        │
└─────────────────────────────────┘   /v1/audio/transcriptions (Hinglish)└─────────────────────────────────┘
                                      /v1/audio/speech (Swara/Neerja/Dhwani)
```

---

## 1. Start BolSamajh Server

Start the BolSamajh web service locally:

```bash
# In BolSamajh virtual environment
python -m uvicorn bolsamajh.web.server:app --port 8000
```

Verify that the health check responds:
```bash
curl http://localhost:8000/api/status
```

---

## 2. Testing the Endpoints Locally

### STT Transcription Test
```bash
curl -X POST http://localhost:8000/v1/audio/transcriptions \
  -F "file=@benchmark_data/synthetic_stress/clip_001.wav" \
  -F "model=whisper-1"
```
**Response:**
```json
{"text": "Is month ka electricity bill kitna aaya hai?"}
```

### TTS Speech Synthesis Test
```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "tts-1", "input": "Aapka claim approve ho gaya hai.", "voice": "alloy"}' \
  --output test_response.mp3
```

---

## 3. Configuring Bolna Agent

In your Bolna agent definition (`agent.json` or through Bolna Studio):

```json
{
  "agent_config": {
    "agent_name": "BolSamajh Customer Care",
    "tasks": [
      {
        "tools_config": {
          "transcriber": {
            "provider": "custom",
            "model": "whisper-1",
            "base_url": "http://localhost:8000/v1",
            "language": "hi"
          },
          "synthesizer": {
            "provider": "custom",
            "model": "tts-1",
            "base_url": "http://localhost:8000/v1",
            "voice": "hi-IN-SwaraNeural"
          }
        }
      }
    ]
  }
}
```

> **Note on Cloud Deployments:** If your Bolna agent runs on the Bolna cloud (`cloud.bolna.ai`), you can expose BolSamajh's local port 8000 using a secure tunnel like Cloudflare Tunnel (`cloudflared tunnel`) or ngrok (`ngrok http 8000`) and set `base_url` to your tunnel URL.
