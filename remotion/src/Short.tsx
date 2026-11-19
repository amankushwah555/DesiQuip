import React from "react";
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/NotoSansDevanagari";
import type { CaptionGroup, SceneProps, ShortProps } from "./types";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["devanagari", "latin"] });

const PALETTE = ["#ff6b35", "#7b2cbf", "#06d6a0", "#ef476f", "#118ab2", "#ffd166"];
const EMOJI = ["😱", "😂", "🤦‍♂️", "😳", "🤣", "🙄", "😅", "🤯"];
const isVideo = (src: string) => /\.(mp4|mov|webm|mkv)$/i.test(src);

const SceneView: React.FC<{ scene: SceneProps; index: number; characterImage: string | null }> = ({ scene, index, characterImage }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  // Zoom punch on every cut (spec: a visual change at least every 3-4 s), then a slow push-in.
  const punch = spring({ frame, fps, config: { damping: 12, stiffness: 180 }, from: 1.25, to: 1 });
  const drift = interpolate(frame, [0, durationInFrames], [1, 1.08], { extrapolateRight: "clamp" });
  const scale = punch * drift;

  if (scene.asset) {
    const src = staticFile(scene.asset);
    return (
      <AbsoluteFill style={{ transform: `scale(${scale})` }}>
        {isVideo(scene.asset)
          ? <OffthreadVideo src={src} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          : <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
      </AbsoluteFill>
    );
  }
  // No clip for this scene (no AI video yet): animated gradient + a bouncing reaction emoji.
  const a = PALETTE[index % PALETTE.length];
  const b = PALETTE[(index + 2) % PALETTE.length];
  const bounce = Math.sin((frame / fps) * Math.PI * 2) * 18;
  const emoji = EMOJI[index % EMOJI.length];
  return (
    <AbsoluteFill style={{ background: `linear-gradient(160deg, ${a}, ${b})`, transform: `scale(${scale})` }}>
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: "17%" }}>
        {characterImage
          ? <Img src={staticFile(characterImage)} style={{ height: "40%", objectFit: "contain", transform: `translateY(${bounce}px) rotate(${bounce / 6}deg)` }} />
          : <div style={{ fontSize: 300, transform: `translateY(${bounce}px) rotate(${bounce / 4}deg)` }}>{emoji}</div>}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Captions: React.FC<{ groups: CaptionGroup[] }> = ({ groups }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const group = groups.find((g) => t >= g.start && t <= g.end + 0.15);
  if (!group) return null;
  const pop = spring({ frame: frame - Math.round(group.start * fps), fps, config: { damping: 14 }, from: 0.8, to: 1 });
  return (
    // Safe zone: kept between ~55% and 75% height, clear of the Shorts UI at the bottom and right.
    <AbsoluteFill style={{ top: "58%", height: "17%", justifyContent: "center", alignItems: "center", padding: "0 90px" }}>
      <div style={{ transform: `scale(${pop})`, textAlign: "center", lineHeight: 1.25 }}>
        {group.words.map((w, i) => {
          const active = t >= w.start && t <= w.end + 0.05;
          return (
            <span key={i} style={{
              fontFamily, fontWeight: 800, fontSize: 96, margin: "0 12px",
              color: active ? "#ffe600" : "#ffffff",
              WebkitTextStroke: "6px #000", paintOrder: "stroke fill",
              textShadow: "0 8px 24px rgba(0,0,0,0.6)",
            }}>{w.text}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Hook: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 10, stiffness: 200 }, from: 0.3, to: 1 });
  return (
    <AbsoluteFill style={{ top: "3%", height: "13%", justifyContent: "center", alignItems: "center", padding: "0 70px" }}>
      <div style={{
        transform: `scale(${s}) rotate(-2deg)`, background: "#ffe600", color: "#000", fontFamily,
        fontWeight: 800, fontSize: 70, padding: "14px 32px", borderRadius: 24, textAlign: "center",
        boxShadow: "0 12px 0 #000",
      }}>{text}</div>
    </AbsoluteFill>
  );
};

const AiTag: React.FC = () => (
  <div style={{
    position: "absolute", top: 60, left: 50, fontFamily: "sans-serif", fontSize: 30, fontWeight: 700,
    color: "rgba(255,255,255,0.85)", background: "rgba(0,0,0,0.35)", padding: "6px 14px", borderRadius: 10,
  }}>AI</div>
);

export const Short: React.FC<ShortProps> = ({ scenes, captionGroups, audio, characterImage, hook, aiTag, loopEnd }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();
  // Loop end: fade the last 6 frames toward the first scene's colour so the replay feels seamless.
  const loopFade = loopEnd ? interpolate(frame, [durationInFrames - 6, durationInFrames], [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {scenes.map((scene, i) => {
        const from = Math.round(scene.start * fps);
        const dur = Math.max(1, Math.round(scene.end * fps) - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur} name={`scene ${i}`}>
            <SceneView scene={scene} index={i} characterImage={characterImage} />
          </Sequence>
        );
      })}
      {loopEnd && <AbsoluteFill style={{ backgroundColor: PALETTE[0], opacity: loopFade * 0.6 }} />}
      <Sequence durationInFrames={Math.round(hook.untilS * fps)} name="hook"><Hook text={hook.text} /></Sequence>
      <Captions groups={captionGroups} />
      {aiTag && <AiTag />}
      {audio && <Audio src={staticFile(audio)} />}
    </AbsoluteFill>
  );
};
