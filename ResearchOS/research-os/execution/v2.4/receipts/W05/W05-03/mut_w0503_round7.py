"""W05-03 mutation self-check, round 7 — five mutants re-aimed at the remediated source.

Round 5 reached 0 survivors but could not aim five of its own cases: V03 and V04 pointed at `verbRequest` and a
single-step refusal that the remediation replaced with `verbSteps` and a worst-of loop, and V01/V11/V12 were compared
against expectation strings naming rows that had since been renamed or newly added. Their red-row lists showed the
actual kills, but a classification computed from a stale name is not evidence, so those five are re-run here against
anchors that exist and expectations that name the rows as they are now called.
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
           GOCACHE=os.path.join(REPO, ".local", "gocache"), RESEARCHOS_GO=GO, PYTHONIOENCODING="utf-8")

MJ = "apps/cli/main.go"
CC = "apps/cli/cli_contract.go"
VB = "apps/cli/cli_verbs.go"

MUTANTS = [
    {"name": "W01-doctor-case-unreachable", "file": MJ, "replaces_round5": "V01 (expectation named a renamed row)",
     "expected": ["W0503-DOCTOR-NOT-FOUND-REFUSES", "W0503-DOCTOR-DOWN-EXIT-1", "W0503-DOCTOR-UP-COMPLETES",
                  "W0503-TABLE-ROWS-ALL-PROVEN"],
     "edits": [('case "doctor":', 'case "doctorX":')]},
    {"name": "W03-verbs-discard-their-arguments", "file": VB, "replaces_round5": "V03 (anchor predated verbSteps)",
     "expected": ["W0503-GOAL-SENDS-GOAL-START", "W0503-CANCEL-SENDS-SESSION-CONTROL",
                  "W0503-RESUME-SENDS-SESSION-ATTACH", "W0503-RUN-SENDS-SESSION-SEND-AND-EVENTS",
                  "W0503-STATUS-SENDS-HOST-STATUS"],
     "edits": [("func verbSteps(name string, args []string, ctx *v2Context, cfg cliConfig) ([]v2Step, string, string) {\n\tswitch name {",
                "func verbSteps(name string, args []string, ctx *v2Context, cfg cliConfig) ([]v2Step, string, string) {\n\treturn []v2Step{{\"host.status\", map[string]any{}, \"\"}}, \"\", \"\"\n\tswitch name {")]},
    {"name": "W04-host-refusal-ignored", "file": VB, "replaces_round5": "V04 (anchor predated the worst-of loop)",
     "expected": ["W0503-STATUS-EXIT-FOLLOWS-THE-HOST-REPLY", "W0503-HOST-NOT-IMPLEMENTED-IS-NOT-EXIT-ZERO",
                  "W0503-MALFORMED-HOST-REPLY-FAILS", "W0503-HOST-HTTP-500-IS-NOT-A-COMPLETION"],
     "edits": [("if code > worst {\n\t\t\tworst, worstReason = code, reason",
                "if false {\n\t\t\tworst, worstReason = code, reason")]},
    {"name": "W11-config-written-before-the-host-answers", "file": CC,
     "replaces_round5": "V11 (expectation named a row that was added under a different name)",
     "expected": ["W0503-HOST-REFUSED-SWITCH-LEAVES-THE-PREVIOUS-MODEL"],
     "edits": [("""		fail(command, code, orDefault(reason, "HOST_CONFIGURE_REFUSED"), replyView(cfgReply))""",
                """		c.Model = model
		c.ConfigRevision = c.ConfigRevision + 1
		_ = writeConfig(c)
		fail(command, code, orDefault(reason, "HOST_CONFIGURE_REFUSED"), replyView(cfgReply))""")]},
    {"name": "W12-interactive-adopts-any-session-id", "file": VB,
     "replaces_round5": "V12 (expectation named the wrong row)",
     "expected": ["W0503-INTERACTIVE-NEVER-SUBSTITUTES-THE-CREATED-SESSION"],
     "edits": [('isMap && ctx.sessionID == "" && s.method == "session.create"', 'isMap && ctx.sessionID == ""')]},
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
        entry = {"mutant": m["name"], "file": m["file"], "replaces_round5": m["replaces_round5"],
                 "expected_rows": m["expected"], "anchor_counts": []}
        mutated, applied = read(m["file"]), True
        for old, new in m["edits"]:
            ob = old.encode()
            n = mutated.count(ob)
            entry["anchor_counts"].append(n)
            if n != 1:
                entry["classification"] = "anchor-missing"
                applied = False
                break
            mutated = mutated.replace(ob, new.encode(), 1)
        if not applied:
            results.append(entry)
            print(entry["mutant"], "anchor-missing", file=sys.stderr)
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
        build_broke = rep.get("status") in ("NO-REPORT", "TIMEOUT") or any("BUILDS" in r for r in red)
        hit = [e for e in m["expected"] if e in red]
        entry.update({"report_status": rep.get("status"), "assertions": rep.get("assertions"), "red_rows": red,
                      "killed_by": hit, "extra_red_rows": [r for r in red if r not in m["expected"]],
                      "uncaught_expected": [e for e in m["expected"] if e not in red]})
        if not red and entry["report_status"] == "PASS":
            entry["classification"] = "survived"
        elif rep.get("status") == "NO-REPORT":
            entry["classification"] = "crashed-mutant-ill-formed"
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
    out = {"card": "W05-03", "round": 7,
           "purpose": "re-aim the five round-5 cases whose anchors or expectations were stale, so no classification "
                      "rests on a name the check no longer emits",
           "mutants": results,
           "counts": {k: sum(1 for r in results if r["classification"] == k) for k in
                      ("caught-by-card-id", "caught-by-gate-id-only", "survived",
                       "caught, but the mutant also failed to compile", "crashed-mutant-ill-formed",
                       "anchor-missing")},
           "baseline": {"status": baseline.get("status"), "assertions": baseline.get("assertions"),
                        "assertion_ids": baseline_ids},
           "restore_verification": {"every_mutant_restored_byte_exact": all(
               r.get("restore_sha256_matches_original", True) for r in results),
               "clean_rerun_matches_baseline_ids": sorted(after.get("assertion_ids", [])) == baseline_ids,
               "clean_rerun_status": after.get("status"), "clean_rerun_assertions": after.get("assertions")},
           "survivors": [r["mutant"] for r in results if r["classification"] == "survived"],
           "completeness_claim": "Five mutants, all re-aimed round-5 cases. Not a complete branch survey; see "
                                 "not_reached in mutation_selfcheck_round5.json.",
           "scope": "CONSTRUCTION_CHECK_MUTATION_MATRIX_NOT_PRODUCT_ACCEPTANCE",
           "executor_id": "qoder-desktop:/root/construction"}
    path = os.path.join(REPO, ".local", "w0503_mutation_round7.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"counts": out["counts"], "survivors": out["survivors"],
                      "restore": out["restore_verification"]}, ensure_ascii=False))


main()
