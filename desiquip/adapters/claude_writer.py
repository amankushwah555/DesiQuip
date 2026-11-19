"""ScriptWriter adapter: the Writer agent (.claude/agents/writer.md) via the shared AgentRunner."""
from __future__ import annotations

from ..ports import AgentRunner
from .claude_agent import build_agent_cmd

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
    return build_agent_cmd(claude, "writer", prompt, ALLOWED_TOOLS, budget_usd)


class ClaudeCodeWriter:
    def __init__(self, runner: AgentRunner) -> None:
        self.runner = runner

    def write(self, job_id: str, feedback: list[str]) -> None:
        self.runner.run("writer", build_write_prompt(job_id, feedback), ALLOWED_TOOLS)
