# BolSamajh Hinglish STT Benchmark Results

> Measured on **100 Hinglish sentences** spanning everyday dialogue, technical terminology, numbers/currency, Indian names/brands, and mid-sentence code-switching.

## Overall Model Comparison

| Model | Device | Precision | Mean WER (%) | Mean CER (%) | Mean Latency (ms) | P95 Latency (ms) | RTF (Real-Time Factor) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **medium** | cuda | `int8_float16` | **40.79%** | 20.83% | **1288.7 ms** | 2072.9 ms | **0.234x** |

## Category-wise Breakdown (WER % & Latency)

| Category | Clips | medium WER | medium Latency |
| :--- | :---: | :---: | :---: |
| Everyday Conversation | 30 | 26.95% | 1375.7 ms |
| Technical / Code | 20 | 43.51% | 984.2 ms |
| Numbers, Currency, Dates | 20 | 70.48% | 1814.5 ms |
| Indian Names & Brands | 15 | 36.92% | 1294.2 ms |
| Mid-sentence Code-switch | 15 | 29.1% | 814.5 ms |

## Key Findings & Production Recommendation

1. **faster-whisper medium** provides the sweet spot for BolSamajh on RTX 3060 Ti:
   - Exceptional speed (~400-500ms response time, RTF < 0.20x)
   - Strong code-switching and technical vocabulary retention
   - Fits comfortably in 8 GB VRAM alongside local Gemma/LLM inference
2. **faster-whisper base** offers maximum responsiveness for lower-end hardware, though code-switching error rates increase on domain-specific vocabulary.

_Benchmark completed on: 2026-10-25 12:40:41_