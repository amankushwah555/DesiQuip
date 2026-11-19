"""Reviewer adapter: the qa-reviewer agent scores hook, humour and safety from the script and opening frames."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..ports import AgentRunner

TOOLS = "Read,Glob,Write(jobs/**)"


class ClaudeReviewer:
    def __init__(self, runner: AgentRunner, root: Path) -> None:
        self.runner, self.root = runner, Path(root)

    def review(self, job_id: str, frames: list[Path]) -> dict[str, Any]:
        rel = [str(p.relative_to(self.root)).replace("\\", "/") for p in frames]
        out = self.root / "jobs" / job_id / "qa_review.json"
        out.unlink(missing_ok=True)
        self.runner.run("qa-reviewer", (
            f"Review job {job_id}. Script: jobs/{job_id}/script.json. Opening frames (0-3 s): "
            f"{', '.join(rel)}. Write your verdict to jobs/{job_id}/qa_review.json."), TOOLS)
        if not out.is_file():
            raise RuntimeError("qa-reviewer did not write qa_review.json")
        data = json.loads(out.read_text(encoding="utf-8"))
        return {"hook": int(data["hook"]), "humour": int(data["humour"]),
                "safety_ok": bool(data["safety_ok"]), "notes": str(data.get("notes", ""))}
