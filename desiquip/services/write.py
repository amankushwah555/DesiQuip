"""Use case: idea.json -> script.json, written by the Writer agent and checked against the spec rules.

Spec: invalid output = retry once (with the reasons), then mark the job failed.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ..domain.models import Script, ScriptValidationError
from ..domain.rules import ScriptRules, check_script, estimate_length_s
from ..ports import JobStore, ScriptWriter

log = logging.getLogger(__name__)


class ScriptRejected(RuntimeError):
    """The Writer could not produce a valid script within the allowed attempts."""


def script_problems(store: JobStore, job_id: str, rules: ScriptRules,
                    expected_source_id: str | None = None) -> list[str]:
    path = store.path(job_id) / "script.json"
    if not path.is_file():
        return ["script.json was not written."]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"script.json is not valid JSON ({e})."]
    try:
        script = Script.from_dict(data)
    except ScriptValidationError as e:
        return [f"script.json breaks the contract: {e}."]
    problems = check_script(script, rules)
    if script.job_id != job_id:
        problems.append(f"job_id must be '{job_id}'.")
    if expected_source_id and script.source_id != expected_source_id:
        problems.append(f"source_id must be '{expected_source_id}' (copied from idea.json; never invent rights).")
    return problems


class WriteService:
    def __init__(self, writer: ScriptWriter, store: JobStore, rules: ScriptRules, retries: int = 1) -> None:
        self.writer, self.store, self.rules, self.retries = writer, store, rules, retries

    def run(self, job_id: str) -> Path:
        jd = self.store.path(job_id)
        if not (jd / "idea.json").is_file():
            raise FileNotFoundError(f"{jd / 'idea.json'} not found; create the job with: new {job_id} --topic \"...\"")
        idea = self.store.read_json(job_id, "idea.json")

        feedback: list[str] = []
        for attempt in range(1, self.retries + 2):
            self.writer.write(job_id, feedback)
            problems = script_problems(self.store, job_id, self.rules, idea.get("source_id"))
            if not problems:
                script = self.store.read_script(job_id)
                log.info("Script accepted on attempt %d: ~%.0f s, %d scenes", attempt,
                         estimate_length_s(script, self.rules), len(script.scenes))
                return jd / "script.json"
            log.warning("Attempt %d rejected: %s", attempt, " | ".join(problems))
            feedback = problems
        raise ScriptRejected("Writer failed after retry: " + " ".join(feedback))
