# Company reference — start here

**SYNTHETIC educational software; not production qualification.** This is the shared reading path for
QA, Engineering, Operations and Product. Private customer/source evidence stays outside this public tree.
It demonstrates defensible software boundaries, not a real product decision or business outcome.

## 1. Pick your role

| Audience | Your question | Next reference |
|---|---|---|
| Product / company leadership | What problem is solved, and what is explicitly not shipped? | Sections 2–4 here; [position paper](position-paper.md) / [3-page PDF](position-paper.pdf), [cost/rollout assumptions](cost-rollout.md) |
| QA / independent reviewer | Why is evidence usable, what blocks it, and what was tested? | Sections 3–4 here; [verification ledger](acceptance.md), [demo](demo.md) |
| Engineering | Where do rules, security, state and interfaces live? | Sections 5–6 here; [HLD](hld.md), [LLD](lld.md), [framework decisions](research.md) |
| Operations | How do I run, diagnose, preserve and recover it? | Section 7 here; [runbook](runbook.md), [threat model](threat-model.md) |

Runtime roles are different from these audiences. **Operator** imports/attaches/evaluates; **QA** attaches/evaluates and
approves/resolves/acknowledges (but does not import cases); **Regulatory** assesses notification obligations; **Reader** reads only.
All are server-provisioned, tenant-bound local demo roles. A display label does not grant authority.

## 2. Understand the problem in one minute

A thermometer alarm is a question, not proof that a product should be released or destroyed.
First establish which item, source, rule and observations apply. If the evidence is incomplete,
ask the responsible role for specific missing evidence. Keep any notification clock running separately.

