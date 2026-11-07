import json

import pytest
from fastapi.testclient import TestClient

from tests.test_store import attach_all, create
from workbench.api import create_app
from workbench.store import Store


@pytest.fixture
def api(tmp_path):
    path = tmp_path / "api.db"
    s = Store(path)
    t = {
        name: s.provision(name, tenant, role)
        for name, tenant, role in [
            ("op", "harbor", "Operator"),
            ("qa", "harbor", "QA"),
            ("ra", "harbor", "Regulatory"),
            ("other", "meadow", "QA"),
        ]
    }
    a = {k: s.authenticate(v) for k, v in t.items()}
    create(s, a["op"])
    attach_all(s, a)
    client = TestClient(create_app(path))
    return client, t, s, a


def hdr(token):
    return {"Authorization": f"Bearer {token}"}


def test_http_working_path_review_and_notice_independence(api):
    c, t, s, a = api
    assert c.get("/healthz").status_code == 200
    b = c.post("/api/cases/DEMO-ALPHA/evaluations", headers=hdr(t["qa"])).json()
    assert b["result"]["recommendation"] == "WITHIN_SYNTHETIC_POLICY"
    r = c.post(
        "/api/cases/DEMO-ALPHA/acknowledgements",
        headers=hdr(t["qa"]),
        json={
            "bundle_id": b["id"],
            "expected_hash": b["hash"],
            "signer_label": "local QA",
            "outcome": "REVIEW_ACCEPTED",
            "idempotency_key": "http-1",
        },
    )
    assert r.status_code == 200, r.text
    assert len(c.get("/api/obligations", headers=hdr(t["qa"])).json()) == 1
    assert c.get(f"/api/bundles/{b['id']}/replay", headers=hdr(t["qa"])).json()["matches"]


@pytest.mark.parametrize(
    "route",
    ["/api/cases", "/api/obligations", "/api/cases/DEMO-ALPHA", "/api/cases/DEMO-ALPHA/documents"],
)
def test_missing_and_invalid_token_http(api, route):
    c, t, _, _ = api
    for headers in [{}, hdr("invalid")]:
        assert c.get(route, headers=headers).status_code == 401


def test_cross_tenant_and_caller_supplied_tenant_cannot_override(api):
    c, t, _, _ = api
    assert c.get("/api/cases/DEMO-ALPHA", headers=hdr(t["other"])).status_code == 403
    assert c.get("/api/cases?tenant=harbor", headers=hdr(t["other"])).json() == []
    assert c.get("/api/obligations?tenant=harbor", headers=hdr(t["other"])).json() == []


def test_write_schema_rejects_null_tenant_forgery_blank_label_and_extra_fields(api):
    c, t, _, _ = api
    r = c.post("/api/cases", headers=hdr(t["op"]), json={"id": "demo", "tenant": None})
    assert r.status_code == 422
    r = c.post(
        "/api/cases/DEMO-ALPHA/acknowledgements",
        headers=hdr(t["qa"]),
        json={
            "bundle_id": 1,
            "expected_hash": "a" * 64,
            "signer_label": " ",
            "outcome": "REVIEW_ACCEPTED",
            "idempotency_key": "key",
        },
    )
    assert r.status_code == 422


def test_operator_cannot_approve_over_http(api):
    c, t, s, a = api
    doc = s.documents(a["qa"], "DEMO-ALPHA")[0]
    assert (
        c.post(
            f"/api/cases/DEMO-ALPHA/documents/{doc['id']}/approval", headers=hdr(t["op"])
        ).status_code
        == 403
    )


def test_ui_and_static_do_not_expose_data_or_tokens(api):
    c, t, _, _ = api
    r = c.get("/")
    assert r.status_code == 200 and "SYNTHETIC" in r.text
    assert all(x not in r.text for x in t.values())
    assert "DEMO-ALPHA" not in r.text
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"


def test_body_limit_and_host_validation(api):
    c, t, _, _ = api
    assert c.post("/api/cases", headers=hdr(t["op"]), content="x" * 300000).status_code == 413
    assert c.get("/healthz", headers={"Host": "attacker.example"}).status_code == 400


