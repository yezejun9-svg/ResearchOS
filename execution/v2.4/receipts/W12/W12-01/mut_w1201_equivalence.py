"""W12-01 mutation self-check, second round: anchors are discovered at runtime.

The first run (4ff99c86) recorded one survivor and three cases whose hard-coded anchors no longer
matched the file byte-for-byte. Hard-coding indentation makes a mutation study silently weaker than it
looks: the case does not fail, it simply never runs. Here every case names a substring that must occur
exactly once, the enclosing line is read out of the file at run time, and the mutation rewrites that
line while keeping its real leading whitespace. A case whose marker is missing or ambiguous is reported
as anchor-missing and is treated as an untested guard, never as a pass.
"""
import io, json, os, subprocess, sys, hashlib

def _find_repo(start):
    d = start
    for _ in range(8):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("cannot locate the repository root from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
BUDGET = os.path.join("internal", "domain", "budget.go")
SCOPES = os.path.join("internal", "domain", "budget_scopes.go")

# marker: unique substring of the line to change; body: the replacement text for that line, without
# its leading whitespace. Guardless means the case flips a refusal open, and the named id must die.
CASES = [
 {"id": "E1-disjunction-drops-strict-term", "file": BUDGET,
  "marker": 'if unknown && (p["enforcement"] == "STRICT" || p["unknown_cost_action"] == "BLOCK") {',
  "body": 'if unknown && p["unknown_cost_action"] == "BLOCK" { // EQUIVALENCE PROBE: the STRICT term is protocol-redundant'},
]

# This runner is deliberately NOT the matrix: it asks whether one term of the disjunction can be
# removed without any observable change. The frozen client protocol forces unknown_cost_action=BLOCK
# whenever enforcement=STRICT (UpdateBudgetRequest allOf), so no legal policy separates the two terms
# and a probe that killed E1 could only be satisfied by an illegal policy. A survivor here is the
# finding, not a defect, which is why it is filed outside the matrix's "0 survived" claim.

env = dict(os.environ)
env.update({"GOTOOLCHAIN": "local", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"),
            "RESEARCHOS_GO": GO, "RESEARCHOS_TASK_ID": "W12", "RESEARCHOS_CHECK_ID": "W12-01"})


def run_check():
    p = subprocess.run([GO, "run", "./tests/resources/check"], cwd=REPO, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    lines = [l for l in (p.stdout or "").splitlines() if l.startswith("{")]
    return (json.loads(lines[-1]) if lines else None), p


def locate(text, marker):
    hits = [i for i, l in enumerate(text.split("\n")) if marker in l]
    if len(hits) != 1:
        return None, len(hits)
    return hits[0], 1


base, proc = run_check()
if base is None or base.get("status") != "PASS":
    print("preflight not green:", json.dumps((base or {}).get("failures"), ensure_ascii=True)[:400])
    sys.exit(1)
baseline_count = base["assertions"]
print("preflight PASS", baseline_count)

results = []
for case in CASES:
    path = os.path.join(REPO, case["file"])
    original = io.open(path, encoding="utf-8").read()
    entry = {"id": case["id"], "file": case["file"], "bucket": None, "killed": [], "detail": ""}
    idx, hits = locate(original, case["marker"])
    if idx is None:
        entry["bucket"] = "anchor-missing"
        entry["detail"] = "marker occurs %d times" % hits
        results.append(entry)
        print(entry["id"], "->", entry["bucket"], entry["detail"])
        continue
    lines = original.split("\n")
    line = lines[idx]
    ws = line[:len(line) - len(line.lstrip("\t "))]
    lines[idx] = ws + (case["body"] if case["body"] is not None
                       else line.replace(case["marker"], case["marker"] + case["append"]))
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    try:
        report, proc = run_check()
        if report is None:
            entry["bucket"] = "crashed"
            entry["detail"] = ((proc.stderr or "") + (proc.stdout or ""))[-300:]
        else:
            killed = sorted({f["id"] for f in (report.get("failures") or [])})
            entry["killed"] = killed
            entry["report_status"] = report.get("status")
            entry["assertions"] = report.get("assertions")
            entry["bucket"] = "caught" if killed else "survived"
    except subprocess.TimeoutExpired:
        entry["bucket"] = "crashed"
        entry["detail"] = "timeout"
    finally:
        io.open(path, "w", encoding="utf-8", newline="\n").write(original)
        entry["restored"] = (hashlib.sha256(open(path, "rb").read()).hexdigest() ==
                             hashlib.sha256(original.encode("utf-8")).hexdigest())
    results.append(entry)
    print(entry["id"], "->", entry["bucket"], "| killed:",
          entry["killed"] or entry["detail"][:110])

dirty = subprocess.run(["git", "status", "--porcelain", "--", "internal", "tests"], cwd=REPO,
                       capture_output=True, text=True).stdout.strip()
summary = {"cases": len(results), "baseline_assertions": baseline_count,
           "buckets": {b: sum(1 for r in results if r["bucket"] == b)
                       for b in ("caught", "survived", "crashed", "anchor-missing")},
           "tree_clean_after_restore": dirty == "", "results": results}
out = os.path.join(REPO, ".local", "mutation_equivalence_w1201.json")
io.open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(summary, indent=1, ensure_ascii=False))
print(json.dumps(summary["buckets"]), "| tree clean:", summary["tree_clean_after_restore"])
