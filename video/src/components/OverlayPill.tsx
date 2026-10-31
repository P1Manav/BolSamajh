import React from "react";
import { Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { Waveform } from "./Waveform";

export type OverlayState = "ready" | "listening" | "transcribing" | "interrupted" | "offline";

export const OverlayPill: React.FC<{
  state?: OverlayState;
  text?: string;
  hotkey?: string;
  delay?: number;
}> = ({
  state = "listening",
  text = "Listening to Hinglish...",
  hotkey = "Alt+Shift+Space",
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delay,
    fps,
    config: theme.spring.smooth,
  });

  const translateY = interpolate(entrance, [0, 1], [25, 0]);

  const stateColors: Record<OverlayState, string> = {
    ready: theme.colors.green,
    listening: theme.colors.cyan,
    transcribing: theme.colors.primary,
    interrupted: theme.colors.red,
    offline: theme.colors.green,
  };

  const currentColor = stateColors[state];

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 16,
        padding: "10px 22px",
        borderRadius: 40,
        backgroundColor: "rgba(18, 23, 36, 0.92)",
        border: `1.5px solid ${currentColor}66`,
        boxShadow: `0 12px 30px rgba(0, 0, 0, 0.6), 0 0 20px ${currentColor}33`,
        backdropFilter: "blur(20px)",
        opacity: entrance,
        transform: `translateY(${translateY}px)`,
      }}
    >
      {/* App Logo */}
      <Img
        src={staticFile("bolsamajh.png")}
        style={{ width: 28, height: 28, borderRadius: 8, objectFit: "contain" }}
      />

      {/* Waveform or Status dot */}
      {state === "listening" || state === "interrupted" ? (
        <Waveform
          bars={12}
          height={24}
          color={currentColor}
          isListening={state === "listening"}
          isInterrupted={state === "interrupted"}
        />
      ) : (
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: currentColor,
            boxShadow: `0 0 10px ${currentColor}`,
          }}
        />
      )}

      {/* Status Label */}
      <div style={{ display: "flex", flexDirection: "column" }}>
        <span
          style={{
            fontFamily: theme.fonts.sans,
            fontSize: 14,
            fontWeight: 600,
            color: theme.colors.text,
            letterSpacing: "-0.01em",
          }}
        >
          {text}
        </span>
      </div>

      {/* Hotkey Tag */}
      {hotkey && (
        <div
          style={{
            fontFamily: theme.fonts.mono,
            fontSize: 11,
            fontWeight: 600,
            color: theme.colors.textMuted,
            padding: "4px 8px",
            borderRadius: 6,
            backgroundColor: "rgba(255, 255, 255, 0.08)",
            border: "1px solid rgba(255, 255, 255, 0.12)",
          }}
        >
          {hotkey}
        </div>
      )}
    </div>
  );
};

