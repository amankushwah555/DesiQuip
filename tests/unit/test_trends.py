import json

import pytest

from desiquip.adapters.jobs_db import SqliteJobs
from desiquip.adapters.rights import SqliteRights
from desiquip.adapters.youtube_trending import build_trending_params, parse_trending
from desiquip.services.trends import TrendService, idea_problems

IDEA = {"topic": "अंकल जी और ऑनलाइन क्लास", "angle": "Uncle Ji attends grandson's online class",
        "scores": {"trend": 7, "humour": 8, "character_fit": 9, "product": 5}, "total": 29,
        "source_type": "original"}


class FakeTrendAgent:
    def __init__(self, root, ideas):
        self.root, self.ideas, self.prompts = root, ideas, []

    def run(self, agent, prompt, tools):
        self.prompts.append(prompt)
        out = prompt.split("Write ")[1].split(" ")[0]
        (self.root / out).parent.mkdir(parents=True, exist_ok=True)
        (self.root / out).write_text(json.dumps({"ideas": self.ideas}, ensure_ascii=False), encoding="utf-8")
        return {}


class FakeSource:
    def fetch(self):
        return [{"title": "Viral school video", "channel": "X", "views": 1000000, "category": "Comedy"}]


@pytest.fixture
def env(tmp_path, store):
    jobs, rights = SqliteJobs(tmp_path / "db.sqlite"), SqliteRights(tmp_path / "db.sqlite")
    return tmp_path, store, jobs, rights


def svc(env, ideas, source=FakeSource()):
    root, store, jobs, rights = env
    agent = FakeTrendAgent(root, ideas)
    return TrendService(agent, source, store, rights, jobs, root, today=lambda: "2026-11-20"), agent


class TestTrendService:
    def test_creates_dated_jobs_from_top_ideas(self, env):
        root, store, jobs, rights = env
        s, agent = svc(env, [IDEA, {**IDEA, "topic": "दूसरा", "total": 25}])
        created = s.run(count=2)
        assert created == ["2026-11-20-01", "2026-11-20-02"]
        idea = store.read_json("2026-11-20-01", "idea.json")
        assert idea["topic"].startswith("अंकल जी और ऑनलाइन क्लास")
        assert rights.is_valid("orig-2026-11-20-01")
        assert jobs.get("2026-11-20-02")["status"] == "idea"
        trends = json.loads((root / "data" / "trends" / "2026-11-20.json").read_text(encoding="utf-8"))
        assert trends["trending"][0]["title"] == "Viral school video"

    def test_job_ids_never_collide_with_existing_jobs(self, env):
        s, _ = svc(env, [IDEA, IDEA, IDEA])
        s.run(count=1)
        assert s.run(count=1) == ["2026-11-20-02"]

    def test_too_few_ideas_is_an_error_after_retry(self, env):
        s, agent = svc(env, [IDEA])
        with pytest.raises(RuntimeError, match="ideas"):
            s.run(count=2)
        assert len(agent.prompts) == 2

    def test_recent_topics_are_listed_so_ideas_dont_repeat(self, env):
        # Found in a real run: the same rejected idea came back the next run.
        s, agent = svc(env, [IDEA])
        s.run(count=1)
        s.run(count=1)
        assert "अंकल जी और ऑनलाइन क्लास" in agent.prompts[-1] and "do not repeat" in agent.prompts[-1].lower()

    def test_works_without_youtube_key(self, env):
        s, _ = svc(env, [IDEA], source=None)
        assert s.run(count=1) == ["2026-11-20-01"]


class TestIdeaRules:
    def test_reuploads_are_never_planned(self):
        # Spec content model: the system never re-uploads other creators' videos.
        assert any("original" in p for p in idea_problems([{**IDEA, "source_type": "reupload"}], 1))

    def test_needs_topic_and_scores(self):
        assert idea_problems([{"source_type": "original"}], 1)


class TestYouTubeTrending:
    def test_request_is_india_most_popular_in_category(self):
        p = build_trending_params("KEY", "23")
        assert p == {"part": "snippet,statistics", "chart": "mostPopular", "regionCode": "IN",
                     "videoCategoryId": "23", "maxResults": 25, "key": "KEY"}

    def test_parse_items(self):
        items = parse_trending({"items": [{"snippet": {"title": "T", "channelTitle": "C", "tags": ["a"]},
                                           "statistics": {"viewCount": "123"}}]}, "Comedy")
        assert items == [{"title": "T", "channel": "C", "views": 123, "tags": ["a"], "category": "Comedy"}]
