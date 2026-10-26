# Bolna Voice Agent Integration with BolSamajh

> **Integration Status:** **Verified locally with Bolna package client; not tested on Bolna cloud.**  
> The gateway endpoints (`/v1/audio/speech`, `/v1/audio/transcriptions`, and `/v1/realtime?intent=transcription`) were tested directly using Bolna's own `OPENAISynthesizer` and OpenAI Realtime WebSocket protocol client against a running BolSamajh server. Empirical proof is committed at [docs/evidence/bolna_client_check.txt](file:///d:/Projects/BolSamajh/docs/evidence/bolna_client_check.txt). Testing against a live call from the Bolna cloud orchestrator was not performed as it requires a Bolna cloud account and telephone telephony setup.

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
| **Synthesizer (TTS)** | OpenAI-compatible HTTP POST `/v1/audio/speech` | **Verified** ([evidence](file:///d:/Projects/BolSamajh/docs/evidence/bolna_client_check.txt)) | Tested directly using Bolna's `OPENAISynthesizer` client code. Configured via `synthesizer_base_url` and `synthesizer_key`. Proxies Microsoft Edge-TTS with Indian neural voices (`swara`, `neerja`, `dhwani`), or 100% offline local neural voice (`piper`). Verified playable output via PyAV for Hindi and English. |
| **Batch Transcriber (STT)** | OpenAI HTTP POST `/v1/audio/transcriptions` | **Verified** ([evidence](file:///d:/Projects/BolSamajh/docs/evidence/bolna_client_check.txt)) | Tested using OpenAI client against BolSamajh `/v1/audio/transcriptions` on benchmark clips. |
| **Realtime Transcriber (STT)** | OpenAI Realtime WebSocket protocol (`/v1/realtime?intent=transcription`) | **Verified** ([evidence](file:///d:/Projects/BolSamajh/docs/evidence/bolna_client_check.txt)) | Minimal Realtime-compatible transcription WebSocket supporting Bolna's message flow: `session.update`, `input_audio_buffer.append` (24 kHz linear16 PCM), `input_audio_buffer.commit`, and `conversation.item.input_audio_transcription.completed`. Powered by local faster-whisper. |

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
│   (realtime transcriber:        │
│    ws://localhost:8000/v1/realtime)
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
  "llm": "fallback(ollama/gemma3:4b -> google-ai/gemini-3.5-flash)",
  "llm_ready": false,
  "tts": "edge-tts",
  "document_loaded": false,
  "document_title": "",
  "refusal_threshold": 0.785
}
```

---

### 1.1 Using the Web UI with BOLSAMAJH_API_KEY Configured

When `BOLSAMAJH_API_KEY` is configured on the server, the Web UI on `http://localhost:8000` remains fully functional while protecting your endpoints against unauthenticated access:

1. **Exempt Endpoints:** The root page (`/`), static assets (`/static/*`), and health check (`/api/status`) are public and load without requiring authentication.
2. **In-Memory Key Input:** In the top navigation bar, enter your configured key into the **API Key** field and click **Set Key** (or press Enter).
   - The key is retained **strictly in memory** for the browser session. It is never stored in `localStorage`, `sessionStorage`, or cookies.
   - Once entered, a green `✓ Set` indicator is displayed.
3. **Authenticated Operations:** All protected API endpoints (`/api/documents/upload`, `/api/documents/url`, `/api/qa`, `/api/qa/voice`, `/api/command`) automatically send `Authorization: Bearer <key>`.
4. **Authenticated Audio Playback (Blob URLs):** Standard HTML `<audio src="...">` elements cannot send HTTP request headers. To prevent 401 Unauthorized errors during playback, the Web UI fetches audio data via an authenticated `fetchWithAuth()` request and converts it into a client-side Blob URL (`URL.createObjectURL(blob)`).
5. **Clear Error Feedback:** If any API request encounters HTTP 401 Unauthorized, the UI displays an alert banner, highlights the key input, and focuses the field so you can enter the correct key.

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
- `swara` / `hi-IN-SwaraNeural`: Natural Hindi / Hinglish female voice (Microsoft Edge-TTS cloud service).
- `neerja` / `alloy` / `en-IN-NeerjaNeural`: Indian English accent (Microsoft Edge-TTS cloud service).
- `dhwani` / `gu-IN-DhwaniNeural`: Gujarati neural voice (Microsoft Edge-TTS cloud service).
- `piper` / `piper-pratham` / `hi_in-pratham-medium`: 100% offline local neural voice using ONNX (`hi_IN-pratham-medium`).

> [!NOTE]
> **Cloud vs. Offline TTS:** The default voices proxy Microsoft Edge-TTS (an unofficial cloud endpoint). For 100% offline air-gapped deployments where audio must never leave the machine, set `voice="piper"` or `model="piper"` to route speech synthesis directly through local Piper ONNX models without network requests.

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

---

## 4. Live Verification Guide (For Developer / User)

Follow these exact steps to test BolSamajh against a live Bolna agent:

### Step 1: Start the BolSamajh Gateway with an API Key
```bash
# Terminal 1: Run BolSamajh with gateway security enabled
export BOLSAMAJH_API_KEY="test-bolna-key-2026"
python -m uvicorn bolsamajh.web.server:app --host 127.0.0.1 --port 8000
```

### Step 2: Expose the Gateway via Secure Tunnel
Use either `cloudflared` (recommended, free, no account needed) or `ngrok`:

**Option A (Cloudflare Tunnel):**
```bash
# Terminal 2:
cloudflared tunnel --url http://127.0.0.1:8000
```
Copy the assigned tunnel URL (e.g., `https://random-words.trycloudflare.com`).

**Option B (ngrok):**
```bash
# Terminal 2:
ngrok http 8000
```
Copy the assigned forwarding URL (e.g., `https://xyz.ngrok-free.app`).

### Step 3: Test Tunnel Connectivity
Verify the tunnel forwards correctly:
```bash
curl -s https://<YOUR-TUNNEL-URL>/api/status
```

### Step 4: Configure the Agent on Bolna Platform
1. Log in to your Bolna Dashboard (or local Bolna instance).
2. Create or open an agent.
3. In **Voice / Synthesizer Settings**, select **Custom OpenAI-Compatible Provider**.
4. Set the following fields:
   - **Base URL:** `https://<YOUR-TUNNEL-URL>/v1`
   - **API Key:** `test-bolna-key-2026`
   - **Model:** `tts-1`
   - **Voice:** `swara` (for Hindi/Hinglish) or `neerja` (for Indian English)
5. Save the agent configuration.

### Step 5: Execute a Live Call & Verify
Trigger a test call from the Bolna web simulator or dial the connected phone number.

### 📋 Live Verification Checklist (Copy & Paste Back)
```markdown
### Bolna Live Verification Checklist
- [ ] Tunnel connectivity verified: `curl https://<YOUR-TUNNEL-URL>/api/status` returns status "ready".
- [ ] Manual endpoint test: `curl -X POST https://<YOUR-TUNNEL-URL>/v1/audio/speech ...` returns audio file.
- [ ] Bolna agent dashboard accepts custom synthesizer base URL and API key without validation error.
- [ ] Live call initiates speech synthesis request to `/v1/audio/speech`.
- [ ] BolSamajh server logs show HTTP 200 on `POST /v1/audio/speech` during the conversation.
- [ ] Synthesized audio plays back clearly in the Bolna call without clipping or silence.
```
