import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { BenchTable } from "../components/BenchTable";

export const Offline: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Phase transition: Frame 0-200 = Air-Gapped Mode; Frame 200-420 = Benchmark Table
  const isBenchPhase = frame >= 200;

  // Animation springs
  const offlineCardEntrance = spring({
    frame: frame - 10,
    fps,
    config: theme.spring.smooth,
  });

  const benchEntrance = spring({
    frame: frame - 200,
    fps,
    config: theme.spring.smooth,
  });

  const engines = [
    { name: "Faster-Whisper", spec: "large-v3-turbo / CUDA (Int8)", role: "STT Engine", icon: "🎙️" },
    { name: "Ollama Local", spec: "llama3.2:3b-instruct-q4", role: "Local Reasoning", icon: "🧠" },
    { name: "Piper TTS", spec: "hi_IN-swara-medium (Onnx)", role: "Local Speech Synth", icon: "🔊" },
    { name: "Multilingual-E5", spec: "intfloat/multilingual-e5 + FAISS", role: "Vector Retrieval", icon: "⚡" },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.green} accentColor={theme.colors.cyan} />

      {/* 2. Content Layer */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 40,
        }}
      >
        {/* Sub-Scene A: Air-Gapped Status (Frames 0 - 200) */}
        {!isBenchPhase && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 28,
              width: 1200,
              opacity: interpolate(frame, [0, 15, 185, 200], [0, 1, 1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `translateY(${interpolate(offlineCardEntrance, [0, 1], [30, 0])}px)`,
            }}
          >
            {/* Airplane Mode Indicator */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "8px 24px",
                borderRadius: 24,
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.4)",
              }}
            >
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  backgroundColor: theme.colors.red,
                  boxShadow: `0 0 10px ${theme.colors.red}`,
                }}
              />
              <span
                style={{
                  fontFamily: theme.fonts.mono,
                  fontSize: 13,
                  fontWeight: 800,
                  color: "#fca5a5",
                  letterSpacing: "0.08em",
                }}
              >
                AIRPLANE MODE ACTIVE • WI-FI DISCONNECTED
              </span>
            </div>

            {/* Main Air-Gapped Banner */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                padding: "28px 48px",
                borderRadius: 24,
                backgroundColor: "rgba(16, 185, 129, 0.08)",
                border: `2px solid ${theme.colors.green}`,
                boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(16, 185, 129, 0.2)",
                gap: 10,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <span style={{ fontSize: 28 }}>🟢</span>
                <span
                  style={{
                    fontFamily: theme.fonts.sans,
                    fontSize: 32,
                    fontWeight: 900,
                    color: theme.colors.text,
                    letterSpacing: "-0.02em",
                  }}
                >
                  100% Air-Gapped Offline Mode
                </span>
              </div>
              <span
                style={{
                  fontFamily: theme.fonts.mono,
                  fontSize: 15,
                  fontWeight: 600,
                  color: theme.colors.green,
                  letterSpacing: "0.05em",
                }}
              >
                ZERO BYTES TRANSMITTED TO FOREIGN CLOUDS • RUNS ON GPU & CPU
              </span>
            </div>

            {/* 4 Engine Badges Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: 16,
                width: 900,
              }}
            >
              {engines.map((eng, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 16,
                    padding: "16px 20px",
                    borderRadius: 14,
                    backgroundColor: theme.colors.bgCard,
                    border: `1px solid ${theme.colors.border}`,
                    boxShadow: theme.shadows.card,
                  }}
                >
                  <span style={{ fontSize: 28 }}>{eng.icon}</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span
                        style={{
                          fontFamily: theme.fonts.sans,
                          fontSize: 16,
                          fontWeight: 700,
                          color: theme.colors.text,
                        }}
                      >
                        {eng.name}
                      </span>
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: 6,
                          backgroundColor: "rgba(16, 185, 129, 0.15)",
                          color: theme.colors.green,
                          fontFamily: theme.fonts.mono,
                          fontSize: 10,
                          fontWeight: 700,
                        }}
                      >
                        LOCAL
                      </span>
                    </div>
                    <span
                      style={{
                        fontFamily: theme.fonts.mono,
                        fontSize: 12,
                        color: theme.colors.textMuted,
                      }}
                    >
                      {eng.spec}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sub-Scene B: Benchmark Table (Frames 200 - 420) */}
        {isBenchPhase && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 20,
              width: 1100,
              opacity: interpolate(frame, [200, 215], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `translateY(${interpolate(benchEntrance, [0, 1], [30, 0])}px)`,
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "6px 16px",
                  borderRadius: 20,
                  backgroundColor: "rgba(99, 102, 241, 0.15)",
                  border: `1px solid ${theme.colors.primary}`,
                }}
              >
                <span
                  style={{
                    fontFamily: theme.fonts.mono,
                    fontSize: 11,
                    fontWeight: 800,
                    color: theme.colors.cyan,
                    letterSpacing: "0.08em",
                  }}
                >
                  TRANSPARENT PUBLIC BENCHMARK
                </span>
              </div>
              <h2
                style={{
                  fontFamily: theme.fonts.sans,
                  fontSize: 28,
                  fontWeight: 800,
                  color: theme.colors.text,
                  margin: 0,
                }}
              >
                Raw vs Normalized WER on 1,000 Real Speech Clips
              </h2>
            </div>

            {/* The Real Benchmark Table Component */}
            <BenchTable delay={0} />

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 24,
                fontFamily: theme.fonts.mono,
                fontSize: 12,
                color: theme.colors.textMuted,
              }}
            >
              <span>• HiACC Hinglish Corpus (IIT/NIT)</span>
              <span>• Zero Cloud Dependency</span>
              <span>• Full Reproducibility Script in /scripts</span>
            </div>
          </div>
        )}
      </AbsoluteFill>

      {/* 3. Top Hud Overlay */}
      <Hud sectionNumber="04" sectionTitle="AIR-GAPPED OFFLINE MODE" />

      {/* 4. Cinematic Grading & Vignette */}
      <Vignette />
      <Grain opacity={0.04} />
      <Grade />
    </AbsoluteFill>
  );
};
