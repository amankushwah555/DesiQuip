"""Domain models. Pure data + validation; no I/O, no external libraries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ScriptValidationError(ValueError):
    """script.json does not match the Writer -> Producer contract (spec section 6)."""


@dataclass(frozen=True)
class Hook:
    text: str
    visual: str = ""
    until_s: float = 2.0


@dataclass(frozen=True)
class Scene:
    t: tuple[float, float]
    prompt: str
    clip: str            # "hero" (AI-generated) or "remotion" (built in the template)
    line: str            # spoken Hindi line
    caption: str
    sfx: str | None = None
    asset: str | None = None   # optional image/video file inside the job folder


@dataclass(frozen=True)
class Product:
    ref: str
    program: str
    query: str


@dataclass(frozen=True)
class Script:
    job_id: str
    source_id: str
    character: str
    hook: Hook
    scenes: tuple[Scene, ...]
    title_options: tuple[str, ...]
    length_s: float = 0.0
    loop_end: bool = False
    products: tuple[Product, ...] = ()
    product_moment: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Script":
        errors: list[str] = []
        for key in ("job_id", "source_id", "character"):
            if not str(d.get(key, "")).strip():
                errors.append(f"{key} is required")
        hook = d.get("hook") or {}
        if not str(hook.get("text", "")).strip():
            errors.append("hook.text is required")
        scenes_raw = d.get("scenes") or []
        if not scenes_raw:
            errors.append("scenes must not be empty")
        for i, s in enumerate(scenes_raw):
            if not (str(s.get("line", "")).strip() or str(s.get("caption", "")).strip()):
                errors.append(f"scenes[{i}] needs a line or a caption")
        titles = d.get("title_options") or []
        if not titles:
            errors.append("title_options must not be empty")
        if errors:
            raise ScriptValidationError("; ".join(errors))

        return cls(
            job_id=d["job_id"],
            source_id=d["source_id"],
            character=d["character"],
            hook=Hook(text=hook["text"], visual=hook.get("visual", ""),
                      until_s=float(hook.get("until_s", 2.0))),
            scenes=tuple(Scene(t=tuple(s.get("t", (0, 0))), prompt=s.get("prompt", ""),
                               clip=s.get("clip", "remotion"), line=s.get("line", ""),
                               caption=s.get("caption", ""), sfx=s.get("sfx"),
                               asset=s.get("asset"))
                         for s in scenes_raw),
            title_options=tuple(titles),
            length_s=float(d.get("length_s", 0)),
            loop_end=bool(d.get("loop_end", False)),
            products=tuple(Product(p["ref"], p["program"], p["query"])
                           for p in d.get("products") or []),
            product_moment=dict(d.get("product_moment") or {}),
        )


@dataclass(frozen=True)
class TimelineScene:
    index: int
    start: float
    end: float
    voice_s: float

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class CaptionGroup:
    start: float
    end: float
    words: tuple[Word, ...]
