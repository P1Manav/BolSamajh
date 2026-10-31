import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { OverlayPill } from "../components/OverlayPill";

export const Dictate: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Typing animation for Dictate (starts around frame 240 to 410)
  const fullDictateText = "Invoice pe 18% GST add karke total ₹15,000 kar do.";
  const charsTyped = Math.floor(
    interpolate(frame, [250, 410], [0, fullDictateText.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    })
  );
  const currentDictateText = fullDictateText.slice(0, charsTyped);

  const windowEntrance = spring({
    frame: frame - 10,
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
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 40,
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 22,
            width: 1240,
            opacity: windowEntrance,
            transform: `translateY(${interpolate(windowEntrance, [0, 1], [30, 0])}px)`,
          }}
        >
          {/* Floating Overlay HUD Pill */}
          <OverlayPill
            state={
              frame < 240
                ? "ready"
                : frame < 420
                ? "listening"
                : frame < 570
                ? "transcribing"
                : "ready"
            }
            text={
              frame < 240
                ? "Hold Alt+Shift+Space to Dictate"
                : frame < 420
                ? "Listening to Hinglish..."
                : frame < 570
                ? "Cleaned & Formatted ✓"
                : "Devanagari Script Mode Active"
            }
            hotkey="Alt+Shift+Space"
          />

          {/* Active Application Window (Windows 11 Notepad) */}
          <div
            style={{
              width: "100%",
              height: 490,
              borderRadius: 16,
              backgroundColor: "#1e1e24",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              boxShadow: theme.shadows.window,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
          >
            {/* Title Bar */}
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
                Untitled — Notepad (Windows 11 RichEdit Control)
              </span>
            </div>

            {/* Notepad Text Canvas */}
            <div style={{ flex: 1, padding: "36px 44px", position: "relative" }}>
              <span
                style={{
                  fontFamily: theme.fonts.sans,
                  fontSize: 34,
                  fontWeight: 600,
                  lineHeight: 1.5,
                  color: "#f8fafc",
                  letterSpacing: "-0.01em",
                }}
              >
                {currentDictateText}
              </span>
              {frame >= 250 && frame < 420 && (
                <span
                  style={{
                    display: "inline-block",
                    width: 3,
                    height: 36,
                    backgroundColor: theme.colors.cyan,
                    marginLeft: 4,
                    verticalAlign: "middle",
                  }}
                />
              )}

              {/* Devanagari Script Toggle Reveal at Frame 570 */}
              {frame >= 570 && (
                <div
                  style={{
                    marginTop: 28,
                    padding: "16px 22px",
                    borderRadius: 12,
                    backgroundColor: "rgba(99, 102, 241, 0.12)",
                    border: `1.5px solid ${theme.colors.primary}`,
                    display: "flex",
                    alignItems: "center",
                    gap: 18,
                  }}
                >
                  <span style={{ fontFamily: theme.fonts.mono, fontSize: 12, color: theme.colors.cyan, fontWeight: 700 }}>
                    SCRIPT TOGGLE: DEVANAGARI
                  </span>
                  <span style={{ fontFamily: theme.fonts.devanagari, fontSize: 26, fontWeight: 700, color: "#ffffff" }}>
                    मीटिंग पोस्टपोन हो गई
                  </span>
                </div>
              )}
            </div>

            {/* Footer with Normalization Badges */}
            <div
              style={{
                height: 48,
                backgroundColor: "#16161b",
                borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                display: "flex",
                alignItems: "center",
                padding: "0 24px",
                gap: 20,
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
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="02" sectionTitle="DICTATE ANYWHERE" />

      {/* 4. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};

