# Local operations / production runbook design

## Start, stop, recover

```bash
uv sync --locked
uv run --locked python -m workbench demo
# Ctrl-C to stop. Same runtime is retained.
uv run --locked python -m workbench serve
```

The server binds **127.0.0.1:8174**. The process must not be exposed to the internet or bound to all
interfaces. A second demo can use `demo --runtime .runtime-second --port 8175`; choose an ignored/private
directory for any custom runtime. Bootstrap never overwrites an existing directory. `seed` explicitly
refuses an existing runtime; `demo` reuses its database. A partially created runtime is not silently reset.
Inspect it and use a new directory rather than destroy evidence.

Role keys are valid for 24 hours. To create a fresh independent demo, use a new runtime directory.
For a retained database, a trusted local administrator can provision a new unique actor ID with the
same approved tenant and role using `Store.provision`; no HTTP provisioning endpoint exists. That is a
local-demo facility, not a production identity lifecycle. Revocation requires trusted administrator
access to set the actor's active field to zero. Never share runtime credentials or DB files publicly.

## Back up and restore

```bash
# Target must not exist. Live SQLite backup API; integrity check included.
uv run --locked python -m workbench backup /private/location/workbench-backup.db
```

The backup includes database records and hashed actor keys, not the raw key file. Secure backups as
sensitive: it is not tenant-separated or encrypted by this demo. Do not use a network filesystem for
this single-host SQLite application. Retain the private credential file separately if needed for the
24-hour demo; production identity should not depend on that file.

Restore by stopping the server and copying the backup to a **new** runtime directory as `workbench.db`.
Do not overwrite a live database. Start with `serve --runtime PATH`, authenticate an authorized retained
or newly provisioned local actor, check pending obligations, inspect bundle hashes and replay known
bundles. A test restores a real backup into a new DB and verifies replay plus queue preservation.
Local integrity checks are not legal retention validation or a guaranteed recovery-point objective.

## If something fails at 03:00

1. **Do not change a clinical decision.** There is no clinical decision function in this build.
2. Check liveness (`GET /healthz`). It only proves HTTP process liveness, not database readiness.
3. Use an authorized key to query `GET /api/obligations` independently. Preserve the response and check
   earliest pending deadline and UNKNOWN cases. Avoid putting keys or source text in logs.
4. If source assembly fails, do not hide clocks, clear tasks or switch to an unqualified source.
   Record the reason and involve the required QA role. Source/bundle integrity errors are stop signals.
5. If storage returns 503, check disk space, filesystem errors and lock contention. Preserve the DB,
   stop nonessential work, use the backup API where safe. Do not delete journal files or edit outcomes.
6. If an acknowledgement response was lost, retry **the identical** bundle/hash/key. Do not generate
   a fresh key blindly. For source upload/evaluation, reconcile lists before retry; they are not idempotent.
7. Changed sources require a new evaluation. Old bundles must remain reconstructable; original replay
   and reassessment answer different questions.
8. Restore into a new path and verify integrity, obligation count/state and known bundle replay before
   resuming. Escalate any missing evidence instead of recreating it from remembered outcome strings.

## Monitoring: what exists and what is designed

**Exists:** liveness endpoint; authenticated queue/history APIs; startup/errors via Uvicorn logs;
source and bundle integrity checks on use; explicit errors; reproducible tests and real-socket smoke.
Access logging is disabled to avoid careless sensitive-route logging. No dashboard/alert daemon exists.

**Production design:** structured redacted events with correlation ID, actor/tenant pseudonymous IDs,
operation/reason/evaluator version; audit access denials and authority changes; metrics for oldest UNKNOWN
assessment, deadline slack, missed deadlines, source freshness, task age by reason/role, source integrity
failures, evaluation latency, queue starvation per tenant, DB lock waits, error rate, disk growth, backup
age, restore time and inspector retrieval completeness. Pager thresholds require approved programme
semantics and measured workload, not invented default legal deadlines.

## Change qualification

Freeze code, lockfile, evaluator version, source mappings and policy versions. Review negative tests and
explain every change on an independently QA-reviewed historical corpus, with total evaluated and excluded
counts. Run tenant-denial and failure/recovery tests before each change. Pilot one tenant in shadow mode,
compare observations without automatic dispositions, then permit only qualified operations under a
rollback plan. Reverting software must not rewrite already issued bundles, notices or human decisions.
