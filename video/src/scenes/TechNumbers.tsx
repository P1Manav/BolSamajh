import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, Sequence } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { CaptionPill } from "../components/CaptionPill";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { BenchTable } from "../components/BenchTable";
import { StatCard } from "../components/StatCard";
import { CodeBlock } from "../components/CodeBlock";
import { facts } from "../loadFacts";
import { SCENE_CAPTIONS } from "../captions";

export const TechNumbers: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.cyan} accentColor={theme.colors.primary} />

      {/* Audio: Voiceover */}
      <Sequence from={12}>
        <Audio src={staticFile("audio/vo/vo_07_tech_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={168}>
        <Audio src={staticFile("audio/vo/vo_07_tech_2.mp3")} volume={1} />
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
          paddingTop: 45,
          gap: 20,
        }}
      >
        {/* Top 3 Metric Stat Cards */}
        <div style={{ display: "flex", gap: 24 }}>
          <StatCard
            targetValue={facts.turboHinglishWer}
            suffix="%"
            decimals={1}
            label="HiACC Hinglish WER"
            sublabel="large-v3-turbo vs 50.7% medium"
            delay={10}
            accentColor={theme.colors.cyan}
          />
          <StatCard
            targetValue={510}
            suffix=" ms"
            decimals={0}
            label="Real Speech Latency"
            sublabel="0.061x RTF on RTX 3060 Ti"
            delay={20}
            accentColor={theme.colors.green}
          />
          <StatCard
            targetValue={facts.retrievalHitAt3}
            suffix="%"
            decimals={1}
            label="Hit@3 Doc Retrieval"
            sublabel="Google XQuAD Hindi Corpus"
            delay={30}
            accentColor={theme.colors.primary}
          />
          <StatCard
            targetValue={facts.bargeinMedianLatencyMs}
            suffix=" ms"
            decimals={0}
            label="Voice Barge-In Stop"
            sublabel="Silero VAD (0 false triggers)"
            delay={40}
            accentColor={theme.colors.green}
          />
        </div>

        {/* Bottom Split: Benchmark Table or Code Block */}
        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          {frame < 165 ? (
            <BenchTable delay={35} />
          ) : (
            <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
              <CodeBlock delay={165} />
              <div
                style={{
                  width: 480,
                  padding: "24px 28px",
                  borderRadius: 14,
                  backgroundColor: "#121724",
                  border: `1px solid ${theme.colors.border}`,
                  display: "flex",
                  flexDirection: "column",
                  gap: 14,
                }}
              >
                <span style={{ fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.cyan, fontWeight: 700 }}>
                  BOLNA VOICE GATEWAY
                </span>
                <h3 style={{ fontFamily: theme.fonts.sans, fontSize: 20, fontWeight: 700, color: "#fff", margin: 0 }}>
                  Drop-In OpenAI Audio Protocol
                </h3>
                <p style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: theme.colors.textMuted, margin: 0, lineHeight: 1.5 }}>
                  BolSamajh exposes OpenAI-compatible audio endpoints (`/v1/audio/speech`, `/v1/audio/transcriptions`, and `/v1/realtime`).
                  Bolna agents connect seamlessly as a free, local audio gateway.
                </p>
                <div
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    backgroundColor: "rgba(16, 185, 129, 0.12)",
                    border: `1px solid ${theme.colors.green}`,
                    color: theme.colors.green,
                    fontFamily: theme.fonts.mono,
                    fontSize: 11,
                    fontWeight: 700,
                  }}
                >
                  ✓ Tested with Bolna OPENAISynthesizer
                </div>
              </div>
            </div>
          )}
        </div>
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="07" sectionTitle="THE TECH & NUMBERS" />

      {/* 4. Burned-in Captions Pill */}
      <CaptionPill cues={SCENE_CAPTIONS.TechNumbers} />

      {/* 5. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};

