import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { CitationChip } from "../components/CitationChip";
import { Waveform } from "../components/Waveform";

export const DocQA: React.FC = () => {
  const frame = useCurrentFrame();

  // Active sub-phases
  const isQuestion1 = frame >= 250 && frame < 530;
  const isBargeIn = frame >= 530 && frame < 620;
  const isGujarati = frame >= 620 && frame < 790;
  const isRefusal = frame >= 790;

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.green} accentColor={theme.colors.cyan} />

      {/* 2. Visual Content Layer */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 45,
          gap: 16,
        }}
      >
        {/* Top Status & Citation Bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          {isQuestion1 && <CitationChip page="Page 1" delay={360} score={0.87} />}
          {isBargeIn && (
            <div
              style={{
                padding: "8px 18px",
                borderRadius: 24,
                backgroundColor: "rgba(244, 63, 94, 0.15)",
                border: `2px solid ${theme.colors.red}`,
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: theme.colors.red }} />
              <span style={{ fontFamily: theme.fonts.mono, fontSize: 13, fontWeight: 800, color: theme.colors.red }}>
                VOICE BARGE-IN: INTERRUPTED IN 66 ms (SILERO VAD)
              </span>
            </div>
          )}
          {isGujarati && <CitationChip page="Page 2" delay={630} score={0.91} />}
          {isRefusal && (
            <div
              style={{
                padding: "8px 18px",
                borderRadius: 24,
                backgroundColor: "rgba(244, 63, 94, 0.15)",
                border: `2px solid ${theme.colors.red}`,
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <span style={{ fontFamily: theme.fonts.mono, fontSize: 13, fontWeight: 800, color: theme.colors.red }}>
                UNGROUNDED REFUSAL GATING (THRESHOLD: 0.785)
              </span>
            </div>
          )}
        </div>

        {/* Split UI: PDF Viewer on Left, Grounded Q&A on Right */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.1fr 1.3fr",
            gap: 26,
            width: 1360,
            height: 520,
          }}
        >
          {/* Left: Real Studio Capture with Highlighting */}
          <div
            style={{
              borderRadius: 16,
              overflow: "hidden",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              boxShadow: theme.shadows.card,
              position: "relative",
              backgroundColor: "#121724",
            }}
          >
            <Img
              src={staticFile("captures/03_documents_rag_1440.png")}
              style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "left top" }}
            />
            {/* Emerald highlight over Page 1 passage */}
            <div
              style={{
                position: "absolute",
                top: 135,
                left: 18,
                right: 18,
                height: 85,
                borderRadius: 8,
                border: `2px solid ${theme.colors.green}`,
                backgroundColor: "rgba(16, 185, 129, 0.18)",
                boxShadow: "0 0 20px rgba(16, 185, 129, 0.3)",
                pointerEvents: "none",
              }}
            />
          </div>

          {/* Right: Dynamic Interactive Chat Bubble Canvas */}
          <div
            style={{
              borderRadius: 16,
              backgroundColor: "#121724",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              padding: "26px 30px",
              display: "flex",
              flexDirection: "column",
              gap: 18,
              boxShadow: theme.shadows.card,
            }}
          >
            {/* User Query Bubble */}
            <div
              style={{
                padding: "16px 20px",
                borderRadius: 14,
                backgroundColor: "rgba(99, 102, 241, 0.15)",
                border: `1.5px solid ${theme.colors.primary}`,
                alignSelf: "flex-end",
                maxWidth: "85%",
              }}
            >
              <span style={{ fontFamily: theme.fonts.sans, fontSize: 17, fontWeight: 600, color: "#ffffff" }}>
                {!isGujarati && !isRefusal
                  ? "Kya ICU charges cover hote hain?"
                  : isGujarati
                  ? "Maternity benefit ketlu male chhe?"
                  : "Space travel cover chhe?"}
              </span>
            </div>

            {/* Answer Bubble */}
            <div
              style={{
                padding: "20px 24px",
                borderRadius: 14,
                backgroundColor: isRefusal ? "rgba(244, 63, 94, 0.08)" : "rgba(16, 185, 129, 0.1)",
                border: `1.5px solid ${isRefusal ? theme.colors.red : theme.colors.green}`,
                alignSelf: "flex-start",
                maxWidth: "92%",
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span
                  style={{
                    fontFamily: theme.fonts.mono,
                    fontSize: 11,
                    fontWeight: 800,
                    color: isRefusal ? theme.colors.red : theme.colors.green,
                  }}
                >
                  {isRefusal
                    ? "OUT-OF-DOCUMENT REFUSAL"
                    : isGujarati
                    ? "PAGE 2 CITATION VERIFIED (GUJARATI TTS)"
                    : "PAGE 1 CITATION VERIFIED (HINGLISH TTS)"}
                </span>
                <Waveform
                  bars={8}
                  height={16}
                  color={isRefusal ? theme.colors.red : theme.colors.green}
                  isListening={!isBargeIn}
                  isInterrupted={isBargeIn}
                />
              </div>

              <span style={{ fontFamily: theme.fonts.sans, fontSize: 17, lineHeight: 1.5, color: "#f8fafc" }}>
                {!isGujarati && !isRefusal
                  ? "Page 1 ke mutabiq ICU charges 100 percent cover hote hain. Room rent 2% sum insured per diem apply hota hai."
                  : isGujarati
                  ? "Page 2 mujab maternity benefit pachas hajaar sudhi male chhe."
                  : "Yeh document mein nahi hai. Document policy sirf medical treatments aur hospitalization cover karti hai."}
              </span>
            </div>
          </div>
        </div>
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="03" sectionTitle="TALK TO ANY DOCUMENT" />

      {/* 4. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};

