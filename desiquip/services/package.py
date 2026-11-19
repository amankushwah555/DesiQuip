"""Use case: Packager agent -> package.json (title, description, tags, hashtags) + 3 thumbnails."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ..domain.package import package_problems
from ..ports import AgentRunner, JobStore, StillRenderer

log = logging.getLogger(__name__)
TOOLS = "Read,Glob,Grep,Write(jobs/**),Edit(jobs/**)"


class PackageService:
    def __init__(self, runner: AgentRunner, stills: StillRenderer, store: JobStore,
                 characters_dir: Path | None = None, retries: int = 1) -> None:
        self.runner, self.stills, self.store = runner, stills, store
        self.characters_dir, self.retries = characters_dir, retries

    def run(self, job_id: str) -> Path:
        jd = self.store.path(job_id)
        script = self.store.read_script(job_id)
        has_products = bool(script.products)
        char_png = self.characters_dir / f"{script.character}.png" if self.characters_dir else None
        feedback: list[str] = []
        for _ in range(self.retries + 1):
            prompt = f"Package job {job_id}. Read jobs/{job_id}/script.json and write jobs/{job_id}/package.json."
            if feedback:
                prompt += "\n\nYour previous package.json was rejected. Fix:\n" + "\n".join(f"- {p}" for p in feedback)
            self.runner.run("packager", prompt, TOOLS)
            try:
                pkg = json.loads((jd / "package.json").read_text(encoding="utf-8"))
                feedback = package_problems(pkg, has_products)
            except (OSError, json.JSONDecodeError) as e:
                feedback = [f"package.json missing or invalid JSON ({e})."]
            if not feedback:
                break
        else:
            raise RuntimeError("Packager failed after retry: " + " ".join(feedback))

        assets = {}
        if char_png and char_png.is_file():
            assets["character.png"] = char_png
        for i, text in enumerate(pkg["thumbnail_texts"], start=1):
            props = {"text": text, "variant": i, "characterImage": "character.png" if assets else None}
            self.stills.still(job_id, props, assets, jd / f"thumb_{i}.png")
        log.info("Packaged: '%s' + 3 thumbnails", pkg["title"])
        return jd / "package.json"
