# Verification ledger and honest boundaries

**Local follow-up: 7 November 2026 (Europe/Berlin); changes awaiting independent review, not pushed.**
Start with the [company reference](company-reference.md) for meaning, roles and requirement-to-code/test
mapping. This page owns exact execution results. Logs remain private outside Git. No result below is
clinical qualification, proof of every possible input, or a production-readiness certificate.

## Current commands actually executed

From repository root, with separate private coverage files per interpreter:

| Exact command | Exit | Observed result |
|---|---:|---|
| `uv sync --locked` | 0 | Locked environment synchronized |
| `uv run --locked python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **144 passed**, Python **3.14.10**; **671 statements, 69 missed, 90%** |
| `uv run --isolated --locked --python 3.12 python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **144 passed**, Python **3.12.16**; **720 statements, 68 missed, 91%** |
| `uv run --isolated --locked --python 3.13 python -m pytest -W error::ResourceWarning --cov=workbench --cov-report=term-missing` | 0 | **144 passed**, Python **3.13.5**; **720 statements, 68 missed, 91%** |
| `uv run --locked ruff check .` | 0 | All checks passed |
| `uv run --locked ruff format --check .` | 0 | Formatting clean |
| `npm ci --ignore-scripts --no-audit` | 0 | Locked development-only DOM dependencies; no install scripts/browser process |
| `npm test` | 0 | **23 passed** on Node **24.22.1**: 15 transport/session races + 8 actual-markup DOM/CSS tests |
| `npm audit --audit-level=low` | 0 | Zero known vulnerabilities |
| `uv run --locked python -m scripts.smoke` | 0 | Real loopback HTTP; auth/evaluation/QA acknowledgement; executable four-task tutorial; old tasks preserved; repeat tutorial refused without writes; independent queue survives full process restart; original replay and empty other tenant |
| `uv run --locked python -m pip_audit -r requirements.txt --require-hashes --disable-pip` | 0 | No known vulnerabilities in hash-pinned runtime export |
| `uv run --locked python -m pip_audit` | 0 | No known vulnerabilities in installed runtime + development dependencies |
| `node --check workbench/static/app.js` | 0 | Syntax accepted; not visual rendering |
| `uv run --locked python -m compileall -q workbench scripts` | 0 | Compilation accepted; not full static typing |
| `pdfinfo docs/position-paper.pdf` | 0 | Existing printable position paper remains **3 A4 pages** |

Suite composition: **43 API + 27 contract + 3 demo/backup + 34 domain + 5 reference/text + 32 store = 144**.
Contract tests span HTTP and Store; they are not double-counted. The 112-test published baseline is
historical, not the current total. Coverage statement accounting differs across Python versions; never
combine the 3.14 denominator with 3.12/3.13. Subprocess CLI/tutorial code is exercised but is not included
in `--cov=workbench`; CLI in-process coverage remains 0%. This is statement coverage, not branch/safety coverage.

### What the text tests do—and do not do

`tests/test_reference.py` checks local Markdown links/anchors/assets, real named Python test references,
one company entrypoint, retained synthetic/qualification boundaries, real tutorial CLI help, and removal
of the duplicated embedded program. No external link crawls or private source uploads occur. The smoke
executes the exact documented tutorial command through real HTTP. The checks caught and helped correct a real stale section anchor during consolidation. A human still reviews semantics,
private source citations, design accuracy and terminology; string checks cannot establish clinical truth.

## Clean-source local quickstart and confidentiality checks

A fresh tracked-tree archive (no `.git`, runtime or original inputs) was extracted outside the project.
Using Python 3.12, `python -m venv .venv` and
`python -m pip install --require-hashes -r requirements.txt` succeeded. Package import was verified to
come from that extraction, not the working repository. With runtime dependencies only, the actual
`python -m workbench demo` server and documented four-task client passed through real loopback HTTP.
Then a separate new environment ran `uv sync --locked`, **144 tests** and restart smoke successfully.
The reduced lockfile was tested again from a new archive after removing unused legacy `httpx`;
framework-selected `httpx2` remains. This is executable evidence for both quickstarts, not a clone-only claim.

All reachable Git blobs and candidate tracked bytes, commit author metadata and extracted public PDF
text were scanned for known private-source identifiers, exact generated demo keys, key patterns and
forbidden source/runtime files: **zero findings**. UI code/assets are unchanged from the previously
reviewed captures. This is a bounded scan, not a penetration test or proof no undiscovered secret exists.
Original attachments, source citations, runtime keys, raw logs and the detailed alignment report remain
outside the public tree. Independent review is still required before publishing these changes.

## Current failing-first evidence

- **23 failures / 1 pre-existing pass** before focused contract fixes: seven ambiguous/nonfinite source
  JSON cases, four non-string Credential failures, twelve coercible JSON authority-reference cases.
  The exact-byte-preservation check already passed and is not a new bug discovery. Initial source tests
  used an incorrect expected 400; corrected to the existing documented 409 **before** the accepted RED rerun.
