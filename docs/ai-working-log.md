# Honest AI working log — public-safe summary

Date: 7 November 2026 (Europe/Berlin). **Time spent was not continuously logged; no hours are claimed.**
This is a narrative record of this new local build, not a verbatim session transcript or evidence of
unrecorded prior work. Private source materials, logs and prompts are not redistributed in this tree.

## Work actually performed

1. Loaded the coding/source-control and generic web-research skills. A new isolated local directory was
   created; no old repository code, assets or Git history were copied. The coordinating agent had already
   established that cloud-agent execution was unavailable and delegated an explicitly local new build.
2. Read the private brief and workbook README before inspecting the remaining reference tabs. Kept
   source facts and business targets in a separate private mapping, not public fixtures.
3. Researched generic framework/security/transaction/locking guidance. Kept FastAPI/Pydantic and standard
   SQLite; rejected unnecessary agent/vector/orchestrator infrastructure. No private case data went to an
   external model or retrieval API. No skill/plugin code is a runtime dependency.
4. Wrote domain regression tests before the evaluator. The first `pytest` console invocation failed to
   find the local module; changing the invocation to `python -m pytest` made it runnable. The stub evaluator
   then produced **27 failing tests**. This collection error is not represented as a meaningful RED result.
5. Implemented domain gates. A test initially used an aliased dictionary fixture, so changing a study scope
   also changed case scope. Corrected the fixture with deep copies; did not weaken the identity requirement.
6. Wrote persistence tests before the store. The unimplemented Store produced **21 setup errors**, not 21
   assertion-demonstrated red regressions. This distinction matters: the initial store RED was coarse, not
   a claim of ideal one-test-at-a-time TDD. Later concrete bug regressions failed at their asserted behavior.
7. Added authentication/tenant HTTP tests before routes. Against a runnable empty FastAPI app, **11 tests
   failed**. Built typed routes and memory-only-key UI; a dedicated UI contract test failed before controls
   existed. UI visual interaction is separately reviewable, not proved by HTML assertions.
8. Loaded the installed test-driven-development, verification-before-completion and systematic-debugging
   skills when made available. Continued from existing work rather than recreating RED evidence.
9. Added focused regressions that exposed real gaps: independent batch-history tasks when exposure authority
   was absent; candidate rejection explanations; accelerated/long-term study types; boolean coercion in
   HTTP measurements; string completeness flags; unknown schema acceptance; multi-source SOP reconciliation.
   Each was run failing before its corresponding fix. Some additional coverage passed immediately; those
   are verification tests, not retroactively claimed test-first discoveries.
10. During the store build, input validation initially ran before authorization on notification updates.
    Tenant tests demonstrated the wrong exception boundary. Moved role/object authorization first for that
    operation. Store request parameters never grant tenant membership.
11. While documenting resolution, found a modeling mistake: replacing one SOP with one new source cannot
    reduce two active conflicting candidates to one. A regression demonstrated the gap. Added an explicit
    replacement relation so approved reconciliation evidence can supersede multiple scoped predecessors.
    No automatic source winner was invented.
12. Bootstrap, backup, API integration, concurrent review, real-socket server restart and dependency audit
    commands were actually executed. Runtime dependency audit found no known advisories; full-development
    audit found Pillow advisories. Upgraded the asset-only dependency and reran the audit cleanly.
13. Created original conceptual GIF/PNG diagrams. They are explicitly not UI recordings. The code uses
    no generated claims about real clinical approvals or complete actual batch histories.

## Kept / rejected / deferred

**Kept:** evidence-before-authority framing, independent clocks, deterministic tiny core, real SQLite
transactions, negative tests, role tasks, understandable UI, immutable replay inputs, explicit synthetic
approved path and explicit unknown path.

**Rejected:** selecting source authority by a name/readable flag/revision number; treating historical
agreement as correctness; combining ambiguous original exposure allowances; calling a typed label a
qualified signature; claiming a load probe establishes scale; claiming configured CI has run; claiming
public publication before remote review.

**Deferred:** professional regulated signing, dual signing, MFA, clinical policy qualification, live source
adapters, raw telemetry completeness, batch ledger, notification delivery/receipts, regional deployment,
long retention, PostgreSQL/RLS and alert-closure automation.

## Verification honesty

Local commands/results are summarized in [acceptance.md](acceptance.md). Raw RED/GREEN logs are retained
privately, not fabricated or added to Git with possible ephemeral test-key diagnostics. There are no
claimed past AI sessions, human disagreements or hours that were not observed. Independent UI and
publication review remain distinct from the implementation agent's own checks.

