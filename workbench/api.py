"""Small HTTP adapter. Authentication is not tenant selection."""

import sqlite3
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from fastapi import Path as PathParameter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import AwareDatetime, Field, StrictBool, StringConstraints
from starlette.middleware.trustedhost import TrustedHostMiddleware

from workbench.domain import Number, StrictModel
from workbench.store import Store

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,80}$")]
Hash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
SQLITE_ID_MAX = 2**63 - 1
PositiveId = Annotated[int, Field(strict=True, gt=0, le=SQLITE_ID_MAX)]
PathId = Annotated[int, PathParameter(gt=0, le=SQLITE_ID_MAX)]


class Scope(StrictModel):
    product: Text
    strength: Text
    presentation: Text
    origin: Text
    destination: Text


class ObservationInput(StrictModel):
    # Import can preserve missing values, but evaluator must reject them as safety evidence.
    min_c: Number | str | None
    max_c: Number | str | None
    duration_minutes: Number | str | None
    complete: StrictBool
    uncertainty_resolved: StrictBool


class Payload(StrictModel):
    synthetic: Literal[True]
    scope: Scope
    event_at: AwareDatetime
    observation: ObservationInput


class CaseInput(StrictModel):
    id: Identifier
    payload: Payload
    raw_reportability: str | None = Field(default=None, max_length=100)
    triage_deadline: AwareDatetime | None = None


class DocumentInput(StrictModel):
    kind: Literal["identity", "study", "sop", "exposure", "history"]
    scope: Scope
    effective_from: AwareDatetime
    effective_to: AwareDatetime
    citation: Text
    content: Annotated[str, StringConstraints(min_length=1, max_length=65536)]
    supersedes: PositiveId | list[PositiveId] | None = None


class AcknowledgementInput(StrictModel):
    bundle_id: PositiveId
    expected_hash: Hash
    signer_label: Text
    outcome: Literal["REVIEW_ACCEPTED", "REVIEW_REJECTED"]
    idempotency_key: Text


class ResolutionInput(StrictModel):
    bundle_id: PositiveId
    reason_code: Text
    document_id: PositiveId


class ObligationInput(StrictModel):
    reportability: Literal["UNKNOWN", "REPORTABLE", "NOT_REQUIRED"]
    deadline: AwareDatetime | None
    basis: Text
    status: Literal["PENDING", "SENT"]


class BodyLimit:
    def __init__(self, app, limit=262144):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.limit:
                response = JSONResponse({"detail": "request exceeds 256 KiB"}, status_code=413)
                return await response(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay_receive():
            if messages:
                return messages.pop(0)
            return await receive()

        await self.app(scope, replay_receive, send)


def create_app(path):
    store = Store(path)
    app = FastAPI(
        title="Coldchain Evidence Workbench — SYNTHETIC",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
    )
    app.add_middleware(BodyLimit)
    bearer = HTTPBearer(auto_error=False)

    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    @app.exception_handler(PermissionError)
    async def forbidden(request, exc):
        return JSONResponse({"detail": "operation not authorized"}, status_code=403)

    @app.exception_handler(ValueError)
    async def conflict(request, exc):
        # Domain errors contain no document contents or secrets.
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(sqlite3.IntegrityError)
    async def constraint(request, exc):
        return JSONResponse(
            {"detail": "immutable record or duplicate request conflict"}, status_code=409
        )

    @app.exception_handler(sqlite3.OperationalError)
    async def unavailable(request, exc):
        return JSONResponse(
            {"detail": "storage unavailable; retry with same idempotency key"}, status_code=503
        )

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse(
            {"detail": [{"loc": list(e["loc"]), "type": e["type"]} for e in exc.errors()]},
            status_code=422,
        )

    def actor(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        from fastapi import HTTPException

        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="bearer credential required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            return store.authenticate(credentials.credentials)
        except PermissionError:
            raise HTTPException(
                status_code=401,
                detail="invalid or expired credential",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

    Auth = Annotated[object, Depends(actor)]

    @app.get("/healthz")
    def health():
        # Deliberately liveness only; authenticated reads exercise readiness.
        return {"status": "alive", "mode": "SYNTHETIC_LOCAL_DEMO"}

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        return Response(status_code=204)

    @app.get("/api/me")
    def me(a: Auth):
        return store.identity(a)

    @app.get("/api/cases")
    def cases(a: Auth):
        return store.cases(a)

    @app.post("/api/cases")
    def create_case(body: CaseInput, a: Auth):
        return store.create_case(
            a,
            body.id,
            body.payload.model_dump(mode="json"),
            body.raw_reportability,
            body.triage_deadline.isoformat() if body.triage_deadline else None,
        )

    @app.get("/api/cases/{case_id}")
    def case(case_id: Identifier, a: Auth):
        return store.case(a, case_id)

    @app.get("/api/cases/{case_id}/documents")
    def documents(case_id: Identifier, a: Auth):
        return store.documents(a, case_id)

    @app.post("/api/cases/{case_id}/documents")
    def attach(case_id: Identifier, body: DocumentInput, a: Auth):
        return store.attach(a, case_id, body.model_dump(mode="json"))

    @app.post("/api/cases/{case_id}/documents/{doc_id}/approval")
    def approve(case_id: Identifier, doc_id: PathId, a: Auth):
        return store.approve(a, case_id, doc_id)

    @app.post("/api/cases/{case_id}/evaluations")
    def assemble(case_id: Identifier, a: Auth):
        return store.assemble(a, case_id)

    @app.get("/api/cases/{case_id}/evaluations")
    def bundles(case_id: Identifier, a: Auth):
        return store.bundles(a, case_id)

    @app.get("/api/bundles/{bundle_id}")
    def bundle(bundle_id: PathId, a: Auth):
        return store.bundle(a, bundle_id)

    @app.get("/api/bundles/{bundle_id}/replay")
    def replay(bundle_id: PathId, a: Auth):
        return store.replay(a, bundle_id)

    @app.post("/api/cases/{case_id}/resolutions")
    def resolve(case_id: Identifier, body: ResolutionInput, a: Auth):
        return store.resolve(a, case_id, body.bundle_id, body.reason_code, body.document_id)

    @app.post("/api/cases/{case_id}/acknowledgements")
    def acknowledge(case_id: Identifier, body: AcknowledgementInput, a: Auth):
        return store.acknowledge(
            a,
            case_id,
            body.bundle_id,
            body.expected_hash,
            body.signer_label,
            body.outcome,
            body.idempotency_key,
        )

    @app.get("/api/cases/{case_id}/acknowledgements")
    def acknowledgements(case_id: Identifier, a: Auth):
        return store.acknowledgements(a, case_id)

    @app.get("/api/obligations")
    def queue(a: Auth):
        return store.queue(a)

    @app.get("/api/cases/{case_id}/obligations")
    def obligation_history(case_id: Identifier, a: Auth):
        return store.obligation_history(a, case_id)

    @app.post("/api/cases/{case_id}/obligations")
    def obligation(case_id: Identifier, body: ObligationInput, a: Auth):
        return store.set_obligation(
            a,
            case_id,
            body.reportability,
            body.deadline.isoformat() if body.deadline else None,
            body.basis,
            body.status,
        )

    static = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/")
    def home():
        return FileResponse(static / "index.html")

    return app
