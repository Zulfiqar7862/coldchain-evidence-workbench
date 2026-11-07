# Low-level design / implemented contract

Read [`store.py`](../workbench/store.py) for exact schema and [`api.py`](../workbench/api.py)
for the generated `/openapi.json` contract. No hidden endpoint performs a product disposition.

## Data model

| Table | Key / immutable content | Notes |
|---|---|---|
| `actors` | actor ID, tenant, role, token hash, expiry, active | Trusted CLI administration; only mutable control table |
| `cases` | composite `(tenant, case ID)`, original payload, raw flag, created | Payload: synthetic marker, exact scope, event time, observation |
| `documents` | integer ID, tenant/case, kind, scope/effectivity/citation metadata, bytes, SHA, supersedes | JSON UTF-8 attachments <=64 KiB; bytes never fetched from caller URL |
| `document_replacements` | replacement document / prior document | Explicit many-source reconciliation; inactive until replacement approval |
| `approvals` | document ID, authenticated QA actor, timestamp | One local synthetic approval; no client-approved flag |
| `bundles` | tenant/case, parent ID, snapshot, result, source revision, created, hash | Every evaluation appends; captured docs and checks included |
| `resolutions` | task's bundle/reason, approved doc ID, resolved bundle, actor | Unique bundle/reason; completion is an event, old task remains OPEN historically |
| `acknowledgements` | unique bundle, authenticated actor, label/outcome, idempotency key/hash | Local review only; not legal signing |
| `obligations` | append-only tenant/case assessments, reportability, deadline, status, basis/actor | Current state is maximum ID **per tenant/case**, not case outcome |

All except `actors` and schema metadata reject application UPDATE/DELETE using triggers.
Triggers are not a privileged-admin security boundary. Foreign keys are enabled per connection.
Case IDs are unique **within a tenant**, with composite tenant/case foreign keys. The same public ID
can be created independently in two tenants. Missing and inaccessible case reads have the same response;
a duplicate conflict concerns only the caller's own tenant. Numeric document/bundle sequence IDs remain
global internal surrogates; access is always tenant-scoped (no claim to hide aggregate allocation volume).

All stored instants are normalized aware UTC ISO-8601 strings; UI displays Europe/Berlin explicitly.
Source validity uses `effective_from <= event_at < effective_to`. No end-date guessing or revision ordering.

## States and policy gates

`Raw input → immutable case + UNKNOWN/PENDING obligation` is one transaction.
`Y`, `N`, blank, `NOT_REQUIRED` and unknown raw strings all remain unqualified UNKNOWN.
The imported optional deadline is a triage input, not a programme-derived legal deadline.

`Attached → QA-approved → active` is independent of applicability. An approved replacement explicitly
names one or more earlier sources of the same kind/case/tenant; only approved replacements deactivate predecessors.
QA sees proposed predecessor IDs, exact scope and effective interval in both the document API and
UI/approval confirmation **before** approval. Two concurrently active applicable SOPs create an ambiguity; neither latest document ID nor name wins.
Study content must explicitly identify `study_type=excursion` for this evaluator.

```mermaid
sequenceDiagram
  actor Operator
  participant API
  participant DB as Tenant-scoped store
  participant Eval as Pure evaluator
  actor QA
  Operator->>API: Create synthetic case
  API->>DB: BEGIN IMMEDIATE / insert case + UNKNOWN obligation / COMMIT
  Operator->>API: Attach source bytes (unapproved)
  QA->>API: Approve source for synthetic local demonstration
  API->>DB: Append approval under authenticated QA role
  QA->>API: Evaluate case
  API->>DB: Capture original payload + verified active source bytes
  DB->>Eval: Explicit snapshot only
  Eval-->>DB: Checks + candidates + unresolved tasks
  DB-->>API: Append hash-checked linked bundle
  QA->>API: Acknowledge expected bundle + hash + idempotency key
  API->>DB: Verify latest version / revision / source hashes / no tasks
  DB-->>API: Atomic local acknowledgement; notification untouched
```

The evaluator returns `EVIDENCE_REQUIRED`, `WITHIN_SYNTHETIC_POLICY` or
`OUTSIDE_SYNTHETIC_POLICY`. None is a disposition or auto-closure. Missing identity, study,
SOP authority, exposure relationship and batch completeness have distinct reason codes.
Each task has reason, required role, evidence requested, completion criterion, source citation and status.
Observation blockers cannot be cleared by document text: immutable bad observations need a new intake
case with corrected approved upstream evidence; generalized corrected-input reassessment is deferred.

Structured policy has nullable lower/upper bound (`gt/ge/lt/le`), nonnegative per-event minutes, nullable
cumulative minutes, explicit approved relationship, and an extra-constraints list. At least one bound is
required. Wrong directions, reversed bounds, strings/booleans/nonfinite measurements fail validation.
Completeness and sensor uncertainty flags must be strict booleans. Unknown history is not a zero value.
Cumulative history requires complete approved history content. Unmodeled extra constraints block support.
No prose parser, mean kinetic temperature calculation, clinical threshold inference or reset counting exists.

## Interface summary

All `/api` endpoints require Bearer authentication; tenant is derived server-side.