Later verification also exercised the full suite on isolated Python 3.12 and 3.14, checked the
plain-venv fallback, and formatted frontend sources with pinned Prettier 3.6.2 for human readability.
Resource warnings from unclosed test-only database fixtures were observed and fixed by closing those
connections explicitly; a warnings-as-errors full run then passed. Nonstring approval text had four
failing adversarial regressions before a type guard was added. No browser visual review or remote CI
run is inferred from these results.

## Independent-review follow-up (same date, Europe/Berlin)

Loaded receiving-code-review, systematic-debugging and TDD guidance. Ran both independent reproductions
against the initial build; the API repro first needed the repository on `PYTHONPATH` (that import error is
not a domain RED). Verified the stale-session render, hidden proposed predecessor relation and globally
unique case-ID collision. Added concrete failing assertions before focused fixes, preserving raw logs
privately. The first delayed-selection test harness could hang on the unfixed chain; bounded it and
observed nine assertion failures, then added cancellation plus session/selection/refresh generations to
all async UI paths, immutable request credentials, stale-error suppression and full logout clearing.

Exposed replacement IDs/scope/effectivity in document review and approval confirmation. Replaced global
case uniqueness with tenant-scoped composite keys and versioned schema v2; deliberately refused v1 and
unversioned existing databases rather than building an unreviewed migration. Added credential-expiry,
approval-only revision and all-write-role denial tests; those 25 checks already passed and are not claimed
as bug discoveries. Fixed the harmless favicon 404 with a test-first 204 handler. No test result was
fabricated to make the original implementation look complete.

Reran the full 111-test suite with independent coverage files on Python 3.12/3.13/3.14, fifteen deterministic
Node race/metadata tests, lint/format/compile checks, real-socket restart smoke and dependency audits. The
coverage denominators differ by interpreter and are recorded separately in acceptance.md. The runtime
audit reported cache-deserialization warnings but no known vulnerabilities; installed-dependency audit
was clean. After the browser worker finished, preserved its v1 runtime, stopped that process and started
a fresh v2 runtime on the same loopback port. Read-only live HTTP checks passed. Repaired visual UI review
and independent publication/security approval were pending at that checkpoint; no remote had been created or pushed.

## Failed v2 browser retest and DOM reset follow-up

Independent browser retest FAILED: old case/product/route persisted with an empty Reader tenant, even
after in-app refresh. Publication remained blocked. Loaded debugging/TDD guidance and inspected actual
markup, CSS and served asset bytes instead of attributing this to caching. CSS already enforced hidden
with `!important`; parsed markup IDs were unique. The served JS matched the working tree and was no-store.
A private exact-snapshot DOM probe reproduced the screenshot pattern with initial script execution, not
fresh v2 execution. The failed browser tab's executing asset identity cannot be recovered here; an old
open tab is a hypothesis, not an established cache diagnosis.

Added locked, development-only jsdom 31 tests against actual HTML/CSS, using the documented Node VM
context API. The first harness used strict eval and lost callable lexical scope; fixed the harness before
accepting RED. Four actual-DOM assertions then failed: empty-list refresh retained residual case text,
old disclosure state remained open, and executing build identity was absent. Added a further failing
form-reset test and an HTTP build-contract test. Implemented explicit selection invalidation and erasure,
separate empty/detail states, disclosure/form reset and a visible script build marker/versioned assets.
The full login/lock/reader/refresh and delayed case-response workflows passed after the fix. Those added
workflow checks are verification, not retroactively claimed RED discoveries.

The new DOM library is only a development dependency, pinned in package-lock.json; Node is still not an
application runtime. No browser process, screenshot automation, original data or external case API was
used. Fresh Python, Node, lint, audits and real-socket persistence smoke results are in acceptance.md.
At that checkpoint a new independent browser retest was required; no public remote or publication had been performed.

## Independent visual acceptance and approved source publication

The coordinator subsequently reported an independent final review of `5de05e4` with no code/security/
confidentiality blockers and a PASSED real-browser retest with visible `UI dom-reset-v3`. Assembly, replay,
QA acknowledgement with a pending notice, empty Reader tenant after lock/refresh, and restored QA tasks
were checked. The earlier failed browser result is retained; this does not establish a cache cause.

Inspected the two supplied real-browser screenshots before copying: only synthetic fixture names, role
labels and public bundle hashes were visible, with no credential fields or keys. Re-encoded them without
PNG metadata and added them as actual UI captures alongside the separately labelled conceptual GIF.
Publication of this new original public repository was explicitly authorized; old repositories and their
branches remain untouched. Remote CI results will be recorded only after an actual run is read.
