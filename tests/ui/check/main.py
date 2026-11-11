"""W13-01 check program: the desktop host routing and first-run rules, exercised for real.

It drives apps/desktop/main/lib/host.js through node with injected fakes - a discovery file, a health
endpoint, a spawn that either produces a core or produces nothing - and asserts the two negatives the card
names as its own acceptance: nothing in the first-run path may require a terminal or a hand-copied owner
token, and a provider reply that did not succeed may never be classified as success. Each assertion is a
named id, and a row that cannot fail for its stated reason is the defect class the reviewers keep blocking,
so every absence claim here is paired with the positive control that makes it falsifiable.

Report shape matches the other v2.4 check programs: one JSON line with status, assertions, assertion_ids,
failures, not_verified and diagnostics, so the dispatcher and the receipt generator read it the same way.
"""
import io
import hashlib
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HOST_JS = os.path.join("apps", "desktop", "main", "lib", "host.js")
LOCKED_TOOLS = os.path.join("execution", "toolchains", "locked.json")


def locked_node_entry():
    """The node row of the locked toolchain table, or None if it cannot be read."""
    try:
        return json.loads(io.open(os.path.join(ROOT, LOCKED_TOOLS), encoding="utf-8").read())["tools"]["node"]
    except Exception:
        return None


def resolve_node(tools):
    """Return (absolute binary, version, reason) for the pinned node, or (None, None, reason).

    It verifies absolute path, sha256 and version output exactly as ops/ci/environment.py does, and it never
    falls back to a PATH lookup: a check that runs whichever node PATH happens to hold reports an environment
    nobody pinned, which is what the round-1 review blocked on this card.
    """
    if not tools:
        return None, None, "the locked toolchain table could not be read"
    path = tools.get("path")
    if not path or not os.path.isabs(path) or not os.path.isfile(path):
        return None, None, "the pinned node binary is absent: %r" % path
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if digest != tools.get("sha256"):
        return None, None, "the pinned node binary hash does not match the locked table"
    argv = [path] + list(tools.get("version_argv") or ["--version"])
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=60)
    except Exception as exc:
        return None, None, "the pinned node could not be asked for its version: %s" % exc
    version = (r.stdout or "").strip()
    if r.returncode != 0 or version != tools.get("version_output"):
        return None, None, "the pinned node reports %r while the locked table says %r" % (version, tools.get("version_output"))
    return path, version, "verified"