- A source below the byte limit with extreme nesting produced an actual **RecursionError on Python 3.12**;
  Python 3.14 accepted it. Added a consistent 64-container resource limit and converted parser recursion to
  controlled conflict. The first smaller nesting probe was accepted; no 3.14 exception is claimed.
  Final nesting RED on 3.12: **1 failed / 7 passed**; final contract suite **27 passed**. Depth-boundary checks
  were added afterward as verification, not retrospectively called failing discoveries.
- Reference tests: **3 failed / 2 passed** before the consolidated entrypoint and executable tutorial existed.
  The real-socket tutorial command also failed before the module existed. Final reference suite **5 passed**;
  socket smoke now executes all four completions and verifies repeat refusal and unchanged notice state.

No new clinical rule, source approval, legal reporting date or human identity was invented by these fixes.
Exact source bytes stay unchanged. Schema remains v2 and evaluator remains v1: admission is stricter,
not a schema migration or changed arithmetic. Existing ambiguous sources can be refused on current reads;
old captured-bundle replay remains a separate path. See the [LLD](lld.md#integrity-and-replay).

## Preserved independent-review history

The initial implementation had a real transient stale-tenant UI response, hidden proposed supersession
metadata and a global case-ID collision oracle. Focused tests failed before those fixes. Schema v2 now
uses tenant/case keys and refuses v1/unknown/unversioned data without silent migration. Expiry, approval-only
invalidation and endpoint-role tests that already passed were correctly recorded as verification, not discoveries.

A later **v2 real-browser retest failed** with persistent old detail in an empty tenant. Actual-markup
investigation found a genuine empty-list recovery gap. Real-DOM tests failed before synchronous erasure,
selection invalidation, disclosure/form reset and an executing-script build marker were added. No CSS
collision or cache cause was proved. Node tests alone were not treated as visual acceptance.

**Independent browser retest PASSED on `5de05e4087205cd0bcf7f195d0ae60d8f7162e57`, visible UI dom-reset-v3:**
assembly/replay; QA acknowledgement with a pending notice; lock → empty Reader tenant → zero cases and
obligations with empty detail even after Refresh; restore QA → four tasks. The two README screenshots
were manually inspected for secrets and re-encoded without PNG metadata. This follow-up changes no
frontend assets; **no new browser retest is claimed**. Full chronological detail and initial scaffold/TDD
limitations remain in the [honest AI log](ai-working-log.md), rather than duplicated here.

## Capability status and exclusions

| Capability | Status |
|---|---|
| Tenant/role enforcement, source hashes/scope/effectivity/approval gates | Implemented and locally negative-tested; teaching approvals only |
| Explicit bounds, uncertainty, unknown history and role evidence tasks | Implemented with invented structured policies; no real clinical policy |
| Immutable linked snapshots, expected-hash review, retries/races, replay | Implemented/tested; integrity and reproducibility are not source truth |
| Independent UNKNOWN/deadline queue, error/restart persistence | Implemented/tested; no reporting calendar, sender or verified receipt |
| Local UI and session erasure | Node regressions executed; earlier independent dom-reset-v3 visual pass only |
| Backup/restore | Implemented/tested locally; not validated long-term retention or HA |
| Professional signing, MFA/dual signers, multilingual regulated output | Deferred; local acknowledgement is not legal signing |
| Real connectors, batch ledger/raw-series completeness, clinical historical comparison | Deferred; no original case outcome comparison executed |
| PostgreSQL/RLS, regional residency, WORM, outbox, fair scheduling, monitoring | Designed/deferred; no multi-host or scale qualification |
| Latest local changes / remote CI | Unpushed; independent review required. Old CI is not evidence for this revision |

No full static type checker, Docker build, production penetration test, representative burst/load/fault
campaign or clinical validation was performed. No test suite covers all possible cases. Historical labels
are not an oracle; three fictional paths cannot establish alert-closure or clinical agreement rates.

**Historical bounded probe only:** before earlier review fixes, 200 loopback queue reads / 8 threads /
three invented cases had zero failures, 0.703 s wall time, 9.568 ms median and 107.708 ms p95. It omitted
write contention, large sources, network outages and real workloads. It is not a current capacity result.

## Previously observed publication and CI

Public source: https://github.com/Zulfiqar7862/coldchain-evidence-workbench (not a deployed service).
Previously published revision: `7aa3ceda8212beb093c957ec78135a3c518faa3e`; default branch
`build/evidence-workbench`. Previously read successful run:
https://github.com/Zulfiqar7862/coldchain-evidence-workbench/actions/runs/42371365226
— 112 pytest + 23 Node tests per Python 3.12/3.13/3.14 job, lint/smoke/audits successful. This is historical
evidence only. No new push, PR, merge, deployment or production/old-repository change occurred in this follow-up.
Monthly Dependabot automatically opened four PRs after the original publication; none was manually
created, merged, closed or changed by this work.