**Built:** a local evidence review desk with attached bytes, typed synthetic comparisons, immutable
captured bundles, explainable tasks, replay, tenant/role checks and an independent durable deadline queue.
**Not built:** professional disposition/signing, live source ingestion, autonomous alert closure,
verified notification delivery, clinical rules, regional production infrastructure or qualified retention.
There are no external model calls and no external submissions. See the [capability ledger](acceptance.md#capability-status-and-exclusions).

### Glossary

| Term | Plain meaning |
|---|---|
| Alert | An observed signal needing investigation; not a closure or decision |
| Candidate | A possible source; finding it does not make it applicable or approved |
| Authority | The approved source that governs this exact scope and event time |
| Bundle | Frozen inputs, verified source content, checks, tasks, version and hash |
| Replay | Recalculate captured inputs; not use today's evidence or infer evidence truth |
| Reassessment | Append a linked new result after evidence changes; preserve the old result |
| Acknowledgement | A local QA review record; **not a professional signature** |
| Obligation | Independent notification assessment/history; UNKNOWN is unresolved, not exempt |
| Hash | A content consistency check; not proof of clinical truth or protection against a DB administrator |

## 3. Follow the six-step flow

1. **Intake:** an authenticated Operator records a labelled synthetic case. One transaction preserves
   original input and creates an UNKNOWN/PENDING obligation—even when an imported flag says N.
2. **Discover:** inspect candidate identity, study, SOP, exposure relationship and history attachments.
   Exact product/strength/presentation, both sites and event-time validity matter; aliases are not proof.
3. **Verify:** check source bytes/hash, readable substantive text and applicable QA authority.
   Unapproved attachments are not permission; conflicting SOPs require explicit approved reconciliation.
4. **Evaluate:** deterministic structured comparisons preserve strict/inclusive bounds and missingness.
   Unknown history is not zero. Unsupported constraints/uncertainty create role-owned evidence tasks.
5. **Review:** resolve tasks with approved attached evidence and a new evaluation. QA may acknowledge
   the latest expected bundle/hash atomically; stale evidence or a racing acknowledgement is rejected.
   This does not release medicine, close an alert or qualify a signature.
6. **Preserve and notify independently:** replay the old captured bundle; retain linked reassessments.
   Regulatory alone may assess reportability/deadline. Acknowledgement never clears the notification queue.
   SENT is an asserted record, not verified delivery; there is no sender.

Try the three invented paths in the [step-by-step demo](demo.md): supported arithmetic, four unresolved
questions and outside-policy arithmetic. Complete the four questions using the maintained executable
client rather than copying a long program out of documentation.

## 4. Requirements → code → observed tests

This is a **generic behavioral matrix**, not a claim that confidential source cases were clinically
adjudicated. Exact private PDF-page/workbook-cell alignment and unresolved original questions are kept
in a separate owner-only report. Named tests below are checked by offline documentation tests.

| Requirement / boundary | Implementation | Executed evidence / status |
|---|---|---|
| Do not confuse evidence, review and notices | [Store](../workbench/store.py), [API](../workbench/api.py) | `test_notice_survives_acknowledgement_and_restart`; implemented for local acknowledgement only |
| Identify exact scope and governing sources before arithmetic | [Evaluator](../workbench/domain.py), `Store._documents` | `test_explicit_approved_reconciliation_can_resolve_two_sop_revisions`; synthetic source gates implemented |
| Reject missing/nonfinite/reversed readings and unknown history | `Observation`, `Policy`, `evaluate` | `test_invalid_measurements_never_safety_evidence`, `test_unknown_history_is_not_zero`; no raw-series completeness inference |
| Preserve exact sources without ambiguous JSON interpretation | `source_document`, `Store.attach` | `test_ambiguous_or_nonfinite_source_json_is_rejected_without_side_effects`, `test_valid_source_preserves_exact_attached_bytes`; not proof the source is true |
| Authenticate tenant membership and trusted role | `Store._actor`, API dependencies | `test_case_identifiers_are_tenant_scoped_without_collision_oracle`, `test_nonstring_credential_fails_as_auth_denial_not_internal_error`; OIDC/MFA deferred |
| Do not silently coerce authority references | API `PositiveId` | `test_json_authority_ids_are_integers_not_coerced_aliases`, `test_oversized_sqlite_reference_is_validation_error_not_server_exception`; strict body types and bounded body/path IDs |
| Resolve missing authority with evidence, not blank text | `Store.resolve` | `test_unapproved_and_blank_attachments_do_not_complete_tasks`, `test_four_question_demo_resolves_end_to_end_with_synthetic_bytes` |
| Pin review inputs despite retries, races and approval changes | `Store.acknowledge` | `test_two_reviewers_racing_only_one_acknowledges`, `test_approval_alone_invalidates_an_otherwise_current_bundle` |
| Reconstruct old reasoning without later outcome leakage | `Store.replay`, immutable bundles | `test_replay_original_inputs_not_later_outcome`, `test_approved_resolution_creates_linked_version_not_overwrite`; only evaluator v1 retained |
| Deadlines survive failed evidence assembly and restart | Independent obligations ledger | `test_assembly_error_does_not_hide_deadline_and_order`, real-process smoke; no legal calendar or guaranteed delivery |
| Empty/new tenant cannot inherit old UI detail | Session + selection generations, synchronous DOM erasure | 23 Node transport/actual-DOM tests; prior dom-reset-v3 browser pass at its recorded SHA; current browser connection attempts UNVERIFIED |
| Durable recovery and change control | SQLite transactions, backup, version refusal | `test_backup_restore_integrity_and_obligations`; no automatic v1 migration or seven-year compliance |
| Company reference remains runnable and navigable | [Text tests](../tests/test_reference.py), [smoke](../scripts/smoke.py) | Local links/anchors/assets, named tests, CLI help and exact tutorial command checked; not universal prose correctness |
| Real clinical disposition, residency, historical qualification | [HLD](hld.md), [qualification gates](runbook.md#change-qualification) | Designed/deferred; not demonstrated by three fictional fixtures |

Exact commands, interpreter-specific denominators and exclusions live **only in the [verification
ledger](acceptance.md)**. Use the exact tested SHA/run in that ledger: configured CI or an older success is not proof of a newer revision.

## 5. HLD and LLD: one boundary at a time

**HLD = boxes and responsibilities:** browser → typed HTTP adapter → tenant-scoped transactional Store →
pure evaluator, with a separate obligations read path. One process and one local SQLite file deliberately
avoid distributed failure modes. Evidence failure must not suppress pending clocks. Detailed trust and
failure boundaries, team ownership and the PostgreSQL migration gates are in the [HLD](hld.md).

**LLD = exact contracts:** composite tenant/case keys; append-only sources, approvals, bundles and
obligations; UTF-8 hashes; source effective interval `[from,to)`; captured evaluator version; expected-hash
and unique request-key checks inside `BEGIN IMMEDIATE`. Endpoint/role/status tables, state transitions,
retry semantics and deferred adapter contracts are in the [LLD](lld.md). Do not duplicate those tables
into a second design that could drift.

**Failure explanation:** if source validation/evaluation fails, that transaction rolls back. The intake
obligation already committed independently and remains queryable. A disk/whole-database outage can still
stop both paths; independent business state is not physical high availability.

## 6. SOLID, honestly applied

| Principle | Concrete fit | Honest limit |
|---|---|---|
| Single responsibility | `domain.py` evaluates; `api.py` adapts HTTP; `store.py` owns authorization + durable invariants; UI presents | Store intentionally combines persistence/security workflows to keep one auditable transaction boundary; it is not one class per use case |
| Open/closed | New evidence creates new records, not mutations to original reasoning; policy operators are explicit data | New clinical semantics require code + evaluator version + qualification; arbitrary plug-ins are deliberately not accepted |
| Liskov substitution | No inheritance tree or interchangeable production adapters is claimed | Not meaningfully exercised here; a future storage adapter must preserve transaction/tenant/replay contracts and pass the same tests |
| Interface segregation | Small endpoint/model contracts; reading, source approval, acknowledgement and obligations have distinct permissions | Store is one concrete service, not a fabricated interface hierarchy; roles do not confer each other's authority |
| Dependency inversion | Pure evaluator consumes captured values, not FastAPI, SQL, network or an LLM; `create_app(path)` selects local state | API depends on the concrete SQLite Store today; no interchangeable PostgreSQL adapter exists. Extract a narrow protocol only when a second implementation earns it |

Do not describe append-only storage alone as full open/closed design, or invented interfaces as proof
of SOLID. Simplicity here means obvious responsibilities and invariant tests, not five abstract factories.

## 7. Run and verify locally

From repository root: `uv sync --locked`, then `uv run --locked python -m workbench demo`.
Open **http://127.0.0.1:8174**; retrieve the local role key in a second terminal as described in the
[README](../README.md#run-it-in-three-steps). Never put it in URLs, screenshots or shared logs.
After server updates reload the page and require **UI dom-reset-v3**; workspace refresh cannot replace JS.

- **First useful result:** QA → DEMO-READY → Assemble → inspect → acknowledge → Replay. Notice remains pending.
- **Questions:** fresh DEMO-QUESTIONS → `uv run --locked python -m scripts.resolve_questions` → four completions,
  old four-task bundle preserved, latest synthetic arithmetic supported, three obligations still pending.
- **Tenant boundary:** lock → meadow-reader → zero cases/obligations and empty detail, also after Refresh.
- **Verification:** run the commands in the [README verification block](../README.md#verify-it-yourself).
  Pytest includes offline text tests; Node tests are not browser rendering; smoke uses real HTTP and restart.
- **Troubleshooting:** existing/partial runtime is not overwritten; use a new `.runtime-*` directory. v1 is
  refused, not migrated. Keys expire after 24h; follow [identity recovery](runbook.md#start-stop-recover).
  Port in use? Use a different `--port` on both server and tutorial. Preserve data; never reset to hide failure.

## 8. Explain it in an interview

### Two-minute story

“The difficult part is earning permission to compare a reading, not calling an AI. I built one small
review desk: exact tenant-scoped source gates, a pure deterministic evaluator, immutable captured
bundles and evidence tasks. An independent ledger keeps UNKNOWN reporting obligations visible even when
assembly fails or QA acknowledges a bundle. Transactions plus expected hashes and scoped request keys
make retry/race behavior inspectable. The three invented cases show a useful path, unresolved questions
and out-of-policy arithmetic. I did not invent clinical limits, professional signatures or legal clocks.
SQLite and plain UI keep the demo easy to run; regional PostgreSQL/OIDC/outbox/WORM require separate
qualification. Passing local tests is evidence about this bounded slice, not production readiness.”

### Twenty-minute walkthrough

1. **0–3 min:** explain the two tracks and the explicit non-goals.
2. **3–8 min:** run supported arithmetic, inspect exact inputs and acknowledge; show pending notice.
3. **8–12 min:** show four questions and resolve with attached/approved evidence; replay the unchanged old bundle.
4. **12–16 min:** explain tenant/session isolation, stale hash/revision, concurrent acknowledgement and recovery tests.
5. **16–20 min:** HLD/LLD trade-offs, qualification blockers and a controlled change scenario.

**Deeper questions:** Why not an agent framework? What can a hash not prove? Why does source approval
invalidate an otherwise current bundle? Why is a second factor not a second signer? How would a sensor
bulletin trigger linked reassessment without rewriting original readings? What must change before
multiple processes/regions? How would an independently qualified old/new corpus explain every change?
Answers and limits are in the [position paper](position-paper.md), [LLD](lld.md), [runbook](runbook.md)
and [threat model](threat-model.md), not invented on the fly.
