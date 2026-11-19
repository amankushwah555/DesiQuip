"""Use case: Auto QA gate (spec section 7). A video reaches the human only if every check passes."""
from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from ..domain.qa import QARules, caption_coverage, evaluate
from ..ports import JobStore, QAMedia, Reviewer, RightsRegistry

log = logging.getLogger(__name__)
FRAME_TIMES = [0.0, 1.0, 2.5]  # spec: Claude watches frames from the first 3 seconds
CONTENT_CHECKS = ("length", "products")  # measurable failures only the Writer can fix


class QAFailed(RuntimeError):
    """kind: 'technical' (re-render can fix), 'content' (re-write needed) or 'rights' (reject)."""

    def __init__(self, kind: str, reasons: list[str]) -> None:
        super().__init__(f"QA failed ({kind}): " + "; ".join(reasons))
        self.kind, self.reasons = kind, reasons


class QAService:
    def __init__(self, media: QAMedia, store: JobStore, rights: RightsRegistry,
                 reviewer: Reviewer | None, rules: QARules) -> None:
        self.media, self.store, self.rights, self.reviewer, self.rules = media, store, rights, reviewer, rules

    def run(self, job_id: str) -> Path:
        jd = self.store.path(job_id)
        script = self.store.read_script(job_id)
        info = self.media.inspect(jd / "final.mp4")
        groups = self.store.read_json(job_id, "captions.json")["groups"]
        checks = evaluate(info, caption_coverage(groups, info.duration_s), len(script.products),
                          self.rights.is_valid(script.source_id), self.rules)

        review = None
        if self.reviewer is not None:
            frames = self.media.frames(jd / "final.mp4", FRAME_TIMES, jd / "qa")
            review = self.reviewer.review(job_id, frames)
            r = self.rules
            checks_review = [("hook", review["hook"] >= r.min_hook, f"hook {review['hook']}/10 (needs {r.min_hook})"),
                             ("humour", review["humour"] >= r.min_humour,
                              f"humour {review['humour']}/10 (needs {r.min_humour})"),
                             ("safety", review["safety_ok"], "safe" if review["safety_ok"] else "safety problem")]
        else:
            checks_review = []

        failed = [f"{c.name}: {c.detail}" for c in checks if not c.ok]
        content_failed = [f"{n}: {d}" for n, ok, d in checks_review if not ok]
        if content_failed and review and review.get("notes"):
            content_failed.append(f"reviewer notes (fix these): {review['notes']}")
        passed = not failed and not content_failed
        self.store.write_json(job_id, "qa.json", {
            "passed": passed, "checks": [asdict(c) for c in checks],
            "review": review, "review_checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in checks_review]})
        if passed:
            log.info("QA passed%s", f" (hook {review['hook']}, humour {review['humour']})" if review else "")
            return jd / "qa.json"
        # Which fix can work: rights -> reject; length or anything subjective -> rewrite the script
        # (a rewrite re-runs every later step too); otherwise -> re-render.
        if any(r.startswith("rights") for r in failed):
            kind = "rights"
        elif content_failed or any(r.startswith(CONTENT_CHECKS) for r in failed):
            kind = "content"
        else:
            kind = "technical"
        raise QAFailed(kind, failed + content_failed)
