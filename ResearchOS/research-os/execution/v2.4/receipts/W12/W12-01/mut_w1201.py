"""W12-01 mutation self-check: does each named assertion die for the reason its label claims?

Each case replaces one precise span of the product code with a weaker version, runs the card's
qualification program, records which named assertion ids fail, and restores the file byte-for-byte.
Cases are bucketed caught / crashed / survived / anchor-missing, and a survivor is only acceptable
with a stated reason - a claim of a complete list that omits reachable branches is the mistake a
previous review rejected.
"""
import io, json, os, subprocess, sys, hashlib

REPO = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(REPO, ".."))
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")

BUDGET = os.path.join("internal", "domain", "budget.go")
SCOPES = os.path.join("internal", "domain", "budget_scopes.go")

CASES = [
 {"id": "T1-no-takeover-release", "file": SCOPES,
  "from": "\t\tholds = append(holds, o)",
  "to": "\t\t_ = o // MUTANT: a dead epoch's hold is left open"},
 {"id": "T2-replay-falls-through", "file": SCOPES,
  "from": "\tif admitted != 0 {\n\t\treturn nil\n\t}",
  "to": "\tif false { // MUTANT: a repeated control request is re-charged\n\t\treturn nil\n\t}"},
 {"id": "T3-unknown-may-carry-money", "file": BUDGET,
  "from": "\t\tif b[\"money\"] != nil || basis != \"UNKNOWN\" {",
  "to": "\t\tif false { // MUTANT: an invented amount is accepted for an unknown cost"},
 {"id": "T4-strict-accepts-unproven-estimate", "file": BUDGET,
  "from": "\t\t\tif p[\"enforcement\"] == \"STRICT\" && basis != \"UPPER_BOUND\" {",
  "to": "\t\t\tif false { // MUTANT: a strict cap admits a cost nobody bounded"},
 {"id": "T5-strict-ignores-unresolved-unknown", "file": BUDGET,
  "from": "\t\t\t\tif unknown && (p[\"enforcement\"] == \"STRICT\" || p[\"unknown_cost_action\"] == \"BLOCK\") {",
  "to": "\t\t\t\tif false { // MUTANT: an unresolved liability stops nothing"},
 {"id": "T6-over-cap-admitted", "file": BUDGET,
  "from": "\t\t\t\tif used.Add(used, n).Cmp(limit) > 0 {",
  "to": "\t\t\t\tif false { // MUTANT: the cap is computed and then ignored"},
 {"id": "T7-settlement-binds-anything", "file": BUDGET,
  "from": "\t\tif reservation[\"reservation_id\"] != nil || reservation[\"run_id\"] != run[\"id\"] || reservation[\"provider_request_id\"] != b[\"provider_request_id\"] || reservation[\"policy_id\"] != leaf || (reservation[\"operation\"] != \"RESERVE\" && reservation[\"operation\"] != \"UNKNOWN\") {",
  "to": "\t\tif false { // MUTANT: a settlement may name any reservation"},
 {"id": "T8-second-commit-allowed", "file": BUDGET,
  "from": "\t\tif terminal != 0 && op != \"RECONCILE\" {",
  "to": "\t\tif false { // MUTANT: an already settled request may be committed twice"},
 {"id": "T10-strict-allows-unknown", "file": BUDGET,
  "from": "					if p[\"enforcement\"] == \"STRICT\" || p[\"unknown_cost_action\"] == \"BLOCK\" {",
  "to": "					if false { // MUTANT: an unknown cost passes a strict cap"},
 {"id": "T9-duplicate-event-recounted", "file": BUDGET,
  "from": "\t\tif Hash(payload) != Hash(b) {\n\t\t\treturn nil, Fail(409, \"IDEMPOTENCY_CONFLICT\", \"provider event payload changed\")\n\t\t}\n\t\treturn o, nil",
  "to": "\t\t_ = payload // MUTANT: a repeated provider event creates another entry\n\t\treturn Object{}, sql.ErrNoRows"},
]

env = dict(os.environ)
env.update({"GOTOOLCHAIN": "local", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"),
            "RESEARCHOS_GO": GO, "RESEARCHOS_TASK_ID": "W12", "RESEARCHOS_CHECK_ID": "W12-01"})


def run_check():
    p = subprocess.run([GO, "run", "./tests/resources/check"], cwd=REPO, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    lines = [l for l in (p.stdout or "").splitlines() if l.startswith("{")]
    if not lines:
        return None, p
    return json.loads(lines[-1]), p


base, proc = run_check()
if base is None or base.get("status") != "PASS":
    print("preflight failed:", (proc.stdout or "")[-300:], (proc.stderr or "")[-300:])
    sys.exit(1)
print("preflight PASS", base["assertions"], "ids; baseline failures:", base.get("failures"))

results = []
for case in CASES:
    path = os.path.join(REPO, case["file"])
    original = io.open(path, encoding="utf-8").read()
    entry = {"id": case["id"], "file": case["file"], "bucket": None, "killed": [], "detail": ""}
    if original.count(case["from"]) != 1:
        entry["bucket"] = "anchor-missing"
        entry["detail"] = "anchor occurs %d times" % original.count(case["from"])
        results.append(entry)
        print(entry["id"], "->", entry["bucket"], entry["detail"])
        continue
    mutated = original.replace(case["from"], case["to"])
    io.open(path, "w", encoding="utf-8", newline="\n").write(mutated)
    try:
        report, proc = run_check()
        if report is None:
            entry["bucket"] = "crashed"
            entry["detail"] = ((proc.stderr or "") + (proc.stdout or ""))[-400:]
        else:
            killed = sorted({f["id"] for f in (report.get("failures") or [])})
            entry["killed"] = killed
            entry["bucket"] = "caught" if killed else "survived"
            entry["report_status"] = report.get("status")
            entry["assertions"] = report.get("assertions")
    except subprocess.TimeoutExpired:
        entry["bucket"] = "crashed"
        entry["detail"] = "timeout"
    finally:
        io.open(path, "w", encoding="utf-8", newline="\n").write(original)
        restored = hashlib.sha256(open(path, "rb").read()).hexdigest()
        entry["restored"] = restored == hashlib.sha256(original.encode("utf-8")).hexdigest()
    results.append(entry)
    print(entry["id"], "->", entry["bucket"], "| killed:", entry["killed"] or entry["detail"][:120])

dirty = subprocess.run(["git", "status", "--porcelain", "--", "internal"], cwd=REPO,
                       capture_output=True, text=True).stdout.strip()
summary = {"cases": len(results),
           "buckets": {b: sum(1 for r in results if r["bucket"] == b)
                       for b in ("caught", "survived", "crashed", "anchor-missing")},
           "tree_clean_after_restore": dirty == "", "results": results}
out = os.path.join(REPO, ".local", "mutation_selfcheck_w1201.json")
io.open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(summary, indent=1, ensure_ascii=False))
print(json.dumps(summary["buckets"], ensure_ascii=False), "| tree clean:", summary["tree_clean_after_restore"])
print("written", out)
