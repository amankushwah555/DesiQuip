import pytest

from desiquip.adapters.approval import ConsoleApprover, build_approval_message
from desiquip.adapters.jobs_db import SqliteJobs
from desiquip.services.orchestrator import Orchestrator
from desiquip.services.qa import QAFailed
from desiquip.services.write import WriteService
from tests.unit.test_writer import FakeWriter, RULES, good_dict

FLOW = ["write", "voice", "clips", "captions", "render", "finalize", "qa", "package"]


class FakeApprover:
    def __init__(self):
        self.requests, self.messages, self.decisions = [], [], []

    def request(self, job_id, video, title):
        self.requests.append(job_id)

    def poll(self):
        d, self.decisions = self.decisions, []
        return d

    def notify(self, text):
        self.messages.append(text)


class StepScript:
    """run_step stand-in: records calls; qa outcomes are scripted per call."""

    def __init__(self, qa_outcomes=(), fail_at=None):
        self.calls, self.qa_outcomes, self.fail_at = [], list(qa_outcomes), fail_at

    def __call__(self, step, job_id):
        self.calls.append((step, job_id))
        if step == self.fail_at:
            raise RuntimeError(f"{step} broke")
        if step == "qa" and self.qa_outcomes:
            outcome = self.qa_outcomes.pop(0)
            if outcome is not None:
                raise outcome


@pytest.fixture
def jobs(tmp_path):
    return SqliteJobs(tmp_path / "db.sqlite")


def orch(steps, jobs, approver, store, learnings=None):
    return Orchestrator(steps, jobs, approver, store, FLOW, max_retries=2, learnings_path=learnings)


class TestProduce:
    def test_happy_path_ends_awaiting_approval(self, jobs, store, job):
        steps, ap = StepScript(), FakeApprover()
        jobs.create(job)
        orch(steps, jobs, ap, store).produce(job)
        assert [s for s, _ in steps.calls] == FLOW
        assert jobs.get(job)["status"] == "awaiting_approval"
        assert ap.requests == [job]

    def test_technical_qa_failure_rerenders(self, jobs, store, job):
        steps = StepScript(qa_outcomes=[QAFailed("technical", ["loudness"]), None])
        jobs.create(job)
        orch(steps, jobs, FakeApprover(), store).produce(job)
        names = [s for s, _ in steps.calls]
        assert names.count("render") == 2 and names.count("write") == 1
        assert jobs.get(job)["retries"] == 1

    def test_content_qa_failure_rewrites_with_reviewer_notes(self, jobs, store, job):
        steps = StepScript(qa_outcomes=[QAFailed("content", ["humour: 5/10"]), None])
        jobs.create(job)
        orch(steps, jobs, FakeApprover(), store).produce(job)
        names = [s for s, _ in steps.calls]
        assert names.count("write") == 2
        assert store.read_json(job, "feedback.json")["notes"] == ["humour: 5/10"]

    def test_gives_up_after_two_retries(self, jobs, store, job):
        fail = QAFailed("technical", ["loudness"])
        steps, ap = StepScript(qa_outcomes=[fail, fail, fail]), FakeApprover()
        jobs.create(job)
        orch(steps, jobs, ap, store).produce(job)
        assert jobs.get(job)["status"] == "rejected" and ap.requests == []

    def test_rights_failure_rejects_immediately(self, jobs, store, job):
        steps = StepScript(qa_outcomes=[QAFailed("rights", ["rights: no record"])])
        jobs.create(job)
        orch(steps, jobs, FakeApprover(), store).produce(job)
        assert jobs.get(job)["status"] == "rejected"
        assert [s for s, _ in steps.calls].count("qa") == 1

    def test_step_error_marks_job_error_without_raising(self, jobs, store, job):
        jobs.create(job)
        orch(StepScript(fail_at="render"), jobs, FakeApprover(), store).produce(job)
        row = jobs.get(job)
        assert row["status"] == "error" and "render broke" in row["error"]

    def test_resumes_after_existing_script(self, jobs, store, job):
        # conftest job already has script.json, so a fresh run skips straight to voice only when told.
        jobs.create(job)
        steps = StepScript()
        orch(steps, jobs, FakeApprover(), store).produce(job, start="voice")
        assert steps.calls[0][0] == "voice"


class TestApprovals:
    def test_approved_job_is_published(self, jobs, store, job):
        steps, ap = StepScript(), FakeApprover()
        jobs.create(job)
        jobs.set(job, "awaiting_approval")
        ap.decisions = [(job, "approve", "")]
        orch(steps, jobs, ap, store).process_approvals()
        assert ("upload", job) in steps.calls
        assert jobs.get(job)["status"] == "published"

    def test_rejected_job_never_publishes_and_note_becomes_a_learning(self, jobs, store, job, tmp_path):
        learnings = tmp_path / "learnings.md"
        learnings.write_text("# Learnings\n", encoding="utf-8")
        steps, ap = StepScript(), FakeApprover()
        jobs.create(job)
        jobs.set(job, "awaiting_approval")
        ap.decisions = [(job, "reject", "hook was boring")]
        orch(steps, jobs, ap, store, learnings).process_approvals()
        assert ("upload", job) not in steps.calls
        assert jobs.get(job)["status"] == "rejected"
        assert "hook was boring" in learnings.read_text(encoding="utf-8")

    def test_decision_for_a_job_not_awaiting_approval_is_ignored(self, jobs, store, job):
        steps, ap = StepScript(), FakeApprover()
        jobs.create(job)
        jobs.set(job, "rejected")
        ap.decisions = [(job, "approve", "")]
        orch(steps, jobs, ap, store).process_approvals()
        assert steps.calls == [] and jobs.get(job)["status"] == "rejected"


class TestSummary:
    def test_daily_summary_counts_statuses(self, jobs, store):
        for j, s in [("a", "awaiting_approval"), ("b", "error"), ("c", "published")]:
            jobs.create(j)
            jobs.set(j, s)
        ap = FakeApprover()
        orch(StepScript(), jobs, ap, store).send_summary()
        msg = ap.messages[0]
        assert "awaiting approval: 1" in msg and "error: 1" in msg and "published: 1" in msg


class TestConsoleApprover:
    def test_cli_decisions_are_polled_once(self, tmp_path):
        ap = ConsoleApprover(tmp_path / "decisions.json")
        ap.decide("j1", "reject", "too long")
        assert ap.poll() == [("j1", "reject", "too long")]
        assert ap.poll() == []


def test_approval_message_names_job_and_title():
    msg = build_approval_message("j1", "Uncle vs Bill", qa={"review": {"hook": 8, "humour": 7}})
    assert "j1" in msg and "Uncle vs Bill" in msg and "humour 7" in msg


def test_writer_uses_reviewer_feedback_on_first_attempt(store):
    store.create_from_topic("j2", "topic")
    store.write_json("j2", "feedback.json", {"from": "qa", "notes": ["humour: 5/10, punchline is weak"]})
    w = FakeWriter(store, [good_dict("j2")])
    WriteService(w, store, RULES).run("j2")
    assert any("punchline is weak" in p for p in w.feedback[0])
