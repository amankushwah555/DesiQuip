"""Use case: Publisher (spec section 3, agent 6 + section 8 checklist).

final.mp4 -> YouTube (AI flag on, Made for Kids off, scheduled at the best slot), custom thumbnail,
series playlist, then cross-posts. A cross-post failure never undoes the YouTube upload.
"""
from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable

from ..domain.models import Script
from ..ports import CrossPoster, JobStore, UploadMetadata, VideoUploader

log = logging.getLogger(__name__)
MAX_TITLE = 50  # spec publisher checklist: title < 50 characters


def build_upload_metadata(script: Script, yt: dict, package: dict | None = None) -> UploadMetadata:
    # Owner decision: no AI wording in the description. The YouTube synthetic-media
    # flag (below) and the on-screen tag are what the platform and India's IT Rules require.
    if package:
        title, description = package["title"], package["description"]
        tags = tuple(package.get("tags") or ()) + (script.character,)
    else:
        title = next((t for t in script.title_options if len(t) < MAX_TITLE), None)
        if title is None:
            raise ValueError(f"No title option under {MAX_TITLE} characters")
        description = "\n".join([script.hook.text, "", "#shorts #comedy #hindi"])
        tags = ("shorts", "comedy", "hindi comedy", script.character)
    return UploadMetadata(
        title=title,
        description=description,
        tags=tags,
        category_id=str(yt["category_id"]),
        language=yt["default_language"],
        privacy=yt["privacy"],
        made_for_kids=False,                     # spec: Made for Kids = NO
        contains_synthetic_media=bool(yt.get("ai_disclosure", True)),
    )


class PublishService:
    def __init__(self, uploader: VideoUploader, store: JobStore, yt: dict,
                 crossposters: list[CrossPoster] = (), publish_at: Callable[[], datetime] | None = None) -> None:
        self.uploader, self.store, self.yt = uploader, store, yt
        self.crossposters, self.publish_at = list(crossposters), publish_at

    def run(self, job_id: str) -> str:
        jd = self.store.path(job_id)
        video = jd / "final.mp4"
        if not video.is_file():
            raise FileNotFoundError(f"{video} not found; run finalize first")
        package = self.store.read_json(job_id, "package.json") if (jd / "package.json").is_file() else None
        meta = build_upload_metadata(self.store.read_script(job_id), self.yt, package)
        if self.yt.get("schedule") and self.publish_at:
            meta = replace(meta, privacy="private", publish_at=self.publish_at())  # YouTube: scheduled = private + publishAt

        video_id = self.uploader.upload(video, meta)
        record: dict = {"youtube_id": video_id, "title": meta.title, "privacy": meta.privacy,
                        "publish_at": meta.publish_at.isoformat() if meta.publish_at else None,
                        "uploaded_at": datetime.now(timezone.utc).isoformat(), "crossposts": {}, "crosspost_errors": {}}

        thumb = jd / "thumb_1.png"
        if thumb.is_file() and hasattr(self.uploader, "set_thumbnail"):
            self._try(record, "thumbnail", lambda: self.uploader.set_thumbnail(video_id, thumb))
        if self.yt.get("playlist_id") and hasattr(self.uploader, "add_to_playlist"):
            self._try(record, "playlist", lambda: self.uploader.add_to_playlist(video_id, self.yt["playlist_id"]))

        caption = meta.title + "\n\n" + " ".join((package or {}).get("hashtags") or ["#shorts", "#comedy"])
        for poster in self.crossposters:
            try:
                record["crossposts"][poster.name] = poster.post(video, caption)
            except Exception as e:  # noqa: BLE001 - spec: a failure never blocks the rest
                log.error("Cross-post to %s failed: %s", poster.name, e)
                record["crosspost_errors"][poster.name] = str(e)
        self.store.write_json(job_id, "upload.json", record)
        return video_id

    @staticmethod
    def _try(record: dict, what: str, fn) -> None:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            log.warning("%s failed: %s", what, e)
            record.setdefault("warnings", {})[what] = str(e)
