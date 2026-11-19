"""Use case: voice.wav -> captions.json (word timings + on-screen groups).

Text is taken from the script so Hindi spelling is always exactly as written;
the transcriber is used only for *when* each word is spoken.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ..domain.captions import align_to_script, group_words
from ..ports import JobStore, Transcriber


class CaptionService:
    def __init__(self, transcriber: Transcriber, store: JobStore, language: str, per_group: int) -> None:
        self.transcriber, self.store = transcriber, store
        self.language, self.per_group = language, per_group

    def run(self, job_id: str) -> Path:
        audio = self.store.path(job_id) / "voice.wav"
        heard = self.transcriber.transcribe(audio, self.language)
        if not heard:
            raise RuntimeError("Transcriber returned no words; is voice.wav silent?")
        script = self.store.read_script(job_id)
        timeline = self.store.read_json(job_id, "timeline.json")["scenes"]
        scenes = [(slot["start"], slot["end"], scene.line) for scene, slot in zip(script.scenes, timeline)]
        words = align_to_script(scenes, heard)
        groups = group_words(words, self.per_group)
        return self.store.write_json(job_id, "captions.json", {
            "words": [asdict(w) for w in words],
            "groups": [{"start": g.start, "end": g.end, "words": [asdict(w) for w in g.words]}
                       for g in groups],
        })
