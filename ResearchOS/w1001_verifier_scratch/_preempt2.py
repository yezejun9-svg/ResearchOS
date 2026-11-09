"""Second attempt: compile-clean mutations, and a build-error guard so a red herring is not read as
a preemption. For each row we ask two different questions:
  (i) break the predicate the row asserts  -> does the row itself report FAIL, or does it vanish?
  (ii) break one LEG of the predicate      -> does anything in the roster notice at all?
"""
import json, os, re, subprocess, sys, pathlib, hashlib

REPO = pathlib.Path(r"D:/作品集/ResearchOS/research-os")
SCR = pathlib.Path(r"D:/作品集/ResearchOS/w1001_verifier_scratch")
GO = REPO / ".local/tools/go1.27.1/go/bin/go.exe"
ENV = dict(os.environ, GOTOOLCHAIN="local", GOENV="off",
           GOPATH=str(REPO / ".local/gopath"), GOCACHE=str(REPO / ".local/gocache"),
           PYTHONIOENCODING="utf-8", RESEARCHOS_GO=str(GO))
EXP = SCR / "internal/domain/experiments.go"
PRISTINE = subprocess.run(["git", "-C", str(REPO), "show", "2ce7fcfc:internal/domain/experiments.go"],
                          capture_output=True).stdout


def domain():
    r = subprocess.run([str(GO), "test", "./internal/domain", "-run", "TestW1001", "-count=1", "-v"],
                       cwd=str(SCR), env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    out = (r.stdout or "") + (r.stderr or "")
    rows = {}
    for line in out.splitlines():
        m = re.match(r"^\s*W10_ASSERTION\s+(\{.*\})$", line)
        if m:
            try:
                d = json.loads(m.group(1)); rows[d["assertion_id"]] = d["status"]
            except Exception:
                pass
    build_err = bool(re.search(r"\.go:\d+:\d+: (declared and not used|undefined|syntax error)", out))
    return r.returncode, rows, build_err, out


def probe(name, old, new, row_id, also_whole_roster=False):
    txt = PRISTINE.decode("utf-8")
    if txt.count(old) != 1:
        print("\n###", name, "\n  ANCHOR PROBLEM count=", txt.count(old)); return
    EXP.write_text(txt.replace(old, new, 1), encoding="utf-8")
    rc, rows, build_err, out = domain()
    res = {"mutant": name, "row_id": row_id, "BUILD_ERROR": build_err, "suite_rc": rc,
           "rows_emitted": len(rows)}
    if build_err:
        res["note"] = "mutation did not compile - discarded, not evidence"
    else:
        res["row_emitted"] = row_id in rows
        res["row_status"] = rows.get(row_id, "ABSENT")
        res["red_rows"] = sorted(i for i, s in rows.items() if s != "PASS")
        res["reading"] = ("row reported FAIL" if rows.get(row_id) == "FAIL"
                          else "row VANISHED (a t.Fatalf above it aborted the test)" if row_id not in rows
                          else "row stayed PASS - the mutation is INVISIBLE to the row it should break")
    EXP.write_bytes(PRISTINE)
    print("\n###", name)
    print(json.dumps(res, ensure_ascii=False, indent=1))


# (i) BETWEEN: drop only the upper-end leg. The card's test feeds candidate 42 into [10,50].
probe("MUT-A2 BETWEEN ignores its upper bound (leg dropped)",
      "pass = cmp >= 0 && v.Cmp(upper) <= 0", "pass = cmp >= 0 && v.Cmp(upper) <= 1000000",
      "W1001-BETWEEN-OPERATOR-EVALUATES-BOTH-ENDS")

# (ii) zero-sample leg made never-true but still referencing n so it compiles
probe("MUT-B2 zero sample_count no longer inconclusive",
      'if r["baseline"] == nil || r["candidate"] == nil || n == 0 {',
      'if r["baseline"] == nil || r["candidate"] == nil || n < 0 {',
      "W1001-ZERO-SAMPLE_AND_ABSENT_ARM_ARE_BOTH_INCONCLUSIVE_AT_METRIC_LEVEL")

print("\nrestored:", EXP.read_bytes() == PRISTINE, hashlib.sha256(EXP.read_bytes()).hexdigest()[:12])
