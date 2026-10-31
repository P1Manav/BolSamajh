import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

export const WindowFrame: React.FC<{
  title?: string;
  width?: number | string;
  height?: number | string;
  children: React.ReactNode;
  delay?: number;
  isLight?: boolean;
}> = ({
  title = "BolSamajh Studio — Local Voice AI Companion",
  width = 1440,
  height = 810,
  children,
  delay = 0,
  isLight = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delay,
    fps,
    config: theme.spring.smooth,
  });

  const scale = interpolate(entrance, [0, 1], [0.94, 1]);
  const translateY = interpolate(entrance, [0, 1], [30, 0]);
  const rotateX = interpolate(entrance, [0, 1], [4, 0]);

  return (
    <div
      style={{
        width,
        height,
        borderRadius: 16,
        overflow: "hidden",
        backgroundColor: isLight ? theme.colors.lightCard : theme.colors.bgCard,
        border: `1px solid ${isLight ? theme.colors.lightBorder : theme.colors.border}`,
        boxShadow: isLight
          ? "0 25px 60px -15px rgba(0, 0, 0, 0.15)"
          : theme.shadows.window,
        display: "flex",
        flexDirection: "column",
        transform: `perspective(1000px) scale(${scale}) translateY(${translateY}px) rotateX(${rotateX}deg)`,
        opacity: entrance,
      }}
    >
      {/* Window Title Bar */}
      <div
        style={{
          height: 42,
          backgroundColor: isLight ? "#f1f5f9" : "#0d111a",
          borderBottom: `1px solid ${isLight ? theme.colors.lightBorder : theme.colors.border}`,
          display: "flex",
          alignItems: "center",
          padding: "0 16px",
          gap: 12,
          flexShrink: 0,
        }}
      >
        {/* Window controls */}
        <div style={{ display: "flex", gap: 8 }}>
          <div style={{ width: 11, height: 11, borderRadius: "50%", backgroundColor: "#ef4444" }} />
          <div style={{ width: 11, height: 11, borderRadius: "50%", backgroundColor: "#f59e0b" }} />
          <div style={{ width: 11, height: 11, borderRadius: "50%", backgroundColor: "#10b981" }} />
        </div>

        {/* Title */}
        <div
          style={{
            flex: 1,
            textAlign: "center",
            fontFamily: theme.fonts.sans,
            fontSize: 13,
            fontWeight: 500,
            color: isLight ? theme.colors.lightTextMuted : theme.colors.textMuted,
            letterSpacing: "0.01em",
            marginRight: 48,
          }}
        >
          {title}
        </div>
      </div>

      {/* Window Body */}
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        {children}
      </div>
    </div>
  );
};

