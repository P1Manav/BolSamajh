import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";
import { facts } from "../loadFacts";

export const BenchTable: React.FC<{ delay?: number }> = ({ delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delay,
    fps,
    config: theme.spring.smooth,
  });

  const rows = [
    {
      model: "faster-whisper large-v3-turbo (Default)",
      wer: facts.turboHinglishWer, // 38.52%
      latency: "573 ms (0.079x RTF)",
      isWinner: true,
    },
    {
      model: "faster-whisper medium",
      wer: facts.mediumHinglishWer, // 50.73%
      latency: "1371 ms (0.176x RTF)",
      isWinner: false,
    },
    {
      model: "whisper-hinglish-swift (Third-party CT2)",
      wer: facts.swiftHinglishWer, // 52.70%
      latency: "100 ms (0.026x RTF)",
      isWinner: false,
    },
  ];

  return (
    <div
      style={{
        width: 1000,
        backgroundColor: "#121724",
        borderRadius: 16,
        border: `1px solid ${theme.colors.border}`,
        boxShadow: theme.shadows.card,
        overflow: "hidden",
        opacity: entrance,
        transform: `translateY(${interpolate(entrance, [0, 1], [30, 0])}px)`,
      }}
    >
      {/* Table Header */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2.2fr 1.2fr 1.6fr",
          padding: "14px 24px",
          backgroundColor: "#0d111a",
          borderBottom: `1px solid ${theme.colors.border}`,
          fontFamily: theme.fonts.mono,
          fontSize: 12,
          fontWeight: 700,
          color: theme.colors.cyan,
          letterSpacing: "0.05em",
        }}
      >
        <div>STT MODEL (HiACC Hinglish Corpus)</div>
        <div>WER (LOWER IS BETTER)</div>
        <div>MEAN LATENCY (RTX 3060 Ti)</div>
      </div>

      {/* Table Rows */}
      {rows.map((row, i) => {
        const rowSpring = spring({
          frame: frame - delay - 10 - i * 4,
          fps,
          config: theme.spring.snappy,
        });

        const barWidth = interpolate(rowSpring, [0, 1], [0, row.wer]);

        return (
          <div
            key={i}
            style={{
              display: "grid",
              gridTemplateColumns: "2.2fr 1.2fr 1.6fr",
              alignItems: "center",
              padding: "16px 24px",
              borderBottom: i < rows.length - 1 ? `1px solid ${theme.colors.border}` : undefined,
              backgroundColor: row.isWinner ? "rgba(99, 102, 241, 0.08)" : "transparent",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              {row.isWinner && (
                <div
                  style={{
                    padding: "2px 8px",
                    borderRadius: 4,
                    backgroundColor: theme.colors.green,
                    color: "#000",
                    fontFamily: theme.fonts.mono,
                    fontSize: 10,
                    fontWeight: 800,
                  }}
                >
                  BEST
                </div>
              )}
              <span
                style={{
                  fontFamily: theme.fonts.sans,
                  fontSize: 15,
                  fontWeight: row.isWinner ? 700 : 500,
                  color: row.isWinner ? theme.colors.text : theme.colors.textMuted,
                }}
              >
                {row.model}
              </span>
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span
                  style={{
                    fontFamily: theme.fonts.mono,
                    fontSize: 16,
                    fontWeight: 700,
                    color: row.isWinner ? theme.colors.cyan : theme.colors.textMuted,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {row.wer.toFixed(1)}%
                </span>
                <div
                  style={{
                    flex: 1,
                    height: 6,
                    backgroundColor: "rgba(255, 255, 255, 0.08)",
                    borderRadius: 3,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${barWidth * 1.5}%`,
                      backgroundColor: row.isWinner ? theme.colors.cyan : theme.colors.textDim,
                    }}
                  />
                </div>
              </div>
            </div>

            <div
              style={{
                fontFamily: theme.fonts.mono,
                fontSize: 14,
                color: row.isWinner ? theme.colors.text : theme.colors.textMuted,
              }}
            >
              {row.latency}
            </div>
          </div>
        );
      })}

      {/* Limitation Callout */}
      <div
        style={{
          padding: "12px 24px",
          backgroundColor: "rgba(244, 63, 94, 0.06)",
          borderTop: `1px solid rgba(244, 63, 94, 0.2)`,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <span
          style={{
            fontFamily: theme.fonts.mono,
            fontSize: 11,
            color: theme.colors.red,
            fontWeight: 700,
          }}
        >
          KNOWN LIMITATION:
        </span>
        <span
          style={{
            fontFamily: theme.fonts.sans,
            fontSize: 12,
            color: theme.colors.textMuted,
          }}
        >
          FLEURS Gujarati WER remains at {facts.turboGujaratiWer.toFixed(1)}% due to Whisper multilingual training distribution.
        </span>
      </div>
    </div>
  );
};

