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
async function api(path, options = {}) {
  const response = await fetch("/api" + path, {
    ...options,
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data;
}
const post = (path, data) =>
  api(path, {
    method: "POST",
    ...(data ? { body: JSON.stringify(data) } : {}),
  });
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
async function guarded(action) {
  try {
    await action();
  } catch (error) {
    say(error.message, true);
  }
}
$("login-form").addEventListener("submit", (event) => {
  event.preventDefault();
  guarded(async () => {
    token = $("credential").value.trim();
    $("credential").value = "";
    try {
      identity = await api("/me");
    } catch (e) {
      token = "";
      throw e;
    }
    $("identity").textContent = identity.tenant + " / " + identity.role;
    $("login").hidden = true;
    $("workspace").hidden = false;
    $("logout").hidden = false;
    $("status").hidden = true;
    await refresh();
  });
});
$("logout").addEventListener("click", () => {
  token = "";
  identity = null;
  selectedCase = null;
  bundle = null;
  $("workspace").hidden = true;
  $("login").hidden = false;
  $("logout").hidden = true;
  $("status").hidden = true;
  $("identity").textContent = "Private by default";
  for (const id of [
    "case-list",
    "notification-list",
    "evidence-tasks",
    "attachment-list",
    "record-history",
    "candidate-list",
    "measurements",
  ])
    $(id).replaceChildren();
  $("attachment-json").value = "";
  $("review-label").value = "";
  $("evaluation-panel").hidden = true;
});
async function loadQueue() {
  const obligations = await api("/obligations");
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
async function loadCases() {
  const cases = await api("/cases");
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
      () => guarded(() => selectCase(c.id)),
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
    );
}
async function refresh() {
  // The queue is loaded independently: case assembly failure must not hide clocks.
  const results = await Promise.allSettled([loadQueue(), loadCases()]);
  for (const result of results)
    if (result.status === "rejected") say(result.reason.message, true);
}
$("refresh").addEventListener("click", () => guarded(refresh));
async function selectCase(id) {
  selectedCase = id;
  bundle = null;
  $("evaluation-panel").hidden = true;
  const c = await api("/cases/" + encodeURIComponent(id));
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
  $("evaluate").disabled = !["QA", "Operator"].includes(identity.role);
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
  await loadAttachments();
  const history = await api("/cases/" + id + "/evaluations");
  if (history.length) renderBundle(history[history.length - 1]);
  await loadHistory(history);
}
function renderBundle(data) {
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
    if (identity.role === "QA")
      card.append(
        button("Link approved evidence to resolve", () =>
          guarded(async () => {
            const id = window.prompt(
              "Approved attachment ID for this task. No flag or blank transcription can resolve it:",
            );
            if (id === null) return;
            const resolved = await post(
              "/cases/" + selectedCase + "/resolutions",
              {
                bundle_id: bundle.id,
                reason_code: task.reason_code,
                document_id: Number(id),
              },
            );
            say(
              "Task completed with approved synthetic evidence; new bundle " +
                resolved.resolved_bundle +
                ". Original bundle remains unchanged.",
            );
            await selectCase(selectedCase);
          }),
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
  $("ack-button").disabled = identity.role !== "QA" || result.tasks.length > 0;
}
$("evaluate").addEventListener("click", () =>
  guarded(async () => {
    const id = selectedCase;
    $("evaluate").disabled = true;
    try {
      const data = await post("/cases/" + id + "/evaluations");
      renderBundle(data);
      await loadHistory(await api("/cases/" + id + "/evaluations"));
      say("Evidence snapshot captured. Notification queue is unchanged.");
    } finally {
      $("evaluate").disabled = !["QA", "Operator"].includes(identity.role);
      await loadQueue();
    }
  }),
);
$("replay").addEventListener("click", () =>
  guarded(async () => {
    const r = await api("/bundles/" + bundle.id + "/replay");
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
  guarded(async () => {
    const result = await post("/cases/" + selectedCase + "/acknowledgements", {
      bundle_id: bundle.id,
      expected_hash: bundle.hash,
      signer_label: $("review-label").value,
      outcome: $("review-outcome").value,
      idempotency_key: crypto.randomUUID(),
    });
    say(
      "Local acknowledgement " +
        result.id +
        " recorded as " +
        result.actor +
        ". No product disposition or notification was sent.",
    );
    await loadQueue();
    await loadHistory(await api("/cases/" + selectedCase + "/evaluations"));
  });
});
async function loadAttachments() {
  const documents = await api("/cases/" + selectedCase + "/documents");
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
    if (identity.role === "QA" && !d.approver)
      row.append(
        button("Approve synthetic attachment", () =>
          guarded(async () => {
            if (
              !window.confirm(
                "Have you verified these synthetic bytes, exact scope, effective interval and authority? This is NOT a professional signature.",
              )
            )
              return;
            await post(
              "/cases/" + selectedCase + "/documents/" + d.id + "/approval",
            );
            await loadAttachments();
            say("Synthetic source approved. Reassess before acknowledging.");
          }),
        ),
      );
    $("attachment-list").append(row);
  }
}
$("attachment-form").addEventListener("submit", (event) => {
  event.preventDefault();
  guarded(async () => {
    const data = JSON.parse($("attachment-json").value);
    const doc = await post("/cases/" + selectedCase + "/documents", data);
    $("attachment-json").value = "";
    await loadAttachments();
    say(
      "Attachment " +
        doc.id +
        " captured as UNAPPROVED. A cleared flag does not resolve a task.",
    );
  });
});
async function loadHistory(history) {
  const ack = await api("/cases/" + selectedCase + "/acknowledgements");
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
  guarded(async () => {
    await post("/cases/" + $("notice-case").value + "/obligations", {
      reportability: $("notice-reportability").value,
      deadline: $("notice-deadline").value || null,
      status: $("notice-status").value,
      basis: $("notice-basis").value,
    });
    await loadQueue();
    say(
      "Qualified local assessment recorded. No message or regulatory submission was sent.",
    );
  });
});
