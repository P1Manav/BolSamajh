import { Easing } from "remotion";

export const theme = {
  colors: {
    // Base backgrounds
    bg: "#07080a",
    bgCard: "#121724",
    bgCardHover: "#192033",
    bgInput: "#171d2d",

    // Brand & Accents
    primary: "#6366f1",    // Indigo Hero
    secondary: "#8b5cf6",  // Purple Glow
    cyan: "#06b6d4",       // Cyan Accent
    green: "#10b981",      // Verified Emerald / Citations / Offline OK
    red: "#f43f5e",        // Refusal / Error / Problem warning
    amber: "#f59e0b",      // Attention

    // Neutral text
    text: "#f1f5f9",
    textMuted: "#94a3b8",
    textDim: "#64748b",

    // Borders
    border: "rgba(255, 255, 255, 0.08)",
    borderStrong: "rgba(255, 255, 255, 0.16)",
    borderAccent: "rgba(99, 102, 241, 0.35)",
    borderGreen: "rgba(16, 185, 129, 0.35)",

    // Problem scene light theme
    lightBg: "#f8fafc",
    lightCard: "#ffffff",
    lightText: "#0f172a",
    lightTextMuted: "#475569",
    lightBorder: "#e2e8f0",
  },

  fonts: {
    sans: "'Inter', system-ui, -apple-system, sans-serif",
    mono: "'JetBrains Mono', 'Fira Code', monospace",
    serif: "'Playfair Display', Georgia, serif",
    devanagari: "'Noto Sans Devanagari', 'Inter', sans-serif",
    gujarati: "'Noto Sans Gujarati', 'Inter', sans-serif",
  },

  ease: {
    out: Easing.bezier(0.22, 1, 0.36, 1),
    inOut: Easing.bezier(0.65, 0, 0.35, 1),
    gentle: Easing.bezier(0.25, 0.1, 0.25, 1),
  },

  spring: {
    smooth: { damping: 16, stiffness: 90, mass: 0.9 },
    snappy: { damping: 14, stiffness: 120, mass: 0.7 },
    bouncy: { damping: 12, stiffness: 140, mass: 0.6 },
    slow: { damping: 20, stiffness: 60, mass: 1.2 },
  },

  shadows: {
    glow: "0 0 35px rgba(99, 102, 241, 0.35)",
    glowGreen: "0 0 35px rgba(16, 185, 129, 0.35)",
    glowCyan: "0 0 35px rgba(6, 182, 212, 0.35)",
    card: "0 20px 40px -15px rgba(0, 0, 0, 0.7)",
    window: "0 30px 60px -20px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.08)",
  },

  layout: {
    safeMarginX: 96,
    safeMarginY: 64,
  },
} as const;

