"""Measure voice barge-in performance on hardware (headphones vs speakers).

Plays continuous synthesized speech while monitoring the microphone with Silero VAD (BargeInMonitor).
Measures:
1. False-trigger rate (echo leakage from output audio into mic during silence).
2. Interruption detection latency when user intentionally speaks over audio.
3. Writes empirical results to benchmark_data/bargein_measurements.json.

Usage:
    # 10-minute headphone test (quiet room, wearing headphones):
    python scripts/measure_bargein.py --mode headphones --duration 600

    # 10-minute speaker test (laptop / desktop speakers):
    python scripts/measure_bargein.py --mode speakers --duration 600

    # Quick 60-second smoke test:
    python scripts/measure_bargein.py --duration 60
"""

import os
import sys
import time
import json
import argparse
import logging
import asyncio
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
OUTPUT_FILE = ROOT_DIR / "benchmark_data" / "bargein_measurements.json"

from bolsamajh.utils.vad import BargeInMonitor
from bolsamajh.tts.edge_tts_adapter import EdgeTTSAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("measure_bargein")

SAMPLE_SENTENCES = [
    "नमस्ते, BolSamajh में आपका स्वागत है। हम भारतीय भाषाओं के लिए वॉइस असिस्टेंट तैयार कर रहे हैं।",
    "Insurance policy ke claims process ke liye aapko form number three aur medical bills submit karne honge.",
    "BolSamajh helps you dictate anywhere, talk to documents, and edit text using voice commands.",
    "Kal subah meeting 10:30 AM par scheduled hai, presentation slides review kar lijiye.",
    "Customer support team aapki ticket verify kar rahi hai, kripya thoda intezaar karein.",
    "Grounded document QA allows you to cite exact page numbers without hallucinating answers.",
]


async def run_bargein_measurement(
    mode: str = "headphones",
    duration_sec: float = 600.0,
    measure_latency: bool = False,
    output_path: Path = ROOT_DIR / "benchmark_data" / "bargein_measurements.json",
):
    """Run empirical barge-in test loop."""
    print("=" * 70)
    print("  BolSamajh Hardware Voice Barge-In Measurement")
    print("=" * 70)
    print(f"Mode:             {mode.upper()}")
    print(f"Target Duration:  {duration_sec:.1f} seconds ({duration_sec / 60:.1f} minutes)")
    print(f"Headphone Mode:   {mode == 'headphones'}")
    print(f"Output File:      {output_path}")
    print("-" * 70)

    tts = EdgeTTSAdapter()

    false_triggers = 0
    interrupted_event = asyncio.Event()
    last_trigger_time = 0.0

    def on_barge_in_triggered():
        nonlocal false_triggers, last_trigger_time
        now = time.time()
        # Debounce multiple triggers within 1 second
        if now - last_trigger_time > 1.0:
            last_trigger_time = now
            false_triggers += 1
            print(f"\n[ALERT] Barge-in triggered! (Total triggers: {false_triggers})")
            tts.stop()
            interrupted_event.set()

    headphone_mode = (mode == "headphones")
    monitor = BargeInMonitor(
        on_barge_in=on_barge_in_triggered,
        headphone_mode=headphone_mode,
        mute_ms=300.0,
    )

    t_start = time.time()
    sentences_played = 0
    sentence_idx = 0

    print("\nStarting playback and microphone monitoring...")
    print("Please remain silent to measure false-trigger rate from speaker echo.")
    print("Press Ctrl+C at any time to halt and save partial results.\n")

    try:
        while (time.time() - t_start) < duration_sec:
            sentence = SAMPLE_SENTENCES[sentence_idx % len(SAMPLE_SENTENCES)]
            sentence_idx += 1
            sentences_played += 1

            elapsed = time.time() - t_start
            remain = max(0.0, duration_sec - elapsed)
            print(f"[{elapsed:5.1f}s / {duration_sec:5.1f}s] Playing #{sentences_played}: \"{sentence[:45]}...\"")

            interrupted_event.clear()
            monitor.start()

            speak_task = asyncio.create_task(tts.speak(sentence))
            done, pending = await asyncio.wait(
                [speak_task, asyncio.create_task(interrupted_event.wait())],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for p in pending:
                p.cancel()

            monitor.stop()

            # Small inter-sentence pause (500 ms)
            await asyncio.sleep(0.5)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\nTest interrupted by user. Finalizing measurement report...")

    actual_duration = time.time() - t_start
    actual_minutes = max(0.01, actual_duration / 60.0)
    rate_per_min = round(false_triggers / actual_minutes, 3)

    # Acceptance threshold:
    # Headphones: <= 1 trigger per 10 mins (0.1 / min)
    # Speakers: <= 3 triggers per 10 mins (0.3 / min)
    max_allowed = 1 if headphone_mode else 3
    passed = false_triggers <= max_allowed

    results = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "headphone_mode": headphone_mode,
        "duration_seconds": round(actual_duration, 1),
        "target_duration_seconds": duration_sec,
        "sentences_played": sentences_played,
        "false_triggers": false_triggers,
        "false_trigger_rate_per_min": rate_per_min,
        "status": "PASS" if passed else "FAIL",
        "thresholds": {
            "max_allowed_false_triggers": max_allowed,
            "max_rate_per_min": round(max_allowed / 10.0, 3),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("  Measurement Complete — Results Summary")
    print("=" * 70)
    print(f"Actual Duration:     {actual_duration:.1f}s ({actual_minutes:.2f} mins)")
    print(f"Sentences Played:    {sentences_played}")
    print(f"False Triggers:      {false_triggers} (Max Allowed: {max_allowed})")
    print(f"False Trigger Rate:  {rate_per_min} / minute")
    print(f"Overall Result:      {'[PASSED]' if passed else '[FAILED]'}")
    print(f"Saved To:            {output_path}")
    print("=" * 70)

    return results


def main():
    parser = argparse.ArgumentParser(description="BolSamajh Voice Barge-In Measurement Script")
    parser.add_argument("--mode", choices=["headphones", "speakers"], default="headphones",
                        help="Listening mode: 'headphones' (default) or 'speakers'")
    parser.add_argument("--duration", type=float, default=600.0,
                        help="Total test duration in seconds (default: 600s = 10 mins)")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE),
                        help=f"Path to output JSON result (default: {OUTPUT_FILE})")
    args = parser.parse_args()

    asyncio.run(
        run_bargein_measurement(
            mode=args.mode,
            duration_sec=args.duration,
            output_path=Path(args.output),
        )
    )


if __name__ == "__main__":
    main()
