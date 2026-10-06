"""W05-03 mutation self-check, round 1.

Each mutant is a named, byte-exact edit to one of this card's own files. The question a mutant asks is always the same:
does a *named assertion id* of the construction check go red for the reason the mutation introduces? Results are
classified caught / survived / crashed-mutant-ill-formed / anchor-missing, files are restored to their original bytes
and the restore is verified by sha256, and a clean run after the loop must return to the recorded baseline.

Anchors are asserted to occur exactly once before any edit, so a drifted anchor is reported as anchor-missing rather
than silently skipping the mutation (which would look like a pass).
"""
import hashlib
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
ENV = dict(os.environ, GOTOOLCHAIN="local", GOENV="off",
           GOPATH=os.path.join(REPO, ".local", "gopath"),
           GOCACHE=os.path.join(REPO, ".local", "gocache"),
           RESEARCHOS_GO=GO, PYTHONIOENCODING="utf-8")

CC = "apps/cli/cli_contract.go"
MJ = "apps/cli/main.go"
DS = "ops/cli_distribution/main.go"
CK = "tests/runtime/cli_contract/main.go"

MUTANTS = [
    {"name": "M01-register-over-accepted-verbs", "file": CC, "expected": ["W0503-ACCEPTED-VERBS-NOT-SHADOWED"],
     "edits": [("\t\tif !registeredHere(name) {\n\t\t\tcontinue\n\t\t}\n", "")]},
    {"name": "M02-human-text-on-stdout-for-refusal", "file": MJ,
     "expected": ["W0503-UNKNOWN-VERB-KEEPS-STDOUT-JSONL-ONLY"],
     "edits": [('outJSON(map[string]any{"command": cmd,',
                'fmt.Fprint(os.Stdout, "human sentence on stdout\\n"); outJSON(map[string]any{"command": cmd,')]},
    {"name": "M03-no-signal-guard-around-host-call", "file": CC, "expected": ["W0503-INTERRUPT-EXITS-130"],
     "edits": [("stop := interruptGuard(name)", "stop := func() {}")]},
    {"name": "M04-model-change-without-naming-revision", "file": CC,
     "expected": ["W0503-MODEL-CHANGE-NEEDS-CONFIG-REVISION"],
     "edits": [('\tif !haveRev {\n\t\tfail(command, exitUsage, "MISSING_CONFIG_REVISION"',
                '\tif false && !haveRev {\n\t\tfail(command, exitUsage, "MISSING_CONFIG_REVISION"')]},
    {"name": "M05-init-accepts-missing-directory", "file": CC,
     "expected": ["W0503-INIT-MISSING-DIRECTORY-FAILS"],
     "edits": [("if err != nil || !info.IsDir() {", "if err == nil && !info.IsDir() {")]},
    {"name": "M06-delegating-to-an-external-binary", "file": CC, "expected": ["W0503-NO-PROCESS-DELEGATION"],
     "edits": [('\t"sort"\n', '\t"os/exec"\n\t"sort"\n'),
               ("func cliEnv(key, fallback string) string {",
                "var delegated = exec.Command\n\nfunc cliEnv(key, fallback string) string {")]},
    {"name": "M07-unquoted-shim-path", "file": DS, "expected": ["W0503-DISTRIBUTION-CANDIDATE-PASSES"],
     "edits": [('shimText := "@echo off\\r\\n\\"%~dp0" + exeName + "\\" %*\\r\\n"',
                'shimText := "@echo off\\r\\n%~dp0" + exeName + " %*\\r\\n"')]},
    {"name": "M08-uninitialised-list-fields", "file": CC, "expected": ["W0503-LIST-FIELDS-ARE-ARRAYS-NOT-NULL"],
     "edits": [("\tentries = []any{}\n\tmissingHandlers = []string{}\n\tmissingChecks = []string{}\n\trefused = []string{}\n", "")]},
    {"name": "M09-help-omits-refused-verbs", "file": CC,
     "expected": ["W0503-HELP-LIST-FIELDS-ARE-ARRAYS-NOT-NULL"],
     "edits": [('"not_implemented": refused, ', "")]},
    {"name": "M10-accepted-verbs-claimed-as-this-cards", "file": CC,
     "expected": ["W0503-HELP-ATTRIBUTES-ACCEPTED-VERBS"],
     "edits": [('state = "ACCEPTED"', 'state = "IMPLEMENTED"')]},
    {"name": "M11-hostless-verb-exits-zero", "file": CC,
     "expected": ["W0503-HOSTLESS-STATUS-REFUSES", "W0503-HOSTLESS-GOAL-REFUSES",
                  "W0503-HOSTLESS-GO-REFUSES", "W0503-HOSTLESS-RESUME-REFUSES", "W0503-HOSTLESS-CANCEL-REFUSES"],
     "edits": [('fail(name, exitNotImplemented, "HOST_DISCOVERY_UNAVAILABLE"',
                'fail(name, exitCompleted, "HOST_DISCOVERY_UNAVAILABLE"')]},
    {"name": "M12-counter-made-vacuous", "file": CK, "expected": [],
     "probe": "the exact-count assertion must go red when the count is off by one",
     "edits": [("answered == 15", "answered == 14")]},
]


