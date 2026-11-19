"""Approver adapters (spec section 3, step 5): the human's 2-minute check.

TelegramApprover: sends the video with Approve / Reject buttons (needs TG_BOT_TOKEN + TG_CHAT_ID).
ConsoleApprover:  free fallback; decisions come from `python -m desiquip approve|reject <job>`.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def build_approval_message(job_id: str, title: str, qa: dict[str, Any] | None = None) -> str:
    lines = [f"🎬 {title}", f"Job: {job_id}"]
    review = (qa or {}).get("review") or {}
    if review:
        lines.append(f"QA: hook {review.get('hook')}, humour {review.get('humour')}")
    lines.append("Approve to publish, Reject to drop it (reply with a note to teach the system).")
    return "\n".join(lines)


class ConsoleApprover:
    def __init__(self, decisions_path: Path) -> None:
        self.path = Path(decisions_path)

    def request(self, job_id: str, video: Path, title: str) -> None:
        log.info("Awaiting approval: %s (%s). Watch %s, then run: python -m desiquip approve %s "
                 "(or reject %s --note \"why\")", job_id, title, video, job_id, job_id)

    def decide(self, job_id: str, decision: str, note: str = "") -> None:
        pending = self._read()
        pending.append([job_id, decision, note])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(pending, ensure_ascii=False), encoding="utf-8")

    def poll(self) -> list[tuple[str, str, str]]:
        pending = self._read()
        self.path.unlink(missing_ok=True)
        return [tuple(d) for d in pending]

    def notify(self, text: str) -> None:
        log.info("SUMMARY\n%s", text)

    def _read(self) -> list:
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.is_file() else []


class TelegramApprover:
    API = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, token: str, chat_id: str, offset_path: Path) -> None:
        self.token, self.chat_id, self.offset_path = token, chat_id, Path(offset_path)

    def _call(self, method: str, files: dict | None = None, **params: Any) -> Any:
        import requests

        r = requests.post(self.API.format(token=self.token, method=method), data=params, files=files, timeout=120)
        r.raise_for_status()
        body = r.json()
        if not body.get("ok"):
            raise RuntimeError(f"Telegram {method} failed: {body}")
        return body["result"]

    def request(self, job_id: str, video: Path, title: str) -> None:
        qa_path = video.parent / "qa.json"
        qa = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.is_file() else None
        keyboard = {"inline_keyboard": [[{"text": "✅ Approve", "callback_data": f"approve:{job_id}"},
                                         {"text": "❌ Reject", "callback_data": f"reject:{job_id}"}]]}
        with open(video, "rb") as f:
            self._call("sendVideo", files={"video": f}, chat_id=self.chat_id,
                       caption=build_approval_message(job_id, title, qa), reply_markup=json.dumps(keyboard))

    def poll(self) -> list[tuple[str, str, str]]:
        offset = int(self.offset_path.read_text()) if self.offset_path.is_file() else 0
        decisions, notes = [], {}
        for upd in self._call("getUpdates", offset=offset, timeout=0):
            offset = upd["update_id"] + 1
            cb = upd.get("callback_query")
            if cb and ":" in cb.get("data", ""):
                decision, job_id = cb["data"].split(":", 1)
                decisions.append((job_id, decision))
                self._call("answerCallbackQuery", callback_query_id=cb["id"], text=f"{decision}d {job_id}")
            msg = upd.get("message") or {}
            if msg.get("text", "").lower().startswith("note "):   # "note <job_id> <why>"
                parts = msg["text"].split(maxsplit=2)
                if len(parts) == 3:
                    notes[parts[1]] = parts[2]
        self.offset_path.parent.mkdir(parents=True, exist_ok=True)
        self.offset_path.write_text(str(offset))
        return [(job_id, d, notes.get(job_id, "")) for job_id, d in decisions]

    def notify(self, text: str) -> None:
        self._call("sendMessage", chat_id=self.chat_id, text=text)
