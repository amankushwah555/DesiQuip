"""VideoUploader adapter: YouTube Data API v3 with OAuth (Desktop app client)."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from ..ports import UploadMetadata

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",  # thumbnails + playlists (week 4)
]
RETRIABLE_STATUS = {500, 502, 503, 504}


def build_request_body(meta: UploadMetadata) -> dict[str, Any]:
    return {
        "snippet": {
            "title": meta.title,
            "description": meta.description,
            "tags": list(meta.tags),
            "categoryId": meta.category_id,
            "defaultLanguage": meta.language,
            "defaultAudioLanguage": meta.language,
        },
        "status": {
            "privacyStatus": meta.privacy,
            "selfDeclaredMadeForKids": meta.made_for_kids,
            "containsSyntheticMedia": meta.contains_synthetic_media,  # altered/synthetic content flag
        },
    }


def authorize(secrets_dir: Path):
    """Load token.json, refresh it, or run the browser OAuth flow once (upload.py --auth)."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token = secrets_dir / "token.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        client = secrets_dir / "client_secret.json"
        if not client.exists():
            raise FileNotFoundError(f"Put your Google OAuth Desktop client at {client}")
        creds = InstalledAppFlow.from_client_secrets_file(str(client), SCOPES).run_local_server(port=0)
    secrets_dir.mkdir(exist_ok=True)
    token.write_text(creds.to_json(), encoding="utf-8")
    return creds


class YouTubeUploader:
    def __init__(self, secrets_dir: Path) -> None:
        self.secrets_dir = Path(secrets_dir)

    def upload(self, video: Path, meta: UploadMetadata) -> str:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        yt = build("youtube", "v3", credentials=authorize(self.secrets_dir), cache_discovery=False)
        request = yt.videos().insert(
            part="snippet,status", body=build_request_body(meta),
            media_body=MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True),
        )
        response, attempt = None, 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    log.info("Upload %d%%", int(status.progress() * 100))
            except HttpError as e:
                if e.resp.status not in RETRIABLE_STATUS or attempt >= 3:
                    raise
                attempt += 1
                time.sleep(2 ** attempt)
        log.info("Uploaded video id %s (%s)", response["id"], meta.privacy)
        return response["id"]
