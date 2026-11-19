"""AgentRunner adapter: runs any .claude/agents/<name>.md agent with Claude Code headless (`claude -p`)."""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def parse_result(stdout: str) -> dict[str, Any]:
    """The JSON result object from `claude -p --output-format json`, ignoring any noise around it."""
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"result": stdout}


def build_agent_cmd(claude: str, agent: str, prompt: str, tools: str, budget_usd: float) -> list[str]:
    return [claude, "-p", prompt, "--agent", agent, "--allowedTools", tools,
            "--permission-mode", "acceptEdits", "--output-format", "json",
            "--max-budget-usd", str(budget_usd)]


class ClaudeAgent:
    def __init__(self, project_dir: Path, budget_usd: float = 1.0, timeout_s: int = 900) -> None:
        self.project_dir = Path(project_dir)
        self.budget_usd, self.timeout_s = budget_usd, timeout_s
        claude = shutil.which("claude")
        if not claude:
            raise RuntimeError("'claude' (Claude Code) not found on PATH. Install it and log in once.")
        self.claude = claude
        if os.environ.get("ANTHROPIC_API_KEY"):
            log.warning("ANTHROPIC_API_KEY is set: agent runs are billed to the API, not your Claude plan.")

    def run(self, agent: str, prompt: str, tools: str) -> dict[str, Any]:
        r = subprocess.run(build_agent_cmd(self.claude, agent, prompt, tools, self.budget_usd),
                           cwd=self.project_dir, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=self.timeout_s)
        if r.returncode != 0:
            raise RuntimeError(f"Agent '{agent}' failed (exit {r.returncode}): {(r.stderr or r.stdout)[-800:]}")
        result = parse_result(r.stdout)
        log.info("Agent %s finished in %.0f s, %s turns, cost $%.3f", agent, result.get("duration_ms", 0) / 1000,
                 result.get("num_turns"), result.get("total_cost_usd", 0) or 0)
        return result
