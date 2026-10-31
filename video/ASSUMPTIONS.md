# BolSamajh Video — Assumptions & Engineering Decisions

> **Project:** BolSamajh Product Launch Film (Bolna × Symphony Voice AI Buildathon)  
> **Hard Cap:** 90 seconds (2700 frames at 30 fps)  
> **Policy:** Zero Spend. Free & open-source only. No paid assets.  

---

## 1. Zero Spend & Audio Strategy

- **Voiceover:** Generated using Edge-TTS (`en-IN-NeerjaNeural` or `en-US-ChristopherNeural` or local free TTS) for English voiceover narration, and Microsoft Edge-TTS / Piper for Hinglish/Gujarati/Hindi dialogue. Can be cleanly replaced by user's real voice recording if `video/public/audio/vo.mp3` is provided.
- **Demo Dialogue Audio:** Real audio files synthesized via the app's own TTS engine (`Edge-TTS` and `Piper`) matching the exact test questions and answers from `docs/evidence/` and `submission/demo_script.md`:
  - Dictation: *"Invoice pe 18 percent GST add karke total pandrah hazar kar do."*
  - Document Q&A (Hinglish): *"Kya ICU charges cover hote hain?"* -> *"Page 1 mein likha hai ki core collaboration hours..."* / *"Page 1 ke mutabiq ICU charges cover hote hain."*
  - Document Q&A (Gujarati): *"Maternity benefit ketlu male chhe?"* -> *"Page 2 mujab maternity benefit..."*
  - Out-of-Document: *"Space travel cover chhe?"* -> *"Yeh document mein nahi hai."*
- **Music:** Commented/wired royalty-free layer; no external paid tracks.
- **SFX:** Synthesized pure web audio / WAV beeps, clicks, and swooshes, or clean procedural sound design.

---

## 2. Real Captures vs Faithful Reconstructions

- **Real Screenshots:** Using high-res Playwright captures already generated from the running app in `docs/screens/`:
  - `01_home_dashboard_1440.png`
  - `02_dictate_1440.png`
  - `03_documents_rag_1440.png`
  - `04_voice_commands_1440.png`
  - `05_web_call_1440.png`
  - `07_why_bolsamajh_1440.png`
  - `08_benchmark_1440.png`
  - `webcall_active_1440.png`
- **Reconstructed In-App Action:** The floating desktop overlay HUD pill typing into Notepad is faithfully reconstructed in React with exact styling from `bolsamajh/web/static/` and `docs/evidence/e2e_dictation.txt`.
- **Recording Requests:** Documented in `video/RECORDING_REQUESTS.md` so the user can optionally replace the reconstructed shots with real OBS recordings at their convenience.

---

## 3. Remotion Configuration

- Resolution: 1920×1080
- Frame Rate: 30 fps
- Duration: 2640 frames = 88.0 seconds (well within 85–90s target, strictly under 90s hard cap).
- Composition: `<Composition id="BolSamajhFilm">`
- Fonts: Google Fonts loaded via CSS / `@remotion/google-fonts`: Inter, JetBrains Mono, Noto Sans Devanagari, Noto Sans Gujarati.

