"""W05-03 mutation self-check, round 2.

Round 1 (mutation_selfcheck_round1.json) produced two honest findings: M01 was killed by W0503-CHAT-KEEPS-THE-ACCEPTED-REFUSAL
rather than by the shadow row it targeted, because the second registration guard alone already protects `run` on a
Windows build; and M09 broke the build (removing the only use of `refused` is a compile error in Go), so it proved
nothing about the help-shape rows. Round 2 therefore aims at the guards individually, at a fabricated verification leg,
and at the two rows the first round showed were missing (the refusal list, and the independent launch of the
installed artefact). The two missing rows were added to the check before this run, and their baseline is recorded here.
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
DS = "ops/cli_distribution/main.go"

MUTANTS = [
    {"name": "N01-drop-both-registration-guards", "file": CC,
     "why": "the shadow-of-accepted-verbs property is only load-bearing when nothing prevents the overwrite",
     "expected": ["W0503-ACCEPTED-VERBS-NOT-SHADOWED"],
     "edits": [("\t\tif !registeredHere(name) {\n\t\t\tcontinue\n\t\t}\n\t\tif _, taken := commandHandlers[name]; taken {\n\t\t\tcontinue\n\t\t}\n", "")]},
    {"name": "N02-refused-verbs-not-listed-in-help", "file": CC,
     "why": "help must name what it refuses, and the state label alone cannot carry that claim",
     "expected": ["W0503-HELP-LISTS-CHAT-IN-NOT-IMPLEMENTED"],
     "edits": [("\t\t\trefused = append(refused, n)\n", "")]},
    {"name": "N03-run-attributed-to-this-card", "file": CC,
     "why": "the ownership attribution in the surface report is a claim about an accepted card's work",
     "expected": ["W0503-HELP-ATTRIBUTES-ACCEPTED-VERBS"],
     "edits": [('{"runCancelCascade", "W0502-CASCADE-RUNS-IN-REQUIRED-ORDER", "job object", "accepted W05-02"}',
                '{"runCancelCascade", "W0502-CASCADE-RUNS-IN-REQUIRED-ORDER", "job object", "W05-03"}')]},
    {"name": "N04-hostless-verb-answers-as-if-the-host-replied", "file": CC,
     "why": "the whole point of exit 3 is that a command with no host never reports an answer",
     "expected": ["W0503-HOSTLESS-STATUS-REFUSES", "W0503-SLASH-COMMANDS-HANDLED"],
     "edits": [('fail(name, exitNotImplemented, "HOST_DISCOVERY_UNAVAILABLE", path+": "+err.Error())',
                'outJSON(map[string]any{"command": name, "status": "HOST_ANSWERED", "exit_code": exitCompleted, "detail": path})\n\t\treturn')]},
    {"name": "N05-distribution-candidate-never-built", "file": DS,
     "why": "a candidate report that runs no compiler is the empty-stub failure the card names",
     "expected": ["W0503-DISTRIBUTION-CANDIDATE-PASSES", "W0503-DISTRIBUTION-ARTIFACT-LAUNCHES-INDEPENDENTLY"],
     "edits": [('build := exec.Command(goExe(), "build", "-o", exe, "./apps/cli")',
                'build := exec.Command(goExe(), "version")')]},
    {"name": "N06-distribution-fabricates-its-launch-leg", "file": DS,
     "why": "the program must not be allowed to invent the answer of the process it is supposed to have started",
     "expected": ["W0503-DISTRIBUTION-SELFREPORT-DIGEST-MATCHES-INDEPENDENT-LAUNCH"],
     "edits": [('code, stdout, stderr, err := installed(exe, "version")',
                'code, stdout, stderr, err := 0, "{\\"status\\":\\"COMPLETED\\"}", "", nil')]},
    {"name": "N07-signal-guard-installed-after-the-call", "file": CC,
     "why": "this is the mistake actually made while writing this card: a guard installed after the call cannot catch it",
     "expected": ["W0503-INTERRUPT-EXITS-130"],
     "edits": [('stop := interruptGuard(name)\n\tstatus, body, err := hostGet(d.URL + "/healthz")\n\tstop()',
                'status, body, err := hostGet(d.URL + "/healthz")\n\tstop := interruptGuard(name)\n\tstop()')]},
    {"name": "N08-shim-aliases-another-vendor-cli", "file": DS,
     "why": "the negative the card names: a shell alias to an external brand CLI counting as the product",
     "expected": ["W0503-DISTRIBUTION-CANDIDATE-PASSES"],
     "edits": [('shimText := "@echo off\\r\\n\\"%~dp0" + exeName + "\\" %*\\r\\n"',
                'shimText := "@echo off\\r\\ncodex %*\\r\\n"')]},
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
        return {"status": "NO-REPORT", "assertion_ids": [], "failures": [], "raw_exit": proc.returncode,
                "stderr": (proc.stderr or "")[-900:]}
    rep = json.loads(line)
    rep["raw_exit"] = proc.returncode
    return rep


def main():
    originals = {m["file"]: read(m["file"]) for m in MUTANTS}
    baseline = run_check()
    baseline_ids = sorted(baseline.get("assertion_ids", []))
    print("baseline", baseline.get("status"), baseline.get("assertions"), file=sys.stderr)

    results = []
    for m in MUTANTS:
        entry = {"mutant": m["name"], "file": m["file"], "why": m["why"],
                 "expected_rows": m["expected"], "assertion_counts": []}
        mutated = read(m["file"])
        applied = True
        for old, new in m["edits"]:
            ob, nb = old.encode(), new.encode()
            n = mutated.count(ob)
            entry["assertion_counts"].append(n)
            if n != 1:
                entry["classification"] = "anchor-missing"
                applied = False
                break
            mutated = mutated.replace(ob, nb, 1)
        if not applied:
            results.append(entry)
            continue
        write(m["file"], mutated)
        try:
            rep = run_check()
        except subprocess.TimeoutExpired:
            rep = {"status": "TIMEOUT", "assertion_ids": [], "failures": [], "raw_exit": None}
        finally:
            write(m["file"], originals[m["file"]])
            entry["restore_sha256_matches_original"] = hashlib.sha256(read(m["file"])).hexdigest() == \
                hashlib.sha256(originals[m["file"]]).hexdigest()

        red = sorted({f["id"] for f in rep.get("failures", [])})
        build_broke = rep.get("status") in ("NO-REPORT", "TIMEOUT") or "W0503-CLI-BUILDS" in red or \
            any("BUILD" in r for r in red)
        hit = [e for e in m["expected"] if e in red]
        entry["report_status"] = rep.get("status")
        entry["red_rows"] = red
        entry["killed_by"] = hit
        entry["extra_red_rows"] = [r for r in red if r not in m["expected"]]
        if not red and entry["report_status"] == "PASS":
            entry["classification"] = "survived"
        elif hit and build_broke:
            entry["classification"] = "caught, but the mutant also failed to compile"
        elif hit:
            entry["classification"] = "caught-by-card-id"
        elif red:
            entry["classification"] = "caught-by-gate-id-only"
        else:
            entry["classification"] = "crashed-mutant-ill-formed"
        results.append(entry)
        print(entry["mutant"], entry["classification"], file=sys.stderr)

    after = run_check()
    out = {"card": "W05-03", "round": 2,
           "reason_for_a_second_round": round_reason(),
           "rows_added_between_rounds": ["W0503-HELP-LISTS-CHAT-IN-NOT-IMPLEMENTED",
                "W0503-DISTRIBUTION-ARTIFACT-LAUNCHES-INDEPENDENTLY",
                "W0503-DISTRIBUTION-SELFREPORT-DIGEST-MATCHES-INDEPENDENT-LAUNCH"],
           "baseline": {"status": baseline.get("status"), "assertions": baseline.get("assertions"),
                        "assertion_ids": baseline_ids},
           "mutants": results,
           "counts": {k: sum(1 for r in results if r["classification"] == k) for k in
                      ("caught-by-card-id", "caught-by-gate-id-only", "survived",
                       "caught, but the mutant also failed to compile", "crashed-mutant-ill-formed",
                       "anchor-missing")},
           "restore_verification": {"every_mutant_restored_byte_exact": all(
               r.get("restore_sha256_matches_original", True) for r in results),
               "clean_rerun_matches_baseline_ids": sorted(after.get("assertion_ids", [])) == baseline_ids,
               "clean_rerun_status": after.get("status"), "clean_rerun_assertions": after.get("assertions")},
           "survivor_reasons": [r for r in results if r["classification"] == "survived"],
           "completeness_claim": "This is the full set of mutants attempted in round 2. It is not a claim that every "
                                 "reachable branch of the CLI contract is covered: the branches this matrix does not "
                                 "reach are listed in not_reached.",
           "not_reached": [
               "The non-Windows build: cancel_run_windows.go is behind a windows build tag, so on Linux neither "
               "registration guard protects `run` from this card's table; the registeredHere guard is what answers "
               "for that portability case and no mutant in this matrix runs a non-Windows build.",
               "Flag-parse failures inside the accepted verbs (run/worker/task), which are W05-01/W05-02 territory.",
               "Real console-attach delivery variants: only CTRL_BREAK_EVENT into a new process group is exercised.",
           ],
           "scope": "CONSTRUCTION_CHECK_MUTATION_MATRIX_NOT_PRODUCT_ACCEPTANCE",
           "executor_id": "qoder-desktop:/root/construction"}
    path = os.path.join(REPO, ".local", "w0503_mutation_round2.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"counts": out["counts"], "restore": out["restore_verification"],
                      "survivors": [r["mutant"] for r in results if r["classification"] == "survived"]},
                     ensure_ascii=False))


def round_reason():
    return ("Round 1 classified M01 as caught-by-gate-id-only because the second guard independently protects `run`, "
            "so the shadow row was never attacked; M09 removed the only Go use of a returned value and failed to "
            "compile, which the report counted as a red run rather than as an ill-formed mutant. Round 2 drops both "
            "guards, targets the refusal list with a well-formed edit, adds the fabricated-verification legs for the "
            "distribution candidate, and records whether each mutant also broke the build.")


main()
