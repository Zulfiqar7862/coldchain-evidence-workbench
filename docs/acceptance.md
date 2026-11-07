# Verification ledger and honest boundaries

Observed locally on **7 November 2026 (Europe/Berlin)**. These are execution results, not production
qualification. The new source repository is public; an actual completed GitHub Actions run was read,
with its exact SHA and results below. No CI badge substitutes for reading a run.

## Commands actually executed

All commands ran from the repository root unless noted. Raw logs are retained privately outside Git.

| Exact command | Observed exit | Observed result |
|---|---:|---|
| `uv sync --locked` | 0 | Locked local environment created |
| `uv run --locked python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **112 passed** on Python 3.13.5; 90% statement coverage (**690 statements, 68 missed**); no warnings |
| `uv run --isolated --locked --python 3.12 python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **112 passed**, Python 3.12.16; **690 statements, 68 missed, 90%** |
| `uv run --isolated --locked --python 3.14 python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **112 passed**, Python 3.14.10; **644 statements, 68 missed, 89%** |
| `uv run --locked ruff check .` | 0 | All checks passed |
| `uv run --locked ruff format --check .` | 0 | Formatting clean |
| `npx --yes prettier@3.6.2 --write workbench/static/index.html workbench/static/app.js workbench/static/app.css` | 0 | Frontend source formatted for human readability; not a required runtime tool |
| `npm ci --ignore-scripts --no-audit` | 0 | Locked development-only jsdom installation; no install scripts or browser process |
| `npm test` | 0 | **23 passed** on Node 24.22.1: 15 delayed-response tests plus 8 actual-markup DOM/CSS/tenant-switch tests; not visual browser rendering |
| `npm audit --audit-level=low` | 0 | No known vulnerabilities in the DOM test dependency tree |
| `node --check workbench/static/app.js` | 0 | JavaScript syntax accepted; not a visual browser test |
| `uv run --locked python -m compileall -q workbench scripts` | 0 | Python compilation accepted; not static type checking |
| `uv run --locked python -m scripts.smoke` | 0 | Real HTTP auth, three synthetic cases, evaluation, QA acknowledgement, unchanged deadline queue, full process restart, original replay and tenant denial |
| `uv export --locked --no-dev --no-emit-project --output-file requirements.txt` | 0 | Hash-pinned runtime export |
| `uv run --locked python -m pip_audit -r requirements.txt --require-hashes --disable-pip` | 0 | No known vulnerabilities found in runtime export; latest rerun had no warnings |
| `uv run --locked python -m pip_audit` | 0 | No known vulnerabilities found in installed runtime + development environment after asset-tool upgrade |
| `weasyprint docs/position-paper.html docs/position-paper.pdf` | 0 | Original position paper rendered; `pdfinfo` reports **3 A4 pages** |

Post-review Python suite composition: **43 HTTP, 3 demo/backup, 34 domain, 32 store tests**. Each
coverage run used a separate private `COVERAGE_FILE`. Interpreter/tool line accounting differs: the
Python 3.14 denominator is not interchangeable with 3.12/3.13. The earlier 80/111-test results are superseded;
no single old coverage percentage is presented as the current cross-version result.

Coverage is a diagnostic, not a safety score. The CLI module is exercised by real-process smoke but is
not included in subprocess coverage; its in-process coverage is 0%. There is no claim of complete branch,
fault-injection, production load, security penetration or clinical policy coverage.

## Test-first evidence (not retroactively idealized)

- Runnable empty evaluator: **27 failed** before implementation; initial console pytest import error
  was fixed separately and is not counted as meaningful RED.
- Unimplemented Store: **21 setup errors**, explicitly not 21 assertion-proven regressions.
- Runnable empty FastAPI app: **11 failed** before routes existed.
- UI controls contract: **1 failed** before the interface was built.
- Independent history question and candidate rejection explanations: **2 failed** before fixes.
- Study type, strict completeness flags and boolean numeric coercion: **6 failed** before fixes.
- Unknown schema gate: **1 failed** before fix; added restart/hash coverage already passed and is not
  claimed to have discovered a previously failing behavior.
- Explicit multi-source SOP reconciliation: **1 failed** before relation/approval implementation.
- Nonstring attachment approval text: **4 failed** before type-guard fix.
- Additional complete four-question HTTP resolution test passed after correcting its missing test import;
  it verifies existing behavior and is not claimed as a test-first feature discovery.

The working log records coarse initial scaffolding and later focused regressions honestly. No raw test
failure logs containing ephemeral credential diagnostics are committed publicly.

## Independent review corrections and observed regression evidence

The initial review reproduced a real transient old-tenant UI rendering bug, hidden proposed supersession
metadata and a cross-tenant case-ID collision oracle. These were defects, not merely documentation gaps.

- **Session/selection isolation:** nine runnable Node assertions failed before the fix. The first harness
  could await an unfixed continuation indefinitely; it was bounded before the accepted RED run. Captured
  credentials, session/selection/refresh-lane generations and cancellation now gate requests **and every
  continuation after response/body awaits**. Stale errors/finally blocks and detached action closures are
  silent; logout clears scalar labels and forms as well as lists. Later additional guards passed immediately
  and are verification coverage, not claimed as additional pre-fix RED results.
- **Proposed supersession:** one API and one UI assertion failed before metadata/display fixes. QA can now
  inspect predecessor IDs, exact scope and effective dates before approval; targets remain active until approval.
- **Tenant case keys:** three focused assertions failed before schema v2; an additional unversioned-database
  assertion also failed before refusal was implemented. Same public IDs coexist safely in two tenants;
  missing/inaccessible reads are identical. Composite case foreign keys are checked. v1/unknown/unversioned
  databases are rejected without changing their bytes; **no offline migration is implemented**.
- **Existing guard verification:** 25 additional expiry-boundary, approval-only invalidation and endpoint
  role/read regressions passed immediately. These confirm existing protections; no production fix is claimed.
- **Favicon:** one assertion failed before the empty no-store 204 route, removing the harmless browser 404.

All raw RED/GREEN diagnostics remain outside Git, including ephemeral disposable test credentials.
The Node regressions are included in CI; the completed remote matrix run is recorded below. The initial build was
visually exercised by an independent browser worker (evaluation/replay/tasks/acknowledgement/queue passed,
transient tenant leak observed); **the subsequent v2 browser retest FAILED with persistent detail under an empty reader tenant**.
That failure remains recorded; the later independent visual retest of `5de05e4` passed as described below. Fresh repaired runtime
HTTP checks passed: three authorized cases, empty other tenant, review metadata, seeded replay, no-store
assets, authentication denial and favicon 204. A separate real-process smoke tested restart/persistence.

## Real-markup follow-up after failed v2 browser retest

The v2 browser screenshot showed an empty Reader tenant with an old case label/product/route and enabled
assembly button. We do **not** count the earlier Node mock tests as proof this browser defect was fixed.

Investigation used the real HTML/CSS and application script in jsdom (Node-only, no browser automation).
IDs were unique and the existing `[hidden] { display:none !important }` rule worked in CSSOM; no stylesheet
collision was demonstrated. The server returned the expected script bytes and `Cache-Control: no-store`.
A fresh exact-snapshot DOM login/lock/reader/refresh probe reproduced the screenshot's persistent text and
enabled button with the **initial** script, but not with fresh v2 script execution. Which script the failed
browser tab was executing was not observable retrospectively; **no cache cause is asserted**.

A genuine recovery defect was independently reproduced: `loadCases()` updated the empty list/count but did
not invalidate an absent selection or erase residual detail. Four real-DOM assertions failed before the
fix (including residual text in both selected/unselected empty-list states, retained disclosure state and
missing build identity); one additional form-choice reset assertion failed before its fix. An initial
strict-eval harness scope error was corrected and is not counted as RED. A separate HTTP build contract
also failed before versioned assets/marker existed. Full fresh login and late-response real-DOM workflows
were subsequently added as verification coverage, not falsely claimed as extra discoveries.

The new implementation clears all case text, containers, labels/titles and fields **before** hiding;
closes disclosures and resets unsubmitted choices; gives detail/empty states separate IDs; invalidates
removed selections and pending selection requests; and enables detail only after an authorized response.
Empty-list refresh now erases residual data even if CSS visibility is forced. The visible executing-script
marker is **UI dom-reset-v3**, with matching versioned asset URLs; UI/assets remain no-store. Server restart
and in-app refresh do not update already executing scripts: navigate/reload and verify the marker.

Eight actual-markup DOM/CSS tests and fifteen transport race tests pass. jsdom has no layout/rendering
engine, so those results did not replace independent visual review.

**Independent browser retest subsequently PASSED on `5de05e4087205cd0bcf7f195d0ae60d8f7162e57`, with
visible `UI dom-reset-v3`:** assembly and captured replay; local QA acknowledgement with the notice still
pending; locking QA then opening the Reader tenant showed zero cases, zero obligations and empty detail
even after workspace refresh; returning to QA showed four unresolved tasks. Independent final review
reported no code/security/confidentiality blockers for that SHA, not production or clinical qualification.
Two actual screenshots were manually inspected for secrets: only invented case/product/tenant data and
public bundle hashes were visible. Re-encoding removed PNG metadata before adding them to the repository.
The earlier browser tab's executing asset identity remains unknown; **no cache cause has been proved**.

## Representative invariants and named tests

| Invariant | Tests |
|---|---|
| Review acknowledgement cannot close outstanding obligations | `test_notice_survives_acknowledgement_and_restart`, `test_http_working_path_review_and_notice_independence` |
| Assembly corruption does not hide deadline ordering | `test_assembly_error_does_not_hide_deadline_and_order` |
| Process restart preserves queue | `test_obligation_survives_separate_interpreter` + real-socket smoke |
| N/blank/unknown imported flags stay UNKNOWN | `test_raw_flags_never_qualified_not_required` |
| Qualified exemption needs Regulatory role and basis | `test_qualified_not_required_needs_regulatory_role_and_nonblank_basis` |
| Missing/revoked/expired/other-tenant credentials fail closed | `test_missing_invalid_revoked_credential_fails`, `test_expiry_boundary_rechecked_for_retained_credentials`, tenant HTTP/store tests |
| Invalid/NaN/infinite/reversed/bool readings never safety evidence | `test_invalid_measurements_never_safety_evidence`, `test_http_boolean_measurement_must_not_coerce_to_one_degree` |
| Strict/inclusive limits survive JSON roundtrip | `test_strict_inclusive_upper_bound_survives_roundtrip`, lower/one-sided tests |
| Different presentation / accelerated study / overlapping SOPs are not permission | Scope, study-type, overlap and candidate-rejection tests |
| Unknown history != zero; missing exposure authority doesn't hide history task | `test_unknown_history_is_not_zero`, `test_history_question_not_hidden_by_missing_exposure_authority` |
| Empty/unapproved sources cannot complete tasks | `test_unapproved_and_blank_attachments_do_not_complete_tasks`, nonstring approval tests |
| Explicit approved SOP reconciliation, not automatic latest-wins | `test_explicit_approved_reconciliation_can_resolve_two_sop_revisions` |
| Four synthetic tasks can actually resolve | `test_four_question_demo_resolves_end_to_end_with_synthetic_bytes` |
| Approval alone invalidates a captured revision | `test_approval_alone_invalidates_an_otherwise_current_bundle` |
| Case ID cannot reserve/probe another tenant's namespace | `test_case_identifiers_are_tenant_scoped_without_collision_oracle`, schema v2 key tests |
| Bundle/source tamper and blank labels rejected | Stored-hash/source-hash/blank/stale tests |
| Concurrent reviews and request-key retries cannot duplicate acknowledgement | `test_two_reviewers_racing_only_one_acknowledges`, idempotency tests |
| Later outcome never leaks into prior evaluation | `test_later_outcomes_cannot_change_evaluation`, `test_replay_original_inputs_not_later_outcome` |
| New evidence creates linked result, original remains | `test_approved_resolution_creates_linked_version_not_overwrite`, stale revision tests |
| Backup can restore real queue and replay | `test_backup_restore_integrity_and_obligations` |

## Bounded probe, not a scalability claim

Before the review fixes, a separate real-loopback queue-read probe used **200 requests / 8 client threads / three synthetic
cases**. Observed: zero request failures, 0.703 seconds wall time, 9.568 ms median, 107.708 ms p95.
No write traffic, large source sets, source-adapter outages, production hardware, regional network,
long-run memory pressure or real burst mix was represented. Do not extrapolate these numbers to
production capacity, multi-tenancy fairness or notification compliance.

## Capability status

| Capability | Honest status |
|---|---|
| Public teaching fixtures, source wording in fixtures | Invented and clearly labelled SYNTHETIC; not verified original-case authority |
| Local server-side authentication / tenant / roles | Implemented; API/store negative tests executed |
| Candidate discovery and specific rejection reasons | Implemented; synthetic tests executed |
| Source bytes, approval, exact scope and effective-time gates | Implemented; local synthetic approval only; real approvals require clarification |
| Five-source evidence chain and role resolution tasks | Implemented; full synthetic resolution executed |
| Independent durable deadlines and UNKNOWN reportability | Implemented; error/restart/role tests executed |
| Clinical policy evaluation and professional disposition | Deferred; no such original-case qualified capability claimed |
| Real signing / MFA / dual professional signers | Deferred; local acknowledgement explicitly not legal signing |
| Verified regulator delivery and receipts | Deferred; SENT is a role's assertion, not actual transmission |
| Captured hash-checked inputs and linked replay | Implemented/tested; proves reproducibility, not evidence truth |
| Frontend controls and API wiring | Implemented; 23 Node race/actual-DOM regressions/API/syntax checked; independent dom-reset-v3 browser retest passed on `5de05e4` |
| Metrics, fair scheduling, regional PostgreSQL/RLS/WORM | Designed; not implemented/executed |
| GitHub Actions | Completed run on `2ac0063` observed successful across Python 3.12/3.13/3.14; exact SHA/link below |
| Internet hardening / production or clinical qualification | Not performed |

Historical clinical comparison has not been executed against a real corpus. The three fixture paths
are not a closure-rate denominator, clinical performance result or production outcome agreement study.
No full static type checker, Docker build or browser automation suite was run. Docker is not required
and no Dockerfile is offered as evidence of scale. Private original requirements/QA questions and exact
source citations remain in a separate owner-only register.

## Public-tree hygiene

The original staged file set and, after review fixes, all reachable Git blobs plus tracked worktree were checked for known private-source identifiers, credential/private-key
patterns, exact generated runtime keys, forbidden workbook/archive/database files and broken local
Markdown links. No matches were found. This is a bounded scan, not a substitute for independent
publication/security review. The plain-venv hash-pinned install and synthetic CLI seeding were also
executed successfully (exit 0); no runtime database or generated key file is tracked.

## Observed GitHub Actions result — exact published revision

- Repository: https://github.com/Zulfiqar7862/coldchain-evidence-workbench — public source only, not a deployed service.
- Tested SHA: `2ac00639e1e409a3423560797ed5317ab47b4eec`.
- Run: https://github.com/Zulfiqar7862/coldchain-evidence-workbench/actions/runs/42371195914
- Observed conclusion: **success**, all three jobs `verify (3.12)`, `verify (3.13)`, `verify (3.14)` completed successfully.
- Actual logs were read: **112 pytest tests passed per interpreter; 23 Node tests passed per job**;
  Ruff checks/format, real-socket restart smoke, npm audit and runtime pip audit all succeeded.
- This records the preceding tested SHA deliberately. The follow-up documentation commit records this
  observation; its own CI is checked separately rather than creating an infinite documentation/CI loop.

No PR, merge, old-repository write, production deployment or public demo-server exposure was performed.
The only pushed branch is `build/evidence-workbench`, also the new repository's default branch.
