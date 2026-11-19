"""JobStore adapter: each job is a folder jobs/<job_id>/ of JSON + media files (spec section 6)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..domain.models import Script


class FileJobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path(self, job_id: str) -> Path:
        d = self.root / job_id
        if not d.is_dir():
            raise FileNotFoundError(f"Job folder not found: {d}")
        return d

    def create(self, job_id: str, template: Path) -> Path:
        """New job folder (creating jobs/ if needed), seeded with the template's files."""
        dest = self.root / job_id
        if dest.exists():
            raise FileExistsError(f"Job already exists: {dest}")
        shutil.copytree(template, dest)
        return dest

    def create_from_topic(self, job_id: str, topic: str, character: str = "uncle_ji") -> Path:
        """New job from just an idea. Hand-given topics are originals (spec content model 1)."""
        dest = self.root / job_id
        if dest.exists():
            raise FileExistsError(f"Job already exists: {dest}")
        dest.mkdir(parents=True)
        self.write_json(job_id, "idea.json", {"topic": topic, "character": character,
                                              "source_id": f"orig-{job_id}", "source_type": "original"})
        return dest

    def has(self, job_id: str, name: str) -> bool:
        return (self.root / job_id / name).is_file()

    def read_json(self, job_id: str, name: str) -> Any:
        with open(self.path(job_id) / name, encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, job_id: str, name: str, data: Any) -> Path:
        out = self.path(job_id) / name
        tmp = out.with_suffix(out.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(out)  # atomic: a crash never leaves a half-written contract file
        return out

    def read_script(self, job_id: str) -> Script:
        return Script.from_dict(self.read_json(job_id, "script.json"))
