"""Use case: script.json -> voice/scene_XX.mp3 + voice.wav + timeline.json."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

from ..domain.timeline import build_timeline
from ..ports import JobStore, MediaTool, TextToSpeech, VoicePlacement

log = logging.getLogger(__name__)


class VoiceService:
    def __init__(self, tts: TextToSpeech, media: MediaTool, store: JobStore,
                 gap_s: float, min_scene_s: float, workers: int = 4) -> None:
        self.tts, self.media, self.store = tts, media, store
        self.gap_s, self.min_scene_s, self.workers = gap_s, min_scene_s, workers

    def run(self, job_id: str) -> Path:
        script = self.store.read_script(job_id)
        jd = self.store.path(job_id)
        vdir = jd / "voice"
        vdir.mkdir(exist_ok=True)

        clips: list[Path | None] = [
            vdir / f"scene_{i:02d}.mp3" if s.line.strip() else None for i, s in enumerate(script.scenes)]

        def synth(i: int) -> float:
            line, out = script.scenes[i].line.strip(), clips[i]
            if out is None:
                return 0.0
            log.info("Scene %d: synthesising %d chars", i, len(line))
            self.tts.synthesize(line, script.character, out)
            return self.media.duration(out)

        # TTS is network-bound: run scenes concurrently; map() keeps scene order.
        with ThreadPoolExecutor(max_workers=max(1, self.workers)) as pool:
            lengths = list(pool.map(synth, range(len(clips))))

        timeline = build_timeline(lengths, self.gap_s, self.min_scene_s)
        total = timeline[-1].end
        placements = [VoicePlacement(clip=c, start_s=s.start)
                      for c, s in zip(clips, timeline) if c is not None]
        wav = jd / "voice.wav"
        self.media.mix_voice(placements, total, wav)

        self.store.write_json(job_id, "timeline.json", {
            "duration_s": total,
            "scenes": [{**asdict(s), "duration": s.duration} for s in timeline],
        })
        log.info("Voice done: %.1fs, %d scenes", total, len(timeline))
        return wav
