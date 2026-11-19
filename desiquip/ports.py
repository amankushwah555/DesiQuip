"""Ports: the interfaces the application needs from the outside world.

Services depend only on these. Real implementations live in desiquip/adapters,
test doubles in tests/fakes. container.py picks the adapters from config.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from .domain.models import Script, Word


@dataclass(frozen=True)
class VideoSpec:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    loudness_lufs: float = -14.0
    encoder: str = "libx264"


@dataclass(frozen=True)
class VoicePlacement:
    clip: Path
    start_s: float


@dataclass(frozen=True)
class UploadMetadata:
    title: str
    description: str
    tags: tuple[str, ...]
    category_id: str
    language: str
    privacy: str
    made_for_kids: bool
    contains_synthetic_media: bool
    publish_at: datetime | None = None   # scheduled publish (requires privacy 'private')


class ScriptWriter(Protocol):
    """Writes jobs/<id>/script.json from jobs/<id>/idea.json; feedback = problems with the last attempt."""
    def write(self, job_id: str, feedback: list[str]) -> None: ...


@dataclass(frozen=True)
class MediaInfo:
    width: int
    height: int
    fps: float
    duration_s: float
    vcodec: str
    acodec: str
    lufs: float


class QAMedia(Protocol):
    def inspect(self, path: Path) -> MediaInfo: ...
    def frames(self, src: Path, times: list[float], out_dir: Path) -> list[Path]: ...


class Reviewer(Protocol):
    """Subjective QA: returns {"hook": 0-10, "humour": 0-10, "safety_ok": bool, "notes": str}."""
    def review(self, job_id: str, frames: list[Path]) -> dict[str, Any]: ...


class RightsRegistry(Protocol):
    def add(self, source_id: str, source_type: str, owner: str, licence_url: str | None = None,
            proof_path: str | None = None, expires_at: str | None = None) -> None: ...
    def is_valid(self, source_id: str) -> bool: ...


class AgentRunner(Protocol):
    """Runs a Claude Code agent (.claude/agents/<agent>.md) headless with the given tool allow-list."""
    def run(self, agent: str, prompt: str, tools: str) -> dict[str, Any]: ...


class CrossPoster(Protocol):
    name: str
    def post(self, video: Path, caption: str) -> str: ...


class TrendSource(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class JobTracker(Protocol):
    """The jobs table: one row per job with its status (spec section 6 status flow)."""
    def create(self, job_id: str) -> None: ...
    def set(self, job_id: str, status: str, error: str | None = None, youtube_id: str | None = None) -> None: ...
    def incr_retries(self, job_id: str) -> int: ...
    def get(self, job_id: str) -> dict[str, Any] | None: ...
    def list(self, status: str | None = None) -> list[dict[str, Any]]: ...
    def counts(self) -> dict[str, int]: ...


class Approver(Protocol):
    def request(self, job_id: str, video: Path, title: str) -> None: ...
    def poll(self) -> list[tuple[str, str, str]]: ...   # (job_id, "approve" | "reject", note)
    def notify(self, text: str) -> None: ...


class StillRenderer(Protocol):
    """Renders a still image (thumbnail) from props + staged assets."""
    def still(self, job_id: str, props: dict[str, Any], assets: dict[str, Path], out: Path) -> None: ...


class ClipGenerator(Protocol):
    """Makes a vertical, silent AI video clip of about `seconds` from an English prompt."""
    def generate(self, prompt: str, seconds: int, out: Path) -> None: ...


class TextToSpeech(Protocol):
    def synthesize(self, text: str, character: str, out: Path) -> None: ...


class Transcriber(Protocol):
    def transcribe(self, audio: Path, language: str) -> list[Word]: ...


class MediaTool(Protocol):
    def duration(self, path: Path) -> float: ...
    def mix_voice(self, placements: list[VoicePlacement], total_s: float, out: Path) -> None: ...
    def finalize(self, src: Path, out: Path, spec: VideoSpec) -> None: ...


class VideoRenderer(Protocol):
    def render(self, job_id: str, props: dict[str, Any], assets: dict[str, Path], out: Path) -> None: ...


class VideoUploader(Protocol):
    def upload(self, video: Path, meta: UploadMetadata) -> str: ...


class JobStore(Protocol):
    def path(self, job_id: str) -> Path: ...
    def read_script(self, job_id: str) -> Script: ...
    def read_json(self, job_id: str, name: str) -> Any: ...
    def write_json(self, job_id: str, name: str, data: Any) -> Path: ...
