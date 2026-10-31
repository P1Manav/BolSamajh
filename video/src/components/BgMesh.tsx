import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { theme } from "../theme";

export const BgMesh: React.FC<{
  primaryColor?: string;
  accentColor?: string;
  isLight?: boolean;
}> = ({
  primaryColor = theme.colors.primary,
  accentColor = theme.colors.cyan,
  isLight = false,
}) => {
  const frame = useCurrentFrame();
  const d1 = Math.sin(frame / 60) * 40;
  const d2 = Math.cos(frame / 75) * 35;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: isLight ? theme.colors.lightBg : theme.colors.bg,
        overflow: "hidden",
      }}
    >
      {/* Primary ambient orb */}
      <div
        style={{
          position: "absolute",
          width: 1100,
          height: 1100,
          borderRadius: "50%",
          top: -350,
          left: -200 + d1,
          filter: "blur(120px)",
          background: `radial-gradient(circle, ${primaryColor}${isLight ? "18" : "28"}, transparent 65%)`,
          pointerEvents: "none",
        }}
      />

      {/* Secondary accent orb */}
      <div
        style={{
          position: "absolute",
          width: 950,
          height: 950,
          borderRadius: "50%",
          bottom: -350,
          right: -200 - d2,
          filter: "blur(130px)",
          background: `radial-gradient(circle, ${accentColor}${isLight ? "15" : "22"}, transparent 68%)`,
          pointerEvents: "none",
        }}
      />

      {/* Subtle dot matrix grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `radial-gradient(rgba(${isLight ? "0,0,0,0.06" : "255,255,255,0.05"}) 1px, transparent 1px)`,
          backgroundSize: "32px 32px",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};

