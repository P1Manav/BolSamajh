import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

export const CodeBlock: React.FC<{ delay?: number }> = ({ delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: frame - delay,
    fps,
    config: theme.spring.smooth,
  });

  const lines = [
    { num: 1, text: '# Bolna Drop-in Gateway Endpoint (/v1/audio/speech)', type: 'comment' },
    { num: 2, text: '@app.post("/v1/audio/speech")', type: 'decorator' },
    { num: 3, text: 'async def synthesize_speech(req: SpeechRequest):', type: 'func' },
    { num: 4, text: '    engine = get_tts_engine(mode=req.model)', type: 'code' },
    { num: 5, text: '    async for chunk in engine.stream_sentences(req.input):', type: 'loop' },
    { num: 6, text: '        if bargein_controller.is_interrupted():', type: 'warn' },
    { num: 7, text: '            break  # Silero VAD Barge-in (<75ms)', type: 'warn' },
    { num: 8, text: '        yield chunk', type: 'code' },
  ];

  return (
    <div
      style={{
        width: 680,
        backgroundColor: "#0d111a",
        borderRadius: 14,
        border: `1px solid ${theme.colors.borderStrong}`,
        boxShadow: theme.shadows.card,
        overflow: "hidden",
        opacity: entrance,
        transform: `translateY(${interpolate(entrance, [0, 1], [25, 0])}px)`,
      }}
    >
      {/* Code Header */}
      <div
        style={{
          height: 36,
          backgroundColor: "#121724",
          borderBottom: `1px solid ${theme.colors.border}`,
          display: "flex",
          alignItems: "center",
          padding: "0 14px",
          gap: 8,
        }}
      >
        <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "#ef4444" }} />
        <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "#f59e0b" }} />
        <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: "#10b981" }} />
        <span
          style={{
            fontFamily: theme.fonts.mono,
            fontSize: 11,
            color: theme.colors.textMuted,
            marginLeft: 8,
          }}
        >
          bolsamajh/web/server.py
        </span>
      </div>

      {/* Code Body */}
      <div style={{ padding: "16px 20px", display: "flex", flexDirection: "column", gap: 6 }}>
        {lines.map((l) => (
          <div key={l.num} style={{ display: "flex", gap: 14, alignItems: "center" }}>
            <span
              style={{
                fontFamily: theme.fonts.mono,
                fontSize: 12,
                color: theme.colors.textDim,
                width: 16,
                textAlign: "right",
                userSelect: "none",
              }}
            >
              {l.num}
            </span>
            <span
              style={{
                fontFamily: theme.fonts.mono,
                fontSize: 13,
                lineHeight: 1.4,
                color:
                  l.type === "comment"
                    ? theme.colors.textDim
                    : l.type === "decorator"
                    ? theme.colors.secondary
                    : l.type === "func"
                    ? theme.colors.cyan
                    : l.type === "warn"
                    ? theme.colors.green
                    : theme.colors.text,
                fontWeight: l.type === "warn" ? 700 : 500,
              }}
            >
              {l.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

