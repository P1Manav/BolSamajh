import React from "react";
import { AbsoluteFill } from "remotion";

export const Vignette: React.FC<{ isLight?: boolean }> = ({ isLight = false }) => (
  <AbsoluteFill
    style={{
      pointerEvents: "none",
      background: isLight
        ? "radial-gradient(ellipse at center, transparent 65%, rgba(0,0,0,0.06) 100%)"
        : "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55) 100%)",
    }}
  />
);

