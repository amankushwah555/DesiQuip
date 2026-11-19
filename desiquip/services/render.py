"""Use case: script + timeline + captions (+ AI clips) -> render.mp4 via a VideoRenderer (Remotion)."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from ..domain.models import Script
from ..ports import JobStore, VideoRenderer


def build_render_props(script: Script, timeline: dict, captions: dict, fps: int,
                       clips: dict[str, str] | None = None, character_image: str | None = None) -> dict[str, Any]:
    """The props contract between Python and the Remotion 'Short' composition (see remotion/src/types.ts)."""
    clips = clips or {}
    scenes = []
    for i, (scene, slot) in enumerate(zip(script.scenes, timeline["scenes"])):
        scenes.append({"start": slot["start"], "end": slot["end"], "caption": scene.caption,
                       "asset": clips.get(str(i)) or scene.asset, "sfx": scene.sfx})
    return {
        "fps": fps,
        "durationInFrames": math.ceil(timeline["duration_s"] * fps),
        "audio": "voice.wav",
        "characterImage": character_image,
        "aiTag": True,  # spec: on-screen "AI-generated" tag is mandatory (India IT Rules 2026)
        "loopEnd": script.loop_end,
        "hook": {"text": script.hook.text, "untilS": script.hook.until_s},
        "scenes": scenes,
        "captionGroups": captions["groups"],
    }


class RenderService:
    def __init__(self, renderer: VideoRenderer, store: JobStore, fps: int, characters_dir: Path | None = None) -> None:
        self.characters_dir = characters_dir
        self.renderer, self.store, self.fps = renderer, store, fps

    def run(self, job_id: str) -> Path:
        jd = self.store.path(job_id)
        script = self.store.read_script(job_id)
        clips = self.store.read_json(job_id, "clips.json") if (jd / "clips.json").is_file() else {}
        char_png = self.characters_dir / f"{script.character}.png" if self.characters_dir else None
        has_char = bool(char_png and char_png.is_file())
        props = build_render_props(script, self.store.read_json(job_id, "timeline.json"),
                                   self.store.read_json(job_id, "captions.json"), self.fps, clips,
                                   "character.png" if has_char else None)

        assets: dict[str, Path] = {"voice.wav": jd / "voice.wav"}
        if has_char:
            assets["character.png"] = char_png
        for s in props["scenes"]:
            if s["asset"]:
                assets[s["asset"]] = jd / s["asset"]
        missing = [name for name, p in assets.items() if not p.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing assets in {jd}: {', '.join(missing)}")

        out = jd / "render.mp4"
        self.renderer.render(job_id, props, assets, out)
        return out
