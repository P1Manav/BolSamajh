# Bolna Voice Agent Integration with BolSamajh

This guide explains how to connect an autonomous conversational voice agent built on [Bolna](https://github.com/bolna-ai/bolna) to **BolSamajh**'s open-source Indian voice gateway.

---

## ⚠️ Security Warning: Tunneling and Authentication

> [!CAUTION]
> **NEVER expose BolSamajh (`/v1/*` or web port 8000) through a public tunnel (such as ngrok, Cloudflare Tunnel, or localtunnel) without setting an API key.**
> 
> Unauthenticated public exposure allows external actors to trigger unlimited speech synthesis, scrape loaded documents, and consume server GPU/CPU resources.
> 
> - Set `BOLSAMAJH_API_KEY=your-secure-secret-token` before launching the server.
> - When `BOLSAMAJH_API_KEY` is configured, all `/v1/*` endpoints require the header:
>   `Authorization: Bearer <BOLSAMAJH_API_KEY>`
> - If the server is bound to an interface other than `127.0.0.1` (e.g. `0.0.0.0`) without `BOLSAMAJH_API_KEY` set, it will refuse to start for security reasons.

---

## Architecture & Protocol Compatibility

Bolna orchestrates voice agents using two distinct audio channels:

| Component | Bolna Protocol | BolSamajh Support | Notes |
|:---|:---|:---|:---|
| **Synthesizer (TTS)** | OpenAI-compatible HTTP POST `/v1/audio/speech` | **Supported** | Configured via `synthesizer_base_url` and `synthesizer_key`. Emits 24 kHz MP3 audio using Indian neural voices (`swara`, `neerja`, `dhwani`). |
| **Realtime Transcriber (STT)** | OpenAI Realtime WebSocket protocol (`REALTIME_TRANSCRIBER_URL`) | **Not Implemented** | Bolna's streaming conversational pipeline requires full-duplex WebSocket connections. BolSamajh provides standard batch REST STT (`/v1/audio/transcriptions`), not the realtime WebSocket server. For Bolna agents, use a supported realtime provider (e.g., Deepgram) for STT and BolSamajh for TTS. |

```
┌─────────────────────────────────┐
│           Bolna Agent           │
│        (bolna-ai/bolna)         │
└─────────────────────────────────┘
          │ (TTS Audio Synthesis)
          │ POST /v1/audio/speech
          ▼
┌─────────────────────────────────┐
│        BolSamajh Gateway        │
│   (synthesizer_base_url:        │
│    http://localhost:8000/v1)    │
└─────────────────────────────────┘
```

---

## 1. Starting the BolSamajh Server

Start the web service locally on port 8000:

```bash
# Set your secure gateway key (required if exposing via tunnel)
export BOLSAMAJH_API_KEY="my-secret-bolna-key"

# Launch server with uvicorn
python -m uvicorn bolsamajh.web.server:app --host 127.0.0.1 --port 8000
```

Verify service readiness using the health check endpoint:

```bash
curl -s http://localhost:8000/api/status
```

**Real output:**
```json
{
  "status": "ready",
  "device": "CUDA GPU",
  "stt": "faster-whisper-medium",
  "llm": "fallback(ollama/gemma3:4b -> google-ai/gemini-1.5-flash)",
  "llm_ready": false,
  "tts": "edge-tts",
  "document_loaded": false,
  "document_title": "",
  "refusal_threshold": 0.785
}
```

---

## 2. Verified Endpoint Interactions (Real Commands & Outputs)

### Text-to-Speech (`/v1/audio/speech`)

Bolna's custom synthesizer calls the standard OpenAI speech synthesis endpoint.

```bash
curl -i -X POST http://localhost:8000/v1/audio/speech \
  -H "Authorization: Bearer my-secret-bolna-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "नमस्ते, BolSamajh में आपका स्वागत है।",
    "voice": "swara"
  }' \
  --output test_response.mp3
```

**Real server output:**
```http
HTTP/1.1 200 OK
date: Sun, 25 Oct 2026 12:22:15 GMT
server: uvicorn
content-type: audio/mpeg
transfer-encoding: chunked
```
*Binary result: Writes `test_response.mp3` (25,341 bytes, MPEG ADTS / ID3 audio stream).*

Supported voice mappings:
- `swara` / `hi-IN-SwaraNeural`: Natural Hindi / Hinglish female voice.
- `neerja` / `alloy` / `en-IN-NeerjaNeural`: Indian English accent.
- `dhwani` / `gu-IN-DhwaniNeural`: Gujarati neural voice.

---

### Batch Speech-to-Text (`/v1/audio/transcriptions`)

For batch transcription jobs or file processing:

```bash
curl -s -X POST http://localhost:8000/v1/audio/transcriptions \
  -H "Authorization: Bearer my-secret-bolna-key" \
  -F "file=@benchmark_data/audio/sentence_001.wav" \
  -F "model=whisper-1"
```

**Real output:**
```json
{"text":"यार कल मीटिंग कितने बजे शेडूल की हैं।"}
```

---

## 3. Configuring Bolna Custom Synthesizer

In Bolna's architecture, custom synthesizers are configured using `synthesizer_base_url` and `synthesizer_key` passed in the task definition or injected by the platform:

```json
{
  "agent_config": {
    "agent_name": "Indian Customer Support Agent",
    "tasks": [
      {
        "tools_config": {
          "synthesizer": {
            "provider": "custom",
            "provider_config": {
              "model": "tts-1",
              "voice": "swara",
              "synthesizer_base_url": "http://localhost:8000/v1",
              "synthesizer_key": "my-secret-bolna-key"
            }
          },
          "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "hi"
          }
        }
      }
    ]
  }
}
```

### Self-Hosted Realtime STT Status
- **Status:** **Not Implemented**.
- **Reason:** Bolna's streaming real-time transcription engine connects via WebSockets using `REALTIME_TRANSCRIBER_URL` and `REALTIME_TRANSCRIBER_KEY` conforming to the OpenAI Realtime protocol. BolSamajh implements the offline/batch HTTP REST transcription protocol (`/v1/audio/transcriptions`), but does not provide the OpenAI Realtime WebSocket server.
