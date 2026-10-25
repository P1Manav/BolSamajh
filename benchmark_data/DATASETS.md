# BolSamajh — Speech & Evaluation Datasets

This document records the exact sources, licenses, and access terms of all datasets used for training, benchmarking, and evaluating the BolSamajh speech-to-text pipeline, adhering to the Zero-Spend and No-Manual-Data-Collection guidelines.

---

## 1. HiACC Adult Test Eval (Real Hindi-English Code-Switched Speech)

- **Dataset Identifier:** `Trelis/hiacc-adult-test-eval` (derived from Singh et al., *HiACC: Hindi-English Accent & Code-switching Corpus*)
- **Repository URL:** [https://huggingface.co/datasets/Trelis/hiacc-adult-test-eval](https://huggingface.co/datasets/Trelis/hiacc-adult-test-eval)
- **License:** Creative Commons Attribution 4.0 International (**CC-BY-4.0**)
  - Verified on official Hugging Face dataset card (`license: cc-by-4.0`).
  - Permissive for benchmarking, commercial/academic evaluation, and reproduction with attribution.
- **Access Terms:** Completely open. Non-gated, no authentication or approval required.
- **Content & Characteristics:**
  - 664 real speech recordings from adult Indian speakers speaking spontaneous and read Hindi-English code-switched sentences.
  - Includes detailed per-clip metadata: code-switch point count (`code_switch_count`), English word count (`num_english_words`), Hindi word count (`num_hindi_words`), speaker gender, and duration.
- **Usage in BolSamajh:** Primary real-world evaluation benchmark for intra-sentence code-switching and conversational Hinglish recognition.

---

## 2. Google FLEURS — Hindi (`hi_in`)

- **Dataset Identifier:** `google/fleurs` (Hindi split `hi_in`)
- **Reference Publication:** Conneau et al., *"FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech"*, IEEE/ACM Transactions on Audio, Speech, and Language Processing (2022).
- **Repository URL:** [https://huggingface.co/datasets/google/fleurs](https://huggingface.co/datasets/google/fleurs)
- **License:** Creative Commons Attribution 4.0 International (**CC-BY-4.0**)
  - Verified on official Google dataset repository.
- **Access Terms:** Open access, un-gated.
- **Content & Characteristics:**
  - High-fidelity recordings (16 kHz) of native Hindi speakers reading multilingual parallel sentences.
  - Contains natural modern Hindi with contemporary English loanwords (technology, institutions, places).
- **Usage in BolSamajh:** Real read-speech Hindi baseline evaluation for standard pronunciation, phonetic accuracy, and CER/WER comparison.

---

## 3. Google FLEURS — Gujarati (`gu_in`)

- **Dataset Identifier:** `google/fleurs` (Gujarati split `gu_in`)
- **Reference Publication:** Conneau et al., Google Research (2022).
- **Repository URL:** [https://huggingface.co/datasets/google/fleurs](https://huggingface.co/datasets/google/fleurs)
- **License:** Creative Commons Attribution 4.0 International (**CC-BY-4.0**)
- **Access Terms:** Open access, un-gated.
- **Content & Characteristics:**
  - 16 kHz recordings of native Gujarati speakers reading domain-balanced sentences.
- **Usage in BolSamajh:** Evaluates regional language generalization and Gujarati speech recognition in bilingual workflows.

---

## 4. BolSamajh Synthetic Stress Test Set (100 Sentences)

- **Dataset Path:** `bolsamajh/benchmark/sentences.py` & `benchmark_data/audio/`
- **Creation Mechanism:** Curated test sentences generated across 5 critical failure modes:
  1. Everyday casual conversation (30 sentences)
  2. Technical, programming, and devops terminology (20 sentences)
  3. Numbers, currency amounts (₹), dates, and timestamps (20 sentences)
  4. Indian names, brands, and geographic places (15 sentences)
  5. Rapid mid-sentence code-switching (15 sentences)
- **Audio Synthesis:** Multi-speaker TTS rotation using Microsoft Neural Voices:
  - `hi-IN-SwaraNeural` (Female Hindi)
  - `hi-IN-MadhurNeural` (Male Hindi)
  - `gu-IN-DhwaniNeural` (Female Gujarati)
  - `en-IN-NeerjaNeural` (Female Indian English)
- **Automated Degradations Applied (Open-Source DSP):**
  - Speed variation: Time stretching between 0.90x and 1.15x.
  - Additive Gaussian / ambient noise: SNR injected between 15 dB and 25 dB.
  - 8 kHz Telephony Simulation: Bandpass filtering (300 Hz – 3,400 Hz) and 8 kHz downsampling/upsampling to simulate real phone calls.
- **License:** Open Source (**MIT License**), part of the BolSamajh repository.

---

## 5. Excluded or Gated Datasets Audit

| Candidate Dataset | Status | Reason / Protocol Followed |
| :--- | :--- | :--- |
| **AI4Bharat Kathbath** (`ai4bharat/Kathbath`) | Gated (`auto`) | Requires Hugging Face login and terms agreement. Avoided in favor of un-gated CC-BY-4.0 FLEURS & HiACC to ensure 100% automated script reproduction without manual intervention. |
| **Microsoft Speech Accent Corpus** | Commercial / Restricted | Excluded per Zero Spend & Open Access guidelines. |
| **Manual recordings** | Prohibited | Strictly rejected in accordance with project hard rules (no manual recording requests). |
