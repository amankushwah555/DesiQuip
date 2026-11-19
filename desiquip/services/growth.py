"""Use case: Growth (spec section 3, agent 7; runs 09:00 daily).

Pull yesterday's metrics, fetch unanswered comments, let the growth agent analyse and write replies plus
3-5 new rules (growth/learnings.md, hooks.md, best-times.json), then post the replies (capped per day).
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable

from ..ports import AgentRunner, JobTracker

log = logging.getLogger(__name__)
TOOLS = "Read,Glob,Grep,Write(data/growth/**),Write(growth/**),Edit(growth/**)"


class GrowthService:
    def __init__(self, runner: AgentRunner, yt: Any, jobs: JobTracker, root: Path, max_replies: int = 20,
                 today: Callable[[], str] = lambda: date.today().isoformat()) -> None:
        self.runner, self.yt, self.jobs, self.root = runner, yt, jobs, Path(root)
        self.max_replies, self.today = max_replies, today

    def run(self) -> None:
        live = [r for r in self.jobs.list("published") + self.jobs.list("measured") if r.get("youtube_id")]
        if not live:
            log.info("Growth: nothing published yet - skipping")
            return
        day = self.today()
        yesterday = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
        gdir = self.root / "data" / "growth"
        gdir.mkdir(parents=True, exist_ok=True)
        ids = [r["youtube_id"] for r in live]
        metrics = self.yt.metrics(ids, yesterday)
        comments = self.yt.new_comments(ids)
        (gdir / f"{day}-metrics.json").write_text(json.dumps(
            {yesterday: metrics, "videos": {r["youtube_id"]: r["job_id"] for r in live}}, ensure_ascii=False,
            indent=2), encoding="utf-8")
        (gdir / f"{day}-comments.json").write_text(json.dumps(comments, ensure_ascii=False, indent=2), encoding="utf-8")

        replies_rel = f"data/growth/{day}-replies.json"
        self.runner.run("growth", (
            f"Daily growth review for {day}. Metrics: data/growth/{day}-metrics.json; history: data/growth/; "
            f"new comments: data/growth/{day}-comments.json; scripts: jobs/<job_id>/script.json. "
            f"Write replies to {replies_rel} and update growth/learnings.md, growth/hooks.md and "
            f"growth/best-times.json following your instructions."), TOOLS)

        replies_path = self.root / replies_rel
        replies = json.loads(replies_path.read_text(encoding="utf-8")).get("replies", []) if replies_path.is_file() else []
        known = {c["comment_id"] for c in comments}
        posted = 0
        for r in replies:
            if posted >= self.max_replies:
                break
            if r.get("comment_id") in known and str(r.get("text", "")).strip():
                try:
                    self.yt.reply(r["comment_id"], r["text"][:500])
                    posted += 1
                except Exception as e:  # noqa: BLE001
                    log.warning("Reply to %s failed: %s", r["comment_id"], e)
        for r in live:
            self.jobs.set(r["job_id"], "measured", youtube_id=r["youtube_id"])
        log.info("Growth: metrics for %d videos, %d replies posted", len(ids), posted)
