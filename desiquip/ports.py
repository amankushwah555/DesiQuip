"""Ports: the interfaces the application needs from the outside world.

Services depend only on these. Real implementations live in desiquip/adapters,
test doubles in tests/fakes. container.py picks the adapters from config.yaml.
"""
from __future__ import annotations

from dataclasses import dataclass
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


class ScriptWriter(Protocol):
    """Writes jobs/<id>/script.json from jobs/<id>/idea.json; feedback = problems with the last attempt."""
    def write(self, job_id: str, feedback: list[str]) -> None: ...


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
