import pytest

from desiquip.adapters.fal_video import FalVideo, build_request
from desiquip.services.clips import ClipService
from desiquip.services.render import build_render_props


class FakeClipGen:
    def __init__(self, fail_models=()):
        self.calls = []

    def generate(self, prompt, seconds, out):
        self.calls.append((prompt, seconds))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"mp4")


TIMELINE = {"duration_s": 8.0, "scenes": [
    {"index": 0, "start": 0.0, "end": 3.2, "voice_s": 3.0},
    {"index": 1, "start": 3.2, "end": 8.0, "voice_s": 4.5}]}


class TestClipService:
    def test_generates_only_hero_scenes_without_an_asset(self, store, job):
        # conftest script: scene 0 is "hero", scene 1 is "remotion" with its own asset
        store.write_json(job, "timeline.json", TIMELINE)
        gen = FakeClipGen()
        ClipService(gen, store, max_hero=3).run(job)
        assert gen.calls == [("uncle shocked", 4)]          # 3.2 s rounded up to whole seconds
        assert store.read_json(job, "clips.json") == {"0": "clips/scene_00.mp4"}

    def test_caps_number_of_paid_clips(self, store, job):
        store.write_json(job, "timeline.json", TIMELINE)
        gen = FakeClipGen()
        ClipService(gen, store, max_hero=0).run(job)
        assert gen.calls == [] and store.read_json(job, "clips.json") == {}

    def test_disabled_generator_writes_empty_clip_list(self, store, job):
        store.write_json(job, "timeline.json", TIMELINE)
        ClipService(None, store, max_hero=3).run(job)
        assert store.read_json(job, "clips.json") == {}

    def test_render_props_use_generated_clip_as_scene_asset(self, store, job):
        props = build_render_props(store.read_script(job), TIMELINE, {"groups": []}, fps=30,
                                   clips={"0": "clips/scene_00.mp4"})
        assert props["scenes"][0]["asset"] == "clips/scene_00.mp4"
        assert props["scenes"][1]["asset"] == "kitchen.png"   # script's own asset kept

    def test_placeholder_scenes_carry_no_debug_text(self, store, job):
        props = build_render_props(store.read_script(job), TIMELINE, {"groups": []}, fps=30)
        assert "prompt" not in props["scenes"][0]  # English prompts never reach the screen


class TestFalRequests:
    def test_veo_request_is_vertical_silent_and_clamped(self):
        model, body = build_request("veo3.1-fast", "uncle laughs", seconds=11)
        assert model == "fal-ai/veo3.1/fast"
        assert body == {"prompt": "uncle laughs", "aspect_ratio": "9:16", "duration": "8s",
                        "generate_audio": False}

    def test_kling_request_turns_off_its_chinese_english_audio(self):
        model, body = build_request("kling-v3-pro", "uncle laughs", seconds=4)
        assert model == "fal-ai/kling-video/v3/pro/text-to-video"
        assert body["generate_audio"] is False and body["duration"] == "5"
        assert body["aspect_ratio"] == "9:16"

    def test_unknown_model_rejected(self):
        with pytest.raises(ValueError):
            build_request("sora", "x", 4)

    def test_falls_back_to_next_model_when_first_fails(self, tmp_path, monkeypatch):
        monkeypatch.setenv("FAL_KEY", "k")
        tried = []

        def fake_run(self, model_key, prompt, seconds, out):
            tried.append(model_key)
            if model_key == "veo3.1-fast":
                raise TimeoutError("10 min")
            out.write_bytes(b"ok")
        monkeypatch.setattr(FalVideo, "_run_one", fake_run)
        FalVideo(["veo3.1-fast", "kling-v3-pro"]).generate("p", 4, tmp_path / "c.mp4")
        assert tried == ["veo3.1-fast", "kling-v3-pro"]
        assert (tmp_path / "c.mp4").read_bytes() == b"ok"

    def test_missing_key_is_clear(self, monkeypatch, tmp_path):
        monkeypatch.delenv("FAL_KEY", raising=False)
        with pytest.raises(RuntimeError, match="FAL_KEY"):
            FalVideo(["veo3.1-fast"]).generate("p", 4, tmp_path / "c.mp4")
