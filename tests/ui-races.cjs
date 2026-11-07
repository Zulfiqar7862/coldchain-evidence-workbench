// Deterministic application-JS tests, not a browser or a mock of the safety assertion.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
function harness() {
  const nodes = new Map(),
    requests = [];
  function node(tag = "div") {
    return {
      tag,
      children: [],
      listeners: {},
      textContent: "",
      hidden: false,
      value: "",
      disabled: false,
      classList: { toggle() {} },
      append(...xs) {
        this.children.push(...xs);
      },
      replaceChildren(...xs) {
        this.children = xs;
        this.textContent = "";
      },
      addEventListener(k, f) {
        this.listeners[k] = f;
      },
      click() {
        return this.listeners.click?.();
      },
      get firstChild() {
        return this.children[0];
      },
    };
  }
  const get = (id) => {
    if (!nodes.has(id)) nodes.set(id, node());
    return nodes.get(id);
  };
  const context = vm.createContext({
    document: {
      documentElement: { dataset: {} },
      getElementById: get,
      createElement: node,
      querySelectorAll: () => [],
    },
    fetch: (url, options) =>
      new Promise((resolve, reject) =>
        requests.push({ url, options, resolve, reject }),
      ),
    AbortController,
    Intl,
    Date,
    console,
    window: { confirm: () => true, prompt: () => "9" },
    URL,
    Blob,
    crypto: { randomUUID: () => "test-key" },
  });
  vm.runInContext(
    fs.readFileSync(path.join(__dirname, "../workbench/static/app.js"), "utf8"),
    context,
  );
  const run = (code) => vm.runInContext(code, context);
  function respond(request, data, ok = true) {
    request.resolve({ ok, json: async () => data });
  }
  function text(n) {
    return [n.textContent, ...n.children.flatMap(text)].join(" ");
  }
  async function ticks() {
    for (let i = 0; i < 12; i++) await Promise.resolve();
  }
  return { get, run, respond, requests, text, ticks };
}
function scope(product) {
  return {
    product,
    strength: "demo",
    presentation: "cartridge",
    origin: "a",
    destination: "b",
  };
}
function caseData(product) {
  return {
    input: {
      scope: scope(product),
      observation: { min_c: 1, max_c: 2, duration_minutes: 3 },
    },
  };
}
function bundle(id, marker) {
  return {
    id,
    hash: "a".repeat(64),
    result: {
      recommendation: marker,
      version: "test",
      checks: [],
      tasks: [],
      candidates: [],
    },
  };
}
function loginDirect(h, tenant = "a") {
  h.run(
    `token='${tenant}-key';identity={tenant:'${tenant}',role:'QA'};selectedCase='CASE-A'`,
  );
}
function switchTenant(h) {
  h.get("logout").listeners.click();
  h.run(
    "token='b-key';identity={tenant:'b',role:'Reader'};selectedCase='CASE-B'",
  );
  h.get("workspace").hidden = false;
}

