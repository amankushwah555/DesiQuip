"""Writer rules from spec section 3, checked on the script before any money is spent on voice/video."""
from __future__ import annotations

from dataclasses import dataclass

from .models import Script


@dataclass(frozen=True)
class ScriptRules:
    chars_per_s: float = 8.0     # measured: Hindi TTS speaks ~8 characters per second
    gap_s: float = 0.25          # pause after each line (must match voice.scene_gap_s)
    min_scene_s: float = 2.0
    max_scene_s: float = 4.5     # spec: a visual change at least every 3-4 s
    min_len_s: float = 30.0
    max_len_s: float = 45.0
    hook_by_s: float = 2.0       # spec: hook in the first 2 seconds
    max_title: int = 50          # spec: title < 50 characters
    max_products: int = 3


def scene_length_s(line: str, r: ScriptRules) -> float:
    return max(len(line.strip()) / r.chars_per_s + r.gap_s, r.min_scene_s)


def estimate_length_s(script: Script, r: ScriptRules) -> float:
    return round(sum(scene_length_s(s.line, r) for s in script.scenes), 2)


def check_script(script: Script, r: ScriptRules) -> list[str]:
    """Every rule the script breaks, as plain sentences the Writer can act on. Empty = OK."""
    problems: list[str] = []
    total = estimate_length_s(script, r)
    if not r.min_len_s <= total <= r.max_len_s:
        problems.append(f"Estimated length is {total:.0f} s; it must be {r.min_len_s:.0f}-{r.max_len_s:.0f} s "
                        f"(Hindi is spoken at about {r.chars_per_s:.0f} characters per second).")
    for i, s in enumerate(script.scenes):
        est = scene_length_s(s.line, r)
        if est > r.max_scene_s:
            problems.append(f"scenes[{i}] is about {est:.1f} s of speech; max is {r.max_scene_s} s "
                            f"(a visual change every 4 s) - split it into two scenes.")
    first = script.scenes[0].line.strip() if script.scenes else ""
    if first and script.hook.text.strip() and (script.hook.text.strip() in first or first in script.hook.text.strip()):
        problems.append("hook.text repeats the first line (the banner and the caption would say the same thing); "
                        "make the hook a tease of the twist instead.")
    if script.hook.until_s > r.hook_by_s:
        problems.append(f"hook.until_s is {script.hook.until_s}; the hook must land within {r.hook_by_s:.0f} s.")
    if len(script.title_options) != 3:
        problems.append(f"Give exactly 3 title options (got {len(script.title_options)}).")
    for t in script.title_options:
        if len(t) >= r.max_title:
            problems.append(f"Title '{t}' is {len(t)} characters; titles must be under {r.max_title}.")
    if not script.loop_end:
        problems.append("loop_end must be true: the last line must lead back into the first.")
    if len(script.products) > r.max_products:
        problems.append(f"At most {r.max_products} products (got {len(script.products)}).")
    ref = script.product_moment.get("product_ref")
    if ref and ref not in {p.ref for p in script.products}:
        problems.append(f"product_moment.product_ref '{ref}' is not in products.")
    return problems
