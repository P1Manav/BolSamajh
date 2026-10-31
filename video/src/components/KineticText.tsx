import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

export const KineticText: React.FC<{
  text: string;
  delay?: number;
  highlightWord?: string;
  highlightColor?: string;
  fontSize?: number;
  fontWeight?: number;
  lineHeight?: number;
  isLight?: boolean;
  align?: "left" | "center" | "right";
}> = ({
  text,
  delay = 0,
  highlightWord,
  highlightColor = theme.colors.primary,
  fontSize = 72,
  fontWeight = 800,
  lineHeight = 1.1,
  isLight = false,
  align = "center",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(" ");

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: align === "center" ? "center" : align === "left" ? "flex-start" : "flex-end",
        gap: "0.28em",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      {words.map((word, i) => {
        const wordDelay = delay + i * 4;
        const p = spring({
          frame: frame - wordDelay,
          fps,
          config: theme.spring.smooth,
        });

        const translateY = interpolate(p, [0, 1], [35, 0]);
        const opacity = p;

        const clean = word.replace(/[.,/#!$%^&*;:{}=\-_`~()?"']/g, "");
        const isHighlight =
          highlightWord &&
          clean.toLowerCase() === highlightWord.toLowerCase();

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontFamily: theme.fonts.sans,
              fontSize,
              fontWeight: isHighlight ? 800 : fontWeight,
              lineHeight,
              letterSpacing: "-0.03em",
              color: isHighlight
                ? highlightColor
                : isLight
                ? theme.colors.lightText
                : theme.colors.text,
              opacity,
              transform: `translateY(${translateY}px)`,
              textShadow: isHighlight
                ? `0 0 40px ${highlightColor}66`
                : undefined,
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};