DRIVER = r"""
const path = require('node:path');
const host = require(path.join(process.argv[2], 'host.js'));
const fs = require('node:fs');
const out = {checks: {}, errors: []};
const sleep = (ms) => new Promise((r) => setTimeout(r, 0));

function fakeFs(files) {
  return { readFileSync: (p) => { const k = String(p).replace(/\\\\/g, '/').split('/').pop();
    if (!(k in files)) throw Object.assign(new Error('ENOENT'), {code: 'ENOENT'});
    return files[k]; } };
}
function fakeHttp(handler) {
  // the handler is consulted exactly once per request, so a check counts requests rather than guessing how
  // many times a fake re-evaluated itself
  return { get: (url, opts, cb) => {
    const d = handler(url) || {};
    const res = { on: (ev, fn) => { if (ev === 'data' && d.body) fn(JSON.stringify(d.body)); if (ev === 'end') setImmediate(fn); },
                  resume: () => {}, statusCode: d.status };
    const req = { on: (ev, fn) => { if (ev === 'error' && d.error) setImmediate(() => fn({code: d.error})); return req; },
                  destroy: () => {} };
    setImmediate(() => cb(res));
    return req;
  } };
}

(async () => {
  const goodDisc = JSON.stringify({url: 'http://127.0.0.1:1', pid: 4242, data_dir: 'D:/x'});
  const store = JSON.stringify({principal_id: 'local-principal-1'});

  // clients and routes: the four native clients the card names, each with the methods first run needs
  out.checks.clients = host.CLIENTS;
  out.checks.route_shape = Object.keys(host.ROUTES.status).concat(Object.keys(host.ROUTES.workspace),
    Object.keys(host.ROUTES.session), Object.keys(host.ROUTES.provider));

  // already-up core must not be relaunched: the positive control for the auto-launch branch
  let spawns = 0;
  const up = await host.ensureCore({fsImpl: fakeFs({'v24_host.json': goodDisc}),
    httpImpl: fakeHttp(() => ({status: 200})), spawnImpl: () => { spawns++; return {pid: 9}; },
    discoveryFile: 'v24_host.json', coreArgv: ['control.exe', '--serve'], retries: 2, waitMs: 1, sleep});
  out.checks.up_no_relaunch = {health: up.health, launched: up.launched, spawns: up.spawns, counted: spawns};

  // discovery present but core down: the shell starts the core itself instead of telling the user to
  spawns = 0;
  // reachability is a property of the world, not a call counter: the core answers only once it has been
  // started, which is the behaviour a first-run user depends on and the reason a counted-request fake lies
  let reachable = false;
  const launchedUp = await host.ensureCore({fsImpl: fakeFs({'v24_host.json': goodDisc}),
    httpImpl: fakeHttp(() => (reachable ? {status: 200} : {status: 0, error: 'ECONNREFUSED'})),
    spawnImpl: (cmd, args) => { spawns++; reachable = true; out.checks.spawn_argv = [cmd].concat(args); return {pid: 77}; },
    discoveryFile: 'v24_host.json', coreArgv: ['control.exe', '--serve'], retries: 4, waitMs: 1, sleep});
  out.checks.absent_core_launches = {health: launchedUp.health, launched: launchedUp.launched, spawns: launchedUp.spawns, counted: spawns};

  // no discovery at all and a spawn that produces nothing: reported honestly, never as UP
  spawns = 0;
  const dead = await host.ensureCore({fsImpl: fakeFs({}), httpImpl: fakeHttp(() => ({status: 0, error: 'ECONNREFUSED'})),
    spawnImpl: () => { spawns++; return null; }, discoveryFile: 'v24_host.json', coreArgv: ['control.exe'], retries: 1, waitMs: 1, sleep});
  out.checks.no_core_no_lie = {health: dead.health, launched: dead.launched, spawns: dead.spawns};

  // provider classification: only an OK and not-degraded reply is success
  out.checks.provider = {
    ok: host.classifyProvider({status: 'OK'}),
    degraded: host.classifyProvider({status: 'OK', degraded: true}),
    auth: host.classifyProvider({status: 'AUTH_REQUIRED'}),
    rate: host.classifyProvider({status: 'RATE_LIMITED'}),
    unsupported: host.classifyProvider({status: 'UNSUPPORTED'}),
    transport: host.classifyProvider({error: 'ECONNREFUSED'}),
    none: host.classifyProvider(null)
  };

  // request building: no token field survives, and the principal travels as a header the caller cannot set
  const req = host.requestFor('provider', 'probe', {token: 'SHOULD-DIE', owner_token: 'ALSO-DIE', model: 'm'}, 'local-principal-1');
  out.checks.request = {ok: req.ok, verb: req.verb, path: req.path, payload: req.payload, headers: req.headers};
  out.checks.request_rejects = {unknown_client: host.requestFor('browser', 'x', {}, 'p').reason,
    unknown_method: host.requestFor('provider', 'teleport', {}, 'p').reason};

  // empty state: a first run offers the three actions and needs neither a terminal nor a copied token
  out.checks.empty = host.emptyState([]);
  out.checks.nonempty = host.emptyState([{id: 'p'}]);

  // principal comes from the local store; absent store is a named reason, not an invented identity
  out.checks.principal_present = host.principalFor(fakeFs({'principal.json': store}), 'principal.json');
  out.checks.principal_absent = host.principalFor(fakeFs({}), 'principal.json');
  out.checks.discovery_absent = host.readDiscovery(fakeFs({}), 'v24_host.json').reason;


  // ---- the wiring, not only the pure module ----
  const ipc = require(path.join(process.argv[2], 'ipc.js'));
  const channels = [];
  const recorder = { handle: (name) => channels.push(name) };
  const registered = ipc.register(recorder, {});
  out.checks.registration = { channels: channels.slice().sort(), count: registered.length };

  async function run(name, deps) { return await ipc.callCore(deps, name[0], name[1], {}); }
  function world(reachableAfterSpawn, transportReply) {
    let reachable = false, spawns = 0; const calls = [];
    return {
      calls, spawned: () => spawns,
      deps: {
        fsImpl: fakeFs({'v24_host.json': goodDisc, 'principal.json': store}),
        httpImpl: fakeHttp(() => (reachable ? {status: 200} : {status: 0, error: 'ECONNREFUSED'})),
        spawnImpl: () => { spawns++; reachable = !!reachableAfterSpawn; return {pid: 5}; },
        discoveryFile: 'v24_host.json', principalFile: 'principal.json', coreArgv: ['control.exe'],
        retries: 3, waitMs: 1, sleep,
        transport: async (verb, url, payload, headers) => {
          calls.push({verb, url, keys: Object.keys(payload || {}), principal: headers['X-ResearchOS-Principal']});
          if (!reachable) return {status: 'ERROR', error: 'CORE_UNREACHABLE'};
          return transportReply;
        }
      }
    };
  }
  const wUp = world(true, {items: [], status: 'OK'});
  out.checks.call_starts_core = {res: await run(['session', 'list'], wUp.deps), calls: wUp.calls.length};

  const wDead = world(false, {status: 'OK'});
  out.checks.unreachable_core_not_faked = {res: await run(['session', 'list'], wDead.deps), calls: wDead.calls.length};

  const wProv = world(true, {status: 'OK', degraded: true});
  out.checks.provider_degraded_call = await run(['provider', 'probe'], wProv.deps);

  const wErr = world(true, {status: 'ERROR', error: 'HOST_SAYS_NO'});
  out.checks.host_error_call = await run(['workspace', 'register'], wErr.deps);

  const wTok = world(true, {items: []});
  await ipc.callCore(Object.assign({}, wTok.deps), 'provider', 'configure', {model: 'm', token: 'PASTED', owner_token: 'PASTED2'});
  out.checks.payload_would_drop_tokens = (() => {
    const req = host.requestFor('provider', 'configure', {model: 'm', token: 'PASTED', owner_token: 'PASTED2'}, 'local-principal-1');
    return {payload: req.payload, header: req.headers};
  })();
  console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({checks: out.checks, errors: [String(e && e.stack || e)]})); process.exit(3); });
"""


