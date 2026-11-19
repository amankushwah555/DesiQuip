"""Publish-time scheduling (spec section 9: posts go out at the best slot, usually 6-9 pm IST)."""
from __future__ import annotations

from datetime import datetime, time, timedelta


def next_publish_time(now: datetime, slots: list[str], taken: list[datetime] = (),
                      min_lead: timedelta = timedelta(minutes=30)) -> datetime:
    """First 'HH:MM' slot at least min_lead after now that no other video has taken (today, else later days)."""
    parsed = sorted(time.fromisoformat(s) for s in slots)
    for day_offset in range(0, 8):
        day = (now + timedelta(days=day_offset)).date()
        for slot in parsed:
            candidate = datetime.combine(day, slot, tzinfo=now.tzinfo)
            if candidate >= now + min_lead and candidate not in taken:
                return candidate
    raise ValueError("No free publish slot in the next week")
