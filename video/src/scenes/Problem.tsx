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

export const Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns zoom on the PDF representation
  const pdfScale = interpolate(frame, [0, 315], [1, 1.06], { easing: theme.ease.inOut });
  const pdfPan = interpolate(frame, [0, 315], [0, -18]);

  const cards = [
    {
      num: "01",
      badge: "500M+ Speakers",
      headline: "500 million people speak Hinglish every day.",
      detail: "Colloquial code-switching is natural, spontaneous, and pervasive.",
      delay: 15,
    },
    {
      num: "02",
      badge: "Dense Documents",
      headline: "Crucial policies arrive in impenetrable legal English.",
      detail: "Health insurance, bank circulars, and policies leave citizens stranded.",
      delay: 115,
    },
    {
      num: "03",
      badge: "Binary Voice Tools",
      headline: "Commercial tools force pure English or formal Hindi.",
      detail: "Whisper transliterations break on currency (₹), GST, and code-switching.",
      delay: 215,
    },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.lightBg }}>
      {/* 1. Background Mesh (Light variant) */}
      <BgMesh primaryColor={theme.colors.primary} accentColor={theme.colors.cyan} isLight />

      {/* Audio: Voiceover sequences */}
      <Sequence from={12}>
        <Audio src={staticFile("audio/vo/vo_02_problem_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={112}>
        <Audio src={staticFile("audio/vo/vo_02_problem_2.mp3")} volume={1} />
      </Sequence>
      <Sequence from={212}>
        <Audio src={staticFile("audio/vo/vo_02_problem_3.mp3")} volume={1} />
      </Sequence>

      <Sequence from={10}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.3} />
      </Sequence>
      <Sequence from={110}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.3} />
      </Sequence>
      <Sequence from={210}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.3} />
      </Sequence>

      {/* 2. Visual Content Layer */}
      <div
        style={{
          position: "absolute",
          top: 130,
          bottom: 120,
          left: theme.layout.safeMarginX,
          right: theme.layout.safeMarginX,
          display: "grid",
          gridTemplateColumns: "1fr 1.25fr",
          gap: 60,
          alignItems: "center",
        }}
      >
        {/* Left Column: Dense Policy Document Preview (Ken Burns) */}
        <div
          style={{
            height: "100%",
            borderRadius: 18,
            backgroundColor: "#ffffff",
            border: "1px solid #e2e8f0",
            boxShadow: "0 20px 45px -10px rgba(0, 0, 0, 0.12)",
            overflow: "hidden",
            position: "relative",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Document header strip */}
          <div
            style={{
              padding: "12px 18px",
              backgroundColor: "#f1f5f9",
              borderBottom: "1px solid #e2e8f0",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontFamily: theme.fonts.mono, fontSize: 12, fontWeight: 700, color: "#64748b" }}>
              sample_policy.pdf (Page 1 of 12)
            </span>
            <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: "#94a3b8" }}>
              Standard Health Insurance Contract
            </span>
          </div>

          {/* Document content undergoing Ken Burns */}
          <div
            style={{
              flex: 1,
              padding: "24px 28px",
              display: "flex",
              flexDirection: "column",
              gap: 14,
              transform: `scale(${pdfScale}) translateY(${pdfPan}px)`,
              opacity: 0.9,
            }}
          >
            <h3 style={{ fontFamily: theme.fonts.sans, fontSize: 18, fontWeight: 800, color: "#0f172a", margin: 0 }}>
              SECTION 4.2 — HOSPITALIZATION COVERAGE & EXCLUSIONS
            </h3>
            <p style={{ fontFamily: theme.fonts.sans, fontSize: 12, lineHeight: 1.6, color: "#475569", margin: 0 }}>
              The insured person shall be indemnified against reasonable and customary medical expenses incurred in respect of an admissible claim.
              All ICU charges shall be subject to room-rent capping of 2% of sum insured per diem, unless expressly waived under endorsement Schedule B.
            </p>
            <div style={{ height: 1, backgroundColor: "#e2e8f0", margin: "4px 0" }} />
            <h4 style={{ fontFamily: theme.fonts.sans, fontSize: 14, fontWeight: 700, color: "#1e293b", margin: 0 }}>
              SCHEDULE C: WAITING PERIODS & CO-PAYMENTS
            </h4>
            <p style={{ fontFamily: theme.fonts.sans, fontSize: 12, lineHeight: 1.6, color: "#475569", margin: 0 }}>
              Pre-existing conditions are excluded until 36 consecutive months of continuous coverage have elapsed.
              A compulsory co-payment of 20% shall apply to all claims where treatment is undertaken in a non-network tertiary care facility.
            </p>
            <div
              style={{
                marginTop: "auto",
                padding: "8px 12px",
                borderRadius: 8,
                backgroundColor: "rgba(244, 63, 94, 0.08)",
                border: "1px solid rgba(244, 63, 94, 0.25)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.red, fontWeight: 700 }}>
                ⚠️ 12 Pages of Dense Legal English
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: 3 Staggered Problem Cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {cards.map((c) => {
            const cardSpring = spring({
              frame: frame - c.delay,
              fps,
              config: theme.spring.smooth,
            });

            return (
              <div
                key={c.num}
                style={{
                  padding: "20px 24px",
                  borderRadius: 16,
                  backgroundColor: "#ffffff",
                  border: "1.5px solid #e2e8f0",
                  boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.06)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                  opacity: cardSpring,
                  transform: `translateX(${interpolate(cardSpring, [0, 1], [40, 0])}px)`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span
                    style={{
                      fontFamily: theme.fonts.mono,
                      fontSize: 11,
                      fontWeight: 700,
                      color: theme.colors.red,
                      padding: "3px 8px",
                      borderRadius: 6,
                      backgroundColor: "rgba(244, 63, 94, 0.08)",
                    }}
                  >
                    {c.badge}
                  </span>
                  <span style={{ fontFamily: theme.fonts.mono, fontSize: 13, fontWeight: 700, color: "#94a3b8" }}>
                    {c.num}
                  </span>
                </div>
                <h2
                  style={{
                    fontFamily: theme.fonts.sans,
                    fontSize: 22,
                    fontWeight: 700,
                    color: "#0f172a",
                    letterSpacing: "-0.02em",
                    margin: 0,
                  }}
                >
                  {c.headline}
                </h2>
                <p style={{ fontFamily: theme.fonts.sans, fontSize: 14, color: "#64748b", margin: 0, lineHeight: 1.4 }}>
                  {c.detail}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="02" sectionTitle="THE PROBLEM" isLight />

      {/* 4. Burned-in Captions Pill */}
      <CaptionPill cues={SCENE_CAPTIONS.Problem} isLight />

      {/* 5. Post Grade & Texture Stack */}
      <Grade isLight />
      <Grain opacity={0.04} />
      <Vignette isLight />
    </AbsoluteFill>
  );
};

