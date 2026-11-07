# Step-by-step local demonstration

Everything below is synthetic. These are teaching approvals, not a claim about an original case.
No external notifications, purchases, regulatory submissions or clinical dispositions occur.

## 1. Start with a fresh, private runtime

```bash
uv sync --locked
uv run --locked python -m workbench demo
# In a second terminal:
uv run --locked python -m workbench credential harbor-qa
```

Login at http://127.0.0.1:8174. A QA key has tenant membership and QA role on the server.
Use `harbor-operator`, `harbor-regulatory` or `meadow-reader` in the credential command to try other
roles. Lock the browser between roles; don't put keys in screenshots. Closing/reloading loses the
in-memory browser key but retains server records. No real person's identity is asserted.

## 2. Follow one working path

Select `DEMO-READY`, assemble evidence, inspect exact checks and attachment content, then acknowledge
with a nonblank label. The recorded actor is the authenticated local QA actor, not the label.
The explicit pending notification remains. Replay and download the bundle to inspect captured inputs.
An outside-policy result is still arithmetic, not a destroy decision.

## 3. Resolve four real software tasks with invented evidence

`DEMO-QUESTIONS` has:
- A study candidate for a different presentation; it is not approved applicable authority.
- Two approved overlapping SOP candidates with no reconciled authority.
- Unapproved exposure wording; no inferred individual/cumulative combination.
- Missing complete batch history, not a zero history.

The following **local Python client** calls the running API, uploads invented attachments, requests
simulated QA approval, then completes each task only after re-evaluation. It handles SOP reconciliation
by an explicit approved replacement naming **both** old candidates, not by selecting the newest row.
Run it only in a disposable demo runtime: it changes that synthetic case's evidence history.

```python
# Run from repository root with: uv run --locked python
import json
from pathlib import Path
from urllib.request import Request, urlopen
from workbench.demo import example_document

keys = json.loads(Path(".runtime/credentials.json").read_text())
base = "http://127.0.0.1:8174/api"


def call(path, method="GET", data=None, role="harbor-qa"):
    request = Request(
        base + path,
        method=method,
        headers={"Authorization": "Bearer " + keys[role], "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data is not None else None,
    )
    with urlopen(request) as response:
        return json.load(response)


path = "/cases/DEMO-QUESTIONS"
original = call(path + "/evaluations")[0]
payload = call(path)["input"]
for kind, reason in [
    ("study", "STUDY_APPLICABILITY"),
    ("sop", "SOP_AUTHORITY"),
    ("exposure", "EXPOSURE_RELATIONSHIP"),
    ("history", "BATCH_HISTORY"),
]:
    document = example_document(payload, kind, row=100)
    if kind == "sop":
        document["supersedes"] = [
            d["id"] for d in call(path + "/documents") if d["kind"] == "sop" and d["approved"]
        ]
    attached = call(path + "/documents", "POST", document, "harbor-operator")
    call(path + f"/documents/{attached['id']}/approval", "POST")
    completed = call(
        path + "/resolutions",
        "POST",
        {"bundle_id": original["id"], "reason_code": reason, "document_id": attached["id"]},
    )
    print(reason, completed["status"], "new bundle", completed["resolved_bundle"])

print("Original task count:", len(call(f"/bundles/{original['id']}")["result"]["tasks"]))
print("Current result:", call(path + "/evaluations")[-1]["result"]["recommendation"])
print("Pending obligations:", len(call("/obligations")))
```

Expected on a **fresh** demo: four COMPLETE resolution events; original bundle still has four tasks;
current synthetic support is WITHIN_SYNTHETIC_POLICY; three pending obligations remain. Re-running with
already resolved original task keys conflicts by design. This exact workflow is exercised in
`test_four_question_demo_resolves_end_to_end_with_synthetic_bytes`.

The UI also supports manual attach/approval and linking an approved attachment ID to a task. Copy a
source with “Use as synthetic template” and edit the structured document carefully. `supersedes` may
be null, one prior ID, or a list of prior IDs of the same source kind/case/tenant. A replacement is
inactive until QA approval. Do not treat document order as source authority.

## 4. Check notifications separately

Login as Regulatory to record an explicit synthetic programme assessment. REPORTABLE needs an aware
ISO deadline. UNKNOWN remains pending. NOT_REQUIRED requires a qualified role and nonblank basis, never
an imported N flag. SENT records an assertion/receipt reference, **not verified transmission**; the demo
has no sender. Preserve historical rows, don't rewrite an earlier obligation to conceal lateness.

## 5. Reproducibility and failure

```bash
uv run --locked python -m pytest
uv run --locked python -m scripts.smoke
```

Tests cover missing/unapproved sources, strict boundaries, invalid readings, unknown history,
authentication/tenant denial, bad hashes, source tampering, stale versions, idempotency/races, preserved
obligations through assembly errors and process restarts, backup/restore and complete synthetic resolution.
For manual corruption drills, use disposable copies only. Do not disable integrity triggers in a real system.
