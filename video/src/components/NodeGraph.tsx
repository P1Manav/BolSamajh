import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { theme } from "../theme";

interface NodeItem {
  id: string;
  label: string;
  sublabel: string;
  x: number;
  y: number;
  isLocal: boolean;
  accent: string;
}

export const NodeGraph: React.FC<{ delay?: number }> = ({ delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const nodes: NodeItem[] = [
    {
      id: "input",
      label: "Global Hotkey / Mic",
      sublabel: "Alt+Shift+Space / Alt+Shift+A",
      x: 180,
      y: 280,
      isLocal: true,
      accent: theme.colors.cyan,
    },
    {
      id: "stt",
      label: "faster-whisper",
      sublabel: "large-v3-turbo (CUDA int8)",
      x: 520,
      y: 180,
      isLocal: true,
      accent: theme.colors.primary,
    },
    {
      id: "rag",
      label: "multilingual-e5 + FAISS",
      sublabel: "512 ctx • 22ms retrieval",
      x: 520,
      y: 380,
      isLocal: true,
      accent: theme.colors.green,
    },
    {
      id: "llm",
      label: "Ollama (Local LLM)",
      sublabel: "gemma3:4b (zero cloud fees)",
      x: 880,
      y: 280,
      isLocal: true,
      accent: theme.colors.secondary,
    },
    {
      id: "tts",
      label: "Piper / Edge-TTS",
      sublabel: "Local ONNX / Sentence Stream",
      x: 1220,
      y: 180,
      isLocal: true,
      accent: theme.colors.cyan,
    },
    {
      id: "output",
      label: "Any Active App",
      sublabel: "Notepad, Slack, WhatsApp, Web",
      x: 1220,
      y: 380,
      isLocal: true,
      accent: theme.colors.green,
    },
  ];

  // Boundary box entrance spring
  const boundarySpring = spring({
    frame: frame - delay - 20,
    fps,
    config: theme.spring.smooth,
  });

  // Animated packet progress (cycles every 45 frames)
  const packetCycle = ((frame - delay) % 45) / 45;

  return (
    <div
      style={{
        position: "relative",
        width: 1500,
        height: 600,
        margin: "0 auto",
      }}
    >
      {/* Local Air-Gapped Boundary Box */}
      <div
        style={{
          position: "absolute",
          left: 450,
          top: 80,
          width: 530,
          height: 440,
          borderRadius: 24,
          border: `2px dashed ${theme.colors.green}`,
          backgroundColor: "rgba(16, 185, 129, 0.03)",
          boxShadow: `0 0 35px rgba(16, 185, 129, 0.1)`,
          opacity: boundarySpring,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: -14,
            left: 24,
            padding: "4px 12px",
            borderRadius: 12,
            backgroundColor: "#07080a",
            border: `1px solid ${theme.colors.green}`,
            color: theme.colors.green,
            fontFamily: theme.fonts.mono,
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.06em",
          }}
        >
          ● RUNS 100% LOCALLY ON YOUR HARDWARE
        </div>
      </div>

      {/* Connection Lines & Flowing Packets SVG */}
      <svg
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      >
        <defs>
          <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={theme.colors.cyan} stopOpacity="0.4" />
            <stop offset="50%" stopColor={theme.colors.primary} stopOpacity="0.8" />
            <stop offset="100%" stopColor={theme.colors.green} stopOpacity="0.4" />
          </linearGradient>
        </defs>

        {/* Path 1: Input to STT */}
        <path d="M 280 280 L 520 220" stroke="url(#lineGrad)" strokeWidth="2.5" fill="none" strokeDasharray="6 4" />
        {/* Path 2: Input to RAG */}
        <path d="M 280 280 L 520 380" stroke="url(#lineGrad)" strokeWidth="2.5" fill="none" strokeDasharray="6 4" />
        {/* Path 3: STT to LLM */}
        <path d="M 640 220 L 880 280" stroke="url(#lineGrad)" strokeWidth="2.5" fill="none" strokeDasharray="6 4" />
        {/* Path 4: RAG to LLM */}
        <path d="M 640 380 L 880 280" stroke="url(#lineGrad)" strokeWidth="2.5" fill="none" strokeDasharray="6 4" />
        {/* Path 5: LLM to TTS */}
        <path d="M 1000 280 L 1220 220" stroke="url(#lineGrad)" strokeWidth="2.5" fill="none" strokeDasharray="6 4" />
        {/* Path 6: TTS to Output */}
        <path d="M 1000 280 L 1220 380" stroke="url(#lineGrad)" strokeWidth="2.5" fill="none" strokeDasharray="6 4" />

        {/* Animated Packets */}
        <circle
          cx={interpolate(packetCycle, [0, 1], [280, 520])}
          cy={interpolate(packetCycle, [0, 1], [280, 220])}
          r="5"
          fill={theme.colors.cyan}
          filter="drop-shadow(0 0 6px #06b6d4)"
        />
        <circle
          cx={interpolate(packetCycle, [0, 1], [640, 880])}
          cy={interpolate(packetCycle, [0, 1], [220, 280])}
          r="5"
          fill={theme.colors.primary}
          filter="drop-shadow(0 0 6px #6366f1)"
        />
        <circle
          cx={interpolate(packetCycle, [0, 1], [1000, 1220])}
          cy={interpolate(packetCycle, [0, 1], [280, 220])}
          r="5"
          fill={theme.colors.green}
          filter="drop-shadow(0 0 6px #10b981)"
        />
      </svg>

      {/* Nodes Render */}
      {nodes.map((n, i) => {
        const nodeSpring = spring({
          frame: frame - delay - i * 4,
          fps,
          config: theme.spring.smooth,
        });

        const scale = interpolate(nodeSpring, [0, 1], [0.8, 1]);

        return (
          <div
            key={n.id}
            style={{
              position: "absolute",
              left: n.x - 110,
              top: n.y - 45,
              width: 220,
              padding: "16px 18px",
              borderRadius: 16,
              backgroundColor: "#121724",
              border: `1.5px solid ${n.accent}55`,
              boxShadow: `0 15px 30px rgba(0, 0, 0, 0.5), 0 0 18px ${n.accent}22`,
              transform: `scale(${scale})`,
              opacity: nodeSpring,
              zIndex: 10,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: n.accent,
                  boxShadow: `0 0 8px ${n.accent}`,
                }}
              />
              <span
                style={{
                  fontFamily: theme.fonts.sans,
                  fontSize: 14,
                  fontWeight: 700,
                  color: theme.colors.text,
                }}
              >
                {n.label}
              </span>
            </div>
            <div
              style={{
                fontFamily: theme.fonts.mono,
                fontSize: 11,
                color: theme.colors.textMuted,
              }}
            >
              {n.sublabel}
            </div>
          </div>
        );
      })}
    </div>
  );
};

