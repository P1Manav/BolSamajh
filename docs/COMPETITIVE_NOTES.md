# BolSamajh — Competitive Analysis & Sourced Notes

> **Document Status:** Verified against official vendor documentation.  
> **Retrieval Date:** 2026-10-31  
> **Repository:** [BolSamajh](https://github.com/P1Manav/BolSamajh)  

---

## 1. Wispr Flow — Verified Capabilities & Current Status

**Sources:**  
- [wisprflow.ai](https://wisprflow.ai) (Retrieved 2026-10-31)  
- [wisprflow.ai/india](https://wisprflow.ai/india) (Retrieved 2026-10-31)  

### Languages & Hinglish Support
- Supports **100+ languages**, including Hindi and Gujarati.
- **Explicit Hinglish Support:** Wispr Flow includes dedicated Hinglish support designed for colloquial Hindi + English code-switching.
- **Script Handling:** Wispr Flow provides script options via language selection: selecting "Hindi" outputs Devanagari script, while selecting "Hinglish" outputs Romanized Latin script.

### Pricing Structure
| Tier | Pricing | Stated Features & Limits |
|------|---------|-------------------------|
| **Free** | $0/month | Core dictation in 100+ languages across platforms; ~2,000 words/week desktop cap. |
| **Pro** | $12/mo (billed annually) / $15/mo | Unlimited dictation, custom dictionary, voice shortcuts, Command Mode. |
| **Growth** | $18/mo (billed annually) / $23/mo | Team workspace, centralized billing, SAML/SSO, HIPAA compliance. |
| **Enterprise** | Custom | SCIM provisioning, custom MDM, dedicated support. |

### Privacy & Security
- Option to turn off Dictation Cloud Storage (audio discarded immediately after transcription).
- Data is not used to train AI models when privacy toggles are enabled.
- TLS 1.2+ encryption in transit, AES-256 encryption at rest; SOC 2 Type II and ISO 27001 certified.

### Features
- **AI-Powered Cleanup:** Automatic disfluency/filler removal ("um", "ah", "matlab"), context-aware punctuation and casing.
- **Command Mode (Voice Editing):** Voice-driven text transformation over highlighted text (shorten, elaborate, change tone, fix formatting).
- **Universal Typing:** Injects dictated text at the active cursor across desktop and mobile applications.

### What Wispr Flow Does NOT Have (Verified)
- **Document-Grounded Voice Q&A:** Wispr Flow does not include a built-in document reader, RAG pipeline, or PDF/DOCX conversational layer with verifiable page/section citations and out-of-document refusal.
- **Local / Air-Gapped Execution:** Requires an active internet connection to transcribe audio through cloud inference servers. Cannot run 100% offline or on air-gapped workstations.
- **Open-Source & Self-Hostable:** Proprietary software; cannot be audited, modified, or self-hosted by enterprise or healthcare organizations.

---

## 2. Where Wispr Flow is Stronger

To maintain absolute credibility and transparent engineering standards, we clearly acknowledge where Wispr Flow outperforms BolSamajh:

1. **Cross-Platform Maturity:** Native desktop and mobile applications for macOS, Windows, iOS, and Android.
2. **Language Breadth:** Production models for 100+ languages compared to BolSamajh's focus on Hinglish, Hindi, Gujarati, and English.
3. **Hardware Independence:** Runs entirely in the cloud, requiring minimal CPU/RAM and no local GPU.
4. **Team & Enterprise Workspaces:** Integrated SSO/SAML, centralized administration, and shared dictionaries.
5. **Meeting Intelligence:** Built-in AI Notetaker for meeting transcription and summarization.

---

## 3. What Genuinely Differentiates BolSamajh

| Feature | Wispr Flow | BolSamajh |
|---------|------------|-----------|
| **License & Auditability** | Proprietary closed-source | **100% Open Source (MIT)** |
| **Cost** | Free (capped ~2k wds/wk) / $12–$15/mo | **$0.00 / Zero mandatory spend** |
| **Air-Gapped / Offline** | Cloud-dependent | **100% Offline Mode** (Faster-Whisper + Piper + Ollama) |
| **Talk to Documents (RAG)** | None (requires external tools) | **Built-in Voice Doc Q&A** with page citations & refusal |
| **Voice Barge-In** | N/A | **Silero VAD Voice Interruption** during speech playback |
| **Script Control** | Implicit (Hindi vs Hinglish) | **Explicit 3-way toggle** (Natural / Roman / Devanagari) |
| **Indian Normalization** | General formatting | **Targeted ₹ currency, GST %, Lakh/Crore, Indian dates** |
| **Voice Agent Gateway** | None | **Drop-in OpenAI-compatible gateway** for Bolna agents |
| **Benchmark Transparency** | Proprietary benchmarks | **Public, reproducible benchmark** with raw + norm WER |

---

## 4. Code Signing & Foundation Programs

**Source:** [signpath.org](https://signpath.org) (Retrieved 2026-10-31)

- **SignPath Foundation OSS Programme:** Provides free code-signing certificates and CI integration for open-source projects.
- **Criteria:** OSI-approved open source license, no malware/adware/PUPs, no commercial dual-licensing, public repository with active development, releases built via public CI.
- **Current Status for BolSamajh:** BolSamajh meets the technical qualification criteria (MIT license, public GitHub repo, GitHub Actions CI). Applying requires project maintainer authorization and identity verification; for this release, Windows binaries use SHA-256 checksums and standard SmartScreen user guidance.

---

## 5. Sponsor STT & Indic Speech Ecosystem

### Sarvam AI
- **Source:** [sarvam.ai](https://sarvam.ai) (Retrieved 2026-10-31)
- **Pricing:** Standard STT at ₹30/hour (~₹0.50/minute); STT + Translation at ₹30/hour.
- **Free Tier:** Developer signup credits (promotional, typically ₹100–₹1,000) that do not expire.
- **Rate Limits:** 60 req/min (REST), 20 concurrent connections (WebSocket).

### Deepgram
- **Source:** [deepgram.com](https://deepgram.com) (Retrieved 2026-10-31)
- **Free Tier:** $200 one-time credit upon developer account registration (no credit card required). One-time credit, not recurring monthly.
- **Pricing:** Nova-3 pre-recorded ~\$0.0043/min; streaming ~\$0.0048–\$0.0077/min.

### AI4Bharat (IndicConformer & IndicWhisper)
- **Source:** [huggingface.co/collections/ai4bharat](https://huggingface.co/collections/ai4bharat/indicconformer-66d9e933a243cba4b679cb7f) (Retrieved 2026-10-31)
- **Models:** IndicConformer 600M multilingual supporting all 22 scheduled Indian languages; open model weights on Hugging Face.
- **Usage:** Apache 2.0 / MIT compatible open research weights; deployable via Hugging Face Transformers and NeMo.

### Piper TTS (Indic Voices)
- **Source:** [github.com/rhasspy/piper](https://github.com/rhasspy/piper) (Retrieved 2026-10-31)
- **Hindi (`hi_IN`):** Medium quality ONNX model (`hi_IN-pratham-medium`), 22.05 kHz, fast CPU inference.
- **Gujarati (`gu_IN`):** Community Rasa Gujarati ONNX model (~63 MB).

