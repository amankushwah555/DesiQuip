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

    def script_rules(self):
        from .domain.rules import ScriptRules
        v, w, vid = self.cfg["voice"], self.cfg.get("writer", {}), self.cfg["video"]
        return ScriptRules(chars_per_s=float(w.get("chars_per_s", 8.0)), gap_s=v["scene_gap_s"],
                           min_scene_s=v["min_scene_s"], max_scene_s=float(w.get("max_scene_s", 4.5)),
                           min_len_s=vid["min_length_s"], max_len_s=vid["max_length_s"])

    def agent_runner(self):
        from .adapters.claude_agent import ClaudeAgent
        budget = float(self.cfg.get("agents", {}).get("budget_usd", 1.0))
        return self._once("agents", lambda: ClaudeAgent(self.root, budget))

    def writer(self):
        from .adapters.claude_writer import ClaudeCodeWriter
        return ClaudeCodeWriter(self.agent_runner())

    def rights(self):
        from .adapters.rights import SqliteRights
        return self._once("rights", lambda: SqliteRights(self.root / "data" / "desiquip.db"))

    def reviewer(self):
        if not self.cfg.get("qa", {}).get("claude_review", True):
            return None
        from .adapters.claude_reviewer import ClaudeReviewer
        return ClaudeReviewer(self.agent_runner(), self.root)

    def qa_service(self):
        from .domain.qa import QARules
        from .services.qa import QAService
        q, vid = self.cfg.get("qa", {}), self.cfg["video"]
        rules = QARules(min_len_s=vid["min_length_s"], max_len_s=vid["max_length_s"],
                        width=vid["width"], height=vid["height"], fps=vid["fps"], lufs=vid["loudness_lufs"],
                        min_humour=int(q.get("min_humour", 7)), min_hook=int(q.get("min_hook", 7)))
        return QAService(self.media(), self.store(), self.rights(), self.reviewer(), rules)

    # --- use cases --------------------------------------------------------
    def write_service(self):
        from .services.write import WriteService
        retries = int(self.cfg.get("writer", {}).get("retries", 1))
        return WriteService(self.writer(), self.store(), self.script_rules(), retries)

    def validate_job(self, job_id: str) -> list[str]:
        from .services.write import script_problems
        store = self.store()
        idea = store.read_json(job_id, "idea.json") if store.has(job_id, "idea.json") else {}
        return script_problems(store, job_id, self.script_rules(), idea.get("source_id"))

    def clip_generator(self):
        models = list(self.cfg.get("clips", {}).get("models") or [])
        if not models:
            return None  # free mode: the template animates every scene
        from .adapters.fal_video import FalVideo
        return self._once("clips", lambda: FalVideo(models))

    def clip_service(self):
        from .services.clips import ClipService
        return ClipService(self.clip_generator(), self.store(),
                           int(self.cfg.get("clips", {}).get("max_hero", 3)))

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
        return RenderService(self.renderer(), self.store(), self.cfg["video"]["fps"], self.root / "characters")

    def jobs(self):
        from .adapters.jobs_db import SqliteJobs
        return self._once("jobs", lambda: SqliteJobs(self.root / "data" / "desiquip.db"))

    def approver(self):
        import os
        from .adapters.approval import ConsoleApprover, TelegramApprover
        token, chat = os.environ.get("TG_BOT_TOKEN", "").strip(), os.environ.get("TG_CHAT_ID", "").strip()
        if token and chat:
            return self._once("approver", lambda: TelegramApprover(token, chat, self.root / "data" / "telegram_offset"))
        return self._once("approver", lambda: ConsoleApprover(self.root / "data" / "decisions.json"))

    def flow(self) -> list[str]:
        return list(self.cfg.get("flow", {}).get("produce") or
                    ["write", "voice", "clips", "captions", "render", "finalize", "qa", "package"])

    def orchestrator(self, run_step):
        from .services.orchestrator import Orchestrator
        return Orchestrator(run_step, self.jobs(), self.approver(), self.store(), self.flow(),
                            int(self.cfg.get("flow", {}).get("max_retries", 2)), self.root / "growth" / "learnings.md")

    def trend_service(self):
        import os
        from .services.trends import TrendService
        source = None
        key = os.environ.get("YT_API_KEY", "").strip()
        if key:
            from .adapters.youtube_trending import YouTubeTrending
            source = YouTubeTrending(key)
        return TrendService(self.agent_runner(), source, self.store(), self.rights(), self.jobs(), self.root,
                            self.cfg.get("daily", {}).get("character", "uncle_ji"))

    def daily_count(self) -> int:
        return int(self.cfg.get("daily", {}).get("jobs", 2))

    def package_service(self):
        from .services.package import PackageService
        return PackageService(self.agent_runner(), self.renderer(), self.store(), self.root / "characters")

    def finalize_service(self):
        from .services.finalize import FinalizeService
        return FinalizeService(self.media(), self.store(), self.video_spec())

    def publish_service(self):
        from .adapters.crosspost import from_env
        from .services.publish import PublishService
        return PublishService(self.uploader(), self.store(), self.cfg["youtube"], from_env(), self._publish_at)

    def _publish_at(self):
        """Next free slot from growth/best-times.json (the Growth agent keeps it updated), in IST."""
        import json
        from datetime import datetime, timedelta, timezone
        from .domain.schedule import next_publish_time
        ist = timezone(timedelta(hours=5, minutes=30))
        bt = self.root / "growth" / "best-times.json"
        slots = json.loads(bt.read_text(encoding="utf-8")).get("slots") if bt.is_file() else None
        taken = []
        for up in (self.root / "jobs").glob("*/upload.json"):
            at = json.loads(up.read_text(encoding="utf-8")).get("publish_at")
            if at:
                taken.append(datetime.fromisoformat(at))
        return next_publish_time(datetime.now(ist), slots or ["18:30", "20:30"], taken)

    def affiliate_service(self):
        import os
        from .adapters.affiliate import BitlyShortener
        from .services.affiliate import AffiliateService
        bitly = os.environ.get("BITLY_TOKEN", "").strip()
        return AffiliateService(self.store(), os.environ.get("AMZ_TAG", "").strip(),
                                BitlyShortener(bitly) if bitly else None, self.root / "data" / "deals.md")

    def growth_service(self):
        from .adapters.youtube_analytics import YouTubeGrowthAPI
        from .services.growth import GrowthService
        return GrowthService(self.agent_runner(), YouTubeGrowthAPI(self.root / "secrets"), self.jobs(), self.root,
                             int(self.cfg.get("growth", {}).get("max_replies", 20)))
