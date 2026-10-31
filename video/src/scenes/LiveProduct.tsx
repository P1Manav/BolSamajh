import React from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, Sequence } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { CaptionPill } from "../components/CaptionPill";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { OverlayPill } from "../components/OverlayPill";
import { CitationChip } from "../components/CitationChip";
import { Waveform } from "../components/Waveform";
import { SCENE_CAPTIONS } from "../captions";

export const LiveProduct: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Sub-beat boundaries
  const isDictate = frame < 240;
  const isDocQa = frame >= 240 && frame < 675;
  const isOffline = frame >= 675;

  // Typing animation for Dictate (starts at frame 90)
  const fullDictateText = "Invoice pe 18% GST add karke total ₹15,000 kar do.";
  const charsTyped = Math.floor(
    interpolate(frame, [95, 175], [0, fullDictateText.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  const currentDictateText = fullDictateText.slice(0, charsTyped);

  // Barge-in active window in DocQA (around frame 515 - 570)
  const isBargeInActive = frame >= 515 && frame < 570;

  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh
        primaryColor={isDictate ? theme.colors.primary : isDocQa ? theme.colors.green : theme.colors.cyan}
        accentColor={theme.colors.secondary}
      />

      {/* Audio Sequences: Dictate sub-beat (0 - 240) */}
      <Sequence from={12} durationInFrames={75}>
        <Audio src={staticFile("audio/vo/vo_05a_dictate_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={88} durationInFrames={85}>
        <Audio src={staticFile("audio/demo/dictation_prompt.mp3")} volume={1} />
      </Sequence>
      <Sequence from={175} durationInFrames={65}>
        <Audio src={staticFile("audio/vo/vo_05a_dictate_2.mp3")} volume={1} />
      </Sequence>

      {/* Audio Sequences: DocQA sub-beat (240 - 675) */}
      <Sequence from={245} durationInFrames={85}>
        <Audio src={staticFile("audio/vo/vo_05b_docqa_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={335} durationInFrames={45}>
        <Audio src={staticFile("audio/demo/doc_qa_question.mp3")} volume={0.9} />
      </Sequence>
      <Sequence from={385} durationInFrames={60}>
        <Audio src={staticFile("audio/demo/doc_qa_answer.mp3")} volume={1} />
      </Sequence>
      <Sequence from={445} durationInFrames={65}>
        <Audio src={staticFile("audio/vo/vo_05b_docqa_2.mp3")} volume={1} />
      </Sequence>
      <Sequence from={515} durationInFrames={35}>
        <Audio src={staticFile("audio/demo/bargein_user.mp3")} volume={1} />
      </Sequence>
      <Sequence from={550} durationInFrames={40}>
        <Audio src={staticFile("audio/vo/vo_05b_docqa_3.mp3")} volume={1} />
      </Sequence>
      <Sequence from={595} durationInFrames={35}>
        <Audio src={staticFile("audio/demo/doc_qa_refusal.mp3")} volume={1} />
      </Sequence>
      <Sequence from={630} durationInFrames={45}>
        <Audio src={staticFile("audio/vo/vo_05b_docqa_4.mp3")} volume={1} />
      </Sequence>

      {/* Audio Sequences: Offline sub-beat (675 - 915) */}
      <Sequence from={680} durationInFrames={95}>
        <Audio src={staticFile("audio/vo/vo_05c_offline_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={785} durationInFrames={120}>
        <Audio src={staticFile("audio/vo/vo_05c_offline_2.mp3")} volume={1} />
      </Sequence>

      {/* 2. Visual Content Layer */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 45,
        }}
      >
        {/* SUB-BEAT 1: DICTATE INTO NOTEPAD (Frames 0 - 240) */}
        {isDictate && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 24,
              width: 1240,
            }}
          >
            {/* Floating Overlay HUD Pill */}
            <OverlayPill
              state={frame < 85 ? "ready" : frame < 175 ? "listening" : "transcribing"}
              text={
                frame < 85
                  ? "Hold Alt+Shift+Space to Dictate"
                  : frame < 175
                  ? "Listening to Hinglish..."
                  : "Cleaned & Formatted ✓"
              }
              hotkey="Alt+Shift+Space"
            />

            {/* Reconstructed Notepad / Active App Window */}
            <div
              style={{
                width: "100%",
                height: 480,
                borderRadius: 16,
                backgroundColor: "#1e1e24",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                boxShadow: theme.shadows.window,
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div
                style={{
                  height: 38,
                  backgroundColor: "#16161b",
                  borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
                  display: "flex",
                  alignItems: "center",
                  padding: "0 16px",
                  gap: 12,
                }}
              >
                <div style={{ display: "flex", gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: "#ef4444" }} />
                  <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: "#f59e0b" }} />
                  <div style={{ width: 10, height: 10, borderRadius: "50%", backgroundColor: "#10b981" }} />
                </div>
                <span style={{ fontFamily: theme.fonts.sans, fontSize: 12, color: "#94a3b8" }}>
                  Untitled — Notepad (Windows 11 RichEdit)
                </span>
              </div>

              {/* Text Area */}
              <div style={{ flex: 1, padding: "32px 40px", position: "relative" }}>
                <span
                  style={{
                    fontFamily: theme.fonts.sans,
                    fontSize: 32,
                    fontWeight: 600,
                    lineHeight: 1.5,
                    color: "#f8fafc",
                    letterSpacing: "-0.01em",
                  }}
                >
                  {currentDictateText}
                </span>
                {frame >= 95 && frame < 180 && (
                  <span
                    style={{
                      display: "inline-block",
                      width: 3,
                      height: 34,
                      backgroundColor: theme.colors.cyan,
                      marginLeft: 4,
                      verticalAlign: "middle",
                    }}
                  />
                )}

                {/* Devanagari script toggle chip at frame 185 */}
                {frame >= 185 && (
                  <div
                    style={{
                      marginTop: 24,
                      padding: "16px 20px",
                      borderRadius: 12,
                      backgroundColor: "rgba(99, 102, 241, 0.12)",
                      border: `1px solid ${theme.colors.primary}`,
                      display: "flex",
                      alignItems: "center",
                      gap: 16,
                    }}
                  >
                    <span style={{ fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.cyan, fontWeight: 700 }}>
                      SCRIPT TOGGLE: DEVANAGARI
                    </span>
                    <span style={{ fontFamily: theme.fonts.devanagari, fontSize: 24, fontWeight: 700, color: "#ffffff" }}>
                      मीटिंग पोस्टपोन हो गई
                    </span>
                  </div>
                )}
              </div>

              {/* Status footer with formatting chips */}
              <div
                style={{
                  height: 48,
                  backgroundColor: "#16161b",
                  borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                  display: "flex",
                  alignItems: "center",
                  padding: "0 24px",
                  gap: 16,
                }}
              >
                <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.green }}>
                  ✓ Hesitation removed (umm/uhh)
                </span>
                <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.cyan }}>
                  ✓ Currency normalized (₹15,000)
                </span>
                <span style={{ fontFamily: theme.fonts.mono, fontSize: 11, color: theme.colors.primary }}>
                  ✓ 18% GST formatted
                </span>
              </div>
            </div>
          </div>
        )}

        {/* SUB-BEAT 2: TALK TO A PDF WITH CITATIONS & BARGE-IN (Frames 240 - 675) */}
        {isDocQa && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 20,
              width: 1360,
            }}
          >
            {/* Top status bar with Citation Chip & Barge-In indicator */}
            <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
              <CitationChip page="Page 1" delay={250} score={0.87} />
              {isBargeInActive && (
                <div
                  style={{
                    padding: "6px 14px",
                    borderRadius: 20,
                    backgroundColor: "rgba(244, 63, 94, 0.15)",
                    border: `1.5px solid ${theme.colors.red}`,
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: theme.colors.red }} />
                  <span style={{ fontFamily: theme.fonts.mono, fontSize: 12, fontWeight: 700, color: theme.colors.red }}>
                    VOICE BARGE-IN: INTERRUPTED (66 ms VAD)
                  </span>
                </div>
              )}
            </div>

            {/* Split Screen: PDF on Left, Conversational Q&A on Right */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1.1fr 1.3fr",
                gap: 24,
                width: "100%",
                height: 520,
              }}
            >
              {/* Left: Real Document UI Capture */}
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
                {/* Visual highlight over Page 1 section */}
                <div
                  style={{
                    position: "absolute",
                    top: 140,
                    left: 20,
                    right: 20,
                    height: 80,
                    borderRadius: 8,
                    border: `2px solid ${theme.colors.green}`,
                    backgroundColor: "rgba(16, 185, 129, 0.15)",
                    pointerEvents: "none",
                  }}
                />
              </div>

              {/* Right: Live Interactive Q&A Card */}
              <div
                style={{
                  borderRadius: 16,
                  backgroundColor: "#121724",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 16,
                  boxShadow: theme.shadows.card,
                }}
              >
                {/* Question Bubble */}
                <div
                  style={{
                    padding: "14px 18px",
                    borderRadius: 12,
                    backgroundColor: "rgba(99, 102, 241, 0.15)",
                    border: `1px solid ${theme.colors.primary}`,
                    alignSelf: "flex-end",
                    maxWidth: "85%",
                  }}
                >
                  <span style={{ fontFamily: theme.fonts.sans, fontSize: 16, fontWeight: 600, color: "#ffffff" }}>
                    {frame < 580 ? "Kya ICU charges cover hote hain?" : "Space travel cover chhe?"}
                  </span>
                </div>

                {/* Streaming Answer Bubble */}
                {frame >= 380 && (
                  <div
                    style={{
                      padding: "18px 22px",
                      borderRadius: 12,
                      backgroundColor: "rgba(16, 185, 129, 0.1)",
                      border: `1px solid ${frame < 580 ? theme.colors.green : theme.colors.red}`,
                      alignSelf: "flex-start",
                      maxWidth: "90%",
                      display: "flex",
                      flexDirection: "column",
                      gap: 8,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span
                        style={{
                          fontFamily: theme.fonts.mono,
                          fontSize: 11,
                          fontWeight: 700,
                          color: frame < 580 ? theme.colors.green : theme.colors.red,
                        }}
                      >
                        {frame < 580 ? "PAGE 1 CITATION VERIFIED" : "REFUSAL (THRESHOLD: 0.785)"}
                      </span>
                      <Waveform
                        bars={8}
                        height={16}
                        color={frame < 580 ? theme.colors.green : theme.colors.red}
                        isListening={!isBargeInActive}
                        isInterrupted={isBargeInActive}
                      />
                    </div>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 16, lineHeight: 1.5, color: "#f8fafc" }}>
                      {frame < 580
                        ? "Page 1 ke mutabiq ICU charges pure cover hote hain. Room rent 2% sum insured per diem apply hota hai."
                        : "Yeh document mein nahi hai. Document sirf standard healthcare aur hospitalization cover karta hai."}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* SUB-BEAT 3: 100% AIR-GAPPED OFFLINE MODE (Frames 675 - 915) */}
        {isOffline && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 24,
              width: 1200,
            }}
          >
            {/* Offline Green Banner */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                padding: "12px 32px",
                borderRadius: 40,
                backgroundColor: "rgba(16, 185, 129, 0.15)",
                border: `2px solid ${theme.colors.green}`,
                boxShadow: "0 0 30px rgba(16, 185, 129, 0.3)",
              }}
            >
              <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: theme.colors.green }} />
              <span style={{ fontFamily: theme.fonts.sans, fontSize: 20, fontWeight: 800, color: theme.colors.green }}>
                🟢 100% AIR-GAPPED OFFLINE MODE (Zero Cloud Transmission)
              </span>
            </div>

            {/* Offline Subsystem Checklist Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 20,
                width: "100%",
              }}
            >
              {[
                { name: "Speech-to-Text", tech: "faster-whisper CT2 (Local GPU/CPU)", status: "100% Offline" },
                { name: "Document Embeddings", tech: "multilingual-e5-base + FAISS (Local RAM)", status: "100% Offline" },
                { name: "Reasoning Engine", tech: "Ollama gemma3:4b (localhost:11434)", status: "100% Offline" },
                { name: "Voice Synthesis", tech: "Piper ONNX (hi_IN-pratham-medium)", status: "100% Offline" },
              ].map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "20px 26px",
                    borderRadius: 14,
                    backgroundColor: "#121724",
                    border: "1px solid rgba(16, 185, 129, 0.3)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <span style={{ fontFamily: theme.fonts.sans, fontSize: 16, fontWeight: 700, color: "#f8fafc" }}>
                      {item.name}
                    </span>
                    <span style={{ fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.textMuted }}>
                      {item.tech}
                    </span>
                  </div>
                  <div
                    style={{
                      padding: "4px 12px",
                      borderRadius: 8,
                      backgroundColor: "rgba(16, 185, 129, 0.15)",
                      fontFamily: theme.fonts.mono,
                      fontSize: 12,
                      fontWeight: 700,
                      color: theme.colors.green,
                    }}
                  >
                    ✓ {item.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="05" sectionTitle="IN ACTION" />

      {/* 4. Burned-in Captions Pill */}
      <CaptionPill cues={SCENE_CAPTIONS.LiveProduct} />

      {/* 5. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};

