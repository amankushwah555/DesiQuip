from pathlib import Path

import pytest

from desiquip.adapters.ffmpeg import (build_finalize_cmd, build_loudness_probe_cmd,
                                      build_mix_cmd, parse_loudnorm)
from desiquip.adapters.remotion import build_render_cmd, stage_assets
from desiquip.adapters.youtube import build_request_body
from desiquip.adapters.tts import voice_for
from desiquip.container import Container
from desiquip.ports import UploadMetadata, VideoSpec, VoicePlacement

LOUDNORM_STDERR = """
[Parsed_loudnorm_0 @ 000001]
{
	"input_i" : "-23.54",
	"input_tp" : "-7.12",
	"input_lra" : "6.30",
	"input_thresh" : "-33.81",
	"output_i" : "-14.02",
	"output_tp" : "-1.50",
	"output_lra" : "5.10",
	"output_thresh" : "-24.20",
	"normalization_type" : "dynamic",
	"target_offset" : "0.02"
}
"""


class TestFFmpeg:
    def test_mix_delays_each_clip_to_its_scene_start(self):
        cmd = build_mix_cmd("ffmpeg", [VoicePlacement(Path("a.mp3"), 0.0),
                                       VoicePlacement(Path("b.mp3"), 2.25)], 5.5, Path("v.wav"))
        f = cmd[cmd.index("-filter_complex") + 1]
        assert "adelay=0|0" in f and "adelay=2250|2250" in f
        assert "amix=inputs=2:normalize=0" in f
        assert "atrim=0:5.5" in f
        assert cmd[-1] == "v.wav"

    def test_mix_with_no_voice_makes_silence(self):
        cmd = build_mix_cmd("ffmpeg", [], 3.0, Path("v.wav"))
        assert "anullsrc" in " ".join(cmd)
        assert "-t" in cmd and "3.0" in cmd

    def test_parse_loudnorm_reads_measured_values(self):
        m = parse_loudnorm(LOUDNORM_STDERR)
        assert m == {"input_i": "-23.54", "input_tp": "-7.12", "input_lra": "6.30",
                     "input_thresh": "-33.81", "target_offset": "0.02"}

    def test_parse_loudnorm_without_json_raises(self):
        with pytest.raises(ValueError):
            parse_loudnorm("no json here")

    def test_loudness_probe_targets_spec_lufs(self):
        cmd = build_loudness_probe_cmd("ffmpeg", Path("r.mp4"), -14)
        assert "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json" in " ".join(cmd)

    def test_finalize_cmd_matches_spec_format(self):
        m = parse_loudnorm(LOUDNORM_STDERR)
        cmd = build_finalize_cmd("ffmpeg", Path("r.mp4"), Path("f.mp4"), VideoSpec(), m)
        s = " ".join(cmd)
        assert "scale=1080:1920:force_original_aspect_ratio=decrease" in s
        assert "pad=1080:1920" in s
        assert "fps=30" in s
        assert "measured_I=-23.54" in s and "linear=true" in s
        assert "-c:v libx264" in s and "-pix_fmt yuv420p" in s
        assert "-c:a aac" in s and "+faststart" in s

    def test_finalize_uses_nvenc_when_configured(self):
        cmd = build_finalize_cmd("ffmpeg", Path("r.mp4"), Path("f.mp4"),
                                 VideoSpec(encoder="h264_nvenc"), parse_loudnorm(LOUDNORM_STDERR))
        s = " ".join(cmd)
        assert "-c:v h264_nvenc" in s and "-crf" not in s


class TestYouTube:
    def test_request_body_sets_disclosure_and_not_for_kids(self):
        meta = UploadMetadata(title="T", description="D", tags=("a",), category_id="23",
                              language="hi", privacy="private", made_for_kids=False,
                              contains_synthetic_media=True)
        body = build_request_body(meta)
        assert body["snippet"] == {"title": "T", "description": "D", "tags": ["a"],
                                   "categoryId": "23", "defaultLanguage": "hi",
                                   "defaultAudioLanguage": "hi"}
        assert body["status"] == {"privacyStatus": "private", "selfDeclaredMadeForKids": False,
                                  "containsSyntheticMedia": True}


class TestYouTubeScopes:
    def test_all_scopes_requested_up_front(self):
        # Desktop OAuth clients can't add scopes later, so request Analytics (week 4 Growth agent) now.
        from desiquip.adapters.youtube import SCOPES
        assert "https://www.googleapis.com/auth/youtube.upload" in SCOPES
        assert "https://www.googleapis.com/auth/yt-analytics.readonly" in SCOPES
        assert "https://www.googleapis.com/auth/youtube.force-ssl" in SCOPES  # comments + thumbnails