def read(p):
    with open(os.path.join(REPO, p), "rb") as f:
        return f.read()


def write(p, b):
    with open(os.path.join(REPO, p), "wb") as f:
        f.write(b)


def run_check():
    proc = subprocess.run([GO, "run", "./tests/runtime/cli_contract"], cwd=REPO, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="replace",
                          timeout=900)
    line = ""
    for l in (proc.stdout or "").splitlines():
        if l.strip().startswith("{") and '"assertion_ids"' in l:
            line = l.strip()
    if not line:
        return {"status": "NO-REPORT", "assertion_ids": [], "failures": [],
                "raw_exit": proc.returncode, "stderr": (proc.stderr or "")[-800:]}
    rep = json.loads(line)
    rep["raw_exit"] = proc.returncode
    return rep


def main():
    originals = {}
    for m in MUTANTS:
        originals.setdefault(m["file"], read(m["file"]))
    baseline = run_check()
    baseline_ids = sorted(baseline.get("assertion_ids", []))
    print("baseline", baseline.get("status"), baseline.get("assertions"), file=sys.stderr)

    results = []
    for m in MUTANTS:
        entry = {"mutant": m["name"], "file": m["file"], "expected_rows": m.get("expected", []),
                 "probe": m.get("probe", "")}
        text = read(m["file"])
        ok_apply = True
        mutated = text
        for old, new in m["edits"]:
            ob, nb = old.encode(), new.encode()
            n = mutated.count(ob)
            entry.setdefault("anchor_counts", []).append(n)
            if n != 1:
                entry["classification"] = "anchor-missing"
                entry["note"] = "anchor occurred %d times; nothing was changed" % n
                ok_apply = False
                break
            mutated = mutated.replace(ob, nb, 1)
        if not ok_apply:
            results.append(entry)
            continue
        write(m["file"], mutated)
        try:
            rep = run_check()
        except subprocess.TimeoutExpired:
            rep = {"status": "TIMEOUT", "assertion_ids": [], "failures": []}
        finally:
            write(m["file"], originals[m["file"]])
            restored = hashlib.sha256(read(m["file"])).hexdigest()
            entry["restore_sha256_matches_original"] = (
                restored == hashlib.sha256(originals[m["file"]]).hexdigest())

        red = sorted({f["id"] for f in rep.get("failures", [])})
        entry["report_status"] = rep.get("status")
        entry["red_rows"] = red
        if rep.get("status") == "NO-REPORT" or rep.get("raw_exit") not in (0, 1):
            entry["classification"] = "crashed-mutant-ill-formed" if not red else "caught"
            entry["note"] = "exit %s; %s" % (rep.get("raw_exit"), (rep.get("stderr") or "")[:300])
        elif red:
            hit = [e for e in m.get("expected", []) if e in red]
            if m.get("expected"):
                entry["classification"] = "caught-by-card-id" if hit else "caught-by-gate-id-only"
            else:
                entry["classification"] = "caught-by-card-id"
                hit = red
            entry["killed_by"] = hit
            entry["extra_red_rows"] = [r for r in red if r not in m.get("expected", [])]
        else:
            entry["classification"] = "survived"
        results.append(entry)
        print(entry["mutant"], entry["classification"], file=sys.stderr)

    after = run_check()
    same = sorted(after.get("assertion_ids", [])) == baseline_ids
    out = {"card": "W05-03", "round": 1, "tool": "tests/runtime/cli_contract (go run)",
           "baseline": {"status": baseline.get("status"), "assertions": baseline.get("assertions"),
                        "assertion_ids": baseline_ids},
           "mutants": results,
           "counts": {k: sum(1 for r in results if r["classification"] == k) for k in
                      ("caught-by-card-id", "caught-by-gate-id-only", "survived", "crashed-mutant-ill-formed",
                       "anchor-missing")},
           "restore_verification": {"every_mutant_restored_byte_exact": all(
               r.get("restore_sha256_matches_original", True) for r in results),
               "clean_rerun_matches_baseline_ids": same,
               "clean_rerun_status": after.get("status"), "clean_rerun_assertions": after.get("assertions")},
           "survivor_reasons": [],
           "scope": "CONSTRUCTION_CHECK_MUTATION_MATRIX_NOT_PRODUCT_ACCEPTANCE",
           "executor_id": "qoder-desktop:/root/construction",
           "disclosed_limits": [
               "Mutants M01..M11 edit this card's own files only; the accepted apps/cli files were restored to their "
               "pre-run digests and that restoration is asserted per mutant, not assumed.",
               "M12 mutates the check program itself: it proves W0503-EVERY-OWNED-VERB-ANSWERS-IN-ITS-OWN-NAME counts "
               "exactly rather than vacuously. A mutation that weakens an assertion in the same breath cannot be "
               "detected by that assertion, so it is listed as an equivalent-mutant-class probe, not as coverage.",
               "Rows about the accepted cascade depend on Windows job objects; on a host without them M01 would report "
               "a different red set, which is why the classification names the rows it actually observed.",
           ]}
    path = os.path.join(REPO, ".local", "w0503_mutation_round1.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"counts": out["counts"], "restore": out["restore_verification"],
                      "survivors": [r["mutant"] for r in results if r["classification"] == "survived"]},
                     ensure_ascii=False))


main()
