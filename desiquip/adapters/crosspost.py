"""CrossPoster adapters (spec section 3, Publisher): Instagram Reel, Facebook Reel, X video.

Each turns on only when its keys are in .env. Request builders are pure and unit-tested; the HTTP
flows follow Meta's resumable Reels upload and X's v2 chunked media upload.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

GRAPH = "https://graph.facebook.com/v21.0"
X_API = "https://api.x.com/2"


def build_ig_container_params(caption: str, token: str) -> dict[str, str]:
    return {"media_type": "REELS", "upload_type": "resumable", "caption": caption,
            "share_to_feed": "true", "access_token": token}


def build_x_post_body(text: str, media_id: str) -> dict[str, Any]:
    return {"text": text, "media": {"media_ids": [media_id]}}


def _upload_bytes(upload_url: str, token: str, video: Path) -> None:
    import requests
    data = video.read_bytes()
    r = requests.post(upload_url, data=data, timeout=600, headers={
        "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))})
    r.raise_for_status()


class InstagramReels:
    name = "instagram"

    def __init__(self, ig_user_id: str, token: str) -> None:
        self.ig_user_id, self.token = ig_user_id, token

    def post(self, video: Path, caption: str) -> str:
        import requests
        c = requests.post(f"{GRAPH}/{self.ig_user_id}/media", data=build_ig_container_params(caption, self.token),
                          timeout=60)
        c.raise_for_status()
        container = c.json()
        _upload_bytes(container["uri"], self.token, video)
        for _ in range(60):                               # processing usually takes < 2 minutes
            s = requests.get(f"{GRAPH}/{container['id']}", timeout=30,
                             params={"fields": "status_code", "access_token": self.token}).json()
            if s.get("status_code") == "FINISHED":
                break
            if s.get("status_code") == "ERROR":
                raise RuntimeError(f"Instagram processing failed: {s}")
            time.sleep(10)
        p = requests.post(f"{GRAPH}/{self.ig_user_id}/media_publish", timeout=60,
                          data={"creation_id": container["id"], "access_token": self.token})
        p.raise_for_status()
        return p.json()["id"]


class FacebookReels:
    name = "facebook"

    def __init__(self, page_id: str, token: str) -> None:
        self.page_id, self.token = page_id, token

    def post(self, video: Path, caption: str) -> str:
        import requests
        url = f"{GRAPH}/{self.page_id}/video_reels"
        start = requests.post(url, data={"upload_phase": "start", "access_token": self.token}, timeout=60)
        start.raise_for_status()
        s = start.json()
        _upload_bytes(s["upload_url"], self.token, video)
        fin = requests.post(url, timeout=60, data={"upload_phase": "finish", "video_id": s["video_id"],
                                                   "video_state": "PUBLISHED", "description": caption,
                                                   "access_token": self.token})
        fin.raise_for_status()
        return s["video_id"]


class XVideo:
    name = "x"

    def __init__(self, api_key: str, api_secret: str, token: str, token_secret: str) -> None:
        self.creds = (api_key, api_secret, token, token_secret)

    def post(self, video: Path, caption: str) -> str:
        from requests_oauthlib import OAuth1Session
        s = OAuth1Session(*self.creds)
        data = video.read_bytes()
        init = s.post(f"{X_API}/media/upload/initialize", timeout=60, json={
            "media_type": "video/mp4", "total_bytes": len(data), "media_category": "tweet_video"})
        init.raise_for_status()
        media_id = init.json()["data"]["id"]
        chunk = 4 * 1024 * 1024
        for i in range(0, len(data), chunk):
            r = s.post(f"{X_API}/media/upload/{media_id}/append", timeout=300,
                       data={"segment_index": i // chunk}, files={"media": data[i:i + chunk]})
            r.raise_for_status()
        s.post(f"{X_API}/media/upload/{media_id}/finalize", timeout=60).raise_for_status()
        for _ in range(60):
            st = s.get(f"{X_API}/media/upload", params={"command": "STATUS", "media_id": media_id}, timeout=30)
            state = st.json().get("data", {}).get("processing_info", {}).get("state", "succeeded")
            if state == "succeeded":
                break
            if state == "failed":
                raise RuntimeError(f"X media processing failed: {st.json()}")
            time.sleep(5)
        t = s.post(f"{X_API}/tweets", json=build_x_post_body(caption[:270], media_id), timeout=60)
        t.raise_for_status()
        return t.json()["data"]["id"]


def from_env() -> list:
    """Every cross-poster whose keys are present in the environment."""
    e = {k: os.environ.get(k, "").strip() for k in
         ("META_TOKEN", "IG_USER_ID", "FB_PAGE_ID", "X_API_KEY", "X_API_SECRET", "X_TOKEN", "X_TOKEN_SECRET")}
    out = []
    if e["META_TOKEN"] and e["IG_USER_ID"]:
        out.append(InstagramReels(e["IG_USER_ID"], e["META_TOKEN"]))
    if e["META_TOKEN"] and e["FB_PAGE_ID"]:
        out.append(FacebookReels(e["FB_PAGE_ID"], e["META_TOKEN"]))
    if all(e[k] for k in ("X_API_KEY", "X_API_SECRET", "X_TOKEN", "X_TOKEN_SECRET")):
        out.append(XVideo(e["X_API_KEY"], e["X_API_SECRET"], e["X_TOKEN"], e["X_TOKEN_SECRET"]))
    return out
