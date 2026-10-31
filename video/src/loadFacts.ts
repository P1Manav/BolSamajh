// Build-time fact loader directly importing measured benchmarks and evidence
import benchmarkResults from "../../benchmark_data/benchmark_results.json";
import retrievalBenchmark from "../../benchmark_data/retrieval_benchmark.json";
import bargeinMeasurements from "../../benchmark_data/bargein_measurements.json";

export interface BenchmarkStats {
  turboHinglishWer: number;
  mediumHinglishWer: number;
  swiftHinglishWer: number;
  turboHindiWer: number;
  turboGujaratiWer: number;
  turboMeanLatencyMs: number;
  turboRtf: number;
  retrievalHitAt1: number;
  retrievalHitAt3: number;
  retrievalThreshold: number;
  bargeinMedianLatencyMs: number;
  docQaEndToEndTtfaMs: number;
  vramUsageMb: number;
}

export const facts: BenchmarkStats = {
  turboHinglishWer: benchmarkResults.real_speech["large-v3-turbo"].splits.code_switched_hinglish.wer_pct, // 38.52%
  mediumHinglishWer: benchmarkResults.real_speech["medium"].splits.code_switched_hinglish.wer_pct, // 50.73%
  swiftHinglishWer: benchmarkResults.real_speech["whisper-hinglish-swift"].splits.code_switched_hinglish.wer_pct, // 52.70%
  turboHindiWer: benchmarkResults.real_speech["large-v3-turbo"].splits.read_hindi.wer_pct, // 25.98%
  turboGujaratiWer: benchmarkResults.real_speech["large-v3-turbo"].splits.read_gujarati.wer_pct, // 66.01%
  turboMeanLatencyMs: benchmarkResults.real_speech["large-v3-turbo"].mean_latency_ms, // 573 ms
  turboRtf: benchmarkResults.real_speech["large-v3-turbo"].mean_rtf, // 0.079x
  retrievalHitAt1: retrievalBenchmark.hit_at_1_pct, // 89.0%
  retrievalHitAt3: retrievalBenchmark.hit_at_3_pct, // 98.0%
  retrievalThreshold: retrievalBenchmark.calibrated_refusal_threshold, // 0.785
  bargeinMedianLatencyMs: bargeinMeasurements.modes.headphones_mode.detection_latency_ms.median, // 74.2 ms
  docQaEndToEndTtfaMs: 1592.6, // from hardware_measurements.json and README.md:289
  vramUsageMb: 1192.0, // from README.md:286
};

