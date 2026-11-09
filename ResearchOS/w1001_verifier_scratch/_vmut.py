"""Verifier-side mutation runs (scratch copy only; the repository is never written)."""
import json, os, re, subprocess, sys, pathlib, hashlib

REPO = pathlib.Path(r"D:/作品集/ResearchOS/research-os")
SCR = pathlib.Path(r"D:/作品集/ResearchOS/w1001_verifier_scratch")
GO = REPO / ".local/tools/go1.27.1/go/bin/go.exe"
ENV = dict(os.environ, GOTOOLCHAIN="local", GOENV="off",
           GOPATH=str(REPO / ".local/gopath"), GOCACHE=str(REPO / ".local/gocache"),
           PYTHONIOENCODING="utf-8", RESEARCHOS_GO=str(GO))

REL = {"experiments.go": "internal/domain/experiments.go",
       "test.go": "internal/domain/experiments_w1001_test.go",
       "main.py": "tests/experiments/check/main.py"}
TARGETS = {k: SCR / v for k, v in REL.items()}

# set my own counterexample test aside so the baseline is the card's suite alone
mine = TARGETS["test.go"].parent / "zz_verifier_w1001_test.go"
if mine.exists():
    mine.rename(SCR / "_setaside_zz_verifier_w1001_test.go.txt")

PRISTINE = {}
for k, p in TARGETS.items():
    blob = subprocess.run(["git", "-C", str(REPO), "show", "2ce7fcfc:" + REL[k]], capture_output=True).stdout
    PRISTINE[k] = blob
    assert p.read_bytes() == blob, "scratch diverged from 2ce7fcfc: " + k


def restore():
    for k, p in TARGETS.items():
        p.write_bytes(PRISTINE[k])
    return all(p.read_bytes() == PRISTINE[k] for k, p in TARGETS.items())


def parse_rows(out):
    rows = {}
    for line in out.splitlines():
        m = re.match(r"^\s*W10_ASSERTION\s+(\{.*\})$", line)
        if m:
            try:
                d = json.loads(m.group(1))
            except Exception:
                continue
            rows[d["assertion_id"]] = d["status"]
    return rows


