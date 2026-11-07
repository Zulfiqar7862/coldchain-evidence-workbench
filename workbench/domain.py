"""Pure, versioned educational evaluator. No I/O, clock, LLM or historical outcomes."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError, model_validator

VERSION = "synthetic-envelope/1"
Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Positive = Annotated[float, Field(strict=True, allow_inf_nan=False, ge=0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class Observation(StrictModel):
    min_c: Number
    max_c: Number
    duration_minutes: Positive
    complete: StrictBool
    uncertainty_resolved: StrictBool

    @model_validator(mode="after")
    def ordered(self):
        if self.min_c > self.max_c:
            raise ValueError("reversed measurements")
        return self


class Bound(StrictModel):
    op: Literal["gt", "ge", "lt", "le"]
    value: Number


class Policy(StrictModel):
    lower: Bound | None
    upper: Bound | None
    duration_minutes: Positive
    cumulative_minutes: Positive | None
    relationship_approved: StrictBool
    extra_constraints: list[str]

    @model_validator(mode="after")
    def bounded(self):
        if self.lower is None and self.upper is None:
            raise ValueError("at least one explicit bound required")
        if self.lower and self.lower.op not in {"gt", "ge"}:
            raise ValueError("wrong lower direction")
        if self.upper and self.upper.op not in {"lt", "le"}:
            raise ValueError("wrong upper direction")
        if self.lower and self.upper and self.lower.value >= self.upper.value:
            raise ValueError("empty or reversed range")
        return self


class History(StrictModel):
    complete: StrictBool
    prior_minutes: Positive


TASKS = {
    "IDENTITY_UNVERIFIED": (
        "QA",
        "Approved identity mapping for exact product, strength and presentation.",
        "identity",
    ),
    "STUDY_APPLICABILITY": (
        "QA",
        "Readable approved study and scope verification; reject wrong presentation or study type.",
        "study",
    ),
    "SOP_AUTHORITY": (
        "QA",
        "One approved governing SOP/annexure set for both sites and event time; resolve overlaps explicitly.",
        "sop",
    ),
    "EXPOSURE_RELATIONSHIP": (
        "QA",
        "Approved explicit relationship of per-event and cumulative limits; clarify reuse, do not infer it.",
        "exposure",
    ),
    "BATCH_HISTORY": (
        "QA",
        "Complete approved batch exposure history and explicit completeness attestation.",
        "history",
    ),
    "INVALID_MEASUREMENTS": (
        "QA",
        "Finite ordered measured observations; recover original measured data.",
        "observation",
    ),
    "INCOMPLETE_OBSERVATIONS": (
        "QA",
        "Resolve telemetry gaps/interpolation and sensor uncertainty using approved evidence.",
        "observation",
    ),
    "UNSUPPORTED_CONSTRAINT": (
        "QA",
        "Qualify an evaluator for every additional constraint, or keep review blocked.",
        "exposure",
    ),
    "REAL_POLICY_UNSUPPORTED": (
        "QA",
        "This public evaluator accepts synthetic educational policies only.",
        "exposure",
    ),
}


def task(code, documents):
    role, request, kind = TASKS[code]
    citations = sorted(
        {d.get("citation", "unlocated candidate") for d in documents if d.get("kind") == kind}
    )
    return {
        "reason_code": code,
        "required_role": role,
        "evidence_requested": request,
        "completion_criterion": "Approved attached bytes of the required kind, exact scope and event validity; re-evaluation must resolve the reason.",
        "source_citation": "; ".join(citations) or f"synthetic-input:{kind} (missing)",
        "status": "OPEN",
    }


def applies(document, snapshot):
    try:
        event = datetime.fromisoformat(snapshot["event_at"].replace("Z", "+00:00"))
        start = datetime.fromisoformat(document["effective_from"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(document["effective_to"].replace("Z", "+00:00"))
        return (
            event.tzinfo is not None
            and start <= event < end
            and document.get("scope") == snapshot["scope"]
            and document.get("verified") is True
            and document.get("approved") is True
            and bool(document.get("content", "").strip())
        )
    except (KeyError, ValueError, TypeError):
        return False


def evaluate(snapshot):
    """Output is arithmetic support, never a pharmaceutical disposition."""
    docs = snapshot.get("documents", [])
    reasons = []
    if snapshot.get("synthetic") is not True:
        reasons.append("REAL_POLICY_UNSUPPORTED")
    try:
        observation = Observation.model_validate(snapshot.get("observation"))
        if not observation.complete or not observation.uncertainty_resolved:
            reasons.append("INCOMPLETE_OBSERVATIONS")
    except ValidationError:
        observation = None
        reasons.append("INVALID_MEASUREMENTS")
    selected = {}
    for kind, code in [
        ("identity", "IDENTITY_UNVERIFIED"),
        ("study", "STUDY_APPLICABILITY"),
        ("sop", "SOP_AUTHORITY"),
        ("exposure", "EXPOSURE_RELATIONSHIP"),
    ]:
        applicable = [
            d
            for d in docs
            if d.get("kind") == kind
            and applies(d, snapshot)
            and (kind != "study" or d.get("study_type") == "excursion")
        ]
        if len(applicable) != 1:
            reasons.append(code)
        else:
            selected[kind] = applicable[0]
    policy = None
    if "exposure" in selected:
        try:
            policy = Policy.model_validate(selected["exposure"].get("policy"))
            if not policy.relationship_approved:
                reasons.append("EXPOSURE_RELATIONSHIP")
            if policy.extra_constraints:
                reasons.append("UNSUPPORTED_CONSTRAINT")
        except ValidationError:
            reasons.append("EXPOSURE_RELATIONSHIP")
    history = None
    # Completeness is required independently of policy discovery.
    try:
        history = History.model_validate(snapshot.get("history"))
        history_docs = [d for d in docs if d.get("kind") == "history" and applies(d, snapshot)]
        if not history.complete or len(history_docs) != 1:
            reasons.append("BATCH_HISTORY")
    except ValidationError:
        reasons.append("BATCH_HISTORY")
    candidates = []
    for d in docs:
        rejected = []
        if d.get("scope") != snapshot.get("scope"):
            rejected.append("SCOPE_MISMATCH")
        if d.get("kind") == "study" and d.get("study_type") != "excursion":
            rejected.append("WRONG_STUDY_TYPE")
        if d.get("approved") is not True:
            rejected.append("NO_APPROVAL")
        if d.get("verified") is not True or not d.get("content", "").strip():
            rejected.append("SOURCE_NOT_VERIFIED")
        if not applies(d, snapshot) and not rejected:
            rejected.append("OUTSIDE_EFFECTIVE_INTERVAL")
        candidates.append(
            {
                "id": d.get("id"),
                "kind": d.get("kind"),
                "citation": d.get("citation"),
                "eligible": not rejected,
                "rejections": rejected,
            }
        )
    tasks = [task(code, docs) for code in sorted(set(reasons))]
    if tasks:
        return {
            "version": VERSION,
            "recommendation": "EVIDENCE_REQUIRED",
            "tasks": tasks,
            "checks": [],
            "candidates": candidates,
        }
    assert observation is not None and policy is not None
    checks = []
    for bound, value in [(policy.lower, observation.min_c), (policy.upper, observation.max_c)]:
        if bound:
            comparison = {
                "ge": value >= bound.value,
                "gt": value > bound.value,
                "le": value <= bound.value,
                "lt": value < bound.value,
            }[bound.op]
            checks.append(
                {"value": value, "op": bound.op, "limit": bound.value, "passed": comparison}
            )
    checks.append(
        {
            "value": observation.duration_minutes,
            "op": "le",
            "limit": policy.duration_minutes,
            "passed": observation.duration_minutes <= policy.duration_minutes,
        }
    )
    if policy.cumulative_minutes is not None:
        assert history is not None
        total = history.prior_minutes + observation.duration_minutes
        checks.append(
            {
                "value": total,
                "op": "le",
                "limit": policy.cumulative_minutes,
                "passed": total <= policy.cumulative_minutes,
            }
        )
    return {
        "version": VERSION,
        "recommendation": "WITHIN_SYNTHETIC_POLICY"
        if all(c["passed"] for c in checks)
        else "OUTSIDE_SYNTHETIC_POLICY",
        "tasks": [],
        "checks": checks,
        "candidates": candidates,
    }
