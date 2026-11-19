"""Use case: affiliate links for a job's products (spec section 8).

Shorts description links aren't clickable, so links go to links.json (for long videos and pinned
comments) and to a "today's deals" page linked from the channel. Every link is tagged and tracked per job.
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

from ..adapters.affiliate import amazon_search_link
from ..ports import JobStore

log = logging.getLogger(__name__)


class AffiliateService:
    def __init__(self, store: JobStore, amazon_tag: str, shortener: Any | None, deals_page: Path) -> None:
        self.store, self.tag, self.shortener, self.deals_page = store, amazon_tag, shortener, Path(deals_page)

    def run(self, job_id: str) -> Path:
        script = self.store.read_script(job_id)
        if not self.tag:
            return self.store.write_json(job_id, "links.json", {"links": [], "note": "AMZ_TAG not set"})
        links = []
        for p in script.products:
            url = amazon_search_link(p.query, self.tag)
            short = url
            if self.shortener is not None:
                try:
                    short = self.shortener.shorten(url)
                except Exception as e:  # noqa: BLE001 - an unshortened link still works
                    log.warning("Shortening failed (%s); using the full link", e)
            links.append({"ref": p.ref, "program": "amazon", "query": p.query, "url": url, "short_url": short})
        out = self.store.write_json(job_id, "links.json", {"links": links})
        if links:
            self.deals_page.parent.mkdir(parents=True, exist_ok=True)
            with open(self.deals_page, "a", encoding="utf-8") as f:
                f.write(f"\n## {date.today().isoformat()} · {script.title_options[0]}\n")
                f.writelines(f"- {l['query']}: {l['short_url']}\n" for l in links)
        return out