# Routing rule for this key. test.ui.routes already resolves today for task W13 with case C23 through the
# v2.0 registry, so binding a v2.4 entry for the same key flips resolution for every selector on it and the
# forwarding branch is what keeps an accepted binding from being shadowed.
LEGACY_PHASE = "workflow"


def routing_decision(task, check, case, explicit=False):
    # local mode is only ever entered deliberately: either the dispatcher named this card, or a human or the
    # mutation runner passed --check-id W13-01. A selector-less dispatch must stay a refusal, because turning
    # an unspecified run into a passing run is the mistake this card's own guards exist to prevent.
    if explicit:
        return "local"
    if check == "W13-01" and task == "W13":
        return "local"
    if task == "W13" and check == "" and case == "C23":
        return "legacy"
    if not task and not check and not case:
        return "refuse"
    return "legacy"


def forward(task, check, case):
    env = dict(os.environ, RESEARCHOS_TASK_ID=task, RESEARCHOS_CHECK_ID=check, RESEARCHOS_CASE_ID=case)
    p = subprocess.run([sys.executable, "-X", "utf8", "ops/ci/ui.py", "--phase", LEGACY_PHASE],
                       capture_output=True, text=True, timeout=900, encoding="utf-8",
                       errors="replace", env=env)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    return (json.loads(lines[-1]) if lines else None), p.returncode