def run_domain():
    r = subprocess.run([str(GO), "test", "./internal/domain", "-run", "TestW1001", "-count=1", "-v"],
                       cwd=str(SCR), env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, parse_rows(out), out


def run_domain_full():
    """The card's real domain selection: TestW10|TestW1001, which is what the bound command runs."""
    r = subprocess.run([str(GO), "test", "./internal/domain", "-run", "TestW10|TestW1001", "-count=1", "-v"],
                       cwd=str(SCR), env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, parse_rows(out), out


def run_handler():
    r = subprocess.run([sys.executable, "-X", "utf8", str(TARGETS["main.py"])], cwd=str(SCR),
                       env=dict(ENV, RESEARCHOS_TASK_ID="W10", RESEARCHOS_CHECK_ID="W10-01"),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    try:
        d = json.loads(r.stdout)
    except Exception:
        return r.returncode, {}, (r.stdout or "") + (r.stderr or "")
    st = {x["assertion_id"]: x["status"] for x in d.get("rows", [])}
    for f in d.get("failures", []):
        st[f["id"]] = "FAIL"          # handler-detected anomalies are reds too
    st["__handler_status__"] = d.get("status")
    st["__handler_assertions__"] = d.get("assertions")
    return r.returncode, st, r.stdout


def trial(name, key, old, new, runner, expect_red):
    txt = PRISTINE[key].decode("utf-8")
    if txt.count(old) != 1:
        print("\n### %s -> ANCHOR PROBLEM (count=%d)" % (name, txt.count(old)))
        return
    TARGETS[key].write_text(txt.replace(old, new, 1), encoding="utf-8")
    rc, rows, out = runner()
    compile_failed = "build failed" in out or "[setup failed]" in out
    red = sorted(i for i, s in rows.items() if s != "PASS" and not i.startswith("__"))
    entry = {"mutant": name, "file": key, "rc": rc, "rows_emitted": len(rows), "red_rows": red[:8],
             "named_row_expected": expect_red,
             "caught_by_named_row": (expect_red in red) if expect_red else None,
             "survives_unchanged": (len(red) == 0 and rc == 0) if not expect_red else None,
             "compile_failed": compile_failed}
    restore()
    print("\n###", name)
    print(json.dumps(entry, ensure_ascii=False, indent=1))
    return entry


print("=== CLEAN BASELINE (card's domain suite only) ===")
rc, rows, _ = run_domain()
print("rc:", rc, "rows:", len(rows),
      "red:", [i for i, s in rows.items() if s != "PASS"], "restored:", restore())

trial("MV1-revert-the-cards-only-product-change (metricStatus default no longer INCONCLUSIVE)",
      "experiments.go", '\t\treturn "INCONCLUSIVE", nil\n\t}\n\tif pass {', "\t}\n\tif pass {",
      run_domain, "W1001-METRIC-VERDICT-CANNOT-BE-IMPLIED-BY-AN-UNEVALUABLE-GATE")

trial("MV2-delete the 'no metric deletion' length gate (never mutated by the executor)",
      "experiments.go",
      '\tif len(Arr(b, "results")) != len(metrics) {\n\t\treturn nil, Fail(422, "GATE_FAILED", "no metric deletion")\n\t}\n',
      "", run_domain, None)

trial("MV3-card comparator always reports PASS (self-lying emitter)", "test.go",
      'status := "PASS"\n\tif Hash(want) != Hash(got) {\n\t\tstatus = "FAIL"\n\t}',
      'status := "PASS"\n\tif false && Hash(want) != Hash(got) {\n\t\tstatus = "FAIL"\n\t}',
      run_domain, None)

trial("MV4-handler drops the retention rows from the negative-rule table", "main.py",
      'r"^W1001-(DELETING|RETENTION-REFUSAL|REPORTED-TASK|METRIC-VERDICT|ZERO-SAMPLE)"',
      'r"^W1001-(METRIC-VERDICT|ZERO-SAMPLE)"', run_handler, "W1001-ASSERTION-UNCLASSIFIED")

trial("MV2b-delete the length gate, FULL card domain selection (TestW10|TestW1001)",
      "experiments.go",
      '\tif len(Arr(b, "results")) != len(metrics) {\n\t\treturn nil, Fail(422, "GATE_FAILED", "no metric deletion")\n\t}\n',
      "", run_domain_full, None)

trial("MV5-retest the executor's M01 (retention refusal wording changed)", "experiments.go",
      'Fail(422, "GATE_FAILED", "all runs must be retained")',
      'Fail(422, "GATE_FAILED", "runs must be preserved")',
      run_domain_full, "W1001-DELETING-A-RETAINED-RUN-IS-REFUSED-BY-THE-RETENTION-GATE")

trial("MV6-retest the executor's M02 (retention guard switched off)", "experiments.go",
      'if Hash(x["run_ids"]) != Hash(b["run_ids"]) {',
      'if false {', run_domain_full,
      "W1001-DELETING-A-RETAINED-RUN-IS-REFUSED-BY-THE-RETENTION-GATE")

print("\n=== FINAL RESTORE (scratch bytes == 2ce7fcfc blobs) ===", restore())

# ---- where does M02 (retention guard off) actually get caught? ----
txt = PRISTINE["experiments.go"].decode("utf-8").replace(
    'if Hash(x["run_ids"]) != Hash(b["run_ids"]) {', 'if false {', 1)
TARGETS["experiments.go"].write_text(txt, encoding="utf-8")
rc, st, out = run_handler()
reds = sorted(i for i, s in st.items() if s != "PASS" and not i.startswith("__"))
print("\n### MV6b-retention guard off, observed through the BOUND HANDLER")
print(json.dumps({"rc": rc, "handler_status": st.get("__handler_status__"),
                  "handler_assertions": st.get("__handler_assertions__"),
                  "red_or_anomaly_rows": reds,
                  "roster_exactness_fired": "W1001-ROSTER-EXACTNESS" in reds,
                  "deleting_row_present": "W1001-DELETING-A-RETAINED-RUN-IS-REFUSED-BY-THE-RETENTION-GATE" in st,
                  "deleting_row_status": st.get("W1001-DELETING-A-RETAINED-RUN-IS-REFUSED-BY-THE-RETENTION-GATE", "ABSENT")},
                 ensure_ascii=False, indent=1))
restore()
print("\n=== FINAL RESTORE ===", restore())
