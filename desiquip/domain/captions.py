from __future__ import annotations

from .models import CaptionGroup, Word


def _spread(tokens: list[str], start: float, end: float) -> list[Word]:
    """Lay tokens back to back over [start, end], each sized by its character count."""
    total = sum(len(t) for t in tokens) or 1
    out, t = [], start
    for tok in tokens:
        length = (end - start) * len(tok) / total
        out.append(Word(text=tok, start=round(t, 3), end=round(t + length, 3)))
        t += length
    return out


def align_to_script(scenes: list[tuple[float, float, str]], heard: list[Word]) -> list[Word]:
    """Caption words spelt exactly as the script, timed by what the ASR heard.

    scenes: (start_s, end_s, spoken line) per scene. A heard word belongs to the scene its
    midpoint falls in. Equal counts map 1:1; otherwise the script words are spread by length
    over the span the ASR heard in that scene (or the whole scene if it heard nothing).
    """
    out: list[Word] = []
    for i, (start, end, text) in enumerate(scenes):
        tokens = text.split()
        if not tokens:
            continue
        last = i == len(scenes) - 1
        mine = [w for w in heard
                if start <= (w.start + w.end) / 2 < end or (last and (w.start + w.end) / 2 >= end)]
        if len(mine) == len(tokens):
            out += [Word(text=tok, start=w.start, end=w.end) for tok, w in zip(tokens, mine)]
        elif mine:
            out += _spread(tokens, mine[0].start, mine[-1].end)
        else:
            out += _spread(tokens, start, end)
    return out


def group_words(words: list[Word], per_group: int, max_gap_s: float = 0.6,
                hold_s: float = 1.5) -> list[CaptionGroup]:
    """Split words into on-screen caption groups; a long pause starts a new group.

    Each group then stays on screen until the next one starts (at most hold_s past its
    last word), so pauses between lines don't blank the captions.
    """
    groups = _split(words, per_group, max_gap_s)
    return [CaptionGroup(start=g.start, end=round(min(nxt.start, g.end + hold_s), 3), words=g.words)
            for g, nxt in zip(groups, groups[1:])] + groups[-1:]


def _split(words: list[Word], per_group: int, max_gap_s: float) -> list[CaptionGroup]:
    groups: list[CaptionGroup] = []
    cur: list[Word] = []

    def flush() -> None:
        if cur:
            groups.append(CaptionGroup(start=cur[0].start, end=cur[-1].end, words=tuple(cur)))

    for w in words:
        if cur and (len(cur) >= per_group or w.start - cur[-1].end > max_gap_s):
            flush()
            cur = []
        cur.append(w)
    flush()
    return groups
