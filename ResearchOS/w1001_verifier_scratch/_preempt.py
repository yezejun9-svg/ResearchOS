"""Prove whether the three suspected rows can ever be emitted as FAIL.
Each mutation makes the predicate the row asserts come out WRONG, then we look for a FAIL row with
that id on stdout. If the row is absent instead of FAIL, a t.Fatalf above it preempted it.
"""
import json, os, re, subprocess, sys, pathlib, hashlib

REPO = pathlib.Path(r"D:/作品集/ResearchOS/research-os")
SCR = pathlib.Path(r"D:/作品集/ResearchOS/w1001_verifier_scratch")
GO = REPO / ".local/tools/go1.27.1/go/bin/go.exe"
ENV = dict(os.environ, GOTOOLCHAIN="local", GOENV="off",
           GOPATH=str(REPO / ".local/gopath"), GOCACHE=str(REPO / ".local/gocache"),
           PYTHONIOENCODING="utf-8", RESEARCHOS_GO=str(GO))

EXP = SCR / "internal/domain/experiments.go"
PRISTINE_EXP = subprocess.run(["git", "-C", str(REPO), "show", "2ce7fcfc:internal/domain/experiments.go"],
                              capture_output=True).stdout
assert EXP.read_bytes() == PRISTINE_EXP, "scratch experiments.go diverged"


def domain():
    r = subprocess.run([str(GO), "test", "./internal/domain", "-run", "TestW1001", "-count=1", "-v"],
                       cwd=str(SCR), env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    out = (r.stdout or "") + (r.stderr or "")
    rows = {}
    for line in out.splitlines():
        m = re.match(r"^\s*W10_ASSERTION\s+(\{.*\})$", line)
        if m:
            d = json.loads(m.group(1))
            rows[d["assertion_id"]] = d["status"]
    return r.returncode, rows, out


def probe(name, old, new, row_id):
    txt = PRISTINE_EXP.decode("utf-8")
    if txt.count(old) != 1:
        print(name, "ANCHOR PROBLEM count=", txt.count(old)); return
    EXP.write_text(txt.replace(old, new, 1), encoding="utf-8")
    rc, rows, out = domain()
    present = row_id in rows
    print("\n###", name)
    print(json.dumps({"row_id": row_id, "suite_rc": rc, "rows_emitted": len(rows),
                      "row_was_emitted": present,
                      "row_status": rows.get(row_id, "ABSENT"),
                      "VERDICT": ("row went RED" if rows.get(row_id) == "FAIL"
                                  else ("row silently VANISHED (preempted by t.Fatalf)"
                                        if not present else "row stayed PASS -> predicate not broken"))},
                     ensure_ascii=False, indent=1))
    EXP.write_bytes(PRISTINE_EXP)


# 1. make BETWEEN reject an in-range candidate -> W1001-BETWEEN-OPERATOR-EVALUATES-BOTH-ENDS must go red
probe("MUT-A BETWEEN cannot evaluate the upper end",
      'pass = cmp >= 0 && v.Cmp(upper) <= 0', 'pass = false',
      "W1001-BETWEEN-OPERATOR-EVALUATES-BOTH-ENDS")

# 2. make a zero sample_count measurable -> W1001-ZERO-SAMPLE_AND_ABSENT_ARM... must go red
probe("MUT-B zero sample no longer inconclusive",
      'if r["baseline"] == nil || r["candidate"] == nil || n == 0 {',
      'if false {',
      "W1001-ZERO-SAMPLE_AND_ABSENT_ARM_ARE_BOTH_INCONCLUSIVE_AT_METRIC_LEVEL")

# 3. make the second retained run not register -> W1001-TWO-ATTEMPTS... must go red
probe("MUT-C retained run ids not accumulated",
      'x["run_ids"] = append(Arr(x, "run_ids"), runID)',
      'x["run_ids"] = append(Arr(x, "run_ids")[:0], runID)',
      "W1001-TWO-ATTEMPTS-PRODUCE-TWO-RETAINED-RUN-IDS")

print("\nrestored byte-identical:", EXP.read_bytes() == PRISTINE_EXP,
      hashlib.sha256(EXP.read_bytes()).hexdigest()[:12])
