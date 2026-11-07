"""Every fixture is invented. No pharmaceutical permission is asserted."""

import copy

import pytest

from workbench.domain import evaluate


def snapshot():
    scope = {
        "product": "Fable reagent",
        "strength": "demo-7",
        "presentation": "cartridge",
        "origin": "lab-a",
        "destination": "lab-b",
    }
    docs = []
    for kind in ("identity", "study", "sop", "exposure", "history"):
        docs.append(
            {
                "id": kind,
                "kind": kind,
                "scope": copy.deepcopy(scope),
                "effective_from": "2029-01-01T00:00:00Z",
                "effective_to": "2031-01-01T00:00:00Z",
                "citation": "synthetic-catalog row 1",
                "verified": True,
                "approved": True,
                "content": "SYNTHETIC teaching attachment",
                "policy": None,
                "study_type": "excursion",
            }
        )
    docs[3]["policy"] = {
        "lower": {"op": "ge", "value": 1.0},
        "upper": {"op": "lt", "value": 19.0},
        "duration_minutes": 40.0,
        "cumulative_minutes": 200.0,
        "relationship_approved": True,
        "extra_constraints": [],
    }
    return {
        "synthetic": True,
        "scope": scope,
        "event_at": "2030-01-02T00:00:00Z",
        "observation": {
            "min_c": 3.0,
            "max_c": 12.0,
            "duration_minutes": 12.0,
            "complete": True,
            "uncertainty_resolved": True,
        },
        "history": {"complete": True, "prior_minutes": 18.0},
        "documents": docs,
    }


def codes(s):
    return {x["reason_code"] for x in evaluate(s)["tasks"]}


def test_verified_synthetic_path_is_useful_not_blanket_blocked():
    assert evaluate(snapshot())["recommendation"] == "WITHIN_SYNTHETIC_POLICY"


@pytest.mark.parametrize(
    "field,value",
    [
        ("min_c", None),
        ("max_c", float("nan")),
        ("max_c", float("inf")),
        ("duration_minutes", -1),
        ("min_c", 20.0),
        ("max_c", "12"),
        ("min_c", True),
    ],
)
def test_invalid_measurements_never_safety_evidence(field, value):
    s = snapshot()
    s["observation"][field] = value
    assert "INVALID_MEASUREMENTS" in codes(s)
    assert evaluate(s)["recommendation"] == "EVIDENCE_REQUIRED"


def test_missing_measurement_never_safety_evidence():
    s = snapshot()
    del s["observation"]["min_c"]
    assert "INVALID_MEASUREMENTS" in codes(s)


@pytest.mark.parametrize(
    "op,expected", [("lt", "OUTSIDE_SYNTHETIC_POLICY"), ("le", "WITHIN_SYNTHETIC_POLICY")]
)
def test_strict_inclusive_upper_bound_survives_roundtrip(op, expected):
    import json

    s = snapshot()
    s["observation"]["max_c"] = 19.0
    s["documents"][3]["policy"]["upper"]["op"] = op
    assert evaluate(json.loads(json.dumps(s)))["recommendation"] == expected


@pytest.mark.parametrize(
    "op,expected", [("gt", "OUTSIDE_SYNTHETIC_POLICY"), ("ge", "WITHIN_SYNTHETIC_POLICY")]
)
def test_strict_inclusive_lower_bound(op, expected):
    s = snapshot()
    s["observation"]["min_c"] = 1.0
    s["documents"][3]["policy"]["lower"]["op"] = op
    assert evaluate(s)["recommendation"] == expected


def test_one_sided_bound_is_explicit_not_silently_filled():
    s = snapshot()
    s["documents"][3]["policy"]["lower"] = None
    assert evaluate(s)["recommendation"] == "WITHIN_SYNTHETIC_POLICY"


@pytest.mark.parametrize(
    "index,code",
    [
        (0, "IDENTITY_UNVERIFIED"),
        (1, "STUDY_APPLICABILITY"),
        (2, "SOP_AUTHORITY"),
        (3, "EXPOSURE_RELATIONSHIP"),
        (4, "BATCH_HISTORY"),
    ],
)
def test_unapproved_document_creates_role_task(index, code):
    s = snapshot()
    s["documents"][index]["approved"] = False
    task = next(t for t in evaluate(s)["tasks"] if t["reason_code"] == code)
    assert all(
        task[k]
        for k in (
            "required_role",
            "evidence_requested",
            "completion_criterion",
            "source_citation",
            "status",
        )
    )


def test_presentation_mismatch_and_overlapping_sops_not_resolved_by_name():
    s = snapshot()
    s["documents"][1]["scope"]["presentation"] = "vial"
    # snapshot helper must not alias scope across docs
    assert "STUDY_APPLICABILITY" in codes(s)
    s = snapshot()
    s["documents"].append(copy.deepcopy(s["documents"][2]))
    s["documents"][-1]["id"] = "other-revision"
    assert "SOP_AUTHORITY" in codes(s)


@pytest.mark.parametrize(
    "history", [{"complete": False, "prior_minutes": 0}, {"complete": True, "prior_minutes": None}]
)
def test_unknown_history_is_not_zero(history):
    s = snapshot()
    s["history"] = history
    assert "BATCH_HISTORY" in codes(s)


def test_per_event_and_cumulative_need_approved_relationship():
    s = snapshot()
    s["documents"][3]["policy"]["relationship_approved"] = False
    assert "EXPOSURE_RELATIONSHIP" in codes(s)


def test_extra_constraints_not_ignored():
    s = snapshot()
    s["documents"][3]["policy"]["extra_constraints"] = ["light exposure unresolved"]
    assert "UNSUPPORTED_CONSTRAINT" in codes(s)


def test_no_real_clinical_evaluation():
    s = snapshot()
    s["synthetic"] = False
    assert "REAL_POLICY_UNSUPPORTED" in codes(s)


def test_source_bytes_and_approval_both_required():
    for key, value in [("verified", False), ("content", " ")]:
        s = snapshot()
        s["documents"][1][key] = value
        assert "STUDY_APPLICABILITY" in codes(s)


def test_later_outcomes_cannot_change_evaluation():
    s = snapshot()
    a = evaluate(s)
    s["later_outcome"] = "destroy"
    assert evaluate(s) == a


def test_history_question_not_hidden_by_missing_exposure_authority():
    s = snapshot()
    s["documents"][3]["approved"] = False
    s["history"] = None
    assert {"EXPOSURE_RELATIONSHIP", "BATCH_HISTORY"} <= codes(s)


def test_candidate_discovery_explains_rejection_without_promoting_authority():
    s = snapshot()
    s["documents"][1]["scope"]["presentation"] = "vial"
    result = evaluate(s)
    candidate = next(d for d in result["candidates"] if d["id"] == "study")
    assert "SCOPE_MISMATCH" in candidate["rejections"]
    assert candidate["eligible"] is False


@pytest.mark.parametrize("study_type", ["accelerated", "long-term", None])
def test_study_type_is_not_relabelled_excursion_authority(study_type):
    s = snapshot()
    s["documents"][1]["study_type"] = study_type
    assert "STUDY_APPLICABILITY" in codes(s)


@pytest.mark.parametrize("field", ["complete", "uncertainty_resolved"])
def test_string_flags_are_not_completeness_attestations(field):
    s = snapshot()
    s["observation"][field] = "true"
    assert "INVALID_MEASUREMENTS" in codes(s)
