import React from "react";
import { Composition } from "remotion";
import { Short } from "./Short";
import type { ShortProps } from "./types";

// Preview data for `npm run studio`. Real renders pass --props from Python.
const preview: ShortProps = {
  fps: 30,
  durationInFrames: 150,
  audio: null,
  aiTag: true,
  loopEnd: true,
  hook: { text: "अंकल ने फिर से किया!", untilS: 2 },
  scenes: [
    { start: 0, end: 2.5, caption: "अरे बाप रे!", prompt: "", asset: null, sfx: null },
    { start: 2.5, end: 5, caption: "ये क्या है?", prompt: "", asset: null, sfx: null },
  ],
  captionGroups: [
    { start: 0.2, end: 1.2, words: [
      { text: "अरे", start: 0.2, end: 0.5 }, { text: "बाप", start: 0.55, end: 0.85 }, { text: "रे!", start: 0.9, end: 1.2 }] },
    { start: 2.7, end: 3.6, words: [
      { text: "ये", start: 2.7, end: 2.9 }, { text: "क्या", start: 2.95, end: 3.2 }, { text: "है?", start: 3.25, end: 3.6 }] },
  ],
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={150}
    defaultProps={preview}
    calculateMetadata={({ props }) => ({ durationInFrames: props.durationInFrames, fps: props.fps })}
  />
);