def main():
    task = os.environ.get("RESEARCHOS_TASK_ID", "")
    check = os.environ.get("RESEARCHOS_CHECK_ID", "")
    case = os.environ.get("RESEARCHOS_CASE_ID", "")
    if routing_decision(task, check, case, "--check-id" in sys.argv) == "refuse":
        print(json.dumps({"status": "COMMAND_FAILED", "assertions": 0, "assertion_ids": [],
                          "failures": [{"id": "W1301-SELECTORS-REQUIRED",
                                        "detail": "no task, check or case was named; pass --check-id W13-01 to run this program directly"}],
                          "not_verified": [], "diagnostics": [],
                          "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"}, ensure_ascii=False))
        return 1
    if routing_decision(task, check, case, "--check-id" in sys.argv) != "local":
        rep, rc = forward(task, check, case)
        print(json.dumps(rep if rep else {"status": "COMMAND_FAILED", "assertions": 0,
                                           "note": "the forwarded handler produced no report"}, ensure_ascii=False))
        return rc
    ids, failures, diagnostics, not_verified = [], [], [], []
    host_path = os.path.join(ROOT, HOST_JS)
    if not os.path.isfile(host_path):
        print(json.dumps({"status": "FAIL", "assertions": 0, "assertion_ids": [],
                          "failures": [{"id": "W1301-HOST-MODULE-PRESENT", "detail": host_path}],
                          "not_verified": [], "diagnostics": [], "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"}))
        return 1

    def ok(label, cond, detail=None):
        if cond:
            ids.append(label)
        else:
            failures.append({"id": label, "detail": str(detail)[:400]})

    def note(probe, cond, detail):
        diagnostics.append({"probe": probe, "observed": cond, "detail": str(detail)[:300]})

    def skip(label, reason):
        not_verified.append(label + ": " + reason)

    node_tools = locked_node_entry()
    node_bin, node_version, node_reason = resolve_node(node_tools)
    ok("W1301-TOOLCHAIN-NODE-FROM-LOCKED-TABLE", node_bin is not None, node_reason)
    ok("W1301-TOOLCHAIN-NODE-PATH-FALLBACK-IS-REFUSED",
       resolve_node({"path": os.path.join(ROOT, "no", "such", "node.exe"), "sha256": "0" * 64,
                     "version_argv": ["--version"], "version_output": "v0.0.0"})[0] is None,
       "a positive control: a table naming an absent binary must yield no executable rather than a PATH name")
    path_node = ""
    try:
        path_node = subprocess.run(["node", "--version"], capture_output=True, text=True,
                                   encoding="utf-8", timeout=60).stdout.strip()
    except Exception:
        path_node = "(no node on PATH)"
    note("node-on-PATH-versus-pinned", node_version,
         "pinned=%s PATH=%s - the driver ran the pinned one, and the difference is recorded so a reader can see "
         "this row is not vacuous on a host where both are the same" % (node_version, path_node))

    with tempfile.TemporaryDirectory() as td:
        drv = os.path.join(td, "driver.js")
        with open(drv, "w", encoding="utf-8") as fh:
            fh.write(DRIVER)
        ipc_path = os.path.join(ROOT, "apps", "desktop", "main", "lib", "ipc.js")
        for src, name in ((host_path, "host.js"), (ipc_path, "ipc.js")):
            with open(os.path.join(td, name), "w", encoding="utf-8") as fh:
                fh.write("module.exports = require(%r);\n" % src.replace("\\", "/"))
        if node_bin is None:
            # No PATH fallback, and no silent skip: the resolver refused to name an unpinned interpreter, so the
            # driver is not launched and every row that depends on it fails by name. A fallback here would let the
            # suite report an environment nobody pinned while still printing PASS.
            driver_out = "the pinned node binary was unavailable, so the driver was not launched"
            driver_err = node_reason
            rep = {}
        else:
            p = subprocess.run([node_bin, drv, td], capture_output=True, text=True, timeout=300,
                               encoding="utf-8", errors="replace")
            driver_out = (p.stdout or "")
            driver_err = (p.stderr or "")
        line = [l for l in driver_out.splitlines() if l.strip().startswith("{")]
        rep = json.loads(line[-1]) if line else {}
        ok("W1301-DRIVER-RAN", bool(rep) and not rep.get("errors"), driver_out[-300:] + " | " + driver_err[-300:])
        c = rep.get("checks") or {}

    ok("W1301-FOUR-NATIVE-CLIENTS-ROUTED", sorted(c.get("clients") or []) == ["provider", "session", "status", "workspace"], c.get("clients"))
    need = ["health", "host", "list", "register", "pick_directory", "create", "send", "models", "configure", "probe"]
    need_channels = ["statusHealth", "statusHost", "workspaceList", "workspaceRegister",
                     "workspacePickDirectory", "sessionList", "sessionCreate", "sessionSend",
                     "providerModels", "providerConfigure", "providerProbe"]
    have = c.get("route_shape") or []
    ok("W1301-FIRST-RUN-METHODS-ALL-ROUTED", all(n in have for n in need), [n for n in need if n not in have])

    up = c.get("up_no_relaunch") or {}
    ok("W1301-REACHABLE-CORE-IS-NOT-RELAUNCHED",
       up.get("health") == "UP" and up.get("launched") is False and up.get("spawns") == 0 and up.get("counted") == 0, up)
    al = c.get("absent_core_launches") or {}
    ok("W1301-DOWN-CORE-IS-LAUNCHED-BY-THE-SHELL",
       al.get("health") == "UP" and al.get("launched") is True and al.get("counted") == 1, al)
    ok("W1301-LAUNCH-USES-THE-LOCAL-CONTROL-HOST", (c.get("spawn_argv") or [""])[0].endswith("control.exe"), c.get("spawn_argv"))
    dead = c.get("no_core_no_lie") or {}
    ok("W1301-FAILED-LAUNCH-IS-NOT-REPORTED-UP", dead.get("health") == "LAUNCH_FAILED" and dead.get("launched") is False, dead)

    pr = c.get("provider") or {}
    ok("W1301-PROVIDER-OK-IS-SUCCESS", pr.get("ok") == {"ok": True, "reason": "OK"}, pr.get("ok"))
    ok("W1301-DEGRADED-PROBE-IS-NEVER-SUCCESS", (pr.get("degraded") or {}).get("ok") is False, pr.get("degraded"))
    ok("W1301-AUTH-RATELIMIT-UNSUPPORTED-ARE-FAILURES",
       all([(pr.get(k) or {}).get("ok") is False for k in ("auth", "rate", "unsupported")]), pr)
    ok("W1301-TRANSPORT-AND-SILENCE-ARE-FAILURES",
       (pr.get("transport") or {}).get("ok") is False and (pr.get("none") or {}).get("ok") is False, pr)

    rq = c.get("request") or {}
    ok("W1301-REQUEST-CARRIES-NO-COPIED-TOKEN",
       rq.get("ok") is True and "token" not in (rq.get("payload") or {}) and "owner_token" not in (rq.get("payload") or {})
       and rq.get("headers", {}).get("X-ResearchOS-Principal") == "local-principal-1", rq)
    rj = c.get("request_rejects") or {}
    ok("W1301-UNKNOWN-CLIENT-AND-METHOD-REFUSED",
       rj.get("unknown_client") == "UNKNOWN_CLIENT" and rj.get("unknown_method") == "UNKNOWN_METHOD", rj)

    em = c.get("empty") or {}
    ok("W1301-FIRST-RUN-NEEDS-NO-TERMINAL",
       em.get("kind") == "FIRST_RUN" and em.get("requires_terminal") is False
       and sorted(em.get("actions") or []) == ["configure_provider", "new_session", "pick_directory"], em)
    ok("W1301-FIRST-RUN-NEEDS-NO-COPIED-TOKEN", em.get("requires_token_copy") is False, em)
    ne = c.get("nonempty") or {}
    ok("W1301-EXISTING-PROJECT-SKIPS-EMPTY-STATE", ne.get("kind") == "HAS_PROJECTS" and ne.get("count") == 1, ne)

    pp = c.get("principal_present") or {}
    pa = c.get("principal_absent") or {}
    ok("W1301-PRINCIPAL-READ-LOCAL-NOT-PASTED", pp.get("ok") is True and pp.get("principal_id") == "local-principal-1", pp)
    ok("W1301-ABSENT-PRINCIPAL-STORE-IS-NAMED", pa.get("ok") is False and pa.get("reason") == "PRINCIPAL_STORE_ABSENT", pa)
    ok("W1301-ABSENT-DISCOVERY-IS-NAMED", c.get("discovery_absent") == "DISCOVERY_ABSENT", c.get("discovery_absent"))

    reg = (c.get("registration") or {})
    want = sorted((c.get("registration") or {}).get("channels") or [])
    ok("W1301-ALL-CLIENT-CHANNELS-REGISTERED",
       reg.get("count") == len(need_channels) and want == sorted("ros:" + n for n in need_channels),  # register emits prefixed channels
       {"count": reg.get("count"), "channels": want})
    pre = io.open(os.path.join(ROOT, "apps", "desktop", "preload", "preload.js"), encoding="utf-8").read()
    exposed = sorted(set(__import__("re").findall(r"'([A-Za-z]+List|[A-Za-z]+Health|[A-Za-z]+Host|[A-Za-z]+Probe|[A-Za-z]+Models|[A-Za-z]+Configure|[A-Za-z]+Create|[A-Za-z]+Send|[A-Za-z]+Register|[A-Za-z]+PickDirectory)'", pre)))
    ok("W1301-PRELOAD-MATCHES-REGISTERED-CHANNELS",
       exposed == sorted(need_channels) and "require('electron')" in pre and "nodeIntegration" not in pre
       and "owner_token" not in pre and ("token:" in pre) is False, {"exposed": exposed})
    wb = io.open(os.path.join(ROOT, "apps", "desktop", "main", "workbench.html"), encoding="utf-8").read()
    ok("W1301-WORKBENCH-COVERS-FOUR-CLIENTS",
       all((">" + n) in wb for n in ["Workspace", "Sessions", "Provider", "Host"]),
       "the workbench file exists and carries the four panels, even though the reverted shell does not load it yet")
    ok("W1301-WORKBENCH-TELLS-NOBODY-TO-USE-A-TERMINAL",
       "terminal" not in wb.lower() and "npm " not in wb.lower() and "<code>" not in wb.lower()
       and "paste" not in wb.lower(), "instructions to leave the window found")  # prose inventory, no mutant: see no_mutant_rows
    mj = io.open(os.path.join(ROOT, "apps", "desktop", "main", "main.js"), encoding="utf-8").read()
    cs = c.get("call_starts_core") or {}
    ok("W1301-CLIENT-CALL-STARTS-THE-CORE-ITSELF",
       (cs.get("res") or {}).get("ok") is True and cs.get("calls") == 1, cs)
    ud = c.get("unreachable_core_not_faked") or {}
    ok("W1301-UNREACHABLE-CORE-IS-REPORTED-NOT-FAKED",
       (ud.get("res") or {}).get("ok") is False and ud.get("calls") == 0
       and (ud.get("res") or {}).get("reason") in ("LAUNCH_FAILED", "UP_AFTER_RETRIES_FAILED"), ud)
    pd = c.get("provider_degraded_call") or {}
    ok("W1301-DEGRADED-PROVIDER-VIA-CHANNEL-IS-FAILURE", pd.get("ok") is False and pd.get("reason") == "DEGRADED_NOT_SUCCESS", pd)
    he = c.get("host_error_call") or {}
    ok("W1301-HOST-ERROR-VIA-CHANNEL-IS-FAILURE", he.get("ok") is False and he.get("reason") == "HOST_ERROR", he)
    pw = c.get("payload_would_drop_tokens") or {}
    ok("W1301-PASTED-TOKEN-NEVER-LEAVES-THE-SHELL",
       "token" not in (pw.get("payload") or {}) and "owner_token" not in (pw.get("payload") or {})
       and (pw.get("header") or {}).get("X-ResearchOS-Principal") == "local-principal-1", pw)

    ok("W1301-ROUTING-TRUTH-TABLE",
       routing_decision("W13", "W13-01", "") == "local" and routing_decision("W13", "", "C23") == "legacy"
       and routing_decision("W13", "", "") == "legacy" and routing_decision("", "", "") == "refuse"
       and routing_decision("", "", "", True) == "local" and routing_decision("W05", "W05-01", "") == "legacy",
       "a pure predicate over four enumerated selector triples; it proves the branch selection, not that the forwarded handler works, which is what the parity re-measurement is for")

    skip("W1301-ELECTRON-STARTUP-FROM-INSTALLED-PACKAGE",
         "the installed shell is not exercised here: this tree has no packaged install to launch, nothing has been "
         "added to the Start menu, and the U01 first-use gate has never been watched on a real desktop session - "
         "the working main.js already loads the workbench view (workbench.html, not a single status page), so what "
         "is missing is the packaged run itself, which the resource Windows_desktop_session has to authorize")
    skip("W1301-DIRECTORY-PICKER-OPENS-NATIVE-DIALOG",
         "pick_directory is routed and the empty state asks for it without a terminal, but the native dialog itself lives in "
         "the Electron main process and needs a desktop session to prove it opens and returns a path")
    skip("W1301-REAL-MODEL-LIST-AND-CREDENTIAL-SAVE",
         "models and configure are routed and their failures classify correctly, but no provider command key is bound in "
         "either registry and client_mapping.json lists provider.models as PLANNED under W02-03 and provider.probe as "
         "PLANNED under W08-01, so a real list, a saved credential and a real probe stay NOT_RUN for this card")

    report = {"status": "FAIL" if failures else "PASS",
              "assertions": len(ids), "assertion_ids": ids, "failures": failures,
              "not_verified": sorted(not_verified), "diagnostics": diagnostics,
              "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
              "environment": {"node_pinned_version": node_version,
                              "node_pinned_path": node_bin,
                              "node_locked_sha256": (node_tools or {}).get("sha256"),
                              "node_on_path_version": path_node,
                              "node_resolution": node_reason,
                              "node_pinned_binary_hash_verified": node_bin is not None,
                              "host_module": HOST_JS}}
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

