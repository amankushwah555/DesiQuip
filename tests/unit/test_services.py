import pytest

from desiquip.domain.models import Word
from desiquip.ports import VideoSpec
from desiquip.services.voice import VoiceService
from desiquip.services.captions import CaptionService
from desiquip.services.render import RenderService, build_render_props
from desiquip.services.finalize import FinalizeService
from desiquip.services.publish import PublishService, build_upload_metadata
from tests.fakes import FakeMedia, FakeRenderer, FakeTranscriber, FakeTTS, FakeUploader


class TestJobStore:
    def test_unknown_job_raises(self, store):
        with pytest.raises(FileNotFoundError):
            store.read_script("nope")

    def test_json_round_trip_keeps_hindi(self, store, job):
        p = store.write_json(job, "x.json", {"t": "नमस्ते"})
        assert "नमस्ते" in p.read_text(encoding="utf-8")
        assert store.read_json(job, "x.json") == {"t": "नमस्ते"}


class TestVoiceService:
    def make(self, store):
        tts, media = FakeTTS(), FakeMedia()
        return VoiceService(tts, media, store, gap_s=0.25, min_scene_s=0.5), tts, media

    def test_synthesises_every_line_with_the_character(self, store, job):
        svc, tts, _ = self.make(store)
        svc.run(job)
        assert tts.calls == [("अरे बाप रे!", "uncle_ji"), ("ये क्या है?", "uncle_ji")]

    def test_writes_timeline_from_real_audio_lengths(self, store, job):
        svc, _, _ = self.make(store)
        svc.run(job)
        tl = store.read_json(job, "timeline.json")
        # "अरे बाप रे!" = 11 chars -> 1.1 s (+0.25 gap); "ये क्या है?" = 11 chars -> 1.1 s
        assert tl["scenes"][0]["start"] == 0.0
        assert tl["scenes"][0]["end"] == pytest.approx(1.35)
        assert tl["duration_s"] == pytest.approx(2.7)

    def test_places_each_clip_at_its_scene_start(self, store, job):
        svc, _, media = self.make(store)
        svc.run(job)
        placements, total, out = media.mixed
        assert [p.start_s for p in placements] == [0.0, pytest.approx(1.35)]
        assert total == pytest.approx(2.7)
        assert out.name == "voice.wav"

    def test_silent_scene_is_not_synthesised(self, store, job):
        import json
        p = store.path(job) / "script.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        d["scenes"][1]["line"] = ""
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        svc, tts, media = self.make(store)
        svc.run(job)
        assert len(tts.calls) == 1
        assert len(media.mixed[0]) == 1


class TestCaptionService:
    TIMELINE = {"duration_s": 2.7, "scenes": [{"index": 0, "start": 0.0, "end": 1.35, "voice_s": 1.1},
                                              {"index": 1, "start": 1.35, "end": 2.7, "voice_s": 1.1}]}

    def test_caption_text_comes_from_script_timing_from_whisper(self, store, job):
        store.write_json(job, "timeline.json", self.TIMELINE)
        heard = [Word("औरे", 0.0, 0.3), Word("बाप", 0.35, 0.6), Word("रे", 0.65, 0.9),   # misspelt by ASR
                 Word("ये", 1.4, 1.6), Word("क्या", 1.7, 1.9), Word("है", 2.0, 2.3)]
        CaptionService(FakeTranscriber(heard), store, language="hi", per_group=3).run(job)
        c = store.read_json(job, "captions.json")
        assert [w["text"] for w in c["words"]] == ["अरे", "बाप", "रे!", "ये", "क्या", "है?"]
        assert c["words"][3]["start"] == 1.4
        assert len(c["groups"]) == 2

    def test_no_words_is_an_error(self, store, job):
        store.write_json(job, "timeline.json", self.TIMELINE)
        with pytest.raises(RuntimeError, match="no words"):
            CaptionService(FakeTranscriber([]), store, language="hi", per_group=3).run(job)


