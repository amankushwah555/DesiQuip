"""Use case: AI 'hero' video clips for the 2-3 key scenes (spec: generate only 2-3 hero clips per Short).

Writes jobs/<id>/clips/scene_XX.mp4 and clips.json {scene index: path}. With no generator configured
(no FAL_KEY yet) it writes an empty clips.json and the template animates those scenes instead.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path

from ..ports import ClipGenerator, JobStore

log = logging.getLogger(__name__)


class ClipService:
    def __init__(self, generator: ClipGenerator | None, store: JobStore, max_hero: int = 3) -> None:
        self.generator, self.store, self.max_hero = generator, store, max_hero

    def run(self, job_id: str) -> Path:
        clips: dict[str, str] = {}
        if self.generator is not None:
            script = self.store.read_script(job_id)
            timeline = self.store.read_json(job_id, "timeline.json")["scenes"]
            heroes = [(i, s) for i, s in enumerate(script.scenes) if s.clip == "hero" and not s.asset]
            for i, scene in heroes[: self.max_hero]:
                seconds = math.ceil(timeline[i]["end"] - timeline[i]["start"])
                rel = f"clips/scene_{i:02d}.mp4"
                log.info("Scene %d: generating %d s hero clip", i, seconds)
                self.generator.generate(scene.prompt, seconds, self.store.path(job_id) / rel)
                clips[str(i)] = rel
        return self.store.write_json(job_id, "clips.json", clips)
