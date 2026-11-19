"""Use case: final.mp4 -> YouTube upload (private until the API audit passes)."""
from __future__ import annotations

from datetime import datetime, timezone

from ..domain.models import Script
from ..ports import JobStore, UploadMetadata, VideoUploader

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
    def __init__(self, uploader: VideoUploader, store: JobStore, yt: dict) -> None:
        self.uploader, self.store, self.yt = uploader, store, yt

    def run(self, job_id: str) -> str:
        video = self.store.path(job_id) / "final.mp4"
        if not video.is_file():
            raise FileNotFoundError(f"{video} not found; run finalize first")
        jd = self.store.path(job_id)
        package = self.store.read_json(job_id, "package.json") if (jd / "package.json").is_file() else None
        meta = build_upload_metadata(self.store.read_script(job_id), self.yt, package)
        video_id = self.uploader.upload(video, meta)
        self.store.write_json(job_id, "upload.json", {
            "youtube_id": video_id, "title": meta.title, "privacy": meta.privacy,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        })
        return video_id
