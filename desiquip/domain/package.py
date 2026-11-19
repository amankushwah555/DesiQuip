"""Packaging rules (spec section 8 publisher checklist)."""
from __future__ import annotations

import re

# Spec section 8 + Amazon operating agreement wording.
AFFILIATE_DISCLOSURE = ("Affiliate links: I earn a small commission at no extra cost to you. "
                        "As an Amazon Associate I earn from qualifying purchases.")
MAX_TITLE = 50
MAX_HASHTAGS = 15          # YouTube ignores all hashtags on a video that has more than 15
MAX_DESCRIPTION = 5000
MAX_TAGS_CHARS = 500
_AI_WORDS = re.compile(r"\bAI\b|artificial intelligence|एआई|AI[- ]generated", re.IGNORECASE)


def package_problems(pkg: dict, has_products: bool) -> list[str]:
    problems = []
    title = str(pkg.get("title", ""))
    if not title or len(title) >= MAX_TITLE:
        problems.append(f"title must be 1-{MAX_TITLE - 1} characters (got {len(title)}).")
    desc = str(pkg.get("description", ""))
    if not desc or len(desc) > MAX_DESCRIPTION:
        problems.append(f"description must be 1-{MAX_DESCRIPTION} characters.")
    if _AI_WORDS.search(desc):
        problems.append("description must not mention AI (owner decision; the platform flag and on-screen tag cover it).")
    if has_products and AFFILIATE_DISCLOSURE not in desc:
        problems.append(f"description must include the affiliate disclosure exactly: \"{AFFILIATE_DISCLOSURE}\"")
    tags = pkg.get("tags") or []
    if sum(len(t) for t in tags) > MAX_TAGS_CHARS:
        problems.append(f"tags must total at most {MAX_TAGS_CHARS} characters.")
    hashtags = pkg.get("hashtags") or []
    if len(hashtags) > MAX_HASHTAGS or any(not h.startswith("#") for h in hashtags):
        problems.append(f"hashtags: at most {MAX_HASHTAGS}, each starting with #.")
    thumbs = pkg.get("thumbnail_texts") or []
    if len(thumbs) != 3 or any(not t or len(t) > 24 for t in thumbs):
        problems.append("Give exactly 3 thumbnail texts, each 1-24 characters.")
    return problems
