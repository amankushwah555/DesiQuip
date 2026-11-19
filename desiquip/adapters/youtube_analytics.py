"""Growth data adapter: YouTube Analytics (per-video metrics) + comments (read and reply), via the same OAuth login."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .youtube import authorize

METRICS = "views,averageViewPercentage,averageViewDuration,likes,comments,shares,subscribersGained"


def build_analytics_params(video_ids: list[str], day: str) -> dict[str, str]:
    return {"ids": "channel==MINE", "startDate": day, "endDate": day, "metrics": METRICS,
            "dimensions": "video", "filters": "video==" + ",".join(video_ids)}


def parse_analytics(body: dict) -> dict[str, dict[str, Any]]:
    names = [h["name"] for h in body.get("columnHeaders", [])]
    return {row[0]: dict(zip(names[1:], row[1:])) for row in body.get("rows", [])}


class YouTubeGrowthAPI:
    def __init__(self, secrets_dir: Path) -> None:
        self.secrets_dir = Path(secrets_dir)

    def _creds(self):
        return authorize(self.secrets_dir)

    def metrics(self, video_ids: list[str], day: str) -> dict[str, dict[str, Any]]:
        from googleapiclient.discovery import build
        api = build("youtubeAnalytics", "v2", credentials=self._creds(), cache_discovery=False)
        return parse_analytics(api.reports().query(**build_analytics_params(video_ids, day)).execute())

    def new_comments(self, video_ids: list[str]) -> list[dict[str, str]]:
        from googleapiclient.discovery import build
        api = build("youtube", "v3", credentials=self._creds(), cache_discovery=False)
        out = []
        for vid in video_ids:
            res = api.commentThreads().list(part="snippet", videoId=vid, maxResults=50, order="time").execute()
            for t in res.get("items", []):
                if t["snippet"].get("totalReplyCount", 0) == 0:   # not answered yet
                    top = t["snippet"]["topLevelComment"]
                    out.append({"comment_id": top["id"], "video_id": vid,
                                "text": top["snippet"]["textOriginal"][:500]})
        return out

    def reply(self, comment_id: str, text: str) -> None:
        from googleapiclient.discovery import build
        api = build("youtube", "v3", credentials=self._creds(), cache_discovery=False)
        api.comments().insert(part="snippet", body={"snippet": {"parentId": comment_id, "textOriginal": text}}).execute()
