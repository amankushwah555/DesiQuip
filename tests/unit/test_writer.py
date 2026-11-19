import json

import pytest

from desiquip.adapters.claude_writer import build_write_cmd, build_write_prompt
from desiquip.domain.models import Script
from desiquip.domain.rules import ScriptRules, check_script
from desiquip.services.write import ScriptRejected, WriteService
from tests.unit.test_domain import valid_script_dict

RULES = ScriptRules(chars_per_s=8.0, gap_s=0.25, min_scene_s=2.0, max_scene_s=4.5, min_len_s=30, max_len_s=45)


def script_with(lines, **overrides):
    d = valid_script_dict(**overrides)
    d["scenes"] = [{"t": [0, 4], "prompt": "p", "clip": "remotion", "line": l, "caption": l, "sfx": None}
                   for l in lines]
    d["product_moment"] = {"t": 5, "product_ref": "p1"}
    return Script.from_dict(d)


GOOD_LINES = ["क" * 30] * 9          # 9 scenes x (30/8 + 0.25 = 4.0 s) = 36 s


class TestScriptRules:
    """Spec section 3 Writer rules, checked before any money is spent on voice or video."""

    def test_good_script_has_no_problems(self):
        assert check_script(script_with(GOOD_LINES), RULES) == []

    def test_too_short_overall(self):
        problems = check_script(script_with(["क" * 30] * 3), RULES)
        assert any("30-45" in p for p in problems)

    def test_too_long_overall(self):
        problems = check_script(script_with(["क" * 30] * 14), RULES)
        assert any("30-45" in p for p in problems)

    def test_scene_longer_than_visual_change_limit(self):
        problems = check_script(script_with(GOOD_LINES[:-1] + ["क" * 60]), RULES)
        assert any("scenes[8]" in p and "split" in p for p in problems)

    def test_hook_must_land_within_2_seconds(self):
        s = script_with(GOOD_LINES, hook={"text": "हुक", "visual": "", "until_s": 3})
        assert any("hook" in p for p in check_script(s, RULES))

    def test_needs_exactly_three_titles_under_50_chars(self):
        assert any("3 title" in p for p in check_script(script_with(GOOD_LINES, title_options=["a", "b"]), RULES))
        long = script_with(GOOD_LINES, title_options=["a", "b", "x" * 50])
        assert any("50" in p for p in check_script(long, RULES))

    def test_needs_loop_ending(self):
        assert any("loop" in p for p in check_script(script_with(GOOD_LINES, loop_end=False), RULES))

    def test_product_moment_must_reference_a_listed_product(self):
        s = script_with(GOOD_LINES, products=[{"ref": "p9", "program": "amazon", "query": "x"}])
        assert any("product_ref" in p for p in check_script(s, RULES))

    def test_at_most_three_products(self):
        many = [{"ref": f"p{i}", "program": "amazon", "query": "x"} for i in range(1, 5)]
        assert any("products" in p for p in check_script(script_with(GOOD_LINES, products=many), RULES))

    def test_estimated_length_is_reported(self):
        from desiquip.domain.rules import estimate_length_s
        assert estimate_length_s(script_with(GOOD_LINES), RULES) == pytest.approx(36.0)


class FakeWriter:
    """Writes the given scripts on successive calls and records the feedback it received."""

    def __init__(self, store, scripts):
        self.store, self.scripts, self.feedback = store, list(scripts), []

    def write(self, job_id, feedback):
        self.feedback.append(list(feedback))
        content = self.scripts.pop(0)
        path = self.store.path(job_id) / "script.json"
        path.write_text(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False),
                        encoding="utf-8")


def good_dict(job_id):
    d = valid_script_dict(job_id=job_id, source_id=f"orig-{job_id}")
    d["scenes"] = [{"t": [0, 4], "prompt": "p", "clip": "remotion", "line": l, "caption": l, "sfx": None}
                   for l in GOOD_LINES]
    return d


@pytest.fixture
def topic_job(store):
    store.create_from_topic("j1", "बिजली का बिल", character="uncle_ji")
    return "j1"


class TestWriteService:
    def test_new_job_from_topic_writes_idea(self, store, topic_job):
        idea = store.read_json(topic_job, "idea.json")
        assert idea["topic"] == "बिजली का बिल"
        assert idea["source_id"] == "orig-j1" and idea["source_type"] == "original"
        assert idea["character"] == "uncle_ji"

    def test_good_first_draft_is_accepted(self, store, topic_job):
        w = FakeWriter(store, [good_dict(topic_job)])
        WriteService(w, store, RULES).run(topic_job)
        assert w.feedback == [[]]
        assert store.read_script(topic_job).job_id == topic_job

    def test_bad_draft_is_retried_once_with_the_problems(self, store, topic_job):
        bad = good_dict(topic_job)
        bad["loop_end"] = False
        w = FakeWriter(store, [bad, good_dict(topic_job)])
        WriteService(w, store, RULES).run(topic_job)
        assert len(w.feedback) == 2
        assert any("loop" in p for p in w.feedback[1])

    def test_invalid_json_counts_as_a_problem(self, store, topic_job):
        w = FakeWriter(store, ["{not json", good_dict(topic_job)])
        WriteService(w, store, RULES).run(topic_job)
        assert any("JSON" in p for p in w.feedback[1])

    def test_still_bad_after_retry_is_rejected(self, store, topic_job):
        bad = good_dict(topic_job)
        bad["loop_end"] = False
        with pytest.raises(ScriptRejected, match="loop"):
            WriteService(FakeWriter(store, [bad, bad]), store, RULES).run(topic_job)

    def test_writer_must_keep_the_ideas_source_id(self, store, topic_job):
        # Spec: never invent source rights; the script must carry the idea's source_id.
        d = good_dict(topic_job)
        d["source_id"] = "made-up"
        with pytest.raises(ScriptRejected, match="source_id"):
            WriteService(FakeWriter(store, [d, d]), store, RULES).run(topic_job)

    def test_needs_an_idea(self, store, job):
        with pytest.raises(FileNotFoundError, match="idea.json"):
            WriteService(FakeWriter(store, []), store, RULES).run(job)


class TestClaudeWriterCommand:
    def test_prompt_names_the_files_and_includes_feedback(self):
        p = build_write_prompt("j1", ["scenes[2] too long"])
        assert "jobs/j1/idea.json" in p and "jobs/j1/script.json" in p
        assert "scenes[2] too long" in p

    def test_headless_command_uses_writer_agent_with_limited_tools(self):
        cmd = build_write_cmd("claude", "PROMPT", budget_usd=1.5)
        assert cmd[:3] == ["claude", "-p", "PROMPT"]
        assert cmd[cmd.index("--agent") + 1] == "writer"
        tools = cmd[cmd.index("--allowedTools") + 1]
        assert "Write(jobs/**)" in tools and "Bash" not in tools
        assert "--max-budget-usd" in cmd and "1.5" in cmd
