import json
from datetime import datetime, timedelta, timezone

import pytest

from desiquip.adapters.crosspost import build_ig_container_params, build_x_post_body
from desiquip.adapters.youtube_analytics import build_analytics_params, parse_analytics
from desiquip.domain.schedule import next_publish_time
from desiquip.services.growth import GrowthService
from desiquip.services.publish import PublishService

IST = timezone(timedelta(hours=5, minutes=30))


class TestSchedule:
    SLOTS = ["18:30", "20:00"]

    def test_next_slot_today(self):
        now = datetime(2026, 11, 20, 14, 0, tzinfo=IST)
        assert next_publish_time(now, self.SLOTS) == datetime(2026, 11, 20, 18, 30, tzinfo=IST)

    def test_too_close_slot_is_skipped(self):
        now = datetime(2026, 11, 20, 18, 10, tzinfo=IST)   # less than 30 min before 18:30
        assert next_publish_time(now, self.SLOTS) == datetime(2026, 11, 20, 20, 0, tzinfo=IST)

    def test_after_last_slot_rolls_to_tomorrow(self):
        now = datetime(2026, 11, 20, 22, 0, tzinfo=IST)
        assert next_publish_time(now, self.SLOTS) == datetime(2026, 11, 21, 18, 30, tzinfo=IST)

    def test_taken_slots_are_not_reused(self):
        now = datetime(2026, 11, 20, 14, 0, tzinfo=IST)
        taken = [datetime(2026, 11, 20, 18, 30, tzinfo=IST)]
        assert next_publish_time(now, self.SLOTS, taken) == datetime(2026, 11, 20, 20, 0, tzinfo=IST)


class RecordingUploader:
    def __init__(self):
        self.meta, self.thumb, self.playlist = None, None, None

    def upload(self, video, meta):
        self.meta = meta
        return "vid1"

    def set_thumbnail(self, video_id, image):
        self.thumb = (video_id, image.name)

    def add_to_playlist(self, video_id, playlist_id):
        self.playlist = (video_id, playlist_id)


class FakeCrossPoster:
    def __init__(self, name):
        self.name, self.posts = name, []

    def post(self, video, caption):
        self.posts.append(caption)
        return f"{self.name}-1"


class TestPublishExtras:
    YT = {"category_id": "23", "default_language": "hi", "privacy": "private", "ai_disclosure": True,
          "schedule": True, "playlist_id": "PL1"}

    def test_scheduled_upload_with_thumbnail_playlist_and_crossposts(self, store, job):
        jd = store.path(job)
        (jd / "final.mp4").write_bytes(b"v")
        (jd / "thumb_1.png").write_bytes(b"p")
        up, ig = RecordingUploader(), FakeCrossPoster("ig")
        when = datetime(2026, 11, 20, 18, 30, tzinfo=IST)
        PublishService(up, store, self.YT, crossposters=[ig], publish_at=lambda: when).run(job)
        assert up.meta.publish_at == when and up.meta.privacy == "private"   # YouTube needs private + publishAt
        assert up.thumb == ("vid1", "thumb_1.png") and up.playlist == ("vid1", "PL1")
        assert ig.posts and store.read_json(job, "upload.json")["crossposts"] == {"ig": "ig-1"}

    def test_crosspost_failure_does_not_undo_youtube(self, store, job):
        (store.path(job) / "final.mp4").write_bytes(b"v")

        class Broken:
            name = "x"

            def post(self, video, caption):
                raise RuntimeError("X down")
        vid = PublishService(RecordingUploader(), store, {**self.YT, "schedule": False},
                             crossposters=[Broken()]).run(job)
        assert vid == "vid1"
        assert "X down" in store.read_json(job, "upload.json")["crosspost_errors"]["x"]


class TestCrossPostRequests:
    def test_instagram_reel_container(self):
        p = build_ig_container_params("cap #shorts", "TOKEN")
        assert p == {"media_type": "REELS", "upload_type": "resumable", "caption": "cap #shorts",
                     "share_to_feed": "true", "access_token": "TOKEN"}

    def test_x_post_with_video(self):
        assert build_x_post_body("hi", "m1") == {"text": "hi", "media": {"media_ids": ["m1"]}}


class TestAnalytics:
    def test_params_for_yesterday_per_video(self):
        p = build_analytics_params(["a", "b"], "2026-11-19")
        assert p["ids"] == "channel==MINE" and p["dimensions"] == "video"
        assert p["filters"] == "video==a,b" and p["startDate"] == p["endDate"] == "2026-11-19"
        assert "averageViewPercentage" in p["metrics"]

    def test_parse_rows(self):
        body = {"columnHeaders": [{"name": "video"}, {"name": "views"}, {"name": "averageViewPercentage"}],
                "rows": [["a", 120, 55.5]]}
        assert parse_analytics(body) == {"a": {"views": 120, "averageViewPercentage": 55.5}}


class FakeYT:
    def __init__(self):
        self.replies = []

    def metrics(self, video_ids, day):
        return {v: {"views": 100, "averageViewPercentage": 60.0} for v in video_ids}

    def new_comments(self, video_ids):
        return [{"comment_id": f"c{i}", "video_id": "vid1", "text": "😂 so true"} for i in range(30)]

    def reply(self, comment_id, text):
        self.replies.append((comment_id, text))


class FakeGrowthAgent:
    def __init__(self, root):
        self.root = root

    def run(self, agent, prompt, tools):
        out = prompt.split("Write replies to ")[1].split(" ")[0]
        replies = [{"comment_id": f"c{i}", "text": "धन्यवाद! 😂"} for i in range(30)]
        (self.root / out).write_text(json.dumps({"replies": replies}, ensure_ascii=False), encoding="utf-8")
        return {}


class TestGrowth:
    def test_collects_metrics_and_posts_capped_replies(self, tmp_path, store):
        from desiquip.adapters.jobs_db import SqliteJobs
        jobs = SqliteJobs(tmp_path / "db.sqlite")
        jobs.create("j1")
        jobs.set("j1", "published", youtube_id="vid1")
        yt = FakeYT()
        GrowthService(FakeGrowthAgent(tmp_path), yt, jobs, tmp_path, max_replies=20,
                      today=lambda: "2026-11-20").run()
        metrics = json.loads((tmp_path / "data" / "growth" / "2026-11-20-metrics.json").read_text(encoding="utf-8"))
        assert metrics["2026-11-19"]["vid1"]["views"] == 100
        assert len(yt.replies) == 20                     # capped
        assert jobs.get("j1")["status"] == "measured"

    def test_nothing_published_is_a_quiet_noop(self, tmp_path, store):
        from desiquip.adapters.jobs_db import SqliteJobs
        yt = FakeYT()
        GrowthService(FakeGrowthAgent(tmp_path), yt, SqliteJobs(tmp_path / "db.sqlite"), tmp_path).run()
        assert yt.replies == []
