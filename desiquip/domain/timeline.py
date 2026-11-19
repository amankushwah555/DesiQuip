from __future__ import annotations

from .models import TimelineScene


def build_timeline(scene_audio_s: list[float], gap_s: float, min_scene_s: float) -> list[TimelineScene]:
    """Scene start/end times from the real voice length of each scene.

    Each scene lasts its audio plus a gap, but never less than min_scene_s,
    so silent scenes (pure visual gags) still get screen time.
    """
    if not scene_audio_s:
        raise ValueError("timeline needs at least one scene")
    t = 0.0
    out: list[TimelineScene] = []
    for i, audio in enumerate(scene_audio_s):
        length = max(audio + gap_s, min_scene_s)
        out.append(TimelineScene(index=i, start=round(t, 3), end=round(t + length, 3),
                                 voice_s=round(audio, 3)))
        t += length
    return out