class TestRemotion:
    def test_stage_copies_assets_and_namespaces_props(self, tmp_path):
        src = tmp_path / "job"
        src.mkdir()
        (src / "voice.wav").write_bytes(b"w")
        (src / "kitchen.png").write_bytes(b"p")
        public = tmp_path / "public"
        props = {"audio": "voice.wav", "scenes": [{"asset": "kitchen.png"}, {"asset": None}]}
        staged = stage_assets(public, "job1", props,
                              {"voice.wav": src / "voice.wav", "kitchen.png": src / "kitchen.png"})
        assert (public / "jobs" / "job1" / "kitchen.png").read_bytes() == b"p"
        assert staged["audio"] == "jobs/job1/voice.wav"
        assert staged["scenes"][0]["asset"] == "jobs/job1/kitchen.png"
        assert staged["scenes"][1]["asset"] is None
        assert props["audio"] == "voice.wav"  # input not mutated

    def test_render_cmd_calls_local_cli_with_node(self):
        # No npx: run the project's pinned CLI directly (robust PATH, no npx startup cost).
        cmd = build_render_cmd("node", Path("props.json"), Path("out.mp4"), concurrency="100%")
        assert cmd[:4] == ["node", str(Path("node_modules/@remotion/cli/remotion-cli.js")), "render", "src/index.ts"]
        assert "Short" in cmd and "--props=props.json" in cmd and "out.mp4" in cmd
        assert "--concurrency=100%" in cmd


class TestTTSConfig:
    CHARS = {"uncle_ji": {"edge_voice": "hi-IN-MadhurNeural", "elevenlabs_voice_env": "VOICE_ID_UNCLE_JI"}}

    def test_voice_lookup(self):
        assert voice_for(self.CHARS, "uncle_ji", "edge_voice") == "hi-IN-MadhurNeural"

    def test_unknown_character_is_a_clear_error(self):
        with pytest.raises(KeyError, match="bua_ji"):
            voice_for(self.CHARS, "bua_ji", "edge_voice")


class TestElevenLabsHTTP:
    """ElevenLabs over plain HTTPS (no SDK: its deep package paths break pip on Windows' 260-char limit)."""

    class Resp:
        status_code = 200
        content = b"mp3-bytes"
        text = ""

        def raise_for_status(self):
            pass

    def test_posts_text_with_voice_and_key(self, tmp_path, monkeypatch):
        from desiquip.adapters.tts import ElevenLabsTTS
        monkeypatch.setenv("ELEVENLABS_API_KEY", "k123")
        monkeypatch.setenv("VOICE_ID_UNCLE_JI", "v456")
        calls = []
        tts = ElevenLabsTTS(TestTTSConfig.CHARS, post=lambda url, **kw: calls.append((url, kw)) or self.Resp())
        out = tmp_path / "a.mp3"
        tts.synthesize("नमस्ते", "uncle_ji", out)
        url, kw = calls[0]
        assert url == "https://api.elevenlabs.io/v1/text-to-speech/v456?output_format=mp3_44100_128"
        assert kw["headers"]["xi-api-key"] == "k123"
        assert kw["json"] == {"text": "नमस्ते", "model_id": "eleven_multilingual_v2"}
        assert out.read_bytes() == b"mp3-bytes"

    def test_missing_key_is_a_clear_error(self, tmp_path, monkeypatch):
        from desiquip.adapters.tts import ElevenLabsTTS
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY"):
            ElevenLabsTTS(TestTTSConfig.CHARS, post=lambda *a, **k: None).synthesize("x", "uncle_ji", tmp_path / "a.mp3")


def test_no_sdk_with_overlong_paths_in_requirements():
    reqs = (Path(__file__).resolve().parents[2] / "requirements.txt").read_text()
    assert "elevenlabs" not in reqs


class TestContainer:
    def cfg(self, engine="edge"):
        return {"video": {"width": 1080, "height": 1920, "fps": 30, "encoder": "libx264", "loudness_lufs": -14},
                "voice": {"engine": engine, "scene_gap_s": 0.25, "min_scene_s": 2.0},
                "captions": {"model": "small", "language": "hi", "device": "cpu", "words_per_group": 3},
                "characters": TestTTSConfig.CHARS,
                "youtube": {"category_id": "23", "default_language": "hi", "privacy": "private", "ai_disclosure": True}}

    def test_tts_engine_is_chosen_by_config(self, tmp_path):
        from desiquip.adapters.tts import EdgeTTS, ElevenLabsTTS
        assert isinstance(Container(self.cfg("edge"), tmp_path).tts(), EdgeTTS)
        assert isinstance(Container(self.cfg("elevenlabs"), tmp_path).tts(), ElevenLabsTTS)

    def test_unknown_engine_is_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="voice.engine"):
            Container(self.cfg("robot"), tmp_path).tts()

    def test_video_spec_from_config(self, tmp_path):
        assert Container(self.cfg(), tmp_path).video_spec() == VideoSpec(1080, 1920, 30, -14, "libx264")
