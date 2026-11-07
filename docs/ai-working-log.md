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