def test_api_source_upload_approval_and_task_resolution(api):
    c, t, s, a = api
    create(s, a["op"], "DEMO-BLOCKED")
    before = c.post("/api/cases/DEMO-BLOCKED/evaluations", headers=hdr(t["qa"])).json()
    d = s.documents(a["qa"], "DEMO-ALPHA")[0]
    payload = {
        k: d[k] for k in ["kind", "scope", "effective_from", "effective_to", "citation", "content"]
    } | {"supersedes": None}
    r = c.post("/api/cases/DEMO-BLOCKED/documents", headers=hdr(t["op"]), json=payload)
    assert r.status_code == 200, r.text
    doc = r.json()["id"]
    assert (
        c.post(
            f"/api/cases/DEMO-BLOCKED/documents/{doc}/approval", headers=hdr(t["qa"])
        ).status_code
        == 200
    )
    r = c.post(
        "/api/cases/DEMO-BLOCKED/resolutions",
        headers=hdr(t["qa"]),
        json={"bundle_id": before["id"], "reason_code": "IDENTITY_UNVERIFIED", "document_id": doc},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "COMPLETE"


def test_ui_has_accessible_workflow_and_no_persisted_browser_credential(api):
    c, _, _, _ = api
    html = c.get("/").text
    for element in [
        "login-form",
        "credential",
        "case-list",
        "notification-list",
        "evaluate",
        "review-ack",
        "evidence-tasks",
        "logout",
        "status",
    ]:
        assert f'id="{element}"' in html
    script = c.get("/static/app.js")
    assert script.status_code == 200
    assert "localStorage" not in script.text and "sessionStorage" not in script.text
    assert "innerHTML" not in script.text
    assert "Europe/Berlin" in script.text
    assert c.get("/static/app.css").status_code == 200


def test_http_boolean_measurement_must_not_coerce_to_one_degree(api):
    from workbench.demo import example_payload

    c, t, _, _ = api
    payload = example_payload()
    payload["observation"]["min_c"] = True
    r = c.post("/api/cases", headers=hdr(t["op"]), json={"id": "BOOL-CASE", "payload": payload})
    assert r.status_code == 422


def test_four_question_demo_resolves_end_to_end_with_synthetic_bytes(tmp_path):
    from workbench.demo import bootstrap, example_document

    runtime = tmp_path / "demo"
    bootstrap(runtime)
    tokens = json.loads((runtime / "credentials.json").read_text())
    c = TestClient(create_app(runtime / "workbench.db"))
    qa = hdr(tokens["harbor-qa"])
    op = hdr(tokens["harbor-operator"])
    original = c.get("/api/cases/DEMO-QUESTIONS/evaluations", headers=qa).json()[0]
    payload = c.get("/api/cases/DEMO-QUESTIONS", headers=qa).json()["input"]
    assert len(original["result"]["tasks"]) == 4
    for kind, reason in [
        ("study", "STUDY_APPLICABILITY"),
        ("sop", "SOP_AUTHORITY"),
        ("exposure", "EXPOSURE_RELATIONSHIP"),
        ("history", "BATCH_HISTORY"),
    ]:
        doc = example_document(payload, kind, 100)
        if kind == "sop":
            docs = c.get("/api/cases/DEMO-QUESTIONS/documents", headers=qa).json()
            doc["supersedes"] = [d["id"] for d in docs if d["kind"] == "sop" and d["approved"]]
        r = c.post("/api/cases/DEMO-QUESTIONS/documents", headers=op, json=doc)
        assert r.status_code == 200, r.text
        doc_id = r.json()["id"]
        assert (
            c.post(f"/api/cases/DEMO-QUESTIONS/documents/{doc_id}/approval", headers=qa).status_code
            == 200
        )
        r = c.post(
            "/api/cases/DEMO-QUESTIONS/resolutions",
            headers=qa,
            json={"bundle_id": original["id"], "reason_code": reason, "document_id": doc_id},
        )
        assert r.status_code == 200, r.text
    versions = c.get("/api/cases/DEMO-QUESTIONS/evaluations", headers=qa).json()
    assert len(versions) == 5
    assert len(versions[0]["result"]["tasks"]) == 4
    assert versions[-1]["result"]["recommendation"] == "WITHIN_SYNTHETIC_POLICY"
    assert len(c.get("/api/obligations", headers=qa).json()) == 3


@pytest.mark.parametrize("text", [None, [], {}, 1])
def test_nonstring_attachment_text_cannot_crash_approval(api, text):
    from workbench.demo import example_document

    c, t, s, a = api
    doc = example_document(s.case(a["qa"], "DEMO-ALPHA")["input"], "identity")
    doc["content"] = json.dumps({"synthetic": True, "text": text})
    response = c.post("/api/cases/DEMO-ALPHA/documents", headers=hdr(t["op"]), json=doc)
    assert response.status_code == 200
    doc_id = response.json()["id"]
    response = c.post(f"/api/cases/DEMO-ALPHA/documents/{doc_id}/approval", headers=hdr(t["qa"]))
    assert response.status_code == 409


def test_qa_can_inspect_proposed_supersession_before_approval(api):
    from workbench.demo import example_document

    c, t, s, a = api
    old = next(d for d in s.documents(a["qa"], "DEMO-ALPHA") if d["kind"] == "sop")
    document = example_document(s.case(a["qa"], "DEMO-ALPHA")["input"], "sop")
    document["supersedes"] = [old["id"]]
    attached = c.post("/api/cases/DEMO-ALPHA/documents", headers=hdr(t["op"]), json=document)
    assert attached.status_code == 200
    docs = c.get("/api/cases/DEMO-ALPHA/documents", headers=hdr(t["qa"])).json()
    proposed = next(d for d in docs if d["id"] == attached.json()["id"])
    assert proposed["supersedes"] == [old["id"]]
    assert proposed["scope"] == document["scope"]
    assert proposed["effective_from"] and proposed["effective_to"]
    assert not proposed["approved"]
    assert next(d for d in docs if d["id"] == old["id"])["approved"]
    assert (
        c.post(
            f"/api/cases/DEMO-ALPHA/documents/{proposed['id']}/approval", headers=hdr(t["qa"])
        ).status_code
        == 200
    )
    final = c.get("/api/cases/DEMO-ALPHA/documents", headers=hdr(t["qa"])).json()
    assert not next(d for d in final if d["id"] == old["id"])["approved"]
    assert next(d for d in final if d["id"] == proposed["id"])["supersedes"] == [old["id"]]


def test_case_identifiers_are_tenant_scoped_without_collision_oracle(api):
    from workbench.demo import example_payload

    c, t, s, _ = api
    other_token = s.provision("other-op", "meadow", "Operator")
    headers = hdr(other_token)
    # An unknown ID and an ID owned only elsewhere have the same read response.
    absent = c.get("/api/cases/UNUSED-ID", headers=headers)
    hidden = c.get("/api/cases/DEMO-ALPHA", headers=headers)
    assert absent.status_code == hidden.status_code == 403
    assert absent.json() == hidden.json()
    for case_id in ["DEMO-ALPHA", "UNUSED-ID"]:
        payload = example_payload()
        payload["scope"]["product"] = "SYNTHETIC-MEADOW-ONLY"
        response = c.post("/api/cases", headers=headers, json={"id": case_id, "payload": payload})
        assert response.status_code == 200, response.text
    assert (
        c.get("/api/cases/DEMO-ALPHA", headers=headers).json()["input"]["scope"]["product"]
        == "SYNTHETIC-MEADOW-ONLY"
    )
    assert (
        c.get("/api/cases/DEMO-ALPHA", headers=hdr(t["op"])).json()["input"]["scope"]["product"]
        != "SYNTHETIC-MEADOW-ONLY"
    )
    assert c.get("/api/cases/DEMO-ALPHA/documents", headers=headers).json() == []
    assert len(c.get("/api/cases/DEMO-ALPHA/documents", headers=hdr(t["op"])).json()) > 0
    evaluated = c.post("/api/cases/DEMO-ALPHA/evaluations", headers=headers)
    assert evaluated.status_code == 200
    assert (
        c.get(f"/api/bundles/{evaluated.json()['id']}/replay", headers=hdr(t["qa"])).status_code
        == 403
    )
    own_duplicate = c.post(
        "/api/cases", headers=headers, json={"id": "DEMO-ALPHA", "payload": example_payload()}
    )
    assert own_duplicate.status_code == 409


def test_expired_credential_is_401_at_http_boundary(api, monkeypatch):
    c, t, s, a = api
    expires = s.identity(a["qa"])["expires"]
    monkeypatch.setattr("workbench.store.now", lambda: expires)
    for path in ["/api/me", "/api/cases", "/api/obligations", "/api/cases/DEMO-ALPHA/documents"]:
        response = c.get(path, headers=hdr(t["qa"]))
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "operation,role",
    [
        ("create", "qa"),
        ("create", "ra"),
        ("create", "reader"),
        ("attach", "ra"),
        ("attach", "reader"),
        ("approve", "op"),
        ("approve", "ra"),
        ("approve", "reader"),
        ("evaluate", "ra"),
        ("evaluate", "reader"),
        ("resolve", "op"),
        ("resolve", "ra"),
        ("resolve", "reader"),
        ("ack", "op"),
        ("ack", "ra"),
        ("ack", "reader"),
        ("notice", "op"),
        ("notice", "qa"),
        ("notice", "reader"),
    ],
)
def test_write_endpoint_role_matrix(api, operation, role):
    from workbench.demo import example_document, example_payload

    c, t, s, a = api
    t["reader"] = s.provision("reader", "harbor", "Reader")
    b = s.assemble(a["qa"], "DEMO-ALPHA")
    d = s.documents(a["qa"], "DEMO-ALPHA")[0]
    suffix, body = {
        "create": ("", {"id": "ROLE-CHECK", "payload": example_payload()}),
        "attach": ("/DEMO-ALPHA/documents", example_document(example_payload(), "identity")),
        "approve": (f"/DEMO-ALPHA/documents/{d['id']}/approval", None),
        "evaluate": ("/DEMO-ALPHA/evaluations", None),
        "resolve": (
            "/DEMO-ALPHA/resolutions",
            {"bundle_id": b["id"], "reason_code": "IDENTITY_UNVERIFIED", "document_id": d["id"]},
        ),
        "ack": (
            "/DEMO-ALPHA/acknowledgements",
            {
                "bundle_id": b["id"],
                "expected_hash": b["hash"],
                "signer_label": "role",
                "outcome": "REVIEW_ACCEPTED",
                "idempotency_key": "role-test",
            },
        ),
        "notice": (
            "/DEMO-ALPHA/obligations",
            {
                "reportability": "UNKNOWN",
                "deadline": None,
                "basis": "SYNTHETIC basis",
                "status": "PENDING",
            },
        ),
    }[operation]
    assert c.post("/api/cases" + suffix, headers=hdr(t[role]), json=body).status_code == 403
    assert c.post("/api/cases" + suffix, json=body).status_code == 401


def test_reader_endpoint_coverage_and_cross_tenant_reads(api):
    c, t, s, a = api
    reader = s.provision("reader", "harbor", "Reader")
    b = s.assemble(a["qa"], "DEMO-ALPHA")
    for path in [
        "/api/me",
        "/api/cases",
        "/api/obligations",
        "/api/cases/DEMO-ALPHA",
        "/api/cases/DEMO-ALPHA/documents",
        "/api/cases/DEMO-ALPHA/evaluations",
        "/api/cases/DEMO-ALPHA/acknowledgements",
        "/api/cases/DEMO-ALPHA/obligations",
        f"/api/bundles/{b['id']}",
        f"/api/bundles/{b['id']}/replay",
    ]:
        assert c.get(path, headers=hdr(reader)).status_code == 200
        assert c.get(path).status_code == 401
        if path.startswith("/api/cases/DEMO") or path.startswith("/api/bundles/"):
            assert c.get(path, headers=hdr(t["other"])).status_code == 403
