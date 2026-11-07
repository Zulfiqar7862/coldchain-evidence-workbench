"""SQLite application boundary: transaction + tenant checks on every operation.

Single-host DELETE journal deliberately avoids relying on a particular WAL patch level.
Application append-only triggers do NOT protect against a database administrator.
"""

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from workbench.domain import VERSION, evaluate


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def now():
    return datetime.now(UTC).isoformat()


def timestamp(value):
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("timezone required")
    return d.astimezone(UTC).isoformat()


@dataclass(frozen=True)
class Credential:
    token: str = field(repr=False)


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.transaction() as db:
            if db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ).fetchone():
                versions = {row[0] for row in db.execute("SELECT version FROM schema_version")}
                if versions != {1}:
                    raise ValueError("unsupported database schema; migration review required")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY);
            INSERT OR IGNORE INTO schema_version VALUES(1);
            CREATE TABLE IF NOT EXISTS actors(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, role TEXT NOT NULL,
              token_hash TEXT UNIQUE NOT NULL, expires TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, payload TEXT NOT NULL,
              created TEXT NOT NULL, raw_flag TEXT);
            CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL,
              case_id TEXT NOT NULL REFERENCES cases(id), kind TEXT NOT NULL, metadata TEXT NOT NULL,
              content TEXT NOT NULL, hash TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS document_replacements(doc_id INTEGER NOT NULL REFERENCES documents(id),
              prior_id INTEGER NOT NULL REFERENCES documents(id), PRIMARY KEY(doc_id,prior_id));
            CREATE TABLE IF NOT EXISTS approvals(doc_id INTEGER PRIMARY KEY REFERENCES documents(id),
              actor TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS bundles(id INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL,
              case_id TEXT NOT NULL REFERENCES cases(id), parent_id INTEGER REFERENCES bundles(id),
              snapshot TEXT NOT NULL, result TEXT NOT NULL, revision TEXT NOT NULL,
              created TEXT NOT NULL, hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS acknowledgements(id INTEGER PRIMARY KEY AUTOINCREMENT,
              tenant TEXT NOT NULL, case_id TEXT NOT NULL, bundle_id INTEGER UNIQUE NOT NULL REFERENCES bundles(id),
              actor TEXT NOT NULL, signer_label TEXT NOT NULL, outcome TEXT NOT NULL,
              request_key TEXT NOT NULL, request_hash TEXT NOT NULL, created TEXT NOT NULL,
              UNIQUE(tenant,actor,request_key));
            CREATE TABLE IF NOT EXISTS obligations(id INTEGER PRIMARY KEY AUTOINCREMENT, tenant TEXT NOT NULL,
              case_id TEXT NOT NULL REFERENCES cases(id), reportability TEXT NOT NULL, deadline TEXT,
              status TEXT NOT NULL, basis TEXT NOT NULL, actor TEXT NOT NULL, created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS resolutions(id INTEGER PRIMARY KEY AUTOINCREMENT,tenant TEXT NOT NULL,
              case_id TEXT NOT NULL,bundle_id INTEGER NOT NULL REFERENCES bundles(id),reason TEXT NOT NULL,
              doc_id INTEGER NOT NULL REFERENCES documents(id),resolved_bundle INTEGER NOT NULL REFERENCES bundles(id),
              actor TEXT NOT NULL, created TEXT NOT NULL,UNIQUE(bundle_id,reason));
            CREATE INDEX IF NOT EXISTS cases_tenant ON cases(tenant,id);
            CREATE INDEX IF NOT EXISTS documents_case ON documents(tenant,case_id,id);
            CREATE INDEX IF NOT EXISTS bundles_case ON bundles(tenant,case_id,id DESC);
            CREATE INDEX IF NOT EXISTS obligations_case ON obligations(tenant,case_id,id DESC);
            """)
            for table in (
                "document_replacements",
                "cases",
                "documents",
                "approvals",
                "bundles",
                "acknowledgements",
                "obligations",
                "resolutions",
            ):
                for op in ("UPDATE", "DELETE"):
                    db.execute(
                        f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_{op.lower()} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append-only'); END"
                    )
        self.path.chmod(0o600)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            if db.in_transaction:
                db.execute("COMMIT")
        except BaseException:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
        finally:
            db.close()

    def provision(self, actor_id, tenant, role):
        """Local administrator CLI only, deliberately not exposed by HTTP."""
        if not all(isinstance(x, str) and x.strip() for x in (actor_id, tenant, role)):
            raise ValueError("explicit actor, tenant and role required")
        if role not in {"Operator", "QA", "Regulatory", "Reader"}:
            raise ValueError("unknown role")
        token = secrets.token_urlsafe(32)
        expires = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
        with self.transaction() as db:
            db.execute(
                "INSERT INTO actors(id,tenant,role,token_hash,expires) VALUES(?,?,?,?,?)",
                (actor_id, tenant, role, digest(token), expires),
            )
        return token

    def _actor(self, db, credential, roles=None):
        if not isinstance(credential, Credential) or not credential.token:
            raise PermissionError("authentication required")
        row = db.execute(
            "SELECT * FROM actors WHERE token_hash=? AND active=1 AND expires>?",
            (digest(credential.token), now()),
        ).fetchone()
        if not row or not row["tenant"] or (roles is not None and row["role"] not in roles):
            raise PermissionError("operation not authorized")
        return row

    def authenticate(self, token):
        credential = Credential(token) if isinstance(token, str) else None
        with self.transaction() as db:
            self._actor(db, credential)
        return credential

    def identity(self, credential):
        with self.transaction() as db:
            actor = self._actor(db, credential)
            return {k: actor[k] for k in ("id", "tenant", "role", "expires")}

    def _case(self, db, actor, case_id):
        row = db.execute(
            "SELECT * FROM cases WHERE id=? AND tenant=?", (case_id, actor["tenant"])
        ).fetchone()
        if not row:
            raise PermissionError("resource not accessible")
        return row

    def create_case(self, credential, case_id, payload, raw_flag=None, deadline=None):
        if not case_id.strip() or len(case_id) > 80:
            raise ValueError("invalid identifier")
        if payload.get("synthetic") is not True:
            raise ValueError("public demo accepts synthetic records only")
        if set(payload) != {"synthetic", "scope", "event_at", "observation"}:
            raise ValueError("unexpected or missing case fields")
        # Measurements are validated by the evaluator; invalid imported records are not safety evidence.
        payload = json.loads(canonical(payload))
        payload["event_at"] = timestamp(payload["event_at"])
        deadline = timestamp(deadline) if deadline else None
        with self.transaction() as db:
            actor = self._actor(db, credential, {"Operator"})
            db.execute(
                "INSERT INTO cases VALUES(?,?,?,?,?)",
                (case_id, actor["tenant"], canonical(payload), now(), raw_flag),
            )
            db.execute(
                "INSERT INTO obligations(tenant,case_id,reportability,deadline,status,basis,actor,created) VALUES(?,?,?,?,?,?,?,?)",
                (
                    actor["tenant"],
                    case_id,
                    "UNKNOWN",
                    deadline,
                    "PENDING",
                    "Imported flag is unqualified; deadline is an explicit triage input, not a legal calculation.",
                    actor["id"],
                    now(),
                ),
            )
        return {"id": case_id}

    def cases(self, credential):
        with self.transaction() as db:
            a = self._actor(db, credential)
            return [
                dict(r)
                for r in db.execute(
                    "SELECT id,created FROM cases WHERE tenant=? ORDER BY id", (a["tenant"],)
                )
            ]

    def case(self, credential, case_id):
        with self.transaction() as db:
            a = self._actor(db, credential)
            r = self._case(db, a, case_id)
            return {"id": r["id"], "tenant": r["tenant"], "input": json.loads(r["payload"])}

    def attach(self, credential, case_id, document):
        required = {
            "kind",
            "scope",
            "effective_from",
            "effective_to",
            "citation",
            "content",
            "supersedes",
        }
        if set(document) != required:
            raise ValueError("document fields differ from contract")
        if document["kind"] not in {"identity", "study", "sop", "exposure", "history"}:
            raise ValueError("unsupported source kind")
        content = document["content"]
        if not content.strip() or len(content.encode()) > 65536:
            raise ValueError("attached bytes must be nonblank and <=64 KiB")
        data = json.loads(content)
        if not isinstance(data, dict) or data.get("synthetic") is not True:
            raise ValueError("synthetic document object required")
        meta = {k: document[k] for k in required - {"content", "supersedes"}}
        meta["effective_from"] = timestamp(meta["effective_from"])
        meta["effective_to"] = timestamp(meta["effective_to"])
        if meta["effective_from"] >= meta["effective_to"] or not meta["citation"].strip():
            raise ValueError("valid source reference and effective interval required")
        with self.transaction() as db:
            a = self._actor(db, credential, {"Operator", "QA"})
            self._case(db, a, case_id)
            prior = document["supersedes"]
            prior = prior if isinstance(prior, list) else ([prior] if prior is not None else [])
            if len(set(prior)) != len(prior) or any(type(i) is not int or i <= 0 for i in prior):
                raise ValueError("replacement IDs must be distinct positive integers")
            for predecessor in prior:
                row = db.execute(
                    "SELECT kind FROM documents WHERE id=? AND tenant=? AND case_id=?",
                    (predecessor, a["tenant"], case_id),
                ).fetchone()
                if not row or row["kind"] != meta["kind"]:
                    raise ValueError("supersession requires same tenant, case and source kind")
            cur = db.execute(
                "INSERT INTO documents(tenant,case_id,kind,metadata,content,hash,created) VALUES(?,?,?,?,?,?,?)",
                (
                    a["tenant"],
                    case_id,
                    meta["kind"],
                    canonical(meta),
                    content,
                    digest(content),
                    now(),
                ),
            )
            doc_id = cur.lastrowid
            db.executemany(
                "INSERT INTO document_replacements VALUES(?,?)",
                [(doc_id, predecessor) for predecessor in prior],
            )
            return {"id": doc_id, "hash": digest(content), "approved": False}

    def approve(self, credential, case_id, doc_id):
        with self.transaction() as db:
            a = self._actor(db, credential, {"QA"})
            self._case(db, a, case_id)
            row = db.execute(
                "SELECT * FROM documents WHERE id=? AND case_id=? AND tenant=?",
                (doc_id, case_id, a["tenant"]),
            ).fetchone()
            if not row or digest(row["content"]) != row["hash"]:
                raise ValueError("source integrity failure")
            text = json.loads(row["content"]).get("text")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("approval requires substantive attached text")
            db.execute("INSERT INTO approvals VALUES(?,?,?)", (doc_id, a["id"], now()))
        return {"id": doc_id, "approved": True, "qualification": "synthetic local QA approval only"}

    def _documents(self, db, actor, case_id):
        rows = db.execute(
            "SELECT d.*,a.actor AS approver FROM documents d LEFT JOIN approvals a ON a.doc_id=d.id WHERE d.tenant=? AND d.case_id=? ORDER BY d.id",
            (actor["tenant"], case_id),
        ).fetchall()
        superseded = {
            r[0]
            for r in db.execute(
                "SELECT r.prior_id FROM document_replacements r JOIN documents d ON d.id=r.doc_id JOIN approvals a ON a.doc_id=d.id WHERE d.tenant=? AND d.case_id=?",
                (actor["tenant"], case_id),
            )
        }
        replacements = {r["id"]: [] for r in rows}
        for relation in db.execute(
            "SELECT r.doc_id,r.prior_id FROM document_replacements r JOIN documents d ON d.id=r.doc_id WHERE d.tenant=? AND d.case_id=? ORDER BY r.prior_id",
            (actor["tenant"], case_id),
        ):
            replacements[relation["doc_id"]].append(relation["prior_id"])
        documents = []
        for r in rows:
            if digest(r["content"]) != r["hash"]:
                raise ValueError("source integrity failure")
            data = json.loads(r["content"])
            documents.append(
                json.loads(r["metadata"])
                | {
                    "id": r["id"],
                    "content": r["content"],
                    "hash": r["hash"],
                    "verified": True,
                    "approved": r["approver"] is not None and r["id"] not in superseded,
                    "approver": r["approver"],
                    "supersedes": replacements[r["id"]],
                    "policy": data.get("policy"),
                    "study_type": data.get("study_type"),
                    "history": data.get("history"),
                }
            )
        return documents

    def documents(self, credential, case_id):
        with self.transaction() as db:
            a = self._actor(db, credential)
            self._case(db, a, case_id)
            return self._documents(db, a, case_id)

    def _revision(self, db, a, case_id):
        row = db.execute(
            "SELECT COUNT(*) n,COALESCE(MAX(id),0) m FROM documents WHERE tenant=? AND case_id=?",
            (a["tenant"], case_id),
        ).fetchone()
        approved = db.execute(
            "SELECT COUNT(*) FROM approvals a JOIN documents d ON a.doc_id=d.id WHERE d.tenant=? AND d.case_id=?",
            (a["tenant"], case_id),
        ).fetchone()[0]
        return f"{row['n']}:{row['m']}:{approved}"

    @staticmethod
    def _hash_bundle(row):
        return digest(
            canonical(
                {
                    k: row[k]
                    for k in (
                        "tenant",
                        "case_id",
                        "parent_id",
                        "snapshot",
                        "result",
                        "revision",
                        "created",
                    )
                }
            )
        )

    def _bundle(self, db, a, bundle_id):
        row = db.execute(
            "SELECT * FROM bundles WHERE id=? AND tenant=?", (bundle_id, a["tenant"])
        ).fetchone()
        if not row:
            raise PermissionError("resource not accessible")
        if row["hash"] != self._hash_bundle(row):
            raise ValueError("bundle integrity failure")
        return dict(row) | {
            "snapshot": json.loads(row["snapshot"]),
            "result": json.loads(row["result"]),
        }

    def bundle(self, credential, bundle_id):
        with self.transaction() as db:
            return self._bundle(db, self._actor(db, credential), bundle_id)

    def bundles(self, credential, case_id):
        with self.transaction() as db:
            a = self._actor(db, credential)
            self._case(db, a, case_id)
            return [
                self._bundle(db, a, r[0])
                for r in db.execute(
                    "SELECT id FROM bundles WHERE tenant=? AND case_id=? ORDER BY id",
                    (a["tenant"], case_id),
                ).fetchall()
            ]

    def _assemble(self, db, a, case_id):
        row = self._case(db, a, case_id)
        docs = self._documents(db, a, case_id)
        snapshot = json.loads(row["payload"]) | {"documents": docs, "history": None}
        # History values come from approved source bytes, not a typed cleared flag.
        from workbench.domain import applies

        histories = [d for d in docs if d["kind"] == "history" and applies(d, snapshot)]
        if len(histories) == 1:
            snapshot["history"] = histories[0]["history"]
        result = evaluate(snapshot)
        parent = db.execute(
            "SELECT MAX(id) FROM bundles WHERE tenant=? AND case_id=?", (a["tenant"], case_id)
        ).fetchone()[0]
        bundle = {
            "tenant": a["tenant"],
            "case_id": case_id,
            "parent_id": parent,
            "snapshot": canonical(snapshot),
            "result": canonical(result),
            "revision": self._revision(db, a, case_id),
            "created": now(),
        }
        bundle["hash"] = self._hash_bundle(bundle)
        cur = db.execute(
            "INSERT INTO bundles(tenant,case_id,parent_id,snapshot,result,revision,created,hash) VALUES(:tenant,:case_id,:parent_id,:snapshot,:result,:revision,:created,:hash)",
            bundle,
        )
        return self._bundle(db, a, cur.lastrowid)

    def assemble(self, credential, case_id):
        with self.transaction() as db:
            return self._assemble(db, self._actor(db, credential, {"QA", "Operator"}), case_id)

    def replay(self, credential, bundle_id):
        bundle = self.bundle(credential, bundle_id)
        if bundle["result"]["version"] != VERSION:
            raise ValueError("evaluator version unavailable")
        actual = evaluate(bundle["snapshot"])
        return {
            "bundle_id": bundle_id,
            "matches": actual == bundle["result"],
            "result": actual,
            "warning": "Identical arithmetic does not establish evidence truth.",
        }

    def resolve(self, credential, case_id, bundle_id, reason, doc_id):
        with self.transaction() as db:
            a = self._actor(db, credential, {"QA"})
            self._case(db, a, case_id)
            before = self._bundle(db, a, bundle_id)
            if before["case_id"] != case_id:
                raise ValueError("case mismatch")
            tasks = [t for t in before["result"]["tasks"] if t["reason_code"] == reason]
            if not tasks:
                raise ValueError("task absent")
            from workbench.domain import TASKS, applies

            doc = next((d for d in self._documents(db, a, case_id) if d["id"] == doc_id), None)
            if not doc or doc["kind"] != TASKS[reason][2] or not applies(doc, before["snapshot"]):
                raise ValueError("approved applicable attached evidence required")
            after = self._assemble(db, a, case_id)
            if reason in {t["reason_code"] for t in after["result"]["tasks"]}:
                raise ValueError("evidence has not resolved the task")
            db.execute(
                "INSERT INTO resolutions(tenant,case_id,bundle_id,reason,doc_id,resolved_bundle,actor,created) VALUES(?,?,?,?,?,?,?,?)",
                (a["tenant"], case_id, bundle_id, reason, doc_id, after["id"], a["id"], now()),
            )
            return {"status": "COMPLETE", "resolved_bundle": after["id"], "evidence_id": doc_id}

    def acknowledge(
        self, credential, case_id, bundle_id, expected_hash, signer_label, outcome, key
    ):
        if not signer_label.strip() or not key.strip():
            raise ValueError("nonblank reviewer label and idempotency key required")
        if outcome not in {"REVIEW_ACCEPTED", "REVIEW_REJECTED"}:
            raise ValueError("not a disposition API")
        request_hash = digest(canonical([case_id, bundle_id, expected_hash, signer_label, outcome]))
        with self.transaction() as db:
            a = self._actor(db, credential, {"QA"})
            self._case(db, a, case_id)
            existing = db.execute(
                "SELECT * FROM acknowledgements WHERE tenant=? AND actor=? AND request_key=?",
                (a["tenant"], a["id"], key),
            ).fetchone()
            bundle = self._bundle(db, a, bundle_id)
            if bundle["case_id"] != case_id:
                raise ValueError("case mismatch")
            if bundle["hash"] != expected_hash:
                raise ValueError("expected hash mismatch")
            if existing:
                if existing["request_hash"] != request_hash:
                    raise ValueError("idempotency key used with different request")
                return dict(existing)
            latest = db.execute(
                "SELECT MAX(id) FROM bundles WHERE tenant=? AND case_id=?", (a["tenant"], case_id)
            ).fetchone()[0]
            if latest != bundle_id:
                raise ValueError("stale bundle")
            if self._revision(db, a, case_id) != bundle["revision"]:
                raise ValueError("evidence changed; reassessment required")
            # Verify current source bytes too, not just their metadata counters.
            self._documents(db, a, case_id)
            if bundle["result"]["tasks"]:
                raise ValueError("unresolved evidence tasks")
            if db.execute(
                "SELECT 1 FROM acknowledgements WHERE bundle_id=?", (bundle_id,)
            ).fetchone():
                raise ValueError("bundle already acknowledged by another request")
            cur = db.execute(
                "INSERT INTO acknowledgements(tenant,case_id,bundle_id,actor,signer_label,outcome,request_key,request_hash,created) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    a["tenant"],
                    case_id,
                    bundle_id,
                    a["id"],
                    signer_label,
                    outcome,
                    key,
                    request_hash,
                    now(),
                ),
            )
            # No notification state transition here. Deliberately independent.
            return dict(
                db.execute("SELECT * FROM acknowledgements WHERE id=?", (cur.lastrowid,)).fetchone()
            )

    def set_obligation(self, credential, case_id, reportability, deadline, basis, status):
        with self.transaction() as db:
            a = self._actor(db, credential, {"Regulatory"})
            self._case(db, a, case_id)
            if reportability not in {"UNKNOWN", "REPORTABLE", "NOT_REQUIRED"} or status not in {
                "PENDING",
                "SENT",
            }:
                raise ValueError("invalid notification state")
            if not basis.strip():
                raise ValueError("qualified assessment basis required")
            if reportability == "REPORTABLE" and not deadline:
                raise ValueError("explicit qualified deadline required")
            if reportability != "REPORTABLE" and status == "SENT":
                raise ValueError("only reportable obligations may be marked sent")
            deadline = timestamp(deadline) if deadline else None
            db.execute(
                "INSERT INTO obligations(tenant,case_id,reportability,deadline,status,basis,actor,created) VALUES(?,?,?,?,?,?,?,?)",
                (a["tenant"], case_id, reportability, deadline, status, basis, a["id"], now()),
            )
        return {"reportability": reportability, "status": status}

    def queue(self, credential):
        with self.transaction() as db:
            a = self._actor(db, credential)
            return [
                dict(r)
                for r in db.execute(
                    """SELECT o.* FROM obligations o WHERE o.tenant=?
             AND o.id=(SELECT MAX(n.id) FROM obligations n WHERE n.tenant=o.tenant AND n.case_id=o.case_id)
             AND o.reportability!='NOT_REQUIRED' AND o.status='PENDING'
             ORDER BY o.deadline IS NULL,o.deadline,o.case_id""",
                    (a["tenant"],),
                )
            ]

    def obligation_history(self, credential, case_id):
        with self.transaction() as db:
            a = self._actor(db, credential)
            self._case(db, a, case_id)
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM obligations WHERE tenant=? AND case_id=? ORDER BY id",
                    (a["tenant"], case_id),
                )
            ]

    def acknowledgements(self, credential, case_id):
        with self.transaction() as db:
            a = self._actor(db, credential)
            self._case(db, a, case_id)
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM acknowledgements WHERE tenant=? AND case_id=? ORDER BY id",
                    (a["tenant"], case_id),
                )
            ]
