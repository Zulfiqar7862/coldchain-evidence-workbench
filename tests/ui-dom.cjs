// Real HTML parsing, DOM mutation and CSSOM in Node. No browser process or network.
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");
const vm = require("node:vm");
const staticPath = path.join(__dirname, "../workbench/static");
const html = fs.readFileSync(path.join(staticPath, "index.html"), "utf8");
const css = fs.readFileSync(path.join(staticPath, "app.css"), "utf8");
const script = fs.readFileSync(path.join(staticPath, "app.js"), "utf8");
const scalarIds = [
  "selected-case",
  "case-scope",
  "recommendation",
  "bundle-version",
  "bundle-hash",
  "task-count",
];
const listIds = [
  "measurements",
  "checks",
  "evidence-tasks",
  "candidate-list",
  "attachment-list",
  "record-history",
];
const fieldIds = [
  "review-label",
  "attachment-json",
  "notice-case",
  "notice-basis",
  "notice-deadline",
];
function harness(t) {
  const dom = new JSDOM(html, {
    runScripts: "outside-only",
    url: "http://127.0.0.1:8174",
  });
  t.after(() => dom.window.close());
  const w = dom.window,
    requests = [];
  const style = w.document.createElement("style");
  style.textContent = css;
  w.document.head.append(style);
  w.fetch = (url, options) =>
    new Promise((resolve) => requests.push({ url, options, resolve }));
  const run = (code) => vm.runInContext(code, dom.getInternalVMContext());
  run(script);
  const get = (id) => w.document.getElementById(id);
  const flush = async () => {
    for (let i = 0; i < 30; i++) await Promise.resolve();
  };
  function respond(suffix, data) {
    const r = requests.find((r) => r.url.endsWith(suffix) && !r.done);
    assert.ok(r, suffix);
    r.done = true;
    r.resolve({ ok: true, json: async () => data });
    return r;
  }
  function dirty() {
    for (const id of scalarIds) get(id).textContent = "SYNTHETIC-OLD-TENANT";
    for (const id of listIds) {
      const n = w.document.createElement("p");
      n.textContent = "SYNTHETIC-OLD-TENANT";
      get(id).append(n);
    }
    for (const id of fieldIds) get(id).value = "SYNTHETIC-OLD-TENANT";
    get("bundle-hash").title = "SYNTHETIC-OLD-TENANT";
    get("attachments-panel").open = true;
    get("evaluation-panel").hidden = false;
    get("evaluate").disabled = false;
  }
  function clean() {
    for (const id of [...scalarIds, ...listIds])
      assert.equal(
        get(id).textContent.includes("SYNTHETIC-OLD-TENANT"),
        false,
        id,
      );
    for (const id of fieldIds) assert.equal(get(id).value, "", id);
    assert.equal(get("bundle-hash").title, "");
    assert.equal(get("evaluate").disabled, true);
  }
  return { w, run, get, flush, respond, dirty, clean, requests };
}
test("actual markup has unique IDs and hidden beats grid/flex author styles", (t) => {
  const h = harness(t),
    ids = [...h.w.document.querySelectorAll("[id]")].map((n) => n.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const id of ["login", "workspace", "evaluation-panel", "status"]) {
    h.get(id).hidden = true;
    assert.equal(h.w.getComputedStyle(h.get(id)).display, "none", id);
  }
});
test("real DOM logout synchronously erases data, including when panels are forced visible", (t) => {
  const h = harness(t);
  h.run("token='a';identity={tenant:'a',role:'QA'};selectedCase='CASE-A'");
  h.dirty();
  const collision = h.w.document.createElement("style");
  collision.textContent = "#case-detail[hidden] { display: block !important; }";
  h.w.document.head.append(collision);
  h.get("logout").click();
  // Deliberately defeat hiding with a stronger author rule: erasure, not CSS,
  // must protect the next actor before any Promise settles.
  assert.equal(h.w.getComputedStyle(h.get("case-detail")).display, "block");
  // Ignore visibility entirely: erasure must be complete before any Promise settles.
  h.clean();
  assert.equal(h.get("workspace").hidden, true);
  assert.equal(
    h.get("attachments-panel").open,
    false,
    "disclosure state must not carry to next actor",
  );
});
test("empty tenant case refresh erases residual detail and invalidates its selection", async (t) => {
  const h = harness(t);
  h.run("token='b';identity={tenant:'b',role:'Reader'};selectedCase='CASE-A'");
  h.dirty();
  const pending = h.run("guarded(()=>refresh())");
  h.respond("/obligations", []);
  h.respond("/cases", []);
  await pending;
  h.clean();
  assert.equal(h.run("selectedCase"), null);
  assert.equal(h.get("case-detail").hidden, true);
  assert.equal(h.get("case-empty").hidden, false);
});
test("no selection plus empty list clears residual data without relying on display", async (t) => {
  const h = harness(t);
  h.run("token='b';identity={tenant:'b',role:'Reader'};selectedCase=null");
  h.dirty();
  const pending = h.run("guarded(()=>loadCases())");
  h.respond("/cases", []);
  await pending;
  h.clean();
});
test("served markup and executed script identify the same explicit UI build", (t) => {
  const h = harness(t);
  const marker = h.get("ui-build");
  assert.ok(marker, "visible build marker");
  const build = h.w.document.documentElement.dataset.uiBuild;
  assert.ok(build);
  assert.equal(marker.textContent, "UI " + build);
  for (const selector of ["script[src]", "link[rel=stylesheet]"])
    assert.equal(
      new URL(
        h.w.document.querySelector(selector).href ||
          h.w.document.querySelector(selector).src,
      ).searchParams.get("v"),
      build,
    );
});
async function login(h, key, identity, cases) {
  h.get("credential").value = key;
  h.get("login-form").dispatchEvent(
    new h.w.Event("submit", { bubbles: true, cancelable: true }),
  );
  h.respond("/me", identity);
  await h.flush();
  h.respond("/obligations", []);
  h.respond("/cases", cases);
  await h.flush();
}
const demoCase = {
  input: {
    scope: {
      product: "SYNTHETIC-A-PRODUCT",
      strength: "demo",
      presentation: "demo",
      origin: "SYNTHETIC-A-ORIGIN",
      destination: "SYNTHETIC-A-DESTINATION",
    },
    observation: { min_c: 1, max_c: 2, duration_minutes: 3 },
  },
};
test("actual QA login -> populated detail -> lock -> empty reader -> refresh erases product and route", async (t) => {
  const h = harness(t);
  await login(h, "a-key", { tenant: "a", role: "QA" }, [{ id: "CASE-A" }]);
  h.respond("/cases/CASE-A", demoCase);
  await h.flush();
  h.respond("/documents", []);
  await h.flush();
  h.respond("/evaluations", []);
  await h.flush();
  h.respond("/acknowledgements", []);
  await h.flush();
  assert.equal(h.get("case-detail").hidden, false);
  assert.equal(
    h.get("case-scope").textContent.includes("SYNTHETIC-A-PRODUCT"),
    true,
  );
  h.get("logout").click();
  assert.equal(
    h.get("case-scope").textContent,
    "",
    "erased synchronously before login",
  );
  await login(h, "b-key", { tenant: "b", role: "Reader" }, []);
  h.get("refresh").click();
  h.respond("/obligations", []);
  h.respond("/cases", []);
  await h.flush();
  assert.equal(h.get("case-count").textContent, "0");
  assert.equal(h.get("notice-count").textContent, "0");
  assert.equal(h.get("case-scope").textContent, "");
  assert.equal(h.get("selected-case").textContent, "");
  assert.equal(
    h.get("case-detail").textContent.includes("SYNTHETIC-A-"),
    false,
  );
  assert.equal(h.get("case-detail").hidden, true);
  assert.equal(h.w.getComputedStyle(h.get("case-detail")).display, "none");
  assert.equal(h.get("case-empty").hidden, false);
  assert.equal(h.w.getComputedStyle(h.get("login")).display, "none");
});
test("real DOM late case response cannot reopen detail after reader login and empty refresh", async (t) => {
  const h = harness(t);
  await login(h, "a-key", { tenant: "a", role: "QA" }, [{ id: "CASE-A" }]);
  const old = h.requests.find((r) => r.url === "/api/cases/CASE-A");
  h.get("logout").click();
  await login(h, "b-key", { tenant: "b", role: "Reader" }, []);
  old.done = true;
  old.resolve({ ok: true, json: async () => demoCase });
  await h.flush();
  assert.equal(old.options.signal.aborted, true);
  assert.equal(h.get("case-scope").textContent, "");
  assert.equal(h.get("case-detail").hidden, true);
  assert.equal(
    h.requests.some((r) => r.url.endsWith("/documents")),
    false,
  );
});
test("logout resets unsubmitted review/assessment choices and all workspace disclosures", (t) => {
  const h = harness(t);
  h.get("review-outcome").value = "REVIEW_REJECTED";
  h.get("notice-status").value = "SENT";
  h.get("notice-reportability").value = "REPORTABLE";
  const notice = h.w.document.querySelector(".notification-panel details");
  notice.open = true;
  h.get("logout").click();
  assert.equal(h.get("review-outcome").value, "REVIEW_ACCEPTED");
  assert.equal(h.get("notice-status").value, "PENDING");
  assert.equal(h.get("notice-reportability").value, "UNKNOWN");
  assert.equal(notice.open, false);
});
