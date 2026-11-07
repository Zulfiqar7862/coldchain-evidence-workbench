# Framework and engineering research

Consulted 7 November 2026 (Europe/Berlin). These are generic public sources; no private case
content was sent to a web service. Repository stars are deliberately not reported: fetch-provider
metadata was sparse and popularity is not a safety or maintenance guarantee.

## Decisions

| Choice | Sources actually consulted | Decision and consequence |
|---|---|---|
| FastAPI + Pydantic | [FastAPI repository](https://github.com/fastapi/fastapi), [security tutorial](https://fastapi.tiangolo.com/tutorial/security/first-steps/), [Pydantic types](https://docs.pydantic.dev/latest/api/types/), [Pydantic security](https://github.com/pydantic/pydantic/security) | Typed HTTP with a small pure domain core. Security helpers parse credentials; they do **not** prove token validity, role or tenant membership. Implemented server-side lookup. Strict/finite validation, forbidden extras, body bounds and safe validation responses matter. |
| Not Django for this slice | [Django repository](https://github.com/django/django), [official transactions](https://docs.djangoproject.com/en/6.0/topics/db/transactions/) | Django is a credible choice for a production workbench with accounts, administration and migrations. It has more facilities than this bounded slice uses. Chose a smaller explicit adapter, while accepting that full identity/admin/migrations are deferred, not automatically solved. |
| SQLite now, PostgreSQL later | [Python sqlite3 docs](https://docs.python.org/3/library/sqlite3.html), [SQLite WAL documentation](https://www.sqlite.org/wal.html), [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) | Zero database setup and inspectable transactions. Explicitly single-host; reads also serialized. DELETE journal avoids relying on a patched WAL library. PostgreSQL/RLS needs a real migration and tests; owners/superusers can bypass row policies unless properly configured. |
| No LLM / workflow agent | [OWASP authorization guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) plus the deterministic domain boundary | Retrieval and authority are different. No agent framework is needed to compare a signed-off structured teaching envelope; an agent would expand the trusted surface and introduce variability without solving authority. Any future retrieval tool produces candidates, not permissions. |
| uv lock + hash export | [uv locking/sync documentation](https://docs.astral.sh/uv/concepts/projects/sync/) | `--locked` refuses dependency drift. A hashed runtime requirements export gives a plain-venv path. Audit the runtime **and** development environment, not just first-party code. |
| Least-privilege CI | [GitHub workflow hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions) | `contents: read`, no deployment secrets, `persist-credentials: false`, full-SHA action pins verified with remote refs; no `pull_request_target`. Configured jobs are not observed runs. |

## Concrete research changed the build

- SQLite's WAL documentation describes a WAL-reset race fixed in patched versions. The box's SQLite
  reports **3.46.1**. Rather than assume an unverified vendor backport, this demo never enables WAL.
  It uses rollback journaling and short serialized transactions. Revisit only after checking the actual
  deployed SQLite build, not just a Python version.
- FastAPI's tutorial explicitly distinguishes extracting a bearer string from validating it. The app
  hashes a locally generated high-entropy key and checks active membership/expiry/role per operation;
  a raw tenant string cannot grant access.
- Tests exposed boolean-to-number coercion at the HTTP boundary. The field now uses a strict finite
  numeric type; a boolean cannot quietly become a temperature of one degree.
- An installed-dependency audit found Pillow 12.3.0 advisories in the **development asset tool**, even
  though runtime dependencies audited clean. The lock now uses Pillow 13.0.0; a subsequent full audit
  returned no known vulnerabilities. An audit is point-in-time coverage, not proof of no vulnerabilities.
- The current Starlette TestClient emitted a deprecation warning when only `httpx` was installed;
  adding its supported `httpx2` test adapter removed the warning. Real-socket smoke tests avoid making
  TestClient compatibility the only execution evidence.

## Dependency and licensing policy

Core direct dependencies: FastAPI (MIT), Pydantic (MIT), Uvicorn (BSD-3-Clause).
Python's SQLite binding is standard-library code; SQLite itself is public domain.
The lock pins exact versions and distribution hashes. No code, licenses or assets were copied from
another case-study repository. The MIT project license applies only to original project code/assets;
third-party packages retain their own licenses. No dependency source or web article is vendored.

CI action refs checked with public read-only `git ls-remote`:

- `actions/checkout` v4 → `11d5960a326750d5838078e36cf38b85af677262`
- `actions/setup-python` v5 → `a26af69be951a213d495a4c3e4e4022e16d87065`
- `astral-sh/setup-uv` v6 → `d0d8abe699bfb85fec6de9f7adb5ae17292296ff`

The Starlette documentation fetch failed at the provider; the installed TestClient warning and a
successful rerun established the local compatibility observation. No missing page was treated as proof
that documentation did not exist. We did not install broad “agent frameworks” merely to list them.
