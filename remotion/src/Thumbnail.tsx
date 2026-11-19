import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { loadFont } from "@remotion/google-fonts/NotoSansDevanagari";

const { fontFamily } = loadFont("normal", { weights: ["800"], subsets: ["devanagari", "latin"] });

export type ThumbnailProps = { text: string; variant: number; characterImage: string | null };

const BG = [
  "linear-gradient(160deg, #ff3d00, #ffb300)",
  "linear-gradient(160deg, #6a00f4, #ff006e)",
  "linear-gradient(160deg, #00b4d8, #06d6a0)",
];

// Vertical 1080x1920 Shorts thumbnail: big character (or reaction emoji) + one punchy Hindi line.
export const Thumbnail: React.FC<ThumbnailProps> = ({ text, variant, characterImage }) => (
  <AbsoluteFill style={{ background: BG[(variant - 1) % BG.length] }}>
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center" }}>
      {characterImage
        ? <Img src={staticFile(characterImage)} style={{ height: "68%", objectFit: "contain" }} />
        : <div style={{ fontSize: 520, marginBottom: 160 }}>{["😱", "🤣", "🤯"][(variant - 1) % 3]}</div>}
    </AbsoluteFill>
    <AbsoluteFill style={{ top: "9%", height: "26%", justifyContent: "center", alignItems: "center", padding: "0 60px" }}>
      <div style={{
        fontFamily, fontWeight: 800, fontSize: 150, lineHeight: 1.15, textAlign: "center", color: "#ffe600",
        WebkitTextStroke: "12px #000", paintOrder: "stroke fill", transform: "rotate(-3deg)",
        textShadow: "0 14px 0 #000",
      }}>{text}</div>
    </AbsoluteFill>
  </AbsoluteFill>
);
