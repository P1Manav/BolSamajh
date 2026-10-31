import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

export const CitationChip: React.FC<{
  page: string;
  delay?: number;
  score?: number;
}> = ({ page = "Page 1", delay = 0, score = 0.87 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delay,
    fps,
    config: theme.spring.bouncy,
  });

  const scale = interpolate(entrance, [0, 1], [0.8, 1]);
  const glow = Math.sin(frame / 12) * 0.2 + 0.8;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "6px 14px",
        borderRadius: 20,
        backgroundColor: "rgba(16, 185, 129, 0.15)",
        border: `1.5px solid ${theme.colors.green}`,
        boxShadow: `0 0 ${16 * glow}px rgba(16, 185, 129, 0.4)`,
        opacity: entrance,
        transform: `scale(${scale})`,
      }}
    >
      <div
        style={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          backgroundColor: theme.colors.green,
          boxShadow: `0 0 8px ${theme.colors.green}`,
        }}
      />
      <span
        style={{
          fontFamily: theme.fonts.mono,
          fontSize: 13,
          fontWeight: 700,
          color: theme.colors.green,
          letterSpacing: "0.02em",
        }}
      >
        [{page}]
      </span>
      {score && (
        <span
          style={{
            fontFamily: theme.fonts.mono,
            fontSize: 11,
            color: "rgba(16, 185, 129, 0.8)",
          }}
        >
          {(score * 100).toFixed(0)}% match
        </span>
      )}
    </div>
  );
};

