"""Use case: render.mp4 -> final.mp4 (1080x1920, 30 fps, H.264/AAC, -14 LUFS)."""
from __future__ import annotations

from pathlib import Path

from ..ports import JobStore, MediaTool, VideoSpec


class FinalizeService:
    def __init__(self, media: MediaTool, store: JobStore, spec: VideoSpec) -> None:
        self.media, self.store, self.spec = media, store, spec

    def run(self, job_id: str) -> Path:
        jd = self.store.path(job_id)
        out = jd / "final.mp4"
        self.media.finalize(jd / "render.mp4", out, self.spec)
        return out
