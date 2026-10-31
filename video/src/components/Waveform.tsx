import React from "react";
import { useCurrentFrame } from "remotion";
import { theme } from "../theme";

export const Waveform: React.FC<{
  bars?: number;
  height?: number;
  color?: string;
  isListening?: boolean;
  isInterrupted?: boolean;
}> = ({
  bars = 16,
  height = 36,
  color = theme.colors.cyan,
  isListening = true,
  isInterrupted = false,
}) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
        height,
      }}
    >
      {Array.from({ length: bars }).map((_, i) => {
        let barHeight = 6;
        if (isInterrupted) {
          barHeight = 2; // Flatlined when interrupted
        } else if (isListening) {
          // Dynamic sine wave height calculation
          const wave1 = Math.sin((frame * 0.22) + i * 0.45);
          const wave2 = Math.cos((frame * 0.15) - i * 0.3);
          const normalized = (wave1 + wave2 + 2) / 4; // 0 to 1
          barHeight = Math.max(4, normalized * height);
        }

        return (
          <div
            key={i}
            style={{
              width: 3.5,
              height: barHeight,
              borderRadius: 3,
              backgroundColor: isInterrupted ? theme.colors.red : color,
              transition: isInterrupted ? "height 0.05s ease" : undefined,
              boxShadow: isInterrupted
                ? "none"
                : `0 0 8px ${color}66`,
            }}
          />
        );
      })}
    </div>
  );
};

