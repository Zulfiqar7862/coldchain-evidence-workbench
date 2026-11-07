"""Ambiguous source bytes and coerced authority references are not evidence contracts."""

import json

import pytest

from tests.test_api import api as api
from tests.test_api import hdr
from tests.test_store import create
from tests.test_store import env as env
from workbench.demo import example_document, example_payload
from workbench.store import Credential


@pytest.mark.parametrize(
    "content",
    [
        '{"synthetic":true,"text":"first","text":"second"}',
        '{"synthetic":true,"text":"first","\\u0074ext":"second"}',
        '{"synthetic":true,"text":"SYNTHETIC","policy":{"upper":1,"upper":2}}',
        '{"synthetic":true,"text":"SYNTHETIC","extra":NaN}',
        '{"synthetic":true,"text":"SYNTHETIC","extra":Infinity}',
        '{"synthetic":true,"text":"SYNTHETIC","extra":-Infinity}',
        '{"synthetic":true,"text":"SYNTHETIC","extra":1e999}',
        '{"synthetic":true,"text":"SYNTHETIC","extra":' + "[" * 20000 + "0" + "]" * 20000 + "}",
    ],
)
def test_ambiguous_or_nonfinite_source_json_is_rejected_without_side_effects(api, content):
    client, tokens, store, actors = api
    before = store.documents(actors["qa"], "DEMO-ALPHA")
    document = example_document(example_payload(), "identity")
    document["content"] = content
    response = client.post(
        "/api/cases/DEMO-ALPHA/documents", json=document, headers=hdr(tokens["op"])
    )
    assert response.status_code == 409
    assert store.documents(actors["qa"], "DEMO-ALPHA") == before
    assert len(store.queue(actors["qa"])) == 1


@pytest.mark.parametrize("token", [7, True, float("nan"), {"token": "not a credential"}])
def test_nonstring_credential_fails_as_auth_denial_not_internal_error(env, token):
    store, actors, _ = env
    create(store, actors["op"])
    with pytest.raises(PermissionError):
        store.case(Credential(token), "DEMO-ALPHA")


@pytest.mark.parametrize("value", [True, 1.0, "1"])
@pytest.mark.parametrize(
    "field", ["supersedes", "ack_bundle", "resolution_bundle", "resolution_doc"]
)
def test_json_authority_ids_are_integers_not_coerced_aliases(api, value, field):
    client, tokens, store, actors = api
    bundle = store.assemble(actors["qa"], "DEMO-ALPHA")
    base = "/api/cases/DEMO-ALPHA"
    if field == "supersedes":
        document = example_document(example_payload(), "identity")
        document["supersedes"] = value
        path, payload = base + "/documents", document
    elif field == "ack_bundle":
        path = base + "/acknowledgements"
        payload = {
            "bundle_id": value,
            "expected_hash": bundle["hash"],
            "signer_label": "SYNTHETIC local QA",
            "outcome": "REVIEW_ACCEPTED",
            "idempotency_key": "strict-reference",
        }
    else:
        path = base + "/resolutions"
        payload = {
            "bundle_id": value if field == "resolution_bundle" else bundle["id"],
            "document_id": value if field == "resolution_doc" else 1,
            "reason_code": "BATCH_HISTORY",
        }
    response = client.post(path, json=payload, headers=hdr(tokens["qa"]))
    assert response.status_code == 422


def test_valid_source_preserves_exact_attached_bytes(api):
    client, tokens, store, actors = api
    document = example_document(example_payload(), "identity")
    document["content"] = json.dumps(
        {"synthetic": True, "text": "SYNTHETIC — distinct spellings preserved", "number": 1.25},
        ensure_ascii=False,
        indent=3,
    )
    attached = client.post(
        "/api/cases/DEMO-ALPHA/documents", json=document, headers=hdr(tokens["op"])
    )
    assert attached.status_code == 200
    assert store.documents(actors["qa"], "DEMO-ALPHA")[-1]["content"] == document["content"]


@pytest.mark.parametrize("arrays,expected", [(63, 200), (64, 409)])
def test_source_json_container_depth_boundary(api, arrays, expected):
    client, tokens, _, _ = api
    document = example_document(example_payload(), "identity")
    document["content"] = (
        '{"synthetic":true,"text":"SYNTHETIC","extra":' + "[" * arrays + "0" + "]" * arrays + "}"
    )
    assert (
        client.post(
            "/api/cases/DEMO-ALPHA/documents", json=document, headers=hdr(tokens["op"])
        ).status_code
        == expected
    )
