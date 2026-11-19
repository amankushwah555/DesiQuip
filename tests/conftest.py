import json

import pytest

from desiquip.adapters.job_store import FileJobStore
from tests.unit.test_domain import valid_script_dict

JOB = "2026-11-19-01"


@pytest.fixture
def store(tmp_path):
    return FileJobStore(tmp_path / "jobs")


@pytest.fixture
def job(store):
    """A job folder containing a valid script.json and one scene asset."""
    d = store.root / JOB
    d.mkdir(parents=True)
    (d / "script.json").write_text(json.dumps(valid_script_dict(), ensure_ascii=False), encoding="utf-8")
    (d / "kitchen.png").write_bytes(b"png")
    return JOB
