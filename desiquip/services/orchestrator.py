"""Orchestrator (spec sections 2, 3a and 9): moves each job through the flow, handles QA retries,
waits for the human, publishes approved jobs, and reports.

The flow (step order) comes from config.yaml, so changing the pipeline is a config edit.
A failed job never blocks the others.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Callable

from ..ports import Approver, JobStore, JobTracker
from .qa import QAFailed

log = logging.getLogger(__name__)
STATUS_AFTER = {"write": "scripted", "finalize": "produced", "qa": "qa_pass"}
RESTART_FROM = {"technical": "render", "content": "write"}


class Orchestrator:
    def __init__(self, run_step: Callable[[str, str], Any], jobs: JobTracker, approver: Approver,
                 store: JobStore, flow: list[str], max_retries: int = 2, learnings_path: Path | None = None) -> None:
        self.run_step, self.jobs, self.approver, self.store = run_step, jobs, approver, store
        self.flow, self.max_retries, self.learnings_path = flow, max_retries, learnings_path

    # --- produce: idea -> awaiting_approval -------------------------------------------------
    def produce(self, job_id: str, start: str | None = None) -> str:
        i = self.flow.index(start) if start else 0
        while i < len(self.flow):
            step = self.flow[i]
            try:
                self.run_step(step, job_id)
            except QAFailed as e:
                self.jobs.set(job_id, "qa_fail", error=str(e))
                retries = self.jobs.incr_retries(job_id)
                if e.kind not in RESTART_FROM or retries > self.max_retries:
                    log.warning("%s rejected after QA (%s, retry %d)", job_id, e.kind, retries)
                    self.jobs.set(job_id, "rejected", error=str(e))
                    return "rejected"
                if e.kind == "content":
                    self.store.write_json(job_id, "feedback.json", {"from": "qa", "notes": e.reasons})
                log.info("%s: QA %s failure, retry %d from %s", job_id, e.kind, retries, RESTART_FROM[e.kind])
                i = self.flow.index(RESTART_FROM[e.kind])
                continue
            except Exception as e:  # noqa: BLE001 - spec: log it, skip the job, continue with others
                log.error("%s failed at %s: %s", job_id, step, e)
                self.jobs.set(job_id, "error", error=f"{step}: {e}")
                return "error"
            if step in STATUS_AFTER:
                self.jobs.set(job_id, STATUS_AFTER[step])
            i += 1
        self.jobs.set(job_id, "awaiting_approval")
        self.approver.request(job_id, self.store.path(job_id) / "final.mp4", self._title(job_id))
        return "awaiting_approval"

    # --- approvals: approved -> published, rejected -> learning ----------------------------
    def process_approvals(self) -> None:
        for job_id, decision, note in self.approver.poll():
            row = self.jobs.get(job_id)
            if not row or row["status"] != "awaiting_approval":
                log.warning("Ignoring %s for %s (status %s)", decision, job_id, row and row["status"])
                continue
            if decision == "approve":
                self.jobs.set(job_id, "approved")
                try:
                    self.run_step("upload", job_id)
                    upload = self._read(job_id, "upload.json") or {}
                    self.jobs.set(job_id, "published", youtube_id=upload.get("youtube_id"))
                except Exception as e:  # noqa: BLE001
                    log.error("%s publish failed: %s", job_id, e)
                    self.jobs.set(job_id, "error", error=f"upload: {e}")
            else:
                self.jobs.set(job_id, "rejected", error=f"rejected by owner: {note}" if note else "rejected by owner")
                self._learn(job_id, note)

    def send_summary(self) -> None:
        counts = self.jobs.counts()
        order = ["awaiting_approval", "published", "rejected", "error", "qa_fail", "approved", "scripted", "produced", "new"]
        lines = [f"DesiQuip daily summary ({date.today().isoformat()})"]
        lines += [f"{s.replace('_', ' ')}: {counts[s]}" for s in order if s in counts]
        for row in self.jobs.list("error")[:5]:
            lines.append(f"  ! {row['job_id']}: {row['error']}")
        self.approver.notify("\n".join(lines))

    # --- helpers -------------------------------------------------------------------------------
    def _title(self, job_id: str) -> str:
        pkg = self._read(job_id, "package.json")
        if pkg:
            return pkg.get("title", job_id)
        try:
            return self.store.read_script(job_id).title_options[0]
        except Exception:  # noqa: BLE001
            return job_id

    def _read(self, job_id: str, name: str) -> dict | None:
        p = self.store.path(job_id) / name
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None

    def _learn(self, job_id: str, note: str) -> None:
        if not self.learnings_path or not note:
            return
        with open(self.learnings_path, "a", encoding="utf-8") as f:
            f.write(f"\n- {date.today().isoformat()} owner rejected {job_id} ({self._title(job_id)}): {note}\n")
