import json

import pytest

from workbench.demo import backup, bootstrap
from workbench.store import Store


def test_bootstrap_creates_private_credentials_and_three_meaningful_cases(tmp_path):
    runtime = tmp_path / "runtime"
    bootstrap(runtime)
    assert (runtime / "credentials.json").exists()
    assert (runtime / "credentials.json").stat().st_mode & 0o777 == 0o600
    creds = json.loads((runtime / "credentials.json").read_text())
    s = Store(runtime / "workbench.db")
    a = s.authenticate(creds["harbor-qa"])
    cases = s.cases(a)
    assert len(cases) == 3
    outcomes = {x["id"]: s.assemble(a, x["id"])["result"] for x in cases}
    assert outcomes["DEMO-READY"]["recommendation"] == "WITHIN_SYNTHETIC_POLICY"
    assert outcomes["DEMO-OUTSIDE"]["recommendation"] == "OUTSIDE_SYNTHETIC_POLICY"
    assert {t["reason_code"] for t in outcomes["DEMO-QUESTIONS"]["tasks"]} == {
        "STUDY_APPLICABILITY",
        "SOP_AUTHORITY",
        "EXPOSURE_RELATIONSHIP",
        "BATCH_HISTORY",
    }
    assert len(s.queue(a)) == 3
    assert s.cases(s.authenticate(creds["meadow-reader"])) == []


def test_bootstrap_never_overwrites_existing_state(tmp_path):
    bootstrap(tmp_path / "runtime")
    path = tmp_path / "runtime" / "credentials.json"
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        bootstrap(tmp_path / "runtime")
    assert path.read_bytes() == before


def test_backup_restore_integrity_and_obligations(tmp_path):
    bootstrap(tmp_path / "runtime")
    creds = json.loads((tmp_path / "runtime" / "credentials.json").read_text())
    a = Store(tmp_path / "runtime" / "workbench.db").authenticate(creds["harbor-qa"])
    b = Store(tmp_path / "runtime" / "workbench.db").assemble(a, "DEMO-READY")
    backup(tmp_path / "runtime" / "workbench.db", tmp_path / "restore.db")
    s = Store(tmp_path / "restore.db")
    assert s.replay(s.authenticate(creds["harbor-qa"]), b["id"])["matches"]
    assert len(s.queue(s.authenticate(creds["harbor-qa"]))) == 3
    with pytest.raises(FileExistsError):
        backup(tmp_path / "runtime" / "workbench.db", tmp_path / "restore.db")
