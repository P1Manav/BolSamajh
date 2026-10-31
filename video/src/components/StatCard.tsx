import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

export const StatCard: React.FC<{
  targetValue: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  label: string;
  sublabel?: string;
  delay?: number;
  accentColor?: string;
}> = ({
  targetValue,
  suffix = "",
  prefix = "",
  decimals = 0,
  label,
  sublabel,
  delay = 0,
  accentColor = theme.colors.cyan,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delay,
    fps,
    config: theme.spring.smooth,
  });

  const animatedValue = interpolate(
    spring({ frame: frame - delay, fps, config: { damping: 28, stiffness: 70 } }),
    [0, 1],
    [0, targetValue]
  );

  return (
    <div
      style={{
        padding: "24px 32px",
        borderRadius: 18,
        backgroundColor: "#121724",
        border: `1.5px solid ${accentColor}44`,
        boxShadow: `0 15px 35px rgba(0, 0, 0, 0.5), 0 0 25px ${accentColor}22`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        minWidth: 260,
        opacity: entrance,
        transform: `translateY(${interpolate(entrance, [0, 1], [25, 0])}px) scale(${interpolate(entrance, [0, 1], [0.92, 1])})`,
      }}
    >
      <div
        style={{
          fontFamily: theme.fonts.mono,
          fontSize: 52,
          fontWeight: 800,
          color: accentColor,
          fontVariantNumeric: "tabular-nums",
          lineHeight: 1.1,
          marginBottom: 8,
          textShadow: `0 0 20px ${accentColor}55`,
        }}
      >
        {prefix}
        {animatedValue.toFixed(decimals)}
        {suffix}
      </div>

      <div
        style={{
          fontFamily: theme.fonts.sans,
          fontSize: 16,
          fontWeight: 700,
          color: theme.colors.text,
          textAlign: "center",
          marginBottom: 4,
        }}
      >
        {label}
      </div>

      {sublabel && (
        <div
          style={{
            fontFamily: theme.fonts.mono,
            fontSize: 12,
            color: theme.colors.textMuted,
            textAlign: "center",
          }}
        >
          {sublabel}
        </div>
      )}
    </div>
  );
};

