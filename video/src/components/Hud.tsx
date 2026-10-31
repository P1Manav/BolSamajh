import React from "react";
import { Img, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { theme } from "../theme";

export const Hud: React.FC<{
  sectionNumber: string;
  sectionTitle: string;
  isLight?: boolean;
}> = ({ sectionNumber, sectionTitle, isLight = false }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Subtle breathing idle motion for the HUD tag
  const pulse = Math.sin(frame / 20) * 0.08 + 0.92;

  // Scene progress indicator
  const progress = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const textColor = isLight ? theme.colors.lightText : theme.colors.text;
  const mutedColor = isLight ? theme.colors.lightTextMuted : theme.colors.textMuted;
  const chipBg = isLight ? "rgba(0, 0, 0, 0.05)" : "rgba(255, 255, 255, 0.06)";
  const chipBorder = isLight ? "rgba(0, 0, 0, 0.12)" : "rgba(255, 255, 255, 0.12)";

  return (
    <>
      {/* Top Header Row */}
      <div
        style={{
          position: "absolute",
          top: theme.layout.safeMarginY,
          left: theme.layout.safeMarginX,
          right: theme.layout.safeMarginX,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          zIndex: 40,
          pointerEvents: "none",
        }}
      >
        {/* Brand & Section Chip */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "6px 14px",
              background: chipBg,
              border: `1px solid ${chipBorder}`,
              borderRadius: 30,
              backdropFilter: "blur(12px)",
            }}
          >
            <Img
              src={staticFile("bolsamajh.png")}
              style={{ width: 24, height: 24, borderRadius: 6, objectFit: "contain" }}
            />
            <span
              style={{
                fontFamily: theme.fonts.sans,
                fontWeight: 700,
                fontSize: 16,
                letterSpacing: "-0.01em",
                color: textColor,
              }}
            >
              BolSamajh
            </span>
          </div>

          <div
            style={{
              fontFamily: theme.fonts.mono,
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: "0.08em",
              color: isLight ? theme.colors.primary : theme.colors.cyan,
              padding: "6px 12px",
              background: isLight ? "rgba(99, 102, 241, 0.08)" : "rgba(6, 182, 212, 0.1)",
              border: `1px solid ${isLight ? "rgba(99, 102, 241, 0.25)" : "rgba(6, 182, 212, 0.25)"}`,
              borderRadius: 6,
              textTransform: "uppercase",
            }}
          >
            [{sectionNumber} // {sectionTitle}]
          </div>
        </div>

        {/* Buildathon Tag */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 14px",
            background: chipBg,
            border: `1px solid ${chipBorder}`,
            borderRadius: 30,
            backdropFilter: "blur(12px)",
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: theme.colors.primary,
              transform: `scale(${pulse})`,
              boxShadow: `0 0 10px ${theme.colors.primary}`,
            }}
          />
          <span
            style={{
              fontFamily: theme.fonts.mono,
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: "0.04em",
              color: mutedColor,
            }}
          >
            #BolnaBuildathon
          </span>
        </div>
      </div>

      {/* Bottom Progress Bar */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 3,
          backgroundColor: isLight ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.08)",
          zIndex: 40,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress}%`,
            background: `linear-gradient(90deg, ${theme.colors.primary}, ${theme.colors.cyan})`,
            boxShadow: `0 0 12px ${theme.colors.primary}`,
          }}
        />
      </div>
    </>
  );
};

