import pytest

from desiquip.adapters.claude_agent import build_agent_cmd
from desiquip.adapters.rights import SqliteRights
from desiquip.domain.qa import QARules, caption_coverage, evaluate
from desiquip.ports import MediaInfo
from desiquip.services.qa import QAFailed, QAService

GOOD = MediaInfo(width=1080, height=1920, fps=30.0, duration_s=38.0, vcodec="h264", acodec="aac", lufs=-14.1)
RULES = QARules()


def names_failed(checks):
    return {c.name for c in checks if not c.ok}


class TestQARules:
    def test_good_video_passes_every_check(self):
        checks = evaluate(GOOD, coverage=0.95, products=2, rights_ok=True, rules=RULES)
        assert names_failed(checks) == set()

    @pytest.mark.parametrize("field,value,check", [
        ("duration_s", 29.0, "length"), ("duration_s", 46.0, "length"),
        ("width", 720, "format"), ("fps", 25.0, "format"), ("vcodec", "hevc", "format"),
        ("lufs", -17.0, "loudness"), ("lufs", -11.0, "loudness")])
    def test_each_measurable_rule(self, field, value, check):
        info = MediaInfo(**{**GOOD.__dict__, field: value})
        assert check in names_failed(evaluate(info, 0.95, 2, True, RULES))

    def test_captions_rights_and_products(self):
        failed = names_failed(evaluate(GOOD, coverage=0.80, products=4, rights_ok=False, rules=RULES))
        assert {"captions", "products", "rights"} <= failed

    def test_caption_coverage_from_groups(self):
        groups = [{"start": 0, "end": 5}, {"start": 6, "end": 10}]
        assert caption_coverage(groups, 10.0) == pytest.approx(0.9)


class FakeMediaQA:
    def __init__(self, info=GOOD):
        self.info = info

    def inspect(self, path):
        return self.info

    def frames(self, src, times, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, _ in enumerate(times):
            p = out_dir / f"frame_{i}.jpg"
            p.write_bytes(b"jpg")
            paths.append(p)
        return paths


class FakeReviewer:
    def __init__(self, review):
        self.review_data, self.frames = review, None

    def review(self, job_id, frames):
        self.frames = frames
        return self.review_data


GOOD_REVIEW = {"hook": 8, "humour": 7, "safety_ok": True, "notes": "funny"}


@pytest.fixture
def qa_job(store, job, tmp_path):
    store.write_json(job, "captions.json", {"groups": [{"start": 0.0, "end": 37.0}]})
    (store.path(job) / "final.mp4").write_bytes(b"mp4")
    rights = SqliteRights(tmp_path / "db.sqlite")
    rights.add("orig-0001", "original", owner="DesiQuip")
    return job, rights


class TestQAService:
    def test_pass_writes_qa_json(self, store, qa_job):
        job, rights = qa_job
        rv = FakeReviewer(GOOD_REVIEW)
        QAService(FakeMediaQA(), store, rights, rv, RULES).run(job)
        qa = store.read_json(job, "qa.json")
        assert qa["passed"] is True and qa["review"]["humour"] == 7
        assert len(rv.frames) == 3  # frames from the first 3 seconds

    def test_unfunny_script_fails_as_content_problem(self, store, qa_job):
        job, rights = qa_job
        with pytest.raises(QAFailed) as e:
            QAService(FakeMediaQA(), store, rights, FakeReviewer({**GOOD_REVIEW, "humour": 5}), RULES).run(job)
        assert e.value.kind == "content"
        assert store.read_json(job, "qa.json")["passed"] is False

    def test_technical_failure_is_reported_as_technical(self, store, qa_job):
        job, rights = qa_job
        loud = MediaInfo(**{**GOOD.__dict__, "lufs": -9.0})
        with pytest.raises(QAFailed) as e:
            QAService(FakeMediaQA(loud), store, rights, FakeReviewer(GOOD_REVIEW), RULES).run(job)
        assert e.value.kind == "technical" and "loudness" in str(e.value)

    def test_unknown_source_fails_rights(self, store, qa_job, tmp_path):
        job, _ = qa_job
        empty = SqliteRights(tmp_path / "other.sqlite")
        with pytest.raises(QAFailed, match="rights"):
            QAService(FakeMediaQA(), store, empty, FakeReviewer(GOOD_REVIEW), RULES).run(job)

    def test_unsafe_content_never_passes(self, store, qa_job):
        job, rights = qa_job
        with pytest.raises(QAFailed, match="safety"):
            QAService(FakeMediaQA(), store, rights, FakeReviewer({**GOOD_REVIEW, "safety_ok": False}), RULES).run(job)


class TestRights:
    def test_expired_rights_are_invalid(self, tmp_path):
        r = SqliteRights(tmp_path / "db.sqlite")
        r.add("lic-1", "licensed", owner="Creator X", expires_at="2020-01-01")
        r.add("orig-1", "original", owner="DesiQuip")
        assert r.is_valid("orig-1") and not r.is_valid("lic-1") and not r.is_valid("nope")


def test_parse_media_info_and_loudness():
    from desiquip.adapters.ffmpeg import parse_integrated_lufs, parse_probe
    lufs = parse_integrated_lufs("  Integrated loudness:\n    I:         -14.0 LUFS\n    Threshold: -24.1 LUFS")
    info = parse_probe({"streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920, "r_frame_rate": "30/1"},
        {"codec_type": "audio", "codec_name": "aac"}], "format": {"duration": "41.1"}}, lufs)
    assert info == MediaInfo(1080, 1920, 30.0, 41.1, "h264", "aac", -14.0)


def test_agent_command_is_generic_and_scoped():
    cmd = build_agent_cmd("claude", "qa-reviewer", "PROMPT", "Read,Write(jobs/**)", 0.5)
    assert cmd[:3] == ["claude", "-p", "PROMPT"]
    assert cmd[cmd.index("--agent") + 1] == "qa-reviewer"
    assert cmd[cmd.index("--allowedTools") + 1] == "Read,Write(jobs/**)"
