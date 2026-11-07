import copy
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager

import pytest

from tests.test_domain import snapshot
from workbench.store import Store


@contextmanager
def database_connection(path):
    with closing(sqlite3.connect(path)) as connection, connection:
        yield connection


@pytest.fixture
def env(tmp_path):
    store = Store(tmp_path / "demo.db")
    tokens = {
        key: store.provision(key, tenant, role)
        for key, tenant, role in [
            ("qa", "harbor", "QA"),
            ("qa2", "harbor", "QA"),
            ("ra", "harbor", "Regulatory"),
            ("op", "harbor", "Operator"),
            ("other", "meadow", "QA"),
        ]
    }
    actors = {k: store.authenticate(v) for k, v in tokens.items()}
    return store, actors, tokens


def create(store, actor, id="DEMO-ALPHA", flag="Y", due="2030-01-03T08:00:00Z"):
    s = snapshot()
    s.pop("documents")
    s.pop("history")
    store.create_case(actor, id, s, flag, due)


def attach_all(store, actors, id="DEMO-ALPHA"):
    for d in snapshot()["documents"]:
        data = {"synthetic": True, "text": d["content"], "study_type": "excursion"}
        if d["kind"] == "exposure":
            data["policy"] = d["policy"]
        if d["kind"] == "history":
            data["history"] = snapshot()["history"]
        doc = store.attach(
            actors["op"],
            id,
            {k: d[k] for k in ["kind", "scope", "effective_from", "effective_to", "citation"]}
            | {"content": json.dumps(data), "supersedes": None},
        )
        store.approve(actors["qa"], id, doc["id"])


def ready(env):
    s, a, _ = env
    create(s, a["op"])
    attach_all(s, a)
    return s, a, s.assemble(a["qa"], "DEMO-ALPHA")


def test_notice_survives_acknowledgement_and_restart(env):
    s, a, b = ready(env)
    s.set_obligation(
        a["ra"],
        "DEMO-ALPHA",
        "REPORTABLE",
        "2030-01-03T08:00:00Z",
        "SYNTHETIC programme attestation",
        "PENDING",
    )
    ack = s.acknowledge(
        a["qa"], "DEMO-ALPHA", b["id"], b["hash"], "reviewer-role", "REVIEW_ACCEPTED", "key-1"
    )
    assert ack["actor"] == "qa"
    assert s.queue(a["qa"])[0]["status"] == "PENDING"
    restarted = Store(s.path)
    assert restarted.queue(restarted.authenticate(env[2]["qa"])) == s.queue(a["qa"])


def test_assembly_error_does_not_hide_deadline_and_order(env):
    s, a, _ = env
    create(s, a["op"], "DEMO-LATE", due="2030-01-04T00:00:00Z")
    create(s, a["op"], "DEMO-EARLY", due="2030-01-02T00:00:00Z")
    attach_all(s, a, "DEMO-EARLY")
    with database_connection(s.path) as db:
        db.execute("DROP TRIGGER documents_immutable_update")
        db.execute("UPDATE documents SET content='tampered' WHERE kind='study'")
    with pytest.raises(ValueError, match="integrity"):
        s.assemble(a["qa"], "DEMO-EARLY")
    assert [n["case_id"] for n in s.queue(a["qa"])] == ["DEMO-EARLY", "DEMO-LATE"]


@pytest.mark.parametrize("flag", ["", None, "N", "unknown", "NOT_REQUIRED", "Y"])
def test_raw_flags_never_qualified_not_required(env, flag):
    s, a, _ = env
    create(s, a["op"], flag=flag)
    assert s.queue(a["qa"])[0]["reportability"] == "UNKNOWN"


def test_qualified_not_required_needs_regulatory_role_and_nonblank_basis(env):
    s, a, _ = env
    create(s, a["op"])
    with pytest.raises(PermissionError):
        s.set_obligation(a["qa"], "DEMO-ALPHA", "NOT_REQUIRED", None, "basis", "PENDING")
    with pytest.raises(ValueError):
        s.set_obligation(a["ra"], "DEMO-ALPHA", "NOT_REQUIRED", None, " ", "PENDING")
    s.set_obligation(
        a["ra"], "DEMO-ALPHA", "NOT_REQUIRED", None, "SYNTHETIC qualified assessment", "PENDING"
    )
    assert s.queue(a["qa"]) == []


