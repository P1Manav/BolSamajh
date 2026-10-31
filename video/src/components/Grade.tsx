import React from "react";
import { AbsoluteFill } from "remotion";
import { theme } from "../theme";

export const Grade: React.FC<{ isLight?: boolean }> = ({ isLight = false }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill
      style={{
        backgroundColor: theme.colors.primary,
        mixBlendMode: isLight ? "multiply" : "soft-light",
        opacity: isLight ? 0.08 : 0.18,
      }}
    />
    <AbsoluteFill
      style={{
        background: isLight
          ? "linear-gradient(180deg, rgba(0,0,0,0.03) 0%, transparent 35%, transparent 70%, rgba(0,0,0,0.06) 100%)"
          : "linear-gradient(180deg, rgba(0,0,0,0.2) 0%, transparent 30%, transparent 75%, rgba(0,0,0,0.4) 100%)",
      }}
    />
  </AbsoluteFill>
);

