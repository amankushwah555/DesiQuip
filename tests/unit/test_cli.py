import pytest

from desiquip import cli
from desiquip.adapters.ffmpeg import choose_encoder


class Recorder:
    """Stands in for the Container: every *_service() returns an object whose run() is recorded."""

    def __init__(self, has_script=True):
        self.calls = []
        self.has_script = has_script

    def store(self):
        rec = self

        class S:
            def has(self, job_id, name):
                return rec.has_script
        return S()

    def __getattr__(self, name):
        if not name.endswith("_service"):
            raise AttributeError(name)
        step = name.removesuffix("_service")

        class Svc:
            def run(_, job_id):
                self.calls.append((step, job_id))
                return f"{step}-out"
        return lambda: Svc()


@pytest.fixture
def rec(monkeypatch):
    r = Recorder()
    monkeypatch.setattr(cli, "make_container", lambda: r)
    return r


def test_make_runs_week1_steps_in_order_without_upload(rec):
    assert cli.main(["make", "job1"]) == 0
    assert rec.calls == [("voice", "job1"), ("clip", "job1"), ("caption", "job1"), ("render", "job1"), ("finalize", "job1"), ("qa", "job1"), ("package", "job1")]


def test_make_starts_with_the_writer_when_there_is_no_script(monkeypatch):
    r = Recorder(has_script=False)
    monkeypatch.setattr(cli, "make_container", lambda: r)
    cli.main(["make", "job1"])
    assert [s for s, _ in r.calls] == ["write", "voice", "clip", "caption", "render", "finalize", "qa", "package"]


def test_validate_returns_nonzero_on_problems(monkeypatch, capsys):
    class C:
        def validate_job(self, job_id):
            return ["loop_end must be true"]
    monkeypatch.setattr(cli, "make_container", lambda: C())
    assert cli.main(["validate", "job1"]) == 1
    assert "loop_end" in capsys.readouterr().out


def test_make_with_upload_publishes_last(rec):
    cli.main(["make", "job1", "--upload"])
    assert rec.calls[-1] == ("publish", "job1")


def test_single_step(rec):
    cli.main(["captions", "job9"])
    assert rec.calls == [("caption", "job9")]


def test_make_can_resume_from_a_step(rec):
    cli.main(["make", "job1", "--from", "render"])
    assert [s for s, _ in rec.calls] == ["render", "finalize", "qa", "package"]


def test_failure_returns_nonzero(monkeypatch):
    class Boom:
        def voice_service(self):
            raise RuntimeError("no ffmpeg")
    monkeypatch.setattr(cli, "make_container", lambda: Boom())
    assert cli.main(["voice", "job1"]) == 1


class TestNewJob:
    def test_new_job_from_template_works_without_jobs_folder(self, tmp_path, monkeypatch):
        from desiquip.adapters.job_store import FileJobStore
        tpl = tmp_path / "examples" / "demo-001"
        tpl.mkdir(parents=True)
        (tpl / "script.json").write_text('{"job_id": "demo-001"}', encoding="utf-8")
        store = FileJobStore(tmp_path / "jobs")          # jobs/ does not exist yet (fresh clone)

        class C:
            def store(self):
                return store
        monkeypatch.setattr(cli, "make_container", lambda: C())
        assert cli.main(["new", "my-job", "--from", str(tpl)]) == 0
        assert (tmp_path / "jobs" / "my-job" / "script.json").is_file()

    def test_new_job_refuses_to_overwrite(self, tmp_path):
        from desiquip.adapters.job_store import FileJobStore
        tpl = tmp_path / "tpl"
        tpl.mkdir()
        store = FileJobStore(tmp_path / "jobs")
        store.create("a", tpl)
        with pytest.raises(FileExistsError):
            store.create("a", tpl)


class TestOrchestratorCommands:
    class C:
        def __init__(self, tmp_path):
            from desiquip.adapters.approval import ConsoleApprover
            from desiquip.adapters.jobs_db import SqliteJobs
            self.ap = ConsoleApprover(tmp_path / "decisions.json")
            self.db = SqliteJobs(tmp_path / "db.sqlite")
            self.orch_calls = []

        def approver(self):
            return self.ap

        def jobs(self):
            return self.db

        def orchestrator(self, run_step):
            outer = self

            class O:
                def produce(self, job_id, start=None):
                    outer.orch_calls.append(("produce", job_id, start))

                def process_approvals(self):
                    outer.orch_calls.append(("approvals",))

                def send_summary(self):
                    outer.orch_calls.append(("summary",))
            return O()

    def test_approve_and_reject_record_decisions_then_process(self, tmp_path, monkeypatch):
        c = self.C(tmp_path)
        monkeypatch.setattr(cli, "make_container", lambda: c)
        assert cli.main(["reject", "j1", "--note", "boring hook"]) == 0
        assert c.orch_calls == [("approvals",)]

    def test_produce_runs_orchestrator(self, tmp_path, monkeypatch):
        c = self.C(tmp_path)
        monkeypatch.setattr(cli, "make_container", lambda: c)
        cli.main(["produce", "j1", "--from", "render"])
        assert c.orch_calls == [("produce", "j1", "render")]
        assert c.db.get("j1") is not None

    def test_status_lists_jobs(self, tmp_path, monkeypatch, capsys):
        c = self.C(tmp_path)
        c.db.create("j9")
        c.db.set("j9", "awaiting_approval")
        monkeypatch.setattr(cli, "make_container", lambda: c)
        cli.main(["status"])
        assert "j9" in capsys.readouterr().out


class TestEncoderChoice:
    def test_auto_prefers_nvenc_when_it_works(self):
        assert choose_encoder("auto", nvenc_ok=True) == "h264_nvenc"

    def test_auto_falls_back_to_x264(self):
        assert choose_encoder("auto", nvenc_ok=False) == "libx264"

    def test_explicit_choice_is_respected(self):
        assert choose_encoder("libx264", nvenc_ok=True) == "libx264"

    def test_unknown_encoder_rejected(self):
        with pytest.raises(ValueError):
            choose_encoder("hevc_magic", nvenc_ok=True)
