# Twenty-minute reviewer walkthrough

1. **0–3 minutes: state the boundary.** An alarm requests investigation. Evidence chain before arithmetic.
   Demonstrate that there is no release/destroy endpoint. All data and approvals are synthetic.
2. **3–7: supported path.** Start from a fresh runtime, log in as local QA, assemble `DEMO-READY`, inspect
   source bytes, explicit operators and captured hashes. Acknowledge locally. Show obligation still pending.
3. **7–11: useful uncertainty.** Open `DEMO-QUESTIONS`. Show four reason-specific role tasks and candidate
   rejection reasons. Two SOPs do not become one just because one arrived later. Show how an approved
   attachment and re-evaluation resolve a task without overwriting original evidence.
4. **11–14: hostile inputs.** Read the negative tests for booleans/nonfinite/reversed measurements,
   strict/inclusive operators, missing membership and source/bundle tampering. Show exact test output.
5. **14–17: concurrency and recovery.** Demonstrate expected-hash stale review rejection and the two-reviewer
   race test. Run `python -m scripts.smoke` through a real process restart. Explain current SQLite serialization.
6. **17–20: operational honesty.** Explain missing professional signing, source connectors, verified delivery,
   raw-series history, regional retention and qualification. Show the migration gates, not pretend capacity.

## Deep dives worth inviting

- Why SHA replay is reproducibility, not truth; why current bytes are rechecked before acknowledgement.
- What commits atomically, what a retry means, and why other APIs are explicitly not exactly-once.
- The difference between source validity at the event, observed evidence time, and later reassessment.
- How an unapproved attachment invalidates an old review snapshot without granting itself authority.
- Why UNKNOWN reporting status remains a live obligation even with a raw N flag.
- How to move to PostgreSQL without inheriting pooled-connection tenant context or RLS-owner bypass.

## Unexpected change exercise

If a new sensor bulletin arrives, preserve original measurements and decisions; link affected source/device
versions to reassessment tasks. Do not subtract or add a guessed correction and silently rewrite history.
If a customer requires dual approval, qualify distinct identities, roles and binding to the same immutable
bundle; two authentication factors do not create a second signer. Both are deferred production work, not
configuration switches this demo already supports.
