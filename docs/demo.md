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

The maintained [local tutorial client](../scripts/resolve_questions.py) uploads invented attachments,
requests simulated QA approval and completes tasks only after re-evaluation. It explicitly reconciles
**both** SOP candidates; newest-row selection is not authority. With the server running, execute:

```bash
uv run --locked python -m scripts.resolve_questions
# Custom disposable demo: add --runtime PATH --port PORT (loopback only)
```

Run only against a fresh disposable synthetic questions case. Expected JSON: `completed: 4`,
`original_tasks: 4`, `current_result: "WITHIN_SYNTHETIC_POLICY"`, `pending_obligations: 3`.
The old bundle still has four tasks; four separate completion events link to new evaluations.
This script is a tutorial, not an idempotent bulk/retry tool. An already partly/completely resolved
questions case is refused before new writes. For uncertain network outcomes reconcile API histories.
The [real-process smoke](../scripts/smoke.py) executes this exact command and verifies persistence.
An independent HTTP test remains: `test_four_question_demo_resolves_end_to_end_with_synthetic_bytes`.

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
