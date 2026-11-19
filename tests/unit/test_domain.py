import pytest

from desiquip.domain.models import Script, ScriptValidationError, Word
from desiquip.domain.timeline import build_timeline
from desiquip.domain.captions import group_words


def valid_script_dict(**overrides):
    d = {
        "job_id": "2026-11-19-01",
        "source_id": "orig-0001",
        "character": "uncle_ji",
        "length_s": 38,
        "hook": {"text": "अंकल ने फिर से किया!", "visual": "close-up shock face", "until_s": 2},
        "scenes": [
            {"t": [0, 4], "prompt": "uncle shocked", "clip": "hero", "line": "अरे बाप रे!",
             "caption": "अरे बाप रे!", "sfx": "boing"},
            {"t": [4, 8], "prompt": "kitchen", "clip": "remotion", "line": "ये क्या है?",
             "caption": "ये क्या है?", "sfx": None, "asset": "kitchen.png"},
        ],
        "product_moment": {"t": 22, "product_ref": "p1"},
        "products": [{"ref": "p1", "program": "amazon", "query": "mini chopper"}],
        "loop_end": True,
        "title_options": ["A", "B", "C"],
    }
    d.update(overrides)
    return d


class TestScript:
    def test_parses_spec_contract(self):
        s = Script.from_dict(valid_script_dict())
        assert s.job_id == "2026-11-19-01"
        assert s.character == "uncle_ji"
        assert s.hook.text.startswith("अंकल")
        assert len(s.scenes) == 2
        assert s.scenes[0].line == "अरे बाप रे!"
        assert s.scenes[1].asset == "kitchen.png"
        assert s.scenes[0].asset is None
        assert s.title_options[0] == "A"

    def test_missing_source_id_is_rejected(self):
        # Spec: never invent source rights; missing data = stop and flag it.
        with pytest.raises(ScriptValidationError, match="source_id"):
            Script.from_dict(valid_script_dict(source_id=""))

    def test_no_scenes_is_rejected(self):
        with pytest.raises(ScriptValidationError, match="scenes"):
            Script.from_dict(valid_script_dict(scenes=[]))

    def test_reports_all_errors_at_once(self):
        with pytest.raises(ScriptValidationError) as e:
            Script.from_dict(valid_script_dict(source_id="", character="", title_options=[]))
        msg = str(e.value)
        assert "source_id" in msg and "character" in msg and "title_options" in msg

    def test_scene_needs_line_or_caption(self):
        bad = valid_script_dict()
        bad["scenes"][0]["line"] = ""
        bad["scenes"][0]["caption"] = ""
        with pytest.raises(ScriptValidationError, match="scenes\\[0\\]"):
            Script.from_dict(bad)


class TestTimeline:
    def test_scenes_follow_audio_length_plus_gap(self):
        tl = build_timeline([2.0, 3.0], gap_s=0.25, min_scene_s=1.0)
        assert [(s.start, s.end) for s in tl] == [(0.0, 2.25), (2.25, 5.5)]

    def test_short_lines_get_minimum_scene_length(self):
        tl = build_timeline([0.5], gap_s=0.25, min_scene_s=2.0)
        assert tl[0].end == 2.0

    def test_silent_scene_still_has_minimum_length(self):
        tl = build_timeline([0.0, 1.0], gap_s=0.25, min_scene_s=2.0)
        assert tl[0].duration == 2.0
        assert tl[1].start == 2.0

    def test_empty_is_rejected(self):
        with pytest.raises(ValueError):
            build_timeline([], gap_s=0.25, min_scene_s=2.0)


class TestCaptionGroups:
    def words(self, *spans):
        return [Word(text=f"w{i}", start=a, end=b) for i, (a, b) in enumerate(spans)]

    def test_groups_by_size(self):
        g = group_words(self.words((0, .2), (.3, .5), (.6, .8), (.9, 1.1)), per_group=3)
        assert [len(x.words) for x in g] == [3, 1]
        assert (g[0].start, g[0].end) == (0, .9)  # held until the next group starts

    def test_long_pause_starts_new_group(self):
        g = group_words(self.words((0, .2), (1.5, 1.7)), per_group=3, max_gap_s=0.6)
        assert len(g) == 2

    def test_empty_gives_no_groups(self):
        assert group_words([], per_group=3) == []

    def test_caption_stays_on_screen_until_the_next_one(self):
        # Spec QA: captions on screen >= 90% of runtime, so short pauses must not blank the screen.
        g = group_words(self.words((0, .5), (1.2, 1.5)), per_group=1, hold_s=1.5)
        assert g[0].end == 1.2
        assert g[1].end == 1.5  # last group keeps its own end

    def test_hold_is_capped_for_long_silences(self):
        g = group_words(self.words((0, .5), (5.0, 5.5)), per_group=1, hold_s=1.5)
        assert g[0].end == 2.0
