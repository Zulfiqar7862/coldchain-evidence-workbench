"""Invented teaching data, generated credentials, safe local backup. No original-case data."""

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from workbench.store import Store


def example_payload(outside=False):
    return {
        "synthetic": True,
        "scope": {
            "product": "Fable research reagent",
            "strength": "demo-7",
            "presentation": "cartridge",
            "origin": "Harbor laboratory",
            "destination": "Hill laboratory",
        },
        "event_at": "2030-01-02T10:00:00Z",
        "observation": {
            "min_c": 4.0,
            "max_c": 24.0 if outside else 12.0,
            "duration_minutes": 12.0,
            "complete": True,
            "uncertainty_resolved": True,
        },
    }


def example_document(payload, kind, row=1):
    data = {
        "synthetic": True,
        "text": f"SYNTHETIC teaching attachment for {kind}. A local QA role must verify scope, content and authority. Not a real approval.",
    }
    if kind == "study":
        data["study_type"] = "excursion"
    if kind == "exposure":
        data["policy"] = {
            "lower": {"op": "ge", "value": 1.0},
            "upper": {"op": "lt", "value": 19.0},
            "duration_minutes": 40.0,
            "cumulative_minutes": 200.0,
            "relationship_approved": True,
            "extra_constraints": [],
        }
        data["text"] += (
            " This invented teaching policy explicitly combines these per-event and cumulative constraints; it does not apply to any medicine."
        )
    if kind == "history":
        data["history"] = {"complete": True, "prior_minutes": 18.0}
    return {
        "kind": kind,
        "scope": payload["scope"].copy(),
        "effective_from": "2029-01-01T00:00:00Z",
        "effective_to": "2031-01-01T00:00:00Z",
        "citation": f"synthetic-catalog row {row}",
        "content": json.dumps(data),
        "supersedes": None,
    }


def bootstrap(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, mode=0o700, exist_ok=False)
    directory.chmod(0o700)
    store = Store(directory / "workbench.db")
    roles = [
        ("harbor-operator", "harbor", "Operator"),
        ("harbor-qa", "harbor", "QA"),
        ("harbor-regulatory", "harbor", "Regulatory"),
        ("meadow-reader", "meadow", "Reader"),
    ]
    tokens = {name: store.provision(name, tenant, role) for name, tenant, role in roles}
    credentials = directory / "credentials.json"
    fd = os.open(credentials, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as out:
        json.dump(tokens, out, indent=2)
    operator, qa, regulatory = [
        store.authenticate(tokens[k]) for k in ("harbor-operator", "harbor-qa", "harbor-regulatory")
    ]
    for case_id, outside, deadline in [
        ("DEMO-READY", False, "2030-01-03T14:00:00Z"),
        ("DEMO-QUESTIONS", False, "2030-01-03T12:00:00Z"),
        ("DEMO-OUTSIDE", True, "2030-01-03T16:00:00Z"),
    ]:
        payload = example_payload(outside)
        store.create_case(operator, case_id, payload, "N", deadline)
        if case_id == "DEMO-QUESTIONS":
            for i, kind in enumerate(["identity", "study", "sop", "sop", "exposure"], 1):
                document = example_document(payload, kind, i)
                if kind == "study":
                    document["scope"]["presentation"] = "vial"
                attached = store.attach(operator, case_id, document)
                if kind in {"identity", "sop"}:
                    store.approve(qa, case_id, attached["id"])
        else:
            for i, kind in enumerate(["identity", "study", "sop", "exposure", "history"], 1):
                attached = store.attach(operator, case_id, example_document(payload, kind, i))
                store.approve(qa, case_id, attached["id"])
        if case_id == "DEMO-READY":
            store.set_obligation(
                regulatory,
                case_id,
                "REPORTABLE",
                deadline,
                "SYNTHETIC programme assessment; explicit demonstration deadline, not a legal rule.",
                "PENDING",
            )
        store.assemble(qa, case_id)
    return {"runtime": str(directory), "credentials_file": str(credentials), "cases": 3}


def backup(source, target):
    source, target = Path(source), Path(target)
    if not source.is_file():
        raise FileNotFoundError(source)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    with closing(sqlite3.connect(source)) as src, closing(sqlite3.connect(target)) as dst:
        src.backup(dst)
        if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("backup integrity check failed")
    return {"backup": str(target), "integrity": "ok"}
