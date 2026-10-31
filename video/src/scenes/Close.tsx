import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";

export const Close: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Sub-phases:
  // Phase 1 (0 - 180): Ecosystem (Web Call, Android, Bolna Gateway)
  // Phase 2 (180 - 300): Download & Release installer
  // Phase 3 (300 - 360): Final Brand Lockup "Bolo. Samjho."

  const ecoEntrance = spring({
    frame: frame - 10,
    fps,
    config: theme.spring.smooth,
  });

  const downloadEntrance = spring({
    frame: frame - 180,
    fps,
    config: theme.spring.smooth,
  });

  const brandFinaleEntrance = spring({
    frame: frame - 295,
    fps,
    config: theme.spring.bouncy,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.primary} accentColor={theme.colors.cyan} />

      {/* 2. Content Layer */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 30,
        }}
      >
        {/* Phase 1: Ecosystem (Frames 0 - 180) */}
        {frame < 185 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 24,
              width: 1240,
              opacity: interpolate(frame, [0, 15, 170, 185], [0, 1, 1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `translateY(${interpolate(ecoEntrance, [0, 1], [30, 0])}px)`,
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
                  FULL VOICE ECOSYSTEM
                </span>
              </div>
              <h2
                style={{
                  fontFamily: theme.fonts.sans,
                  fontSize: 32,
                  fontWeight: 900,
                  color: theme.colors.text,
                  margin: 0,
                }}
              >
                Browser Web-Call, Android Remote & Bolna Gateway
              </h2>
            </div>

            {/* 3 Ecosystem Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, width: "100%" }}>
              {/* Card 1: Web-Call */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  padding: 24,
                  borderRadius: 16,
                  backgroundColor: theme.colors.bgCard,
                  border: `1px solid ${theme.colors.border}`,
                  boxShadow: theme.shadows.card,
                  gap: 14,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontSize: 28 }}>🌐</span>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 18, fontWeight: 700, color: theme.colors.text }}>
                      Browser Web-Call
                    </span>
                    <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.cyan }}>
                      localhost:8000/call
                    </span>
                  </div>
                </div>
                <p style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: theme.colors.textMuted, lineHeight: 1.5, margin: 0 }}>
                  Low-latency voice call in any modern browser. Real-time duplex audio with animated voice visualizer.
                </p>
                <div
                  style={{
                    padding: "8px 12px",
                    borderRadius: 8,
                    backgroundColor: "rgba(16, 185, 129, 0.1)",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    fontFamily: theme.fonts.mono,
                    fontSize: 11,
                    color: theme.colors.green,
                  }}
                >
                  ● Duplex Audio WebSocket Ready
                </div>
              </div>

              {/* Card 2: Android Companion */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  padding: 24,
                  borderRadius: 16,
                  backgroundColor: theme.colors.bgCard,
                  border: `1px solid ${theme.colors.border}`,
                  boxShadow: theme.shadows.card,
                  gap: 14,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontSize: 28 }}>📱</span>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 18, fontWeight: 700, color: theme.colors.text }}>
                      Android Companion
                    </span>
                    <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.cyan }}>
                      QR Code Instant Pair
                    </span>
                  </div>
                </div>
                <p style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: theme.colors.textMuted, lineHeight: 1.5, margin: 0 }}>
                  Turn your phone into a tactile wireless mic & push-to-talk remote. Stream audio directly over LAN.
                </p>
                <div
                  style={{
                    padding: "8px 12px",
                    borderRadius: 8,
                    backgroundColor: "rgba(99, 102, 241, 0.1)",
                    border: "1px solid rgba(99, 102, 241, 0.3)",
                    fontFamily: theme.fonts.mono,
                    fontSize: 11,
                    color: theme.colors.cyan,
                  }}
                >
                  ● Native Kotlin App & APK Ready
                </div>
              </div>

              {/* Card 3: Bolna Gateway */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  padding: 24,
                  borderRadius: 16,
                  backgroundColor: theme.colors.bgCard,
                  border: `1px solid ${theme.colors.border}`,
                  boxShadow: theme.shadows.card,
                  gap: 14,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontSize: 28 }}>⚡</span>
                  <div style={{ display: "flex", flexDirection: "column" }}>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 18, fontWeight: 700, color: theme.colors.text }}>
                      Bolna Agent Gateway
                    </span>
                    <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.cyan }}>
                      /v1/audio/speech
                    </span>
                  </div>
                </div>
                <p style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: theme.colors.textMuted, lineHeight: 1.5, margin: 0 }}>
                  OpenAI-compatible drop-in endpoints. Connect Bolna voice agents to local Piper TTS & Whisper STT for zero cloud cost.
                </p>
                <div
                  style={{
                    padding: "8px 12px",
                    borderRadius: 8,
                    backgroundColor: "rgba(245, 158, 11, 0.1)",
                    border: "1px solid rgba(245, 158, 11, 0.3)",
                    fontFamily: theme.fonts.mono,
                    fontSize: 11,
                    color: theme.colors.amber,
                  }}
                >
                  ● Bolna Client Verified (100% Pass)
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Phase 2: Download Card (Frames 185 - 295) */}
        {frame >= 185 && frame < 300 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 28,
              width: 1000,
              opacity: interpolate(frame, [185, 200, 285, 300], [0, 1, 1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `translateY(${interpolate(downloadEntrance, [0, 1], [30, 0])}px)`,
            }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                padding: "36px 48px",
                borderRadius: 24,
                backgroundColor: theme.colors.bgCard,
                border: `2px solid ${theme.colors.primary}`,
                boxShadow: "0 25px 60px rgba(0, 0, 0, 0.6), 0 0 50px rgba(99, 102, 241, 0.25)",
                gap: 22,
                width: "100%",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <Img
                  src={staticFile("bolsamajh.png")}
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: 14,
                    boxShadow: "0 8px 20px rgba(0,0,0,0.5)",
                  }}
                />
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontFamily: theme.fonts.sans, fontSize: 30, fontWeight: 900, color: theme.colors.text }}>
                    Get Started in Under 60 Seconds
                  </span>
                  <span style={{ fontFamily: theme.fonts.mono, fontSize: 13, color: theme.colors.cyan }}>
                    github.com/P1Manav/BolSamajh • Apache 2.0 Open Source
                  </span>
                </div>
              </div>

              {/* Download Buttons */}
              <div style={{ display: "flex", gap: 16, width: "100%", justifyContent: "center" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "16px 32px",
                    borderRadius: 14,
                    backgroundColor: theme.colors.primary,
                    color: "#fff",
                    fontFamily: theme.fonts.sans,
                    fontSize: 18,
                    fontWeight: 800,
                    boxShadow: "0 10px 25px rgba(99, 102, 241, 0.4)",
                  }}
                >
                  <span>⬇️</span>
                  <span>Download Windows Installer (.exe)</span>
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "16px 28px",
                    borderRadius: 14,
                    backgroundColor: "rgba(255, 255, 255, 0.05)",
                    border: `1px solid ${theme.colors.border}`,
                    color: theme.colors.text,
                    fontFamily: theme.fonts.mono,
                    fontSize: 15,
                    fontWeight: 700,
                  }}
                >
                  <span>💻</span>
                  <span>git clone & poetry install</span>
                </div>
              </div>

              {/* Badges Row */}
              <div style={{ display: "flex", gap: 24, fontFamily: theme.fonts.mono, fontSize: 13, color: theme.colors.textMuted }}>
                <span>✓ Windows 10/11 x64 Ready</span>
                <span>✓ NVIDIA CUDA & CPU Fallback</span>
                <span>✓ Zero Monthly Fees ($0 Forever)</span>
              </div>
            </div>
          </div>
        )}

        {/* Phase 3: Final Brand Lockup (Frames 295 - 360) */}
        {frame >= 295 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 20,
              opacity: interpolate(frame, [295, 310], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              transform: `scale(${interpolate(brandFinaleEntrance, [0, 1], [0.85, 1])})`,
            }}
          >
            <Img
              src={staticFile("bolsamajh.png")}
              style={{
                width: 120,
                height: 120,
                borderRadius: 28,
                boxShadow: "0 20px 50px rgba(0, 0, 0, 0.8), 0 0 60px rgba(99, 102, 241, 0.5)",
              }}
            />
            <h1
              style={{
                fontFamily: theme.fonts.sans,
                fontSize: 64,
                fontWeight: 900,
                color: theme.colors.text,
                letterSpacing: "-0.03em",
                margin: 0,
              }}
            >
              BolSamajh
            </h1>
            <div
              style={{
                fontFamily: theme.fonts.sans,
                fontSize: 36,
                fontWeight: 800,
                background: `linear-gradient(135deg, ${theme.colors.cyan}, ${theme.colors.primary})`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                letterSpacing: "-0.01em",
              }}
            >
              Bolo. Samjho.
            </div>
            <div
              style={{
                marginTop: 10,
                padding: "8px 20px",
                borderRadius: 20,
                backgroundColor: "rgba(255, 255, 255, 0.05)",
                border: `1px solid ${theme.colors.border}`,
                fontFamily: theme.fonts.mono,
                fontSize: 13,
                fontWeight: 700,
                color: theme.colors.textMuted,
                letterSpacing: "0.05em",
              }}
            >
              Bolna × Symphony Voice AI Buildathon 2026
            </div>
          </div>
        )}
      </AbsoluteFill>

      {/* 3. Top Hud Overlay */}
      <Hud sectionNumber="05" sectionTitle="ECOSYSTEM & RELEASE" />

      {/* 4. Cinematic Grading & Vignette */}
      <Vignette />
      <Grain opacity={0.04} />
      <Grade />
    </AbsoluteFill>
  );
};
