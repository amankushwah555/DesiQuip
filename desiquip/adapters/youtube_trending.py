"""TrendSource adapter: YouTube's most-popular chart for India (videos.list, 1 quota unit per call)."""
from __future__ import annotations

from typing import Any

URL = "https://www.googleapis.com/youtube/v3/videos"
CATEGORIES = {"23": "Comedy", "24": "Entertainment"}


def build_trending_params(api_key: str, category_id: str) -> dict[str, Any]:
    return {"part": "snippet,statistics", "chart": "mostPopular", "regionCode": "IN",
            "videoCategoryId": category_id, "maxResults": 25, "key": api_key}


def parse_trending(body: dict, category: str) -> list[dict[str, Any]]:
    return [{"title": it["snippet"]["title"], "channel": it["snippet"].get("channelTitle", ""),
             "views": int(it.get("statistics", {}).get("viewCount", 0)), "tags": it["snippet"].get("tags", [])[:10],
             "category": category} for it in body.get("items", [])]


class YouTubeTrending:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def fetch(self) -> list[dict[str, Any]]:
        import requests

        out: list[dict[str, Any]] = []
        for cat_id, name in CATEGORIES.items():
            r = requests.get(URL, params=build_trending_params(self.api_key, cat_id), timeout=30)
            if r.status_code == 404:   # category has no chart in this region
                continue
            r.raise_for_status()
            out += parse_trending(r.json(), name)
        return out
