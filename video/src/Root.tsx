import React from "react";
import {
  Composition,
  Series,
  Sequence,
  Audio,
  staticFile,
  useCurrentFrame,
  AbsoluteFill,
} from "remotion";

import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadDevanagari } from "@remotion/google-fonts/NotoSansDevanagari";
import { loadFont as loadGujarati } from "@remotion/google-fonts/NotoSansGujarati";

import { Hook } from "./scenes/Hook";
import { Dictate } from "./scenes/Dictate";
import { DocQA } from "./scenes/DocQA";
import { Offline } from "./scenes/Offline";
import { Close } from "./scenes/Close";
import { CaptionPill } from "./components/CaptionPill";

import {
  FPS,
  SCENE_DURATIONS,
  TOTAL_DURATION_IN_FRAMES,
  AUDIO_CUES,
} from "./timeline";

// Load Google Fonts for standard, monospace, and Indic scripts
loadInter("normal", { ignoreTooManyRequestsWarning: true });
loadMono("normal", { ignoreTooManyRequestsWarning: true });
loadDevanagari("normal", { ignoreTooManyRequestsWarning: true });
loadGujarati("normal", { ignoreTooManyRequestsWarning: true });

// Main 90-second product launch film
const MainFilm: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#06080e" }}>
      {/* 1. Visual Scene Sequence (2700 frames total) */}
      <Series>
        {/* Chapter 1: Problem Hook (0 - 360f / 12.0s) */}
        <Series.Sequence durationInFrames={SCENE_DURATIONS.Hook}>
          <Hook />
        </Series.Sequence>

        {/* Chapter 2: Dictation Anywhere (360 - 1020f / 22.0s) */}
        <Series.Sequence durationInFrames={SCENE_DURATIONS.Dictate}>
          <Dictate />
        </Series.Sequence>

        {/* Chapter 3: Talk-to-Document Intelligence (1020 - 1920f / 30.0s) */}
        <Series.Sequence durationInFrames={SCENE_DURATIONS.DocQA}>
          <DocQA />
        </Series.Sequence>

        {/* Chapter 4: Air-Gapped Offline Mode & Benchmark (1920 - 2340f / 14.0s) */}
        <Series.Sequence durationInFrames={SCENE_DURATIONS.Offline}>
          <Offline />
        </Series.Sequence>

        {/* Chapter 5: Ecosystem & Close (2340 - 2700f / 12.0s) */}
        <Series.Sequence durationInFrames={SCENE_DURATIONS.Close}>
          <Close />
        </Series.Sequence>
      </Series>

      {/* 2. Master Audio Sequences (Calibrated & Non-overlapping) */}
      {Object.entries(AUDIO_CUES).map(([id, cue]) => (
        <Sequence key={id} from={cue.from} durationInFrames={cue.duration}>
          <Audio src={staticFile(cue.file)} volume={1.0} />
        </Sequence>
      ))}

      {/* 3. Global Synchronized Caption Pill */}
      <CaptionPill globalFrame={frame} />
    </AbsoluteFill>
  );
};

// 12-second Teaser Preview
const Teaser: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: "#06080e" }}>
      <Hook />
      <Sequence from={AUDIO_CUES.c1_hook_narrator.from} durationInFrames={AUDIO_CUES.c1_hook_narrator.duration}>
        <Audio src={staticFile(AUDIO_CUES.c1_hook_narrator.file)} volume={1.0} />
      </Sequence>
      <CaptionPill globalFrame={frame} />
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* The Master Film — Hard Cap 90.0s @ 30fps */}
      <Composition
        id="BolSamajhFilm"
        component={MainFilm}
        durationInFrames={TOTAL_DURATION_IN_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />

      {/* 12s Social Teaser */}
      <Composition
        id="BolSamajhTeaser"
        component={Teaser}
        durationInFrames={360}
        fps={FPS}
        width={1920}
        height={1080}
      />

      {/* Individual Scene Previews */}
      <Composition
        id="Scene-01-Hook"
        component={Hook}
        durationInFrames={SCENE_DURATIONS.Hook}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="Scene-02-Dictate"
        component={Dictate}
        durationInFrames={SCENE_DURATIONS.Dictate}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="Scene-03-DocQA"
        component={DocQA}
        durationInFrames={SCENE_DURATIONS.DocQA}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="Scene-04-Offline"
        component={Offline}
        durationInFrames={SCENE_DURATIONS.Offline}
        fps={FPS}
        width={1920}
        height={1080}
      />
      <Composition
        id="Scene-05-Close"
        component={Close}
        durationInFrames={SCENE_DURATIONS.Close}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
