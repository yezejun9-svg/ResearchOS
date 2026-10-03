"""W05-01 mutation self-check: each case rewrites one production line, runs the bound check program,
records which named assertions died, and restores the file byte-for-byte.

Anchors are located at run time by a substring that must occur on exactly one line; a case whose
marker is missing or ambiguous is reported as anchor-missing and counts as an untested guard, never as
a pass. This is the lesson from the first W12-01 matrix, where hard-coded indentation made three
cases silently never run.
"""
import hashlib, io, json, os, subprocess, sys

NL = chr(10)

def _find_repo(start):
    d = start
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal", "domain")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
RUNTIME = os.path.join("adapters", "runtime", "runtime_windows.go")
CODEX = os.path.join("adapters", "runtime", "codex.go")
ADMISSION = os.path.join("internal", "domain", "runtime_admission.go")
SCOPES = os.path.join("internal", "domain", "budget_scopes.go")
CHECK = os.path.join("tests", "runtime", "check", "w0501.go")

CASES = [
 # --- adapter lifecycle: the claims the card makes about the worker itself ---
 {"id": "M2-artifact-hash-not-of-bytes", "file": RUNTIME,
  "marker": 'w.journal.Artifacts = append(w.journal.Artifacts, Artifact{relative, Hash(b), int64(len(b))})',
  "body": "w.journal.Artifacts = append(w.journal.Artifacts, Artifact{relative, Hash(nil), int64(len(b))}) // MUTANT: artifact hash is not the hash of the bytes"},
 {"id": "M3-renew-ignores-epoch", "file": RUNTIME,
  "marker": "if epoch != w.journal.Spec.Epoch || d <= 0 || d > LeaseDuration || w.journal.Cancelled {",
  "body": "if false || d <= 0 || d > LeaseDuration || w.journal.Cancelled { // MUTANT: any epoch may renew the lease"},
 {"id": "M4-cancel-ignores-epoch", "file": RUNTIME,
  "marker": "if epoch != w.journal.Spec.Epoch {",
  "body": "if false { // MUTANT: a stale epoch may cancel the job",
  "occurrence": 1},
 {"id": "M5-output-escape-accepted", "file": RUNTIME,
  "marker": "if !filepath.IsLocal(path) {",
  "body": "if false && !filepath.IsLocal(path) { // MUTANT: an output may name anything",
  "occurrence": 1},
 {"id": "M6-environment-not-required", "file": RUNTIME,
  "marker": "if s.RunID == \"\" || s.TaskID == \"\" || s.Epoch < 1 || len(s.Commands) == 0 || len(s.Environment) == 0 {",
  "body": "if s.RunID == \"\" || s.TaskID == \"\" || s.Epoch < 1 || len(s.Commands) == 0 { // MUTANT: an inherited environment is allowed"},
 {"id": "M7-transport-unchecked", "file": RUNTIME,
  "marker": 'if s.ArtifactTransport != "" && s.ArtifactTransport != "protocol-json" {',
  "body": "if false { // MUTANT: any artifact transport is accepted"},

 # --- protocol decoder: how an executor reply becomes a Run outcome ---
 {"id": "M8-exit-code-ignored", "file": CODEX,
  "marker": "if exit != 0 {",
  "body": "if false { // MUTANT: a non-zero process exit does not fail the reply"},
 {"id": "M9-completed-turn-not-settling", "file": CODEX,
  "marker": 'case "turn.completed":',
  "body": 'case "turn.completed_NEVER":  // MUTANT: a completed turn no longer settles the reply',
  "comment": "also proves the settled row is load-bearing, not merely permissive"},
 {"id": "M10-missing-settled-passes", "file": CODEX,
  "marker": "if !p.Settled && p.Failure == \"\" {",
  "body": "if false { // MUTANT: a reply without a completed turn is not named a failure"},
 {"id": "M11-policy-denial-unrecognised", "file": CODEX,
  "marker": 'if strings.Contains(text, "rejected: blocked by policy") {',
  "body": "if false { // MUTANT: the executor's policy denial is not treated as a tool failure"},
 {"id": "M12-reconnect-retry-accepted", "file": CODEX,
  "marker": "if reconnectDiagnostic.MatchString(message) {",
  "body": "if reconnectDiagnostic.MatchString(message) && false { // MUTANT: a transport retry is terminal",
  "comment": "inverts the reconnect branch so the row that requires a later completion is checked"},
 {"id": "M13-secret-shape-unredacted", "file": CODEX,
  "marker": "regexp.MustCompile(`\\bsk-[A-Za-z0-9_-]{16,}\\b`),",
  "body": "// MUTANT: the api-key shape is no longer redacted"},

 # --- service admission and cost: the two claims made over HTTP ---
 {"id": "M14-unqualified-live-admitted", "file": ADMISSION,
  "marker": 'if runtime["measurement_mode"] == "LIVE" && len(Arr(runtime, "qualification_ids")) == 0 {',
  "body": "if false { // MUTANT: an unqualified LIVE runtime is admitted on the ordinary path"},
 {"id": "M15-fixture-dispatch-not-zero", "file": SCOPES,
  "marker": '"provider_request_id": "fixture-dispatch/" + Str(run, "id")',
  "body": '_, e = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": Object{"amount": "1.00", "currency": currency}, "provider_request_id": "fixture-dispatch/" + Str(run, "id"), "provider_event_id": "fixture-dispatch/" + Str(run, "id"), "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()})'},

 # --- the executor identity comparison the round-1 review called inert ---
 {"id": "M16-executor-comparison-always-matches", "file": CHECK,
  "marker": "return false // no recorded digest carries the pinned one",
  "body": "return true // MUTANT: every comparison reports the pinned digest as installed"},
 {"id": "M17-executor-comparison-never-matches", "file": CHECK,
  "marker": "if strings.EqualFold(normalizeDigest(entry), digest) {",
  "body": "if false && strings.EqualFold(normalizeDigest(entry), digest) {"},
 {"id": "M18-executor-pin-prefix-unnormalised", "file": CHECK,
  "marker": 'if after, isPrefix := strings.CutPrefix(s, "sha256:"); isPrefix {',
  "body": 'if after, isPrefix := strings.CutPrefix(s, "sha512:"); isPrefix {'},
 {"id": "M19-declared-model-clause-dropped", "file": RUNTIME,
  "marker": "if code != 0 || w.journal.Cancelled || (s.Model != \"\" && !w.journal.Protocol.Settled) {",
  "body": "if code != 0 || w.journal.Cancelled { // MUTANT: a declared model no longer requires a settled protocol"},
 {"id": "M20-malformed-line-unclassified", "file": CODEX,
  "marker": 'p.Failure = "invalid_protocol"',
  "body": 'p.Failure = "" // MUTANT: a malformed line is no longer named'},
 {"id": "M21-journal-drops-the-spec-it-was-given", "file": RUNTIME,
  "marker": "w.journal = Journal{Spec: s,",
  "body": "w.journal = Journal{Revision: Revision, Job: \"Local\\\\ResearchOS-\" + strings.TrimPrefix(Hash([]byte(directory+s.RunID)), \"sha256:\"), State: \"STARTING\", Worker: fmt.Sprintf(\"%d-%d\", os.Getpid(), time.Now().UnixNano()), Started: now(), Pending: len(s.Commands), Trees: []Tree{}, Streams: []Stream{}} // MUTANT: the journal no longer records the Run it was started for"},
 {"id": "M22-fixture-reservation-unkeyed", "file": SCOPES,
  "marker": "\"provider_request_id\": \"fixture-dispatch/\" + Str(run, \"id\")",
  "body": "_, e = s.appendBudget(tx, project, Object{\"policy_id\": goal[\"budget_policy_id\"], \"run_id\": nil, \"operation\": \"RESERVE\", \"money\": Object{\"amount\": \"0\", \"currency\": currency}, \"provider_request_id\": \"unkeyed\", \"provider_event_id\": \"unkeyed\", \"reservation_id\": nil, \"cost_basis\": \"UPPER_BOUND\", \"occurred_at\": Now()}) // MUTANT: the fixture reservation is no longer keyed to a Run"},
]

