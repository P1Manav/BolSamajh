import React from "react";
import { AbsoluteFill, Audio, staticFile, Sequence } from "remotion";
import { theme } from "../theme";
import { Hud } from "../components/Hud";
import { CaptionPill } from "../components/CaptionPill";
import { BgMesh } from "../components/BgMesh";
import { Grade } from "../components/Grade";
import { Grain } from "../components/Grain";
import { Vignette } from "../components/Vignette";
import { NodeGraph } from "../components/NodeGraph";
import { SCENE_CAPTIONS } from "../captions";

export const HowItWorks: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: theme.colors.bg }}>
      {/* 1. Background Mesh */}
      <BgMesh primaryColor={theme.colors.cyan} accentColor={theme.colors.green} />

      {/* Audio: Voiceover */}
      <Sequence from={12}>
        <Audio src={staticFile("audio/vo/vo_04_arch_1.mp3")} volume={1} />
      </Sequence>
      <Sequence from={148}>
        <Audio src={staticFile("audio/vo/vo_04_arch_2.mp3")} volume={1} />
      </Sequence>

      <Sequence from={8}>
        <Audio src={staticFile("sfx/whoosh.wav")} volume={0.35} />
      </Sequence>

      {/* 2. Visual Content Layer: Animated Node Graph */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          paddingTop: 50,
        }}
      >
        <NodeGraph delay={10} />
      </AbsoluteFill>

      {/* 3. HUD Layer */}
      <Hud sectionNumber="04" sectionTitle="HOW IT WORKS" />

      {/* 4. Burned-in Captions Pill */}
      <CaptionPill cues={SCENE_CAPTIONS.HowItWorks} />

      {/* 5. Post Grade & Texture Stack */}
      <Grade />
      <Grain opacity={0.06} />
      <Vignette />
    </AbsoluteFill>
  );
};

