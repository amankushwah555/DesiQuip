"""Use case: script + timeline + captions -> render.mp4 (via a VideoRenderer, e.g. Remotion)."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from ..domain.models import Script
from ..ports import JobStore, VideoRenderer


def build_render_props(script: Script, timeline: dict, captions: dict, fps: int) -> dict[str, Any]:
    """The props contract between Python and the Remotion 'Short' composition."""
    scenes = []
    for scene, slot in zip(script.scenes, timeline["scenes"]):
        scenes.append({"start": slot["start"], "end": slot["end"], "caption": scene.caption,
                       "prompt": scene.prompt, "asset": scene.asset, "sfx": scene.sfx})
    return {
        "fps": fps,
        "durationInFrames": math.ceil(timeline["duration_s"] * fps),
        "audio": "voice.wav",
        "aiTag": True,  # spec: on-screen "AI-generated" tag is mandatory (India IT Rules 2026)
        "loopEnd": script.loop_end,
        "hook": {"text": script.hook.text, "untilS": script.hook.until_s},
        "scenes": scenes,
        "captionGroups": captions["groups"],
    }


class RenderService:
    def __init__(self, renderer: VideoRenderer, store: JobStore, fps: int) -> None:
        self.renderer, self.store, self.fps = renderer, store, fps

    def run(self, job_id: str) -> Path:
        jd = self.store.path(job_id)
        script = self.store.read_script(job_id)
        props = build_render_props(script, self.store.read_json(job_id, "timeline.json"),
                                   self.store.read_json(job_id, "captions.json"), self.fps)

        assets: dict[str, Path] = {"voice.wav": jd / "voice.wav"}
        for s in script.scenes:
            if s.asset:
                assets[s.asset] = jd / s.asset
        missing = [name for name, p in assets.items() if not p.is_file()]
        if missing:
            raise FileNotFoundError(f"Missing assets in {jd}: {', '.join(missing)}")

        out = jd / "render.mp4"
        self.renderer.render(job_id, props, assets, out)
        return out
