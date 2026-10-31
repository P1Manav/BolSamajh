// BolSamajh Product Launch Film — Master Timeline
// Target Duration: Exactly 90.0 seconds @ 30 fps = 2700 frames (Hard cap)
// 5 Core Story Chapters based on submission/demo_script.md

export const FPS = 30;

export const SCENE_DURATIONS = {
  Hook: 360,     // 0:00 - 0:12 (12.0s) - Problem Hook: 500M Hinglish speakers vs closed cloud pricing
  Dictate: 660,  // 0:12 - 0:34 (22.0s) - Push-to-Talk in Notepad: Alt+Shift+Space, ₹/GST formatting, Devanagari script
  DocQA: 900,    // 0:34 - 1:04 (30.0s) - Talk-to-Document: sample_policy.pdf, [Page 1] chip, 66ms barge-in, refusal
  Offline: 420,  // 1:04 - 1:18 (14.0s) - Wi-Fi off: 100% Air-Gapped Mode badge & public benchmark table
  Close: 360,    // 1:18 - 1:30 (12.0s) - Web-Call, Android companion, Bolna gateway & Windows installer
} as const;

export const TOTAL_DURATION_IN_FRAMES = 2700; // Exactly 90.0 seconds

// Exact Audio Sequence Cue Sheet (Global Frames 0 - 2700)
// Verified ZERO temporal overlap across all 2700 frames
export const AUDIO_CUES = {
  // Chapter 1: Problem Hook (0 - 360)
  c1_hook_narrator: { from: 15, duration: 307, file: "audio/final/c1_hook_narrator.mp3" },

  // Chapter 2: Dictation Anywhere (360 - 1020)
  c2_dictate_intro: { from: 375, duration: 199, file: "audio/final/c2_dictate_intro.mp3" },
  c2_demo_prompt: { from: 585, duration: 161, file: "audio/final/c2_demo_prompt.mp3" },
  c2_dictate_formatting: { from: 760, duration: 205, file: "audio/final/c2_dictate_formatting.mp3" },

  // Chapter 3: Talk-to-Document Intelligence (1020 - 1920)
  c3_docqa_intro: { from: 1030, duration: 207, file: "audio/final/c3_docqa_intro.mp3" },
  c3_demo_q1: { from: 1245, duration: 99, file: "audio/final/c3_demo_q1.mp3" },
  c3_demo_a1: { from: 1355, duration: 145, file: "audio/final/c3_demo_a1.mp3" },
  c3_bargein_user: { from: 1505, duration: 75, file: "audio/final/c3_bargein_user.mp3" },
  c3_bargein_narrator: { from: 1585, duration: 143, file: "audio/final/c3_bargein_narrator.mp3" },
  c3_demo_a_refusal: { from: 1735, duration: 68, file: "audio/final/c3_demo_a_refusal.mp3" },
  c3_refusal_narrator: { from: 1810, duration: 102, file: "audio/final/c3_refusal_narrator.mp3" },

  // Chapter 4: Air-Gapped Offline Mode & Benchmark (1920 - 2340)
  c4_offline_narrator: { from: 1930, duration: 199, file: "audio/final/c4_offline_narrator.mp3" },
  c4_benchmark_narrator: { from: 2145, duration: 163, file: "audio/final/c4_benchmark_narrator.mp3" },

  // Chapter 5: Web Call, Android & Close (2340 - 2700)
  c5_close_unified: { from: 2350, duration: 338, file: "audio/final/c5_close_unified.mp3" },
} as const;
