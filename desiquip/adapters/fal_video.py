"""ClipGenerator adapter: AI video through fal's queue API (one aggregator, so models swap by config).

Spec: Veo 3.1 first, Kling as fallback; poll up to 10 minutes, then fall back to the next model.
Audio is always off: the Hindi voice comes from our TTS (Kling's audio only speaks Chinese/English).
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

QUEUE = "https://queue.fal.run"


def build_request(model_key: str, prompt: str, seconds: int) -> tuple[str, dict[str, Any]]:
    if model_key in ("veo3.1-fast", "veo3.1"):
        model = "fal-ai/veo3.1/fast" if model_key == "veo3.1-fast" else "fal-ai/veo3.1"
        dur = 4 if seconds <= 4 else 6 if seconds <= 6 else 8      # Veo clips: 4/6/8 s
        return model, {"prompt": prompt, "aspect_ratio": "9:16", "duration": f"{dur}s", "generate_audio": False}
    if model_key == "kling-v3-pro":
        dur = 5 if seconds <= 5 else 10
        return ("fal-ai/kling-video/v3/pro/text-to-video",
                {"prompt": prompt, "aspect_ratio": "9:16", "duration": str(dur), "generate_audio": False})
    raise ValueError(f"Unknown clip model '{model_key}' (use veo3.1-fast, veo3.1 or kling-v3-pro)")


class FalVideo:
    def __init__(self, models: list[str], timeout_s: int = 600, poll_s: float = 5.0) -> None:
        self.models, self.timeout_s, self.poll_s = models, timeout_s, poll_s

    def generate(self, prompt: str, seconds: int, out: Path) -> None:
        if not os.environ.get("FAL_KEY", "").strip():
            raise RuntimeError("Set FAL_KEY in .env to generate AI clips (or set clips.models: [] in config.yaml)")
        out.parent.mkdir(parents=True, exist_ok=True)
        errors = []
        for model_key in self.models:
            try:
                self._run_one(model_key, prompt, seconds, out)
                return
            except Exception as e:  # noqa: BLE001 - try the next model, report all at the end
                log.warning("Clip model %s failed: %s", model_key, e)
                errors.append(f"{model_key}: {e}")
        raise RuntimeError("All clip models failed: " + "; ".join(errors))

    def _run_one(self, model_key: str, prompt: str, seconds: int, out: Path) -> None:
        import requests

        model, body = build_request(model_key, prompt, seconds)
        headers = {"Authorization": f"Key {os.environ['FAL_KEY'].strip()}"}
        job = requests.post(f"{QUEUE}/{model}", json=body, headers=headers, timeout=60)
        job.raise_for_status()
        job = job.json()
        deadline = time.monotonic() + self.timeout_s
        while True:
            status = requests.get(job["status_url"], headers=headers, timeout=30).json().get("status")
            if status == "COMPLETED":
                break
            if status not in ("IN_QUEUE", "IN_PROGRESS"):
                raise RuntimeError(f"fal job ended with status {status}")
            if time.monotonic() > deadline:
                raise TimeoutError(f"no result after {self.timeout_s} s")
            time.sleep(self.poll_s)
        result = requests.get(job["response_url"], headers=headers, timeout=60)
        result.raise_for_status()
        video = requests.get(result.json()["video"]["url"], timeout=300)
        video.raise_for_status()
        out.write_bytes(video.content)
        log.info("Clip ready from %s (%d KB)", model, len(video.content) // 1024)
