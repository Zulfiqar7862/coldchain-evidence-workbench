# Cost, scaling and rollout — design, not achieved targets

Original private business targets and their source citations are retained outside this public repository.
This public edition does not republish actual customer volumes, contractual limits, pricing or timelines.

## Cost accounting

The selected implementation makes **no model or embedding calls**. That removes inference spend, not
operating cost. Separate:

1. Model inference + serving retrieval (zero calls in this slice).
2. Intake/validation and source adapters.
3. Raw-series/source storage, replicas, backup and restore.
4. Index construction/maintenance and regional separation.
5. Long-term retention, legal hold, versioned evaluator replay and cold retrieval.
6. Reviewer/regulatory time, administration, security and qualification.

Cost per screened alert and per reviewed case can be stage-specific or inclusive budgets. Obtain a
written accounting decision about double-counted screening and shared retrieval; don't silently choose
one interpretation. Compare quiet/idle and peak months. A permanent model instance is charged when idle.

**Illustrative sizing only:** if there were 2,000 evaluation snapshots/day, 150 KiB each, then one copy
would add about 293 MiB/day, 104 GiB/year, or 731 GiB over seven years before indexes, backups and replicas.
These are invented planning assumptions, not source facts or observed storage growth. Capturing large
source bytes repeatedly scales poorly; production should use immutable deduplicated **tenant-local**
objects plus versioned manifests. Raw sensor telemetry is a separate size and ingestion calculation.

Local compute uses an existing workstation. No cloud cost or throughput measurement establishes
production capacity. CPU, memory, storage, qualified operations and incident handling still have costs.

## Scale and availability gates

| Stage | Entry gate | Exit evidence | Deliberately not assumed |
|---|---|---|---|
| Local synthetic slice | Generated fixtures and isolated runtime | Tests + real-socket smoke + inspectable records | Clinical authority or production capacity |
| Private qualification | Approved source bytes, identity/SOP/history ownership | Independent historical differences with denominators; security assessment | Historical label agreement equals correctness |
| One-tenant shadow pilot | Residency, source attribution, deadlines and professional roles signed off | Source freshness, deadline behavior, task resolution and restore drills | Ability to automate regulated decisions |
| Controlled operational pilot | Qualified signing, reporting delivery/receipts, monitoring and rollback | Independent QA approval and programme-specific compliance evidence | Global qualification from one tenant |
| Multi-tenant/regional rollout | Per-tenant isolation, fair queues, tested PostgreSQL/RLS and per-region objects | Representative burst/failure load, no deadline starvation, retention retrieval tests | A diagram or Dockerfile demonstrates scale |

Business lead-time/closure/retention/deadline/cost/onboarding targets remain **targets** until these
systems operate with valid denominators. This public slice reports no production closure rate.

## Historical evaluation contract

Join outcomes only **after** evaluation using a sealed as-of input set. Keep historical recommendation,
human disposition and new machine support state distinct. Report `N_total`, `N_evaluated`, `N_excluded`
with exclusion reasons, then agreement/difference/needs-review counts over clearly defined denominators.
Explain each material difference with evidence and missing-source limitations. A stratified extract cannot
be used to estimate population closure rates. No original historical corpus is publicly redistributed here.

The three invented fixture results validate paths, not real historical clinical differences. All real-case
outcome comparisons remain **deferred pending authoritative source content and independent QA**.
