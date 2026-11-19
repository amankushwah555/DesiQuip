import threading
import time

import pytest

from desiquip.domain.captions import align_to_script
from desiquip.domain.models import Word
from desiquip.services.voice import VoiceService
from tests.fakes import FakeMedia, FakeTTS


class TestAlignToScript:
    """Caption text comes from the script (exact spelling); Whisper only supplies timing."""

    def test_same_word_count_keeps_whisper_timing_and_script_text(self):
        heard = [Word("औरे", 0.0, 0.3), Word("बाप्रे", 0.4, 0.8)]
        out = align_to_script([(0.0, 1.0, "अरे बापरे")], heard)
        assert out == [Word("अरे", 0.0, 0.3), Word("बापरे", 0.4, 0.8)]

    def test_different_word_count_spreads_by_length_over_heard_span(self):
        # Whisper merged "बाप रे" into one word: 2 heard vs 3 written.
        heard = [Word("औरे", 1.0, 1.4), Word("बाप्रे", 1.5, 2.0)]
        out = align_to_script([(1.0, 3.0, "अरे बाप रे")], heard)
        assert [w.text for w in out] == ["अरे", "बाप", "रे"]
        assert out[0].start == 1.0 and out[-1].end == 2.0
        assert all(a.end <= b.start for a, b in zip(out, out[1:]))

    def test_scene_with_nothing_heard_spreads_over_whole_scene(self):
        out = align_to_script([(2.0, 4.0, "एक दो")], [])
        assert out[0].start == 2.0 and out[-1].end == pytest.approx(4.0)

    def test_words_are_assigned_to_their_own_scene(self):
        heard = [Word("a", 0.1, 0.4), Word("b", 2.1, 2.4)]
        out = align_to_script([(0.0, 2.0, "एक"), (2.0, 4.0, "दो")], heard)
        assert out == [Word("एक", 0.1, 0.4), Word("दो", 2.1, 2.4)]

    def test_silent_scene_is_skipped(self):
        assert align_to_script([(0.0, 2.0, "")], []) == []


class SlowTTS(FakeTTS):
    """Each call takes 0.2 s and records peak concurrency."""

    def __init__(self):
        super().__init__()
        self.active = 0
        self.peak = 0
        self.lock = threading.Lock()

    def synthesize(self, text, character, out):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        time.sleep(0.2)
        super().synthesize(text, character, out)
        with self.lock:
            self.active -= 1


class TestParallelVoice:
    def test_scenes_are_synthesised_concurrently(self, store, job):
        tts = SlowTTS()
        VoiceService(tts, FakeMedia(), store, gap_s=0.25, min_scene_s=0.5, workers=4).run(job)
        assert tts.peak == 2  # the demo script has 2 scenes; both ran at once

    def test_order_is_preserved_regardless_of_finish_order(self, store, job):
        media = FakeMedia()
        VoiceService(SlowTTS(), media, store, gap_s=0.25, min_scene_s=0.5, workers=4).run(job)
        names = [p.clip.name for p in media.mixed[0]]
        assert names == ["scene_00.mp3", "scene_01.mp3"]


class TestContainerCaching:
    def test_adapters_are_built_once_per_process(self, tmp_path):
        from desiquip.container import Container
        from tests.unit.test_adapters import TestContainer
        c = Container(TestContainer().cfg(), tmp_path)
        assert c.tts() is c.tts()
        assert c.transcriber() is c.transcriber()


class TestStepTiming:
    def test_each_step_logs_its_duration(self, monkeypatch, caplog):
        from desiquip import cli
        from tests.unit.test_cli import Recorder
        monkeypatch.setattr(cli, "make_container", lambda: Recorder())
        with caplog.at_level("INFO"):
            cli.main(["voice", "job1"])
        assert any("voice done in" in r.message for r in caplog.records)
