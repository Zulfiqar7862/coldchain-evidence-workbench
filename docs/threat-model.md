# Threat model and security boundary

**Deployment assumption:** trusted developer workstation, loopback-only server, invented data. This is
not a hardened internet service. Publishing source code does not mean exposing the demo server publicly.

## Assets and adversaries

Protect tenant case contents, source bytes, authority records, notification assessments, role keys and
immutable review snapshots from an unauthenticated web client or a different tenant member. Consider an
operator who can submit malformed or misleading evidence, a stolen key, XSS, retries, stale views and
concurrent reviewers. A local machine/database administrator is trusted in this demo and can bypass
triggers or rewrite data/hashes; production must materially change that boundary.

| Threat | Implemented control / evidence | Remaining gap |
|---|---|---|
| Cross-tenant object/queue read or update | Membership derived from hashed credential; scoped store methods; tenant/case composite keys; API/store negative tests | Single DB, no RLS or separate keys; internal numeric allocation volume not hidden |
| Client claims a role/tenant or omits it | No write-model tenant parameter; forbidden extras; no raw header role trust | Provisioning is a trusted local CLI function |
| Invalid/revoked/expired token | 256-bit random keys, hashed at rest, active + 24h expiry checked on each operation | No OIDC, MFA, refresh/login session system or rate-limited authentication |
| XSS / token theft from storage | Plain text DOM rendering, no dynamic HTML insertion, restrictive CSP, no browser key persistence | An extension/local admin or compromised script can read in-memory credentials |
| Stale asynchronous UI response across logout or case selection | Captured credentials, session/selection/refresh generations; abort on invalidation; post-body checks; deterministic Node race plus actual-markup DOM/CSS regressions; empty-list erasure independent of visibility | Not a substitute for server-side tenant authorization; browser visual retest is separate |
| CSRF / DNS rebinding | No cookies; explicit Authorization header; Host allowlist; no permissive CORS | HTTP only; TLS reverse proxy and production origin policy not implemented |
| Unbounded upload / JSON coercion | 256 KiB streamed body cap; 64 KiB document bytes; strict numeric/boolean validation | UI lists/bundles unpaginated; slow-client resource protection not fully qualified |
| False authority / wrong product study | Attached bytes + QA role approval + exact scope/effectivity + excursion type + conflict gates | Local approval is simulated; no external study approval verification or delegation |
| Empty evidence clears a blocker | Unapproved/blank attachments rejected for completion; approved-kind/scoped evidence + successful reassessment required | Text meaning depends on simulated QA; no clinical fact-verification capability |
| Source/bundle corruption | SHA checks, immutable application triggers, stale revision checks | Not protected against malicious DB admin; no signed/WORM external anchor |
| Retry / race / stale review | Transaction, unique bundle acknowledgement, scoped idempotency key/hash, expected hash and latest revision | Request-key semantics implemented only for acknowledgements |
| Notification hidden by review failure | Independent append-only ledger and read endpoint; real restart and failure regressions | Same database/host availability; no external sender, receipts or escalation daemon |
| Historical leakage / reassessment overwrites | Captured inputs only in pure replay; append-only parent-linked versions | Historical-policy version registry has v1 only; no bitemporal query engine |
| Compromised supply chain | Dependency lock/hashes, audits, pinned CI refs, read-only workflow permissions | Audits do not prove safety; pinned refs still require maintenance/review |

## Public-data boundary

The repository contains invented fixtures and original diagrams only. Do not add private briefs, source
spreadsheets, documents, screenshots with keys, real batch identifiers, transcripts or runtime databases.
`.gitignore` is defense in depth, not a publication review. Check **Git history and staged files**, not only
the working tree. Downloaded bundles are synthetic in this demo; production downloads require separate
retention/access classification.

## Production security gates (not completed)

Independent assessment and penetration test; professional identity/delegation and qualified signing;
MFA vs dual-signature distinction; least-privilege DB roles and tested tenant RLS; origin/TLS policy;
per-tenant regional objects/encryption/retention; key rotation/revocation; access audit events with safe
redaction; dependency maintenance; disaster recovery; regulatory/QA validation. No “production ready”
claim follows from passing the local test suite.
