import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, Sequence } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { CaptionPill } from "../components/CaptionPill";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { SCENE_CAPTIONS } from "../captions";

export const Different: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - 10,
    fps,
    config: theme.spring.smooth,
  });

  const comparisonRows = [
    {
      feature: "License & Auditability",
      wispr: "Proprietary closed-source",
      bolsamajh: "100% Open Source (MIT)",
      highlight: true,
    },
    {
      feature: "Cost / Pricing",
      wispr: "Free (capped) / $12–$15/mo",
      bolsamajh: "$0.00 / Zero mandatory spend",
      highlight: true,
    },
    {
      feature: "100% Offline Air-Gapped",
      wispr: "Cloud-dependent (audio sent to cloud)",
      bolsamajh: "Fully air-gapped (Faster-Whisper+Piper+Ollama)",
      highlight: true,
    },
    {
      feature: "Talk to Documents (RAG)",
      wispr: "None (requires external tools)",
      bolsamajh: "Built-in Voice Doc Q&A with Page Citations",
      highlight: true,
    },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.primary} accentColor={theme.colors.cyan} />

      {/* Audio: Voiceover */}
      <Sequence from={12}>
        <Audio src={staticFile("audio/vo/vo_06_diff_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={148}>
        <Audio src={staticFile("audio/vo/vo_06_diff_2.mp3")} volume={1} />
      </Sequence>

      <Sequence from={8}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.35} />
      </Sequence>

      {/* 2. Visual Content Layer */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 40,
        }}
      >
        <div
          style={{
            width: 1240,
            borderRadius: 18,
            backgroundColor: "#121724",
            border: `1px solid ${theme.colors.borderStrong}`,
            boxShadow: theme.shadows.card,
            overflow: "hidden",
            opacity: entrance,
            transform: `translateY(${interpolate(entrance, [0, 1], [30, 0])}px)`,
          }}
        >
          {/* Header Row */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1.4fr 1.3fr 1.6fr",
              padding: "18px 28px",
              backgroundColor: "#0d111a",
              borderBottom: `1px solid ${theme.colors.border}`,
              alignItems: "center",
            }}
          >
            <span style={{ fontFamily: theme.fonts.mono, fontSize: 13, fontWeight: 700, color: theme.colors.textMuted }}>
              CAPABILITY (Sourced 2026-10-31)
            </span>
            <span style={{ fontFamily: theme.fonts.sans, fontSize: 16, fontWeight: 700, color: theme.colors.textMuted }}>
              Wispr Flow
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontFamily: theme.fonts.sans, fontSize: 17, fontWeight: 800, color: theme.colors.cyan }}>
                BolSamajh
              </span>
              <span
                style={{
                  padding: "2px 8px",
                  borderRadius: 4,
                  backgroundColor: theme.colors.green,
                  color: "#000",
                  fontFamily: theme.fonts.mono,
                  fontSize: 10,
                  fontWeight: 800,
                }}
              >
                100% AUDITABLE
              </span>
            </div>
          </div>

          {/* Comparison Rows */}
          {comparisonRows.map((row, i) => {
            const rowSpring = spring({
              frame: frame - 15 - i * 6,
              fps,
              config: theme.spring.smooth,
            });

            return (
              <div
                key={i}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1.4fr 1.3fr 1.6fr",
                  padding: "16px 28px",
                  borderBottom: i < comparisonRows.length - 1 ? `1px solid ${theme.colors.border}` : undefined,
                  alignItems: "center",
                  opacity: rowSpring,
                  backgroundColor: i % 2 === 0 ? "rgba(255, 255, 255, 0.02)" : "transparent",
                }}
              >
                <span style={{ fontFamily: theme.fonts.sans, fontSize: 15, fontWeight: 600, color: theme.colors.text }}>
                  {row.feature}
                </span>
                <span style={{ fontFamily: theme.fonts.sans, fontSize: 14, color: theme.colors.textDim }}>
                  {row.wispr}
                </span>
                <span
                  style={{
                    fontFamily: theme.fonts.sans,
                    fontSize: 15,
                    fontWeight: 700,
                    color: theme.colors.green,
                  }}
                >
                  ✓ {row.bolsamajh}
                </span>
              </div>
            );
          })}

          {/* Transparent Engineering Reality Callout */}
          <div
            style={{
              padding: "14px 28px",
              backgroundColor: "rgba(99, 102, 241, 0.06)",
              borderTop: `1px solid rgba(99, 102, 241, 0.2)`,
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            <span style={{ fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.cyan, fontWeight: 700 }}>
              WHERE WISPR FLOW IS STRONGER:
            </span>
            <span style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: theme.colors.textMuted }}>
              100+ production languages, mature cross-platform sync (macOS/iOS/Windows/Android), and zero local GPU requirement.
            </span>
          </div>
        </div>
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="06" sectionTitle="DIFFERENT BY DESIGN" />

      {/* 4. Burned-in Captions Pill */}
      <CaptionPill cues={SCENE_CAPTIONS.Different} />

      {/* 5. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};