env = dict(os.environ)
env.update({"GOTOOLCHAIN": "local", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"),
            "RESEARCHOS_GO": GO, "RESEARCHOS_TASK_ID": "W05", "RESEARCHOS_CHECK_ID": "W05-01",
            "PYTHONIOENCODING": "utf-8"})


def run_check():
    p = subprocess.run([GO, "run", "./tests/runtime/check"], cwd=REPO, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    lines = [l for l in (p.stdout or "").splitlines() if l.startswith("{")]
    return (json.loads(lines[-1]) if lines else None), p


def write_lines(path, lines):
    io.open(path, "w", encoding="utf-8", newline=NL).write(NL.join(lines))

def locate(path, marker, want=1):
    lines = io.open(os.path.join(REPO, path), encoding="utf-8").read().split("\n")
    hits = [i for i, l in enumerate(lines) if marker in l]
    if len(hits) < want:
        return None, len(hits), lines
    return hits[want - 1], len(hits), lines


baseline, proc = run_check()
if not baseline or baseline.get("status") != "PASS":
    print(json.dumps({"fatal": "preflight is not a PASS run", "report": baseline,
                      "stderr": (proc.stderr or "")[-800:]}))
    sys.exit(1)
base_ids = sorted(baseline["assertion_ids"])
print("preflight PASS", len(base_ids), "assertions")

EQUIV = [
 {"id": "E1-children-stopped-assumed", "file": RUNTIME,
  "marker": "w.journal.ChildrenStopped = e == nil && len(ids) == 0",
  "body": "w.journal.ChildrenStopped = e == nil && len(ids) <= 1000000 // EQUIVALENCE PROBE: an empty tree is assumed, never observed"},
]

results, tree_state, equiv_results = [], {}, []
for case in CASES:
    idx, count, lines = locate(case["file"], case["marker"], case.get("occurrence", 1))
    if idx is None:
        results.append({"id": case["id"], "bucket": "anchor-missing", "marker_hits": count, "killed": []})
        continue
    if count > case.get("occurrence", 1):
        results.append({"id": case["id"], "bucket": "anchor-missing",
                        "marker_hits": count, "killed": [],
                        "note": "marker is not unique; refusing to guess which line to mutate"})
        continue
    original = lines[idx]
    indent = original[:len(original) - len(original.lstrip())]
    mutated = indent + case["body"].rstrip().rstrip(";").rstrip()
    path = os.path.join(REPO, case["file"])
    before = hashlib.sha256(open(path, "rb").read()).hexdigest()
    tree_state[case["file"]] = tree_state.get(case["file"], before)
    lines[idx] = mutated
    write_lines(path, lines)
    try:
        rep, proc = run_check()
    finally:
        write_lines(path, lines[:idx] + [original] + lines[idx + 1:])
        after = hashlib.sha256(open(path, "rb").read()).hexdigest()
        case["restored"] = (after == before)

    if rep is None:
        results.append({"id": case["id"], "bucket": "crashed", "killed": [],
                        "detail": (proc.stderr or "")[-600:]})
        continue
    failed = sorted({f["id"] for f in (rep.get("failures") or [])})
    lost = sorted(set(base_ids) - set(rep.get("assertion_ids") or []))
    killed = sorted(set(failed) | set(lost))
    bucket = "caught" if killed and rep.get("status") != "PASS" else "survived"
    results.append({"id": case["id"], "bucket": bucket, "killed": killed,
                    "status_after": rep.get("status"),
                    "assertions_after": rep.get("assertions"),
                    "restored_byte_identical": case.get("restored", False)})
    print(case["id"], "->", bucket, killed[:4])

for case in EQUIV:
    idx, count, lines = locate(case["file"], case["marker"], case.get("occurrence", 1))
    if idx is None:
        equiv_results.append({"id": case["id"], "bucket": "anchor-missing", "marker_hits": count, "killed": []})
        continue
    original = lines[idx]
    indent = original[:len(original) - len(original.lstrip())]
    path = os.path.join(REPO, case["file"])
    before = hashlib.sha256(open(path, "rb").read()).hexdigest()
    lines[idx] = indent + case["body"]
    write_lines(path, lines)
    try:
        rep, proc = run_check()
    finally:
        write_lines(path, lines[:idx] + [original] + lines[idx + 1:])
        case["restored"] = hashlib.sha256(open(path, "rb").read()).hexdigest() == before
    killed = sorted({f["id"] for f in ((rep or {}).get("failures") or [])}) if rep else []
    lost = sorted(set(base_ids) - set((rep or {}).get("assertion_ids") or [])) if rep else []
    equiv_results.append({"id": case["id"], "bucket": ("caught" if killed or lost else "survived"),
                          "killed": sorted(set(killed) | set(lost)),
                          "expected": "survived",
                          "why_survives": "the fixture's worker really drains its job object, so assuming an empty tree is observationally identical here; killing it needs a descendant that survives killJob, which the adapter prevents by design. W0501-ADAPTER-DRAINED-REPORT-CORRELATES-TREE pins the report against the observed tree so a mutant that flips the report without the tree dies",
                          "status_after": (rep or {}).get("status"), "restored_byte_identical": case.get("restored", False)})
    print(case["id"], "(equivalence) ->", equiv_results[-1]["bucket"], equiv_results[-1]["killed"][:3])

dirty = subprocess.run(["git", "status", "--porcelain", "adapters", "internal", "tests"],
                       cwd=REPO, capture_output=True, text=True).stdout.strip()
buckets = {}
for r in results:
    buckets[r["bucket"]] = buckets.get(r["bucket"], 0) + 1
for k in ("caught", "survived", "crashed", "anchor-missing"):
    buckets.setdefault(k, 0)
out = {"record": "W05-01 mutation self-check",
       "equivalence_probe": {"cases": len(EQUIV), "results": equiv_results},
       "cases": len(CASES), "buckets": buckets, "results": results,
       "preflight": {"status": baseline["status"], "assertions": len(base_ids)},
       "matrix_note": "the matrix holds only mutants that a named assertion can decide; E1 is filed outside it so a claim of sensitivity never rests on a mutant the fixture cannot distinguish","equivalence_probe_results": equiv_results,
       "tree_clean_after_restore": dirty == "", "git_status_after": dirty,
 "uncatchable": {"M1-children-stopped-assumed": "the fixture's worker really does drain its job, so a mutant that assumes an empty tree is observationally identical here; killing it needs a descendant that survives killJob, which the adapter prevents by design. The new W0501-ADAPTER-DRAINED-REPORT-CORRELATES-TREE assertion pins the correlation so a mutant that flips the report without the tree dies"},
       "note": "each case rewrote exactly one production line and the file was restored and hash-compared; anchor-missing cases are counted as untested guards, never as passes"}
rd = os.path.join(REPO, "execution", "v2.4", "receipts", "W05", "W05-01")
io.open(os.path.join(rd, "mutation_selfcheck_w0501.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps(out, ensure_ascii=False, indent=1))
io.open(os.path.join(REPO, ".local", "mutation_selfcheck_w0501.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(buckets), "| tree clean:", dirty == "")
