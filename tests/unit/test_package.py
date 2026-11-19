import json

import pytest

from desiquip.domain.package import AFFILIATE_DISCLOSURE, package_problems
from desiquip.services.package import PackageService
from desiquip.services.publish import build_upload_metadata

GOOD = {"title": "अंकल जी vs बिजली का बिल 😂", "description": "हर घर की कहानी!\n\n#shorts #comedy",
        "tags": ["hindi comedy", "uncle ji"], "hashtags": ["#shorts", "#comedy", "#hindicomedy"],
        "thumbnail_texts": ["₹5000 बिल?!", "अरे बाप रे!", "बत्ती गुल!"]}


class TestPackageRules:
    def test_good_package(self):
        assert package_problems(GOOD, has_products=False) == []

    def test_title_and_thumbnail_limits(self):
        bad = {**GOOD, "title": "x" * 50, "thumbnail_texts": ["a", "b"]}
        problems = package_problems(bad, has_products=False)
        assert any("title" in p for p in problems) and any("3 thumbnail" in p for p in problems)

    def test_no_ai_wording_in_description(self):
        # Owner decision: no "AI generated" text in descriptions (platform flag + on-screen tag cover it).
        bad = {**GOOD, "description": "This video is AI generated"}
        assert any("AI" in p for p in package_problems(bad, has_products=False))

    def test_affiliate_disclosure_required_when_products(self):
        assert any("disclosure" in p for p in package_problems(GOOD, has_products=True))
        ok = {**GOOD, "description": GOOD["description"] + "\n\n" + AFFILIATE_DISCLOSURE}
        assert package_problems(ok, has_products=True) == []

    def test_hashtag_limit(self):
        many = {**GOOD, "hashtags": [f"#t{i}" for i in range(16)]}
        assert any("hashtag" in p for p in package_problems(many, has_products=False))


class FakePackager:
    def __init__(self, store, pkg):
        self.store, self.pkg, self.calls = store, pkg, 0

    def run(self, agent, prompt, tools):
        self.calls += 1
        job = prompt.split("job ")[1].split(".")[0]
        (self.store.path(job) / "package.json").write_text(json.dumps(self.pkg, ensure_ascii=False), encoding="utf-8")
        return {}


class FakeStills:
    def __init__(self):
        self.calls = []

    def still(self, job_id, props, assets, out):
        self.calls.append(props["text"])
        out.write_bytes(b"png")


class TestPackageService:
    def test_writes_package_and_three_thumbnails(self, store, job):
        pkg = {**GOOD, "description": GOOD["description"] + "\n\n" + AFFILIATE_DISCLOSURE}  # demo has products
        stills = FakeStills()
        PackageService(FakePackager(store, pkg), stills, store).run(job)
        assert store.read_json(job, "package.json")["title"] == GOOD["title"]
        assert stills.calls == GOOD["thumbnail_texts"]
        assert all((store.path(job) / f"thumb_{i}.png").is_file() for i in (1, 2, 3))

    def test_invalid_package_is_rejected_after_retry(self, store, job):
        bad = {**GOOD, "title": "x" * 80}
        runner = FakePackager(store, bad)
        with pytest.raises(RuntimeError, match="title"):
            PackageService(runner, FakeStills(), store).run(job)
        assert runner.calls == 2


class TestPublishUsesPackage:
    YT = {"category_id": "23", "default_language": "hi", "privacy": "private", "ai_disclosure": True}

    def test_package_overrides_defaults(self, store, job):
        meta = build_upload_metadata(store.read_script(job), self.YT, package=GOOD)
        assert meta.title == GOOD["title"]
        assert meta.description.startswith("हर घर की कहानी")
        assert "hindi comedy" in meta.tags