@pytest.mark.parametrize("actor_key", ["other", None])
def test_tenant_checks_cover_read_and_update(env, actor_key):
    s, a, _ = env
    create(s, a["op"])
    actor = a.get(actor_key)
    for operation in [
        lambda: s.case(actor, "DEMO-ALPHA"),
        lambda: s.assemble(actor, "DEMO-ALPHA"),
        lambda: s.set_obligation(actor, "DEMO-ALPHA", "REPORTABLE", None, "basis", "PENDING"),
    ]:
        with pytest.raises(PermissionError):
            operation()
    if actor is None:
        with pytest.raises(PermissionError):
            s.queue(None)
    else:
        assert s.queue(actor) == []


def test_missing_invalid_revoked_credential_fails(env):
    s, a, t = env
    for token in [None, "", "not-a-token"]:
        with pytest.raises(PermissionError):
            s.authenticate(token)
    with database_connection(s.path) as db:
        db.execute("UPDATE actors SET active=0 WHERE id=?", ("qa",))
    with pytest.raises(PermissionError):
        s.case(a["qa"], "DEMO-ALPHA")


def test_operator_cannot_approve_or_acknowledge(env):
    s, a, b = ready(env)
    with pytest.raises(PermissionError):
        s.approve(a["op"], "DEMO-ALPHA", 1)
    with pytest.raises(PermissionError):
        s.acknowledge(
            a["op"], "DEMO-ALPHA", b["id"], b["hash"], "operator", "REVIEW_ACCEPTED", "op-key"
        )


def test_unapproved_and_blank_attachments_do_not_complete_tasks(env):
    s, a, _ = env
    create(s, a["op"])
    b = s.assemble(a["qa"], "DEMO-ALPHA")
    d = copy.deepcopy(snapshot()["documents"][0])
    d["content"] = " "
    with pytest.raises(ValueError):
        s.attach(a["op"], "DEMO-ALPHA", d)
    d["content"] = json.dumps({"synthetic": True, "text": "SYNTHETIC mapping"})
    d.pop("id")
    d.pop("verified")
    d.pop("approved")
    d.pop("policy")
    d.pop("study_type", None)
    d["supersedes"] = None
    doc = s.attach(a["op"], "DEMO-ALPHA", d)
    with pytest.raises(ValueError):
        s.resolve(a["qa"], "DEMO-ALPHA", b["id"], "IDENTITY_UNVERIFIED", doc["id"])
    assert s.bundle(a["qa"], b["id"])["result"]["tasks"][0]["status"] == "OPEN"


def test_approved_resolution_creates_linked_version_not_overwrite(env):
    s, a, _ = env
    create(s, a["op"])
    before = s.assemble(a["qa"], "DEMO-ALPHA")
    attach_all(s, a)
    doc = s.documents(a["qa"], "DEMO-ALPHA")[0]
    resolved = s.resolve(a["qa"], "DEMO-ALPHA", before["id"], "IDENTITY_UNVERIFIED", doc["id"])
    assert resolved["status"] == "COMPLETE"
    after = s.bundle(a["qa"], resolved["resolved_bundle"])
    assert after["parent_id"] == before["id"]
    assert after["result"]["recommendation"] == "WITHIN_SYNTHETIC_POLICY"
    assert s.bundle(a["qa"], before["id"])["result"]["recommendation"] == "EVIDENCE_REQUIRED"


def test_blank_signer_stale_bundle_idempotency_and_hash(env):
    s, a, b = ready(env)
    with pytest.raises(ValueError):
        s.acknowledge(a["qa"], "DEMO-ALPHA", b["id"], b["hash"], " ", "REVIEW_ACCEPTED", "key")
    with pytest.raises(ValueError, match="hash"):
        s.acknowledge(a["qa"], "DEMO-ALPHA", b["id"], "bad", "role", "REVIEW_ACCEPTED", "key")
    s.assemble(a["qa"], "DEMO-ALPHA")
    with pytest.raises(ValueError, match="stale"):
        s.acknowledge(a["qa"], "DEMO-ALPHA", b["id"], b["hash"], "role", "REVIEW_ACCEPTED", "key")
    latest = s.assemble(a["qa"], "DEMO-ALPHA")
    x = s.acknowledge(
        a["qa"], "DEMO-ALPHA", latest["id"], latest["hash"], "role", "REVIEW_ACCEPTED", "key"
    )
    assert (
        s.acknowledge(
            a["qa"], "DEMO-ALPHA", latest["id"], latest["hash"], "role", "REVIEW_ACCEPTED", "key"
        )
        == x
    )
    with pytest.raises(ValueError, match="idempotency"):
        s.acknowledge(
            a["qa"], "DEMO-ALPHA", latest["id"], latest["hash"], "role", "REVIEW_REJECTED", "key"
        )


