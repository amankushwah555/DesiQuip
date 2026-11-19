"""Use case: Trend finder (spec section 3, agent 1) -> today's ideas -> new jobs.

Sources: YouTube trending in India (Comedy, Entertainment) when YT_API_KEY is set, plus growth/topics.md.
The trend-finder agent turns them into ORIGINAL ideas for the channel's character (never a re-upload),
scored on trend growth, humour, character fit and product tie-in.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Callable

from ..ports import AgentRunner, JobStore, JobTracker, RightsRegistry, TrendSource

log = logging.getLogger(__name__)
TOOLS = "Read,Glob,Grep,Write(data/trends/**)"
SCORE_KEYS = ("trend", "humour", "character_fit", "product")


def idea_problems(ideas: list[dict], count: int) -> list[str]:
    problems = []
    if len(ideas) < count:
        problems.append(f"Need at least {count} ideas (got {len(ideas)}).")
    for i, idea in enumerate(ideas):
        if not str(idea.get("topic", "")).strip():
            problems.append(f"ideas[{i}] needs a topic.")
        if idea.get("source_type") != "original":
            problems.append(f"ideas[{i}]: only original ideas are allowed (never plan a re-upload).")
        scores = idea.get("scores") or {}
        if any(not isinstance(scores.get(k), (int, float)) for k in SCORE_KEYS):
            problems.append(f"ideas[{i}] needs numeric scores for {', '.join(SCORE_KEYS)}.")
    return problems


class TrendService:
    def __init__(self, runner: AgentRunner, source: TrendSource | None, store: JobStore, rights: RightsRegistry,
                 jobs: JobTracker, root: Path, character: str = "uncle_ji",
                 today: Callable[[], str] = lambda: date.today().isoformat(), retries: int = 1) -> None:
        self.runner, self.source, self.store, self.rights, self.jobs = runner, source, store, rights, jobs
        self.root, self.character, self.today, self.retries = Path(root), character, today, retries

    def run(self, count: int) -> list[str]:
        day = self.today()
        tdir = self.root / "data" / "trends"
        tdir.mkdir(parents=True, exist_ok=True)
        trending = []
        if self.source is not None:
            try:
                trending = self.source.fetch()
            except Exception as e:  # noqa: BLE001 - trends are optional input; topics.md still works
                log.warning("Trending fetch failed (%s); using growth/topics.md only", e)
        (tdir / f"{day}.json").write_text(json.dumps({"date": day, "trending": trending}, ensure_ascii=False,
                                                     indent=2), encoding="utf-8")

        ideas_rel = f"data/trends/{day}-ideas.json"
        feedback: list[str] = []
        for _ in range(self.retries + 1):
            prompt = (f"Find today's ideas. Inputs: data/trends/{day}.json (YouTube trending in India; may be empty), "
                      f"growth/topics.md, growth/learnings.md, characters/{self.character}.md. "
                      f"Give at least {count} ideas. Write {ideas_rel} following your instructions.")
            if feedback:
                prompt += "\n\nYour previous file was rejected. Fix:\n" + "\n".join(f"- {p}" for p in feedback)
            self.runner.run("trend-finder", prompt, TOOLS)
            try:
                ideas = json.loads((self.root / ideas_rel).read_text(encoding="utf-8"))["ideas"]
                feedback = idea_problems(ideas, count)
            except (OSError, KeyError, json.JSONDecodeError) as e:
                feedback = [f"{ideas_rel} missing or invalid ({e})."]
            if not feedback:
                break
        else:
            raise RuntimeError("Trend finder failed: " + " ".join(feedback))

        best = sorted(ideas, key=lambda i: sum(i["scores"][k] for k in SCORE_KEYS), reverse=True)[:count]
        created = []
        for idea in best:
            job_id = self._next_job_id(day)
            topic = idea["topic"] + (f" — {idea['angle']}" if idea.get("angle") else "")
            self.store.create_from_topic(job_id, topic, self.character)
            self.rights.add(f"orig-{job_id}", "original", owner="DesiQuip")
            self.jobs.create(job_id)
            self.jobs.set(job_id, "idea")
            created.append(job_id)
            log.info("New job %s: %s", job_id, topic)
        return created

    def _next_job_id(self, day: str) -> str:
        k = 1
        while True:
            job_id = f"{day}-{k:02d}"
            try:
                self.store.path(job_id)
            except FileNotFoundError:
                if self.jobs.get(job_id) is None:
                    return job_id
            k += 1
