/* No dependency build, no persisted browser key, no clinical decision endpoint. */
"use strict";
let token = "",
  identity = null,
  selectedCase = null,
  bundle = null;
const $ = (id) => document.getElementById(id);
const el = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
function say(message, error = false) {
  $("status").textContent = message;
  $("status").className = "toast" + (error ? " error" : "");
  $("status").hidden = false;
}
// A response belongs to a session, selection and optional refresh lane. Aborting
// saves work; generation checks also protect delayed bodies/abort-ignoring transports.
let sessionGeneration = 0,
  selectionGeneration = 0;
const lanes = new Map(),
  pending = new Set();
class StaleAction extends Error {}
function sessionContext() {
  return {
    session: sessionGeneration,
    token,
    role: identity?.role,
    selection: null,
    lane: null,
  };
}
function caseContext() {
  return {
    ...sessionContext(),
    selection: selectionGeneration,
    caseId: selectedCase,
  };
}
function current(ctx) {
  return (
    ctx.session === sessionGeneration &&
    ctx.token === token &&
    (ctx.selection === null || ctx.selection === selectionGeneration) &&
    (!ctx.lane || lanes.get(ctx.lane) === ctx.generation)
  );
}
function check(ctx) {
  if (!current(ctx)) throw new StaleAction();
}
function cancelWhere(predicate) {
  for (const request of pending)
    if (predicate(request.ctx)) request.controller.abort();
}
function laneContext(name, ctx) {
  check(ctx);
  cancelWhere((c) => c.lane === name);
  const generation = (lanes.get(name) || 0) + 1;
  lanes.set(name, generation);
  return { ...ctx, lane: name, generation };
}
function sessionOnly(ctx) {
  return { ...ctx, selection: null, lane: null };
}
async function api(path, options = {}, ctx = caseContext()) {
  check(ctx);
  const request = { ctx, controller: new AbortController() };
  pending.add(request);
  try {
    const response = await fetch("/api" + path, {
      ...options,
      signal: request.controller.signal,
      headers: {
        Authorization: "Bearer " + ctx.token,
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
    check(ctx);
    const data = await response.json();
    check(ctx);
    if (!response.ok)
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail),
      );
    return data;
  } finally {
    pending.delete(request);
  }
}
const post = (path, data, ctx) =>
  api(
    path,
    {
      method: "POST",
      ...(data ? { body: JSON.stringify(data) } : {}),
    },
    ctx,
  );
function berlin(time) {
  if (!time) return "Unresolved deadline";
  return (
    new Intl.DateTimeFormat("en-GB", {
      timeZone: "Europe/Berlin",
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(time)) + " · Berlin"
  );
}
function button(text, handler, className = "quiet") {
  const b = el("button", text, className);
  b.type = "button";
  b.addEventListener("click", handler);
  return b;
}
async function guarded(action, ctx = caseContext()) {
  try {
    check(ctx);
    await action(ctx);
  } catch (error) {
    if (
      current(ctx) &&
      !(error instanceof StaleAction) &&
      error.name !== "AbortError"
    )
      say(error.message, true);
  }
}
function clearCase() {
  bundle = null;
  for (const id of [
    "evidence-tasks",
    "attachment-list",
    "record-history",
    "candidate-list",
    "measurements",
    "checks",
  ])
    $(id).replaceChildren();
  for (const id of [
    "case-scope",
    "selected-case",
    "recommendation",
    "bundle-hash",
    "bundle-version",
    "task-count",
  ])
    $(id).textContent = "";
  $("bundle-hash").title = "";
  for (const id of [
    "notice-case",
    "notice-basis",
    "notice-deadline",
    "attachment-json",
    "review-label",
  ])
    $(id).value = "";
  $("evaluation-panel").hidden = true;
  $("evaluate").disabled = true;
  $("ack-button").disabled = true;
}
function beginSession(key) {
  cancelWhere(() => true);
  sessionGeneration++;
  selectionGeneration++;
  token = key;
  identity = null;
  selectedCase = null;
  clearCase();
  for (const id of ["case-list", "notification-list"]) $(id).replaceChildren();
  for (const id of ["case-count", "notice-count"]) $(id).textContent = "0";
  $("workspace").hidden = true;
  $("login").hidden = false;
  $("logout").hidden = true;
  $("status").hidden = true;
  $("status").textContent = "";
  $("identity").textContent = "Private by default";
  return sessionContext();
}
$("login-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const key = $("credential").value.trim();
  $("credential").value = "";
  const ctx = beginSession(key);
  guarded(async (ctx) => {
    const me = await api("/me", {}, ctx);
    check(ctx);
    identity = me;
    $("identity").textContent = me.tenant + " / " + me.role;
    $("login").hidden = true;
    $("workspace").hidden = false;
    $("logout").hidden = false;
    await refresh(sessionContext());
  }, ctx);
});
$("logout").addEventListener("click", () => beginSession(""));
async function loadQueue(parent = sessionContext()) {
  const ctx = laneContext("queue", sessionOnly(parent));
  const obligations = await api("/obligations", {}, ctx);
  check(ctx);
  $("notice-count").textContent = obligations.length;
  const table = el("table", undefined, "notification-table");
  const head = el("tr");
  [
    "CASE",
    "REPORTABILITY",
    "EXPLICIT DEADLINE · EUROPE/BERLIN",
    "STATE",
  ].forEach((x) => head.append(el("th", x)));
  const thead = el("thead");
  thead.append(head);
  table.append(thead);
  const body = el("tbody");
  for (const n of obligations) {
    const row = el("tr");
    row.append(
      el("td", n.case_id),
      el("td", n.reportability),
      el("td", berlin(n.deadline)),
      el("td", n.status),
    );
    body.append(row);
  }
  table.append(body);
  $("notification-list").replaceChildren(
    obligations.length
      ? table
      : el(
          "p",
          "No pending obligations in your tenant. Historical assessments remain available through the API.",
          "muted",
        ),
  );
}
async function loadCases(parent = sessionContext()) {
  const ctx = laneContext("cases", sessionOnly(parent));
  const cases = await api("/cases", {}, ctx);
  check(ctx);
  $("case-count").textContent = cases.length;
  $("case-list").replaceChildren();
  const captions = {
    "DEMO-READY": "Verified synthetic support",
    "DEMO-QUESTIONS": "Four unresolved evidence questions",
    "DEMO-OUTSIDE": "Outside the invented envelope",
  };
  for (const c of cases) {
    const b = button(
      "",
      () => guarded(() => selectCase(c.id, ctx), ctx),
      "case-item" + (selectedCase === c.id ? " active" : ""),
    );
    b.append(
      el("strong", c.id),
      el("small", captions[c.id] || "Synthetic case file"),
    );
    $("case-list").append(b);
  }
  if (!selectedCase && cases.length)
    await selectCase(
      cases.some((c) => c.id === "DEMO-READY") ? "DEMO-READY" : cases[0].id,
      ctx,
    );
}
async function refresh(ctx = sessionContext()) {
  // Each lane handles its own errors: failed assembly must not hide clocks.
  await Promise.all([
    guarded(() => loadQueue(ctx), ctx),
    guarded(() => loadCases(ctx), ctx),
  ]);
}
$("refresh").addEventListener("click", () =>
  guarded((ctx) => refresh(sessionOnly(ctx))),
);
async function selectCase(id, parent = sessionContext()) {
  check(parent);
  cancelWhere((c) => c.selection !== null);
  selectionGeneration++;
  selectedCase = id;
  clearCase();
  const ctx = caseContext();
  const c = await api("/cases/" + encodeURIComponent(id), {}, ctx);
  check(ctx);
  $("selected-case").textContent = id;
  const scope = c.input.scope;
  $("case-scope").textContent =
    scope.product +
    " · " +
    scope.strength +
    " · " +
    scope.presentation +
    "\n" +
    scope.origin +
    " → " +
    scope.destination;
  $("notice-case").value = id;
  $("evaluate").disabled = !["QA", "Operator"].includes(ctx.role);
  const obs = c.input.observation;
  $("measurements").replaceChildren();
  for (const [label, value, unit] of [
    ["MINIMUM", obs.min_c, "°C"],
    ["MAXIMUM", obs.max_c, "°C"],
    ["DURATION", obs.duration_minutes, "min"],
  ]) {
    const box = el("div", undefined, "measurement");
    box.append(
      el("span", label),
      el("strong", value === null ? "Unknown" : value + " " + unit),
    );
    $("measurements").append(box);
  }
  document
    .querySelectorAll(".case-item")
    .forEach((b) =>
      b.classList.toggle("active", b.firstChild.textContent === id),
    );
  await loadAttachments(ctx);
  check(ctx);
  const history = await api("/cases/" + id + "/evaluations", {}, ctx);
  check(ctx);
  if (history.length) renderBundle(history[history.length - 1], ctx);
  await loadHistory(history, ctx);
}
function renderBundle(data, ctx = caseContext()) {
  check(ctx);
  bundle = data;
  $("evaluation-panel").hidden = false;
  const result = data.result;
  const labels = {
    WITHIN_SYNTHETIC_POLICY: "SUPPORTED BY SYNTHETIC POLICY",
    OUTSIDE_SYNTHETIC_POLICY: "OUTSIDE SYNTHETIC POLICY",
    EVIDENCE_REQUIRED: "EVIDENCE REQUIRED",
  };
  $("recommendation").textContent =
    labels[result.recommendation] || result.recommendation;
  $("recommendation").className =
    "result" +
    (result.recommendation === "WITHIN_SYNTHETIC_POLICY" ? "" : " warn");
  $("bundle-version").textContent =
    "BUNDLE " + data.id + " / " + result.version;
  $("bundle-hash").textContent = "SHA-256 " + data.hash.slice(0, 24) + "…";
  $("bundle-hash").title = data.hash;
  $("checks").replaceChildren();
  const checks = el("div", undefined, "checks");
  result.checks.forEach((c) =>
    checks.append(
      el(
        "span",
        (c.passed ? "✓ " : "✕ ") + c.value + " " + c.op + " " + c.limit,
        "check" + (c.passed ? "" : " fail"),
      ),
    ),
  );
  $("checks").append(checks);
  $("task-count").textContent = "(" + result.tasks.length + " OPEN)";
  $("evidence-tasks").replaceChildren();
  if (!result.tasks.length)
    $("evidence-tasks").append(
      el(
        "div",
        "✓ No unresolved evidence tasks in this captured synthetic snapshot. QA review remains separate from notification.",
        "empty",
      ),
    );
  for (const task of result.tasks) {
    const card = el("article", undefined, "task"),
      title = el("div", undefined, "task-title");
    title.append(
      el("h4", task.reason_code.replaceAll("_", " ")),
      el("span", task.required_role + " · " + task.status, "tag"),
    );
    card.append(
      title,
      el("p", task.evidence_requested),
      el("small", "Source: " + task.source_citation),
      el("small", "Complete only when: " + task.completion_criterion),
    );
    if (ctx.role === "QA")
      card.append(
        button("Link approved evidence to resolve", () =>
          guarded(async (ctx) => {
            const id = window.prompt(
              "Approved attachment ID for this task. No flag or blank transcription can resolve it:",
            );
            if (id === null) return;
            const resolved = await post(
              "/cases/" + ctx.caseId + "/resolutions",
              {
                bundle_id: data.id,
                reason_code: task.reason_code,
                document_id: Number(id),
              },
              ctx,
            );
            check(ctx);
            say(
              "Task completed with approved synthetic evidence; new bundle " +
                resolved.resolved_bundle +
                ". Original bundle remains unchanged.",
            );
            await selectCase(ctx.caseId, ctx);
          }, ctx),
        ),
      );
    $("evidence-tasks").append(card);
  }
  $("candidate-list").replaceChildren();
  for (const candidate of result.candidates) {
    const row = el("div", undefined, "source-row");
    row.append(
      el("strong", String(candidate.id) + " · " + candidate.kind),
      el("p", candidate.citation),
      el(
        "small",
        candidate.eligible
          ? "Eligible at captured scope and time; not itself a disposition."
          : candidate.rejections.join(" · "),
      ),
    );
    $("candidate-list").append(row);
  }
  $("ack-button").disabled = ctx.role !== "QA" || result.tasks.length > 0;
}
$("evaluate").addEventListener("click", () =>
  guarded(async (ctx) => {
    const id = ctx.caseId;
    $("evaluate").disabled = true;
    try {
      const data = await post("/cases/" + id + "/evaluations", null, ctx);
      check(ctx);
      renderBundle(data, ctx);
      await loadHistory(
        await api("/cases/" + id + "/evaluations", {}, ctx),
        ctx,
      );
      check(ctx);
      say("Evidence snapshot captured. Notification queue is unchanged.");
    } finally {
      if (current(ctx)) {
        $("evaluate").disabled = !["QA", "Operator"].includes(ctx.role);
        await loadQueue(ctx);
      }
    }
  }),
);
$("replay").addEventListener("click", () =>
  guarded(async (ctx) => {
    const r = await api("/bundles/" + bundle.id + "/replay", {}, ctx);
    check(ctx);
    say(
      r.matches
        ? "Replay matches the captured result. Matching hashes and arithmetic do not prove source truth."
        : "Replay differs. Stop and investigate.",
      !r.matches,
    );
  }),
);
$("download").addEventListener("click", () => {
  if (!bundle) return;
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" }),
  );
  const a = el("a");
  a.href = url;
  a.download = selectedCase + "-bundle-" + bundle.id + ".json";
  a.click();
  URL.revokeObjectURL(url);
});
$("review-ack").addEventListener("submit", (event) => {
  event.preventDefault();
  guarded(async (ctx) => {
    const result = await post(
      "/cases/" + ctx.caseId + "/acknowledgements",
      {
        bundle_id: bundle.id,
        expected_hash: bundle.hash,
        signer_label: $("review-label").value,
        outcome: $("review-outcome").value,
        idempotency_key: crypto.randomUUID(),
      },
      ctx,
    );
    check(ctx);
    say(
      "Local acknowledgement " +
        result.id +
        " recorded as " +
        result.actor +
        ". No product disposition or notification was sent.",
    );
    await loadQueue(ctx);
    check(ctx);
    await loadHistory(
      await api("/cases/" + ctx.caseId + "/evaluations", {}, ctx),
      ctx,
    );
  });
});
async function loadAttachments(ctx = caseContext()) {
  const documents = await api("/cases/" + ctx.caseId + "/documents", {}, ctx);
  check(ctx);
  $("attachment-list").replaceChildren();
  for (const d of documents) {
    const row = el("div", undefined, "source-row");
    row.append(
      el(
        "strong",
        d.id +
          " · " +
          d.kind +
          " · " +
          (d.approved ? "APPROVED (synthetic)" : "NOT ACTIVE / NOT APPROVED"),
      ),
      el("p", d.citation),
    );
    const detail = el("details");
    detail.append(
      el("summary", "Inspect attached source bytes"),
      el("pre", d.content),
    );
    row.append(detail);
    row.append(
      button("Use as synthetic template", () => {
        if (!current(ctx)) return;
        const template = {};
        [
          "kind",
          "scope",
          "effective_from",
          "effective_to",
          "citation",
          "content",
        ].forEach((k) => (template[k] = d[k]));
        template.supersedes = null;
        $("attachment-json").value = JSON.stringify(template, null, 2);
        say(
          "Template loaded. Edit it deliberately. A new attachment starts unapproved.",
        );
      }),
    );
    if (ctx.role === "QA" && !d.approver)
      row.append(
        button("Approve synthetic attachment", () =>
          guarded(async (ctx) => {
            if (
              !window.confirm(
                "Have you verified these synthetic bytes, exact scope, effective interval and authority? This is NOT a professional signature.",
              )
            )
              return;
            await post(
              "/cases/" + ctx.caseId + "/documents/" + d.id + "/approval",
              null,
              ctx,
            );
            check(ctx);
            await loadAttachments(ctx);
            check(ctx);
            say("Synthetic source approved. Reassess before acknowledging.");
          }, ctx),
        ),
      );
    $("attachment-list").append(row);
  }
}
$("attachment-form").addEventListener("submit", (event) => {
  event.preventDefault();
  guarded(async (ctx) => {
    const data = JSON.parse($("attachment-json").value);
    const doc = await post("/cases/" + ctx.caseId + "/documents", data, ctx);
    check(ctx);
    $("attachment-json").value = "";
    await loadAttachments(ctx);
    check(ctx);
    say(
      "Attachment " +
        doc.id +
        " captured as UNAPPROVED. A cleared flag does not resolve a task.",
    );
  });
});
async function loadHistory(history, ctx = caseContext()) {
  const ack = await api("/cases/" + ctx.caseId + "/acknowledgements", {}, ctx);
  check(ctx);
  $("record-history").replaceChildren();
  for (const h of history)
    $("record-history").append(
      el(
        "p",
        "Bundle " +
          h.id +
          " ← " +
          (h.parent_id || "initial") +
          " · " +
          h.result.recommendation +
          " · " +
          berlin(h.created),
      ),
    );
  for (const a of ack)
    $("record-history").append(
      el(
        "p",
        "Local acknowledgement " +
          a.id +
          " · " +
          a.actor +
          " · " +
          a.outcome +
          " · bundle " +
          a.bundle_id,
      ),
    );
}
$("notification-form").addEventListener("submit", (event) => {
  event.preventDefault();
  guarded(async (ctx) => {
    await post(
      "/cases/" + $("notice-case").value + "/obligations",
      {
        reportability: $("notice-reportability").value,
        deadline: $("notice-deadline").value || null,
        status: $("notice-status").value,
        basis: $("notice-basis").value,
      },
      ctx,
    );
    check(ctx);
    await loadQueue(ctx);
    check(ctx);
    say(
      "Qualified local assessment recorded. No message or regulatory submission was sent.",
    );
  });
});
