"""ScriptWriter adapter: runs the Writer agent (.claude/agents/writer.md) with Claude Code headless."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

# The Writer may read anything but only write inside jobs/. No shell access.
ALLOWED_TOOLS = "Read,Glob,Grep,Write(jobs/**),Edit(jobs/**)"


def build_write_prompt(job_id: str, feedback: list[str]) -> str:
    prompt = (f"Write the Short script for job {job_id}. "
              f"The idea is in jobs/{job_id}/idea.json. "
              f"Save the result to jobs/{job_id}/script.json, following your instructions exactly.")
    if feedback:
        prompt += ("\n\nYour previous script.json was rejected. Fix every one of these problems "
                   "and save the file again:\n" + "\n".join(f"- {p}" for p in feedback))
    return prompt


def build_write_cmd(claude: str, prompt: str, budget_usd: float) -> list[str]:
    return [claude, "-p", prompt, "--agent", "writer", "--allowedTools", ALLOWED_TOOLS,
            "--permission-mode", "acceptEdits", "--output-format", "json",
            "--max-budget-usd", str(budget_usd)]


class ClaudeCodeWriter:
    def __init__(self, project_dir: Path, budget_usd: float = 1.0, timeout_s: int = 600) -> None:
        self.project_dir = Path(project_dir)
        self.budget_usd, self.timeout_s = budget_usd, timeout_s
        claude = shutil.which("claude")
        if not claude:
            raise RuntimeError("'claude' (Claude Code) not found on PATH. Install it and log in once.")
        self.claude = claude
        if os.environ.get("ANTHROPIC_API_KEY"):
            log.warning("ANTHROPIC_API_KEY is set: this run is billed to the API, not your Claude plan.")

    def write(self, job_id: str, feedback: list[str]) -> None:
        cmd = build_write_cmd(self.claude, build_write_prompt(job_id, feedback), self.budget_usd)
        r = subprocess.run(cmd, cwd=self.project_dir, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=self.timeout_s)
        if r.returncode != 0:
            raise RuntimeError(f"Writer agent failed (exit {r.returncode}): {(r.stderr or r.stdout)[-800:]}")
        try:
            result = json.loads(r.stdout)
            log.info("Writer agent finished in %.0f s, %s turns, cost $%.3f",
                     result.get("duration_ms", 0) / 1000, result.get("num_turns"), result.get("total_cost_usd", 0))
        except json.JSONDecodeError:
            log.info("Writer agent finished")
