import React from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, Sequence } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { CaptionPill } from "../components/CaptionPill";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { WindowFrame } from "../components/WindowFrame";
import { SCENE_CAPTIONS } from "../captions";

export const Solution: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const pills = [
    {
      icon: "🎤",
      title: "Speak to write",
      desc: "Push-to-talk in any app • Alt+Shift+Space",
      accent: theme.colors.cyan,
      delay: 70,
    },
    {
      icon: "📄",
      title: "Talk to any document",
      desc: "PDF/DOCX/Web RAG with page citations",
      accent: theme.colors.green,
      delay: 85,
    },
    {
      icon: "⚡",
      title: "Speak to edit",
      desc: "In-place text rewrite • Alt+Shift+C",
      accent: theme.colors.primary,
      delay: 100,
    },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.primary} accentColor={theme.colors.secondary} />

      {/* Audio: Voiceover */}
      <Sequence from={10}>
        <Audio src={staticFile("audio/vo/vo_03_solution_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={145}>
        <Audio src={staticFile("audio/vo/vo_03_solution_2.mp3")} volume={1} />
      </Sequence>
      <Sequence from={68}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.4} />
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
        {/* Main Application Window Frame with Real Dashboard Capture */}
        <WindowFrame width={1240} height={600} delay={10}>
          <div style={{ position: "relative", width: "100%", height: "100%" }}>
            <Img
              src={staticFile("captures/01_home_dashboard_1440.png")}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "top",
              }}
            />

            {/* Overlaid 3 Pillars Banner across bottom */}
            <div
              style={{
                position: "absolute",
                bottom: 0,
                left: 0,
                right: 0,
                padding: "24px 32px",
                background: "linear-gradient(180deg, transparent 0%, rgba(10, 13, 20, 0.95) 30%, #0a0d14 100%)",
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 20,
              }}
            >
              {pills.map((p) => {
                const pillSpring = spring({
                  frame: frame - p.delay,
                  fps,
                  config: theme.spring.smooth,
                });

                return (
                  <div
                    key={p.title}
                    style={{
                      padding: "16px 20px",
                      borderRadius: 14,
                      backgroundColor: "rgba(18, 23, 36, 0.92)",
                      border: `1.5px solid ${p.accent}66`,
                      boxShadow: `0 10px 25px rgba(0, 0, 0, 0.5), 0 0 20px ${p.accent}22`,
                      display: "flex",
                      alignItems: "center",
                      gap: 14,
                      opacity: pillSpring,
                      transform: `translateY(${interpolate(pillSpring, [0, 1], [25, 0])}px)`,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 26,
                        width: 44,
                        height: 44,
                        borderRadius: 12,
                        backgroundColor: `${p.accent}18`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {p.icon}
                    </div>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontFamily: theme.fonts.sans, fontSize: 16, fontWeight: 700, color: theme.colors.text }}>
                        {p.title}
                      </span>
                      <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.textMuted }}>
                        {p.desc}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </WindowFrame>
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="03" sectionTitle="THE SOLUTION" />

      {/* 4. Burned-in Captions Pill */}
      <CaptionPill cues={SCENE_CAPTIONS.Solution} />

      {/* 5. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};

