"""In-memory test doubles for every port. No ffmpeg, GPU or network needed."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from desiquip.adapters.job_store import FileJobStore
from desiquip.domain.models import Word
from desiquip.ports import UploadMetadata, VideoSpec, VoicePlacement


class FakeTTS:
    """Writes the text into the output file; duration is 0.1 s per character."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, text: str, character: str, out: Path) -> None:
        self.calls.append((text, character))
        out.write_text(text, encoding="utf-8")


class FakeMedia:
    def __init__(self) -> None:
        self.mixed: tuple[list[VoicePlacement], float, Path] | None = None
        self.finalized: tuple[Path, Path, VideoSpec] | None = None

    def duration(self, path: Path) -> float:
        return round(len(path.read_text(encoding="utf-8")) * 0.1, 3)

    def mix_voice(self, placements: list[VoicePlacement], total_s: float, out: Path) -> None:
        self.mixed = (placements, total_s, out)
        out.write_bytes(b"wav")

    def finalize(self, src: Path, out: Path, spec: VideoSpec) -> None:
        self.finalized = (src, out, spec)
        out.write_bytes(b"mp4")


class FakeTranscriber:
    def __init__(self, words: list[Word]) -> None:
        self.words = words

    def transcribe(self, audio: Path, language: str) -> list[Word]:
        return list(self.words)


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any], dict[str, Path], Path]] = []

    def render(self, job_id: str, props: dict[str, Any], assets: dict[str, Path], out: Path) -> None:
        self.calls.append((job_id, props, assets, out))
        out.write_bytes(b"render")


class FakeUploader:
    def __init__(self, video_id: str = "vid123") -> None:
        self.video_id = video_id
        self.calls: list[tuple[Path, UploadMetadata]] = []

    def upload(self, video: Path, meta: UploadMetadata) -> str:
        self.calls.append((video, meta))
        return self.video_id


__all__ = ["FakeTTS", "FakeMedia", "FakeTranscriber", "FakeRenderer", "FakeUploader", "FileJobStore"]
