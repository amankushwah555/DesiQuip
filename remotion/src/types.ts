// Mirrors desiquip/services/render.py::build_render_props. Change both together.
export type CaptionWord = { text: string; start: number; end: number };
export type CaptionGroup = { start: number; end: number; words: CaptionWord[] };
export type SceneProps = {
  start: number;
  end: number;
  caption: string;
  asset: string | null;
  sfx: string | null;
};
export type ShortProps = {
  fps: number;
  durationInFrames: number;
  audio: string | null;
  characterImage: string | null;
  aiTag: boolean;
  loopEnd: boolean;
  hook: { text: string; untilS: number };
  scenes: SceneProps[];
  captionGroups: CaptionGroup[];
};