test("old tenant queue cannot render after logout/relogin even when transport ignores abort", async () => {
  const h = harness();
  loginDirect(h);
  const pending = h.run("guarded(()=>loadQueue())");
  const request = h.requests[0];
  switchTenant(h);
  h.respond(request, [
    {
      case_id: "PRIVATE-A",
      reportability: "REPORTABLE",
      deadline: null,
      status: "PENDING",
    },
  ]);
  await pending;
  assert.equal(h.text(h.get("notification-list")).includes("PRIVATE-A"), false);
  assert.equal(
    request.options.signal?.aborted,
    true,
    "logout must also cancel transport",
  );
});
test("delayed JSON body cannot render after a tenant switch", async () => {
  const h = harness();
  loginDirect(h);
  let body;
  const pending = h.run("guarded(()=>loadQueue())");
  h.requests[0].resolve({
    ok: true,
    json: () => new Promise((resolve) => (body = resolve)),
  });
  await h.ticks();
  switchTenant(h);
  body([
    {
      case_id: "BODY-A",
      reportability: "REPORTABLE",
      deadline: null,
      status: "PENDING",
    },
  ]);
  await pending;
  assert.equal(h.text(h.get("notification-list")).includes("BODY-A"), false);
});
test("old queue error cannot appear in new session", async () => {
  const h = harness();
  loginDirect(h);
  const pending = h.run("guarded(()=>loadQueue())");
  switchTenant(h);
  h.requests[0].reject(new Error("SECRET-A-ERROR"));
  await pending;
  assert.equal(h.get("status").textContent.includes("SECRET-A-ERROR"), false);
});
test("latest case selection owns rendering, including same-case reselects", async () => {
  const h = harness();
  loginDirect(h);
  const first = h.run("guarded(()=>selectCase('CASE-A'))");
  const old = h.requests[0];
  const second = h.run("guarded(()=>selectCase('CASE-B'))");
  h.respond(h.requests[1], caseData("CURRENT-B"));
  await h.ticks();
  h.respond(h.requests[2], []);
  await h.ticks();
  h.respond(h.requests[3], []);
  await h.ticks();
  h.respond(h.requests[4], []);
  await h.ticks();
  h.respond(old, caseData("OLD-A"));
  await h.ticks();
  assert.equal(h.get("selected-case").textContent, "CASE-B");
  assert.equal(h.get("case-scope").textContent.includes("OLD-A"), false);
  assert.equal(old.options.signal?.aborted, true);
});
test("old attachments and history requests cannot render after logout", async () => {
  for (const expression of ["loadAttachments()", "loadHistory([])"]) {
    const h = harness();
    loginDirect(h);
    const pending = h.run(`guarded(()=>${expression})`);
    switchTenant(h);
    const data = expression.startsWith("loadAttachments")
      ? [
          {
            id: 1,
            kind: "study",
            approved: true,
            citation: "PRIVATE-A-SOURCE",
            content: "PRIVATE-A",
            scope: scope("A"),
            effective_from: "2030-01-01T00:00:00Z",
            effective_to: "2031-01-01T00:00:00Z",
          },
        ]
      : [
          {
            id: 1,
            actor: "PRIVATE-A-ACTOR",
            outcome: "accepted",
            bundle_id: 1,
          },
        ];
    h.respond(h.requests[0], data);
    await pending;
    assert.equal(h.text(h.get("attachment-list")).includes("PRIVATE-A"), false);
    assert.equal(h.text(h.get("record-history")).includes("PRIVATE-A"), false);
  }
});
test("old login response cannot restore a logged-out session", async () => {
  const h = harness();
  h.get("credential").value = "a-key";
  h.get("login-form").listeners.submit({ preventDefault() {} });
  const old = h.requests[0];
  h.get("logout").listeners.click();
  h.respond(old, { tenant: "PRIVATE-A", role: "QA" });
  await h.ticks();
  assert.equal(h.get("workspace").hidden, true);
  assert.equal(h.get("identity").textContent.includes("PRIVATE-A"), false);
  assert.equal(h.requests.length, 1);
});
test("old evaluation success/finally cannot render or launch requests under new credentials", async () => {
  const h = harness();
  loginDirect(h);
  h.get("evaluate").listeners.click();
  const request = h.requests[0];
  switchTenant(h);
  h.respond(request, bundle(1, "PRIVATE-A-RESULT"));
  await h.ticks();
  assert.equal(
    h.get("recommendation").textContent.includes("PRIVATE-A"),
    false,
  );
  assert.equal(h.requests.length, 1);
});
test("old replay or acknowledgement cannot render toast after a switch", async () => {
  for (const element of ["replay", "review-ack"]) {
    const h = harness();
    loginDirect(h);
    h.run("bundle={id:1,hash:'a'.repeat(64)}");
    h.get("review-label").value = "role";
    h.get("review-outcome").value = "REVIEW_ACCEPTED";
    if (element === "replay") h.get(element).listeners.click();
    else h.get(element).listeners.submit({ preventDefault() {} });
    switchTenant(h);
    h.respond(h.requests[0], {
      id: "PRIVATE-A",
      actor: "PRIVATE-A",
      matches: true,
    });
    await h.ticks();
    assert.equal(h.get("status").hidden, true);
    assert.equal(h.requests.length, 1);
  }
});
test("logout clears all case, queue, bundle and form text, not just containers", () => {
  const h = harness();
  loginDirect(h);
  for (const id of [
    "case-scope",
    "selected-case",
    "recommendation",
    "bundle-hash",
    "case-count",
    "notice-count",
  ])
    h.get(id).textContent = "PRIVATE-A";
  for (const id of [
    "notice-case",
    "notice-basis",
    "attachment-json",
    "review-label",
  ])
    h.get(id).value = "PRIVATE-A";
  h.get("logout").listeners.click();
  for (const id of [
    "case-scope",
    "selected-case",
    "recommendation",
    "bundle-hash",
    "case-count",
    "notice-count",
  ])
    assert.equal(h.get(id).textContent.includes("PRIVATE-A"), false, id);
  for (const id of [
    "notice-case",
    "notice-basis",
    "attachment-json",
    "review-label",
  ])
    assert.equal(h.get(id).value.includes("PRIVATE-A"), false, id);
});
test("old case list cannot render or auto-select in a new tenant", async () => {
  const h = harness();
  loginDirect(h);
  h.run("selectedCase=null");
  const pending = h.run("guarded(()=>loadCases())");
  switchTenant(h);
  h.respond(h.requests[0], [{ id: "PRIVATE-A" }]);
  await pending;
  assert.equal(h.text(h.get("case-list")).includes("PRIVATE-A"), false);
  assert.equal(h.requests.length, 1);
});
test("reselecting the same case still invalidates prior selection generation", async () => {
  const h = harness();
  loginDirect(h);
  h.run("guarded(()=>selectCase('CASE-A'))");
  const old = h.requests[0];
  h.run("guarded(()=>selectCase('CASE-A'))");
  h.respond(old, caseData("OLD-SAME-ID"));
  await h.ticks();
  assert.equal(h.get("case-scope").textContent.includes("OLD-SAME-ID"), false);
  assert.equal(h.requests.length, 2);
  assert.equal(old.options.signal.aborted, true);
});
test("latest queue refresh wins within the same session", async () => {
  const h = harness();
  loginDirect(h);
  const one = h.run("guarded(()=>loadQueue())");
  const two = h.run("guarded(()=>loadQueue())");
  h.respond(h.requests[1], []);
  await two;
  h.respond(h.requests[0], [
    {
      case_id: "OLD-QUEUE",
      reportability: "UNKNOWN",
      deadline: null,
      status: "PENDING",
    },
  ]);
  await one;
  assert.equal(h.text(h.get("notification-list")).includes("OLD-QUEUE"), false);
  assert.equal(h.requests[0].options.signal.aborted, true);
});
test("attachment and notification mutation continuations cannot use a new session", async () => {
  for (const form of ["attachment-form", "notification-form"]) {
    const h = harness();
    loginDirect(h);
    h.get("attachment-json").value = "{}";
    h.get(form).listeners.submit({ preventDefault() {} });
    switchTenant(h);
    h.get("attachment-json").value = "NEW-TENANT-DRAFT";
    h.respond(h.requests[0], { id: 1 });
    await h.ticks();
    assert.equal(h.requests.length, 1);
    assert.equal(h.get("status").hidden, true);
    assert.equal(h.get("attachment-json").value, "NEW-TENANT-DRAFT");
  }
});
function descendants(n) {
  return [n, ...n.children.flatMap(descendants)];
}
test("approval and evidence-resolution closures retain original session and selection", async () => {
  for (const kind of ["approval", "resolution"]) {
    const h = harness();
    loginDirect(h);
    if (kind === "approval") {
      const pending = h.run("guarded(()=>loadAttachments())");
      h.respond(h.requests[0], [
        {
          id: 1,
          kind: "study",
          approved: false,
          citation: "source",
          content: "bytes",
          scope: scope("demo"),
          supersedes: [],
          effective_from: "2030-01-01T00:00:00Z",
          effective_to: "2031-01-01T00:00:00Z",
        },
      ]);
      await pending;
    } else {
      const data = bundle(1, "EVIDENCE_REQUIRED");
      data.result.tasks = [
        {
          reason_code: "STUDY",
          required_role: "QA",
          status: "OPEN",
          evidence_requested: "bytes",
          source_citation: "demo",
          completion_criterion: "approved bytes",
        },
      ];
      h.run(`renderBundle(${JSON.stringify(data)})`);
    }
    const root = h.get(
      kind === "approval" ? "attachment-list" : "evidence-tasks",
    );
    const action = descendants(root).find(
      (n) =>
        n.tag === "button" &&
        n.textContent.startsWith(kind === "approval" ? "Approve" : "Link"),
    );
    action.click();
    const request = h.requests.at(-1);
    const count = h.requests.length;
    switchTenant(h);
    h.respond(request, { resolved_bundle: 2 });
    await h.ticks();
    assert.equal(h.requests.length, count);
    assert.equal(h.get("status").hidden, true);
    // Detached buttons are also stale capabilities, not a route into a new session.
    action.click();
    await h.ticks();
    assert.equal(h.requests.length, count);
  }
});
test("QA sees proposed replacement targets, scope and dates before approving", async () => {
  const h = harness();
  loginDirect(h);
  const pending = h.run("guarded(()=>loadAttachments())");
  const d = {
    id: 31,
    kind: "sop",
    approved: false,
    citation: "SYNTHETIC proposal",
    content: "bytes",
    scope: scope("ILLUSTRATIVE-PRODUCT"),
    supersedes: [8, 12],
    effective_from: "2030-01-01T00:00:00Z",
    effective_to: "2031-01-01T00:00:00Z",
  };
  h.respond(h.requests[0], [d]);
  await pending;
  const visible = h.text(h.get("attachment-list"));
  for (const expected of [
    "8, 12",
    "ILLUSTRATIVE-PRODUCT",
    "2030-01-01T00:00:00Z",
    "2031-01-01T00:00:00Z",
  ])
    assert.equal(visible.includes(expected), true, expected);
});
