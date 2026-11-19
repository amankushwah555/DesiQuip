"""Composition root: the only place that knows which adapter implements which port.

Swapping a model or engine = changing one value in config.yaml (spec, definition of done).
Adapters are built once per process and reused, so heavy ones (the Whisper model on the GPU)
load once even when one worker processes many jobs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, TypeVar

from .adapters.job_store import FileJobStore
from .ports import VideoSpec

T = TypeVar("T")


class Container:
    def __init__(self, cfg: dict[str, Any], root: Path) -> None:
        self.cfg, self.root = cfg, Path(root)
        self._cache: dict[str, Any] = {}

    @classmethod
    def from_files(cls, root: Path) -> "Container":
        import yaml
        from dotenv import load_dotenv

        load_dotenv(root / ".env")
        with open(root / "config.yaml", encoding="utf-8-sig") as f:
            return cls(yaml.safe_load(f), root)

    def _once(self, key: str, build: Callable[[], T]) -> T:
        if key not in self._cache:
            self._cache[key] = build()
        return self._cache[key]

    # --- adapters ---------------------------------------------------------
    def store(self) -> FileJobStore:
        return self._once("store", lambda: FileJobStore(self.root / "jobs"))

    def video_spec(self) -> VideoSpec:
        v = self.cfg["video"]
        return VideoSpec(v["width"], v["height"], v["fps"], v["loudness_lufs"], v["encoder"])

    def tts(self):
        from .adapters.tts import EdgeTTS, ElevenLabsTTS

        engines = {"edge": EdgeTTS, "elevenlabs": ElevenLabsTTS}
        engine = self.cfg["voice"]["engine"]
        if engine not in engines:
            raise ValueError(f"Unknown voice.engine '{engine}' (choose: {', '.join(engines)})")
        return self._once("tts", lambda: engines[engine](self.cfg["characters"]))

    def media(self):
        from .adapters.ffmpeg import FFmpegMedia
        return self._once("media", FFmpegMedia)

    def transcriber(self):
        from .adapters.whisper import FasterWhisperTranscriber
        c = self.cfg["captions"]
        return self._once("transcriber", lambda: FasterWhisperTranscriber(c["model"], c["device"]))

    def renderer(self):
        from .adapters.remotion import RemotionRenderer
        conc = str(self.cfg["video"].get("render_concurrency", "100%"))
        return self._once("renderer", lambda: RemotionRenderer(self.root / "remotion", conc))

    def uploader(self):
        from .adapters.youtube import YouTubeUploader
        return self._once("uploader", lambda: YouTubeUploader(self.root / "secrets"))

    # --- use cases --------------------------------------------------------
    def voice_service(self):
        from .services.voice import VoiceService
        v = self.cfg["voice"]
        return VoiceService(self.tts(), self.media(), self.store(), v["scene_gap_s"], v["min_scene_s"],
                            workers=int(v.get("workers", 4)))

    def caption_service(self):
        from .services.captions import CaptionService
        c = self.cfg["captions"]
        return CaptionService(self.transcriber(), self.store(), c["language"], c["words_per_group"])

    def render_service(self):
        from .services.render import RenderService
        return RenderService(self.renderer(), self.store(), self.cfg["video"]["fps"])

    def finalize_service(self):
        from .services.finalize import FinalizeService
        return FinalizeService(self.media(), self.store(), self.video_spec())

    def publish_service(self):
        from .services.publish import PublishService
        return PublishService(self.uploader(), self.store(), self.cfg["youtube"])