def test_database_tampered_bundle_rejected(env):
    s, a, b = ready(env)
    with database_connection(s.path) as db:
        db.execute("DROP TRIGGER bundles_immutable_update")
        db.execute("UPDATE bundles SET snapshot='{}' WHERE id=?", (b["id"],))
    with pytest.raises(ValueError, match="integrity"):
        s.bundle(a["qa"], b["id"])


def test_replay_original_inputs_not_later_outcome(env):
    s, a, b = ready(env)
    s.acknowledge(a["qa"], "DEMO-ALPHA", b["id"], b["hash"], "role", "REVIEW_REJECTED", "later")
    assert s.replay(a["qa"], b["id"])["matches"] is True


def test_two_reviewers_racing_only_one_acknowledges(env):
    s, a, b = ready(env)

    def ack(key):
        try:
            s.acknowledge(a[key], "DEMO-ALPHA", b["id"], b["hash"], "role", "REVIEW_ACCEPTED", key)
            return "ok"
        except ValueError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(ack, ["qa", "qa2"]))
    assert sorted(results) == ["conflict", "ok"]


def test_source_added_after_bundle_requires_reassessment_before_ack(env):
    s, a, b = ready(env)
    d = copy.deepcopy(snapshot()["documents"][2])
    d.pop("id")
    d.pop("verified")
    d.pop("approved")
    d.pop("policy")
    d.pop("study_type", None)
    d["content"] = json.dumps({"synthetic": True, "text": "new SOP"})
    d["supersedes"] = None
    s.attach(a["op"], "DEMO-ALPHA", d)
    with pytest.raises(ValueError, match="evidence changed"):
        s.acknowledge(
            a["qa"], "DEMO-ALPHA", b["id"], b["hash"], "role", "REVIEW_ACCEPTED", "freshness"
        )


def test_append_only_case_and_bundles(env):
    s, a, b = ready(env)
    with database_connection(s.path) as db:
        for table in ["cases", "bundles", "documents"]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(f"DELETE FROM {table}")


def test_unknown_database_schema_is_not_silently_accepted(tmp_path):
    path = tmp_path / "future.db"
    with database_connection(path) as db:
        db.execute("CREATE TABLE schema_version(version INTEGER PRIMARY KEY)")
        db.execute("INSERT INTO schema_version VALUES(99)")
    with pytest.raises(ValueError, match="schema"):
        Store(path)


def test_obligation_survives_separate_interpreter(env):
    import subprocess
    import sys

    s, a, t = env
    create(s, a["op"])
    code = "import sys,json;from workbench.store import Store;s=Store(sys.argv[1]);a=s.authenticate(sys.stdin.read());print(json.dumps(s.queue(a)))"
    result = subprocess.run(
        [sys.executable, "-c", code, str(s.path)],
        input=t["qa"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert json.loads(result.stdout) == s.queue(a["qa"])


def test_source_hash_tampering_rejected_at_ack_not_only_assembly(env):
    s, a, b = ready(env)
    with database_connection(s.path) as db:
        db.execute("DROP TRIGGER documents_immutable_update")
        db.execute("UPDATE documents SET content='tampered' WHERE kind='study'")
    with pytest.raises(ValueError, match="integrity"):
        s.acknowledge(
            a["qa"], "DEMO-ALPHA", b["id"], b["hash"], "role", "REVIEW_ACCEPTED", "hash-check"
        )


def test_explicit_approved_reconciliation_can_resolve_two_sop_revisions(env):
    from workbench.demo import example_document

    s, a, _ = env
    create(s, a["op"])
    attach_all(s, a)
    payload = s.case(a["qa"], "DEMO-ALPHA")["input"]
    second = s.attach(a["op"], "DEMO-ALPHA", example_document(payload, "sop", 12))
    s.approve(a["qa"], "DEMO-ALPHA", second["id"])
    before = s.assemble(a["qa"], "DEMO-ALPHA")
    assert "SOP_AUTHORITY" in {t["reason_code"] for t in before["result"]["tasks"]}
    old = [d["id"] for d in s.documents(a["qa"], "DEMO-ALPHA") if d["kind"] == "sop"]
    resolution = example_document(payload, "sop", 13)
    resolution["supersedes"] = old
    new = s.attach(a["op"], "DEMO-ALPHA", resolution)
    # Unapproved replacements must not deactivate originals.
    assert "SOP_AUTHORITY" in {
        t["reason_code"] for t in s.assemble(a["qa"], "DEMO-ALPHA")["result"]["tasks"]
    }
    s.approve(a["qa"], "DEMO-ALPHA", new["id"])
    result = s.resolve(a["qa"], "DEMO-ALPHA", before["id"], "SOP_AUTHORITY", new["id"])
    assert result["status"] == "COMPLETE"
