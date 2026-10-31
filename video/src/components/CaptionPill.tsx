import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { MasterCaptionCue, MASTER_CAPTIONS } from "../captions";

export const CaptionPill: React.FC<{
  globalFrame?: number;
  cues?: MasterCaptionCue[];
  isLight?: boolean;
}> = ({ globalFrame, cues = MASTER_CAPTIONS, isLight = false }) => {
  const currentFrame = useCurrentFrame();
  const frame = globalFrame !== undefined ? globalFrame : currentFrame;
  const { fps } = useVideoConfig();

  // Find active cue
  const activeCue = cues.find((c) => frame >= c.from && frame <= c.to);
  if (!activeCue) return null;

  // Entrance spring (10 frames)
  const enterProgress = spring({
    frame: frame - activeCue.from,
    fps,
    config: theme.spring.snappy,
  });

  // Fast exit (8 frames before cue end)
  const framesToEnd = activeCue.to - frame;
  const exitProgress = interpolate(framesToEnd, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const opacity = Math.min(enterProgress, exitProgress);
  const translateY = interpolate(enterProgress, [0, 1], [18, 0]);

  // Split text to highlight keyword
  const words = activeCue.text.split(" ");

  return (
    <div
      style={{
        position: "absolute",
        bottom: 48,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 50,
        pointerEvents: "none",
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.28em",
          padding: "12px 28px",
          borderRadius: 36,
          backgroundColor: isLight ? "rgba(255, 255, 255, 0.94)" : "rgba(10, 13, 20, 0.92)",
          border: `1px solid ${isLight ? "rgba(0, 0, 0, 0.12)" : "rgba(255, 255, 255, 0.15)"}`,
          boxShadow: isLight
            ? "0 10px 25px rgba(0, 0, 0, 0.08)"
            : "0 15px 35px rgba(0, 0, 0, 0.6), 0 0 20px rgba(99, 102, 241, 0.15)",
          backdropFilter: "blur(16px)",
          maxWidth: 1100,
          textAlign: "center",
        }}
      >
        <span
          style={{
            fontFamily: theme.fonts.sans,
            fontSize: 24,
            fontWeight: 600,
            lineHeight: 1.3,
            color: isLight ? theme.colors.lightText : theme.colors.text,
            letterSpacing: "-0.01em",
          }}
        >
          {words.map((w, idx) => {
            const cleanWord = w.replace(/[.,/#!$%^&*;:{}=\-_`~()?"']/g, "");
            const isHighlight =
              activeCue.highlight &&
              activeCue.highlight.toLowerCase().includes(cleanWord.toLowerCase()) &&
              cleanWord.length > 1;

            return (
              <span
                key={idx}
                style={{
                  color: isHighlight
                    ? isLight
                      ? theme.colors.primary
                      : theme.colors.cyan
                    : undefined,
                  fontWeight: isHighlight ? 700 : 500,
                  marginRight: "0.24em",
                }}
              >
                {w}
              </span>
            );
          })}
        </span>
      </div>
    </div>
  );
};