| Operation | Path | Role |
|---|---|---|
| Read membership/cases/documents/bundles/obligations | `GET /api/me`, `/api/cases`, `/api/cases/{id}/...`, `/api/bundles/{id}` | Any authenticated tenant member |
| Import case | `POST /api/cases` | Operator |
| Attach source | `POST /api/cases/{id}/documents` | Operator or QA |
| Local source approval | `POST /api/cases/{id}/documents/{doc}/approval` | QA |
| Capture evaluation | `POST /api/cases/{id}/evaluations` | Operator or QA |
| Resolve task | `POST /api/cases/{id}/resolutions` | QA |
| Local review acknowledgement | `POST /api/cases/{id}/acknowledgements` | QA |
| Replay | `GET /api/bundles/{id}/replay` | Any authenticated tenant member |
| Qualified local notification assessment | `POST /api/cases/{id}/obligations` | Regulatory |

401 invalid/missing/expired key; 403 inaccessible object/role; 422 invalid typed body;
409 domain/integrity/state/duplicate conflict; 413 oversized body; 503 storage operational error.
JSON body reference IDs must be positive integers: strings, floats and booleans are rejected rather
than coerced. All numeric HTTP references are bounded to SQLite signed-64-bit positive IDs; oversized
values return 422 before SQL binding. URL path integers are parsed separately (not strict JSON types). Unknown fields in write models are rejected. Extra query strings such as `tenant=...` cannot change membership.
`GET /healthz` is liveness only; it does not prove database readiness.

## Transactions, retries and concurrency

Every store operation opens a fresh connection and takes `BEGIN IMMEDIATE`; synchronous FULL, foreign
keys ON, timeout 10 seconds, default DELETE journaling. This intentionally trades throughput for a simple
serial order. No WAL mode is enabled: older system SQLite versions have a known WAL-reset issue.
Schema bootstrapping is idempotent for **version 2**, not a general migration engine. Version 1, unknown
versions and unversioned existing databases refuse **before schema changes**. No automatic migration is
implemented; use a new disposable synthetic runtime, or commission a separately reviewed offline migration
that preserves captured hashes and tenant ownership. A fresh runtime is not a migration or data recovery.
Initialization uses SQLite `executescript` (which may commit schema operations); request transactions do not.

An acknowledgement transaction checks membership, case ownership, existing actor/key request,
stored-bundle hash, supplied hash, latest bundle ID, source revision and current source hashes, then
no unresolved tasks, then unique bundle acknowledgement. A repeated identical key returns the recorded
response; different content conflicts. Two concurrent reviewers cannot both acknowledge one bundle.
A new source or approval increments the source revision; stale bundles require reassessment.

Only acknowledgement has request-key retry semantics. Intake has a tenant-unique case ID, source attachment
may duplicate after an uncertain response, and repeated evaluation intentionally creates a new bundle.
Approvals are unique per document, resolutions per original bundle/reason. Clients must reconcile lists
before retrying non-idempotent operations. There is no external side effect/outbox in this version.

`resolve` validates an existing task and a current approved applicable document of its required kind,
then evaluates current evidence in the same transaction. It appends completion only if the reason is gone.
Failure rolls back the new bundle and resolution together. Historical task status is never rewritten.

## Integrity and replay

Source attachments are synthetic JSON objects: duplicate keys (including nested/escaped spellings),
nonfinite numbers/overflow and more than 64 container levels are rejected. Excessive parser recursion
becomes a controlled conflict, not a server exception. This is a resource/interpretation limit, not a
clinical rule. The same parser is used at intake, approval and current source reads. Previously stored
ambiguous sources may therefore be refused; captured old-bundle replay remains separate. No bytes are
normalized or silently repaired.

Source hash is SHA-256 over exact stored content text encoded as UTF-8. The bundle hash covers canonical
JSON of tenant, case, parent, serialized snapshot/result, revision and created timestamp. Canonical JSON
sorts keys, uses compact separators and disallows NaN. Stored bundle reads verify the stored expectation.
Client expected hashes protect against stale or changed review content, not a malicious administrator.

Replay checks supported evaluator version and recalculates only from captured input. Later outcomes,
new source records and new approvals cannot leak backwards. New evidence requires a new linked bundle.
Only evaluator v1 is available; future release work must retain old evaluator implementations or explicitly
refuse old-version replay. A hash match proves neither valid source approval nor pharmaceutical truth.

## Notification state

A Regulatory role may append UNKNOWN, REPORTABLE or NOT_REQUIRED with a nonblank assessment basis.
REPORTABLE requires an explicit aware deadline. Only REPORTABLE can be SENT. Pending UNKNOWN and
REPORTABLE rows remain in the queue, ordered by deadline ascending, missing deadlines last and case ID
as deterministic tie-breaker. NOT_REQUIRED and SENT leave the pending view but remain in history.
No QA acknowledgement changes any obligation row. Notification basis/receipt is asserted text, not approved
attached delivery evidence: verified receipts and programme-policy configuration are production gaps.

## Deferred exact contracts

- **OIDC adapter:** validate issuer/audience/expiry, map immutable subject to approved tenant memberships
  and professional delegations; never accept UI role/tenant. Step-up factors are not additional signers.
- **Delivery outbox:** transactional `(tenant,obligation,assessment_version,channel)` key; sender records
  attempts and external receipt; reconcile uncertain delivery, do not re-send blindly; escalation independent.
- **Source adapter:** `(tenant,system,record_id,source_version,observed_at,effective_at,hash,object_version)`;
  scoped retries/rate limits; unknown attribution quarantined; late bytes invalidate affected snapshots.
- **Retention service:** bundle manifest + versioned source object, legal hold, residency, expiry policy,
  cryptographic anchoring, restore/verifiable cold retrieval test. Local backup is not seven-year compliance.