class TestRender:
    TIMELINE = {"duration_s": 4.0, "scenes": [
        {"index": 0, "start": 0.0, "end": 2.0, "voice_s": 1.5},
        {"index": 1, "start": 2.0, "end": 4.0, "voice_s": 1.5}]}
    CAPTIONS = {"words": [], "groups": [{"start": 0.0, "end": 0.5,
                                         "words": [{"text": "अरे", "start": 0.0, "end": 0.5}]}]}

    def test_props_combine_script_timeline_and_captions(self, store, job):
        script = store.read_script(job)
        props = build_render_props(script, self.TIMELINE, self.CAPTIONS, fps=30)
        assert props["durationInFrames"] == 120
        assert props["fps"] == 30
        assert props["audio"] == "voice.wav"
        assert props["aiTag"] is True
        assert props["hook"]["text"] == script.hook.text
        assert props["scenes"][1] == {"start": 2.0, "end": 4.0, "caption": "ये क्या है?",
                                      "prompt": "kitchen", "asset": "kitchen.png", "sfx": None}
        assert props["captionGroups"] == self.CAPTIONS["groups"]

    def test_render_passes_voice_and_scene_assets(self, store, job):
        store.write_json(job, "timeline.json", self.TIMELINE)
        store.write_json(job, "captions.json", self.CAPTIONS)
        (store.path(job) / "voice.wav").write_bytes(b"wav")
        r = FakeRenderer()
        out = RenderService(r, store, fps=30).run(job)
        job_id, props, assets, rendered = r.calls[0]
        assert job_id == job
        assert set(assets) == {"voice.wav", "kitchen.png"}
        assert rendered == out and out.name == "render.mp4"

    def test_missing_scene_asset_is_an_error(self, store, job):
        store.write_json(job, "timeline.json", self.TIMELINE)
        store.write_json(job, "captions.json", self.CAPTIONS)
        (store.path(job) / "voice.wav").write_bytes(b"wav")
        (store.path(job) / "kitchen.png").unlink()
        with pytest.raises(FileNotFoundError, match="kitchen.png"):
            RenderService(FakeRenderer(), store, fps=30).run(job)


class TestFinalize:
    def test_exports_final_mp4_with_spec(self, store, job):
        (store.path(job) / "render.mp4").write_bytes(b"r")
        media, spec = FakeMedia(), VideoSpec(encoder="h264_nvenc")
        out = FinalizeService(media, store, spec).run(job)
        src, dst, used = media.finalized
        assert src.name == "render.mp4" and dst == out and out.name == "final.mp4"
        assert used is spec


class TestPublish:
    YT = {"category_id": "23", "default_language": "hi", "privacy": "private", "ai_disclosure": True}

    def test_metadata_is_private_and_sets_platform_flag(self, store, job):
        meta = build_upload_metadata(store.read_script(job), self.YT)
        assert meta.privacy == "private"
        assert meta.made_for_kids is False          # spec: Made for Kids = NO
        assert meta.contains_synthetic_media is True
        assert meta.category_id == "23"

    def test_description_has_no_ai_text(self, store, job):
        # Owner decision 2026-11-19: no "AI generated" wording in the description.
        meta = build_upload_metadata(store.read_script(job), self.YT)
        assert "AI" not in meta.description

    def test_uses_first_title_under_50_chars(self, store, job):
        script = store.read_script(job)
        long = "x" * 60
        script = type(script)(**{**script.__dict__, "title_options": (long, "Short title", "C")})
        meta = build_upload_metadata(script, self.YT)
        assert meta.title == "Short title"

    def test_all_titles_too_long_is_an_error(self, store, job):
        script = store.read_script(job)
        script = type(script)(**{**script.__dict__, "title_options": ("x" * 60,)})
        with pytest.raises(ValueError, match="50"):
            build_upload_metadata(script, self.YT)

    def test_uploads_final_and_saves_video_id(self, store, job):
        (store.path(job) / "final.mp4").write_bytes(b"f")
        up = FakeUploader("abc123")
        vid = PublishService(up, store, self.YT).run(job)
        assert vid == "abc123"
        assert up.calls[0][0].name == "final.mp4"
        assert store.read_json(job, "upload.json")["youtube_id"] == "abc123"

    def test_refuses_without_final_video(self, store, job):
        with pytest.raises(FileNotFoundError):
            PublishService(FakeUploader(), store, self.YT).run(job)
