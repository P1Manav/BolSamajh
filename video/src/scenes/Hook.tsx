import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { KineticText } from "../components/KineticText";

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo entrance
  const logoEntrance = spring({
    frame: frame - 65,
    fps,
    config: theme.spring.bouncy,
  });

  // Problem cards entrance (starts frame 150)
  const problemEntrance = spring({
    frame: frame - 150,
    fps,
    config: theme.spring.smooth,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.primary} accentColor={theme.colors.cyan} />

      {/* 2. Visual Content Layer */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          paddingTop: 30,
        }}
      >
        {/* Kinetic Statement (Frames 0 - 75) */}
        {frame < 80 && (
          <div
            style={{
              opacity: interpolate(frame, [65, 75], [1, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            <KineticText
              text="We speak Hinglish. Software doesn't."
              delay={5}
              highlightWord="Hinglish."
              highlightColor={theme.colors.cyan}
              fontSize={80}
            />
          </div>
        )}

        {/* Brand & Problem Split View (Frames 75 - 360) */}
        {frame >= 70 && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 28,
              width: 1300,
            }}
          >
            {/* Top Brand Banner */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 20,
                opacity: logoEntrance,
                transform: `scale(${interpolate(logoEntrance, [0, 1], [0.85, 1])})`,
              }}
            >
              <Img
                src={staticFile("bolsamajh.png")}
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  boxShadow: "0 10px 25px rgba(0, 0, 0, 0.6), 0 0 25px rgba(99, 102, 241, 0.4)",
                }}
              />
              <div style={{ display: "flex", flexDirection: "column" }}>
                <h1
                  style={{
                    fontFamily: theme.fonts.sans,
                    fontSize: 52,
                    fontWeight: 800,
                    color: theme.colors.text,
                    letterSpacing: "-0.03em",
                    margin: 0,
                    lineHeight: 1,
                  }}
                >
                  BolSamajh
                </h1>
                <span
                  style={{
                    fontFamily: theme.fonts.sans,
                    fontSize: 18,
                    fontWeight: 600,
                    color: theme.colors.cyan,
                    letterSpacing: "0.02em",
                  }}
                >
                  Bolo. Samjho. 🇮🇳🎙️
                </span>
              </div>
            </div>

            {/* Problem Comparison Card (Frames 150 - 360) */}
            {frame >= 140 && (
              <div
                style={{
                  width: "100%",
                  borderRadius: 18,
                  backgroundColor: "#121724",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  boxShadow: theme.shadows.card,
                  padding: "24px 32px",
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 32,
                  opacity: problemEntrance,
                  transform: `translateY(${interpolate(problemEntrance, [0, 1], [25, 0])}px)`,
                }}
              >
                {/* Left: The Problem with Commercial Voice Tools */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                    padding: "20px 24px",
                    borderRadius: 14,
                    backgroundColor: "rgba(244, 63, 94, 0.08)",
                    border: "1.5px solid rgba(244, 63, 94, 0.3)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, fontWeight: 700, color: theme.colors.red }}>
                      COMMERCIAL CLOSED TOOLS (e.g. Wispr Flow)
                    </span>
                  </div>
                  <div style={{ fontFamily: theme.fonts.sans, fontSize: 24, fontWeight: 800, color: "#ffffff" }}>
                    $12 – $15 / month
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: "#cbd5e1" }}>
                      ❌ Dictation capped on free tier (~2,000 words/week)
                    </span>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: "#cbd5e1" }}>
                      ❌ Voice audio and sensitive documents sent to cloud
                    </span>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: "#cbd5e1" }}>
                      ❌ No document intelligence or page citations
                    </span>
                  </div>
                </div>

                {/* Right: The BolSamajh Answer */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                    padding: "20px 24px",
                    borderRadius: 14,
                    backgroundColor: "rgba(16, 185, 129, 0.08)",
                    border: "1.5px solid rgba(16, 185, 129, 0.3)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, fontWeight: 700, color: theme.colors.green }}>
                      BOLSAMAJH (100% OPEN SOURCE & LOCAL)
                    </span>
                  </div>
                  <div style={{ fontFamily: theme.fonts.sans, fontSize: 24, fontWeight: 800, color: theme.colors.green }}>
                    $0.00 / Zero Mandatory Spend
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: "#cbd5e1" }}>
                      ✓ Built for 500M+ fluid Hinglish speakers
                    </span>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: "#cbd5e1" }}>
                      ✓ 100% Air-Gapped: audio never leaves your device
                    </span>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 13, color: "#cbd5e1" }}>
                      ✓ Talk to PDFs with verifiable page citations
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="01" sectionTitle="PROBLEM HOOK" />

      {/* 4. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};
