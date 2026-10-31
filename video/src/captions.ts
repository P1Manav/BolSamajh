// Synchronized captions mapped to global timeline frames (0 - 2700)
export interface MasterCaptionCue {
  from: number;
  to: number;
  text: string;
  highlight?: string;
}

export const MASTER_CAPTIONS: MasterCaptionCue[] = [
  // Chapter 1: Problem Hook (0 - 360)
  {
    from: 15,
    to: 335,
    text: "500 million Indians speak fluid Hinglish. Commercial tools charge subscriptions, sending voice to foreign clouds.",
    highlight: "500 million",
  },

  // Chapter 2: Dictate in Notepad (360 - 1020)
  {
    from: 375,
    to: 575,
    text: "With BolSamajh, push-to-talk dictation works in any desktop app. Hold Alt+Shift+Space.",
    highlight: "Alt+Shift+Space",
  },
  {
    from: 585,
    to: 746,
    text: "Invoice pe 18% GST add karke total ₹15,000 kar do.",
    highlight: "₹15,000",
  },
  {
    from: 760,
    to: 975,
    text: "Speech is cleaned of fillers, with automatic rupee formatting and explicit script control.",
    highlight: "rupee formatting",
  },

  // Chapter 3: Talk-to-Document (1020 - 1920)
  {
    from: 1030,
    to: 1237,
    text: "Here is the wedge: Talk-to-Document intelligence. Index any PDF, then hold Alt+Shift+A.",
    highlight: "Talk-to-Document",
  },
  {
    from: 1245,
    to: 1345,
    text: "Kya ICU charges cover hote hain?",
    highlight: "ICU charges",
  },
  {
    from: 1355,
    to: 1500,
    text: "Page 1 ke mutabiq ICU charges 100% cover hote hain.",
    highlight: "Page 1",
  },
  {
    from: 1505,
    to: 1580,
    text: "Ruko! Ek minute.",
    highlight: "Ruko!",
  },
  {
    from: 1585,
    to: 1730,
    text: "Interrupt anytime with hands-free voice barge-in in under 70 milliseconds.",
    highlight: "70 milliseconds",
  },
  {
    from: 1735,
    to: 1805,
    text: "Yeh document mein nahi hai.",
    highlight: "Yeh document",
  },
  {
    from: 1810,
    to: 1915,
    text: "And it refuses out-of-document queries honestly.",
    highlight: "refuses honestly",
  },

  // Chapter 4: Offline & Benchmark (1920 - 2340)
  {
    from: 1930,
    to: 2135,
    text: "Turn off Wi-Fi: BolSamajh runs 100% air-gapped on-device with Faster-Whisper and Piper TTS.",
    highlight: "100% air-gapped",
  },
  {
    from: 2145,
    to: 2320,
    text: "Our public benchmark publishes raw and normalized WER side-by-side with complete transparency.",
    highlight: "transparency",
  },

  // Chapter 5: Web Call, Android & Close (2340 - 2700)
  {
    from: 2350,
    to: 2515,
    text: "Access browser Web-Call mode, pair with Android, or use as a free Bolna gateway.",
    highlight: "Bolna gateway",
  },
  {
    from: 2520,
    to: 2635,
    text: "Download the Windows installer on GitHub and try it in under 60 seconds.",
    highlight: "GitHub",
  },
  {
    from: 2640,
    to: 2700,
    text: "BolSamajh — Bolo. Samjho.",
    highlight: "Bolo. Samjho.",
  },
];

// Backwards-compatible shim for legacy scene files
export const SCENE_CAPTIONS: Record<string, any[]> = {};
