# Verification ledger and honest boundaries

Observed locally on **7 November 2026 (Europe/Berlin)**. These are execution results, not production
qualification. No GitHub Actions run has been observed: the repository has not been published in this
implementation phase. No CI badge is used as a substitute for a run actually read.

## Commands actually executed

All commands ran from the repository root unless noted. Raw logs are retained privately outside Git.

| Exact command | Observed exit | Observed result |
|---|---:|---|
| `uv sync --locked` | 0 | Locked local environment created |
| `uv run --locked python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **111 passed** on Python 3.13.5; 90% statement coverage (**690 statements, 68 missed**); no warnings |
| `uv run --isolated --locked --python 3.12 python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **111 passed**, Python 3.12.16; **690 statements, 68 missed, 90%** |
| `uv run --isolated --locked --python 3.14 python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **111 passed**, Python 3.14.10; **644 statements, 68 missed, 89%** |
| `uv run --locked ruff check .` | 0 | All checks passed |
| `uv run --locked ruff format --check .` | 0 | Formatting clean |
| `npx --yes prettier@3.6.2 --write workbench/static/index.html workbench/static/app.js workbench/static/app.css` | 0 | Frontend source formatted for human readability; not a required runtime tool |
| `node --test tests/ui-races.cjs` | 0 | **15 passed** on Node 24.22.1; real application JS in a minimal Node VM/DOM harness, delayed transport/body/errors, all asynchronous read/action paths; not a browser suite |
| `node --check workbench/static/app.js` | 0 | JavaScript syntax accepted; not a visual browser test |
| `uv run --locked python -m compileall -q workbench scripts` | 0 | Python compilation accepted; not static type checking |
| `uv run --locked python -m scripts.smoke` | 0 | Real HTTP auth, three synthetic cases, evaluation, QA acknowledgement, unchanged deadline queue, full process restart, original replay and tenant denial |
| `uv export --locked --no-dev --no-emit-project --output-file requirements.txt` | 0 | Hash-pinned runtime export |
| `uv run --locked python -m pip_audit -r requirements.txt --require-hashes --disable-pip` | 0 | No known vulnerabilities found in runtime export; harmless audit-cache deserialization warnings observed |
| `uv run --locked python -m pip_audit` | 0 | No known vulnerabilities found in installed runtime + development environment after asset-tool upgrade |
| `weasyprint docs/position-paper.html docs/position-paper.pdf` | 0 | Original position paper rendered; `pdfinfo` reports **3 A4 pages** |

Post-review Python suite composition: **42 HTTP, 3 demo/backup, 34 domain, 32 store tests**. Each
coverage run used a separate private `COVERAGE_FILE`. Interpreter/tool line accounting differs: the
Python 3.14 denominator is not interchangeable with 3.12/3.13. The earlier 80-test result is superseded;
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
The Node regressions are included in CI. CI itself remains unobserved remotely. The initial build was
visually exercised by an independent browser worker (evaluation/replay/tasks/acknowledgement/queue passed,
transient tenant leak observed); **visual retest of the repaired build is pending**. Fresh repaired runtime
HTTP checks passed: three authorized cases, empty other tenant, review metadata, seeded replay, no-store
assets, authentication denial and favicon 204. A separate real-process smoke tested restart/persistence.

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
| Frontend controls and API wiring | Implemented; 15 Node race regressions/API/syntax checked; initial visual review found the fixed race; repaired visual retest pending |
| Metrics, fair scheduling, regional PostgreSQL/RLS/WORM | Designed; not implemented/executed |
| CI YAML | Configured with pinned actions/read-only permissions; **not yet observed** on GitHub |
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
