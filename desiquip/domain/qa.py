"""Auto QA gate rules (spec section 7): measurable checks on the finished video."""
from __future__ import annotations

from dataclasses import dataclass

from ..ports import MediaInfo


@dataclass(frozen=True)
class QARules:
    min_len_s: float = 30.0
    max_len_s: float = 45.0
    width: int = 1080
    height: int = 1920
    fps: float = 30.0
    vcodec: str = "h264"
    acodec: str = "aac"
    lufs: float = -14.0
    lufs_tolerance: float = 2.0
    min_caption_coverage: float = 0.90
    max_products: int = 3
    min_humour: int = 7
    min_hook: int = 7


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str


def caption_coverage(groups: list[dict], duration_s: float) -> float:
    if duration_s <= 0:
        return 0.0
    return min(1.0, sum(g["end"] - g["start"] for g in groups) / duration_s)


def evaluate(info: MediaInfo, coverage: float, products: int, rights_ok: bool, rules: QARules) -> list[Check]:
    r = rules
    fmt_ok = (info.width, info.height) == (r.width, r.height) and abs(info.fps - r.fps) < 0.01 \
        and info.vcodec == r.vcodec and info.acodec == r.acodec
    return [
        Check("length", r.min_len_s <= info.duration_s <= r.max_len_s,
              f"{info.duration_s:.1f} s (needs {r.min_len_s:.0f}-{r.max_len_s:.0f} s)"),
        Check("format", fmt_ok, f"{info.width}x{info.height} {info.fps:g} fps {info.vcodec}/{info.acodec} "
                                f"(needs {r.width}x{r.height} {r.fps:g} fps {r.vcodec}/{r.acodec})"),
        Check("loudness", abs(info.lufs - r.lufs) <= r.lufs_tolerance,
              f"{info.lufs:.1f} LUFS (needs {r.lufs:g} +/- {r.lufs_tolerance:g})"),
        Check("captions", coverage >= r.min_caption_coverage,
              f"on screen {coverage:.0%} of the time (needs {r.min_caption_coverage:.0%})"),
        Check("products", products <= r.max_products, f"{products} products (max {r.max_products})"),
        Check("rights", rights_ok, "source_id has a valid rights record" if rights_ok
              else "source_id has no valid (unexpired) rights record"),
    ]
