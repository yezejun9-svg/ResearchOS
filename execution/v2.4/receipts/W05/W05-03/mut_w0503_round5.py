"""W05-03 mutation self-check, round 5 — the review's counterexamples, run as mutants.

Round 4 (mutation_selfcheck_round4.json) left V11 and V12 surviving and V07 pointed at the wrong file; those three are re-attacked here after adding the rows that reach them. Round 3 was a re-classification of round 1, but the review rejected the card, so this round does the work
that matters: every blocker the reviewer proved by mutation is re-run here as a named mutant, with the assertion that
must now go red named in advance. A fix that is not accompanied by the counter-example it defeats is a claim.

V01 and V02 are the reviewer's own R02 and R04 (delete doctor's case; delete the settled-run condition), reproduced as
close as the source allows. V03/V04/V05 attack the stub the review caught (P-R1-1) from three directions: discarding
arguments, ignoring the host's refusal, and inventing a credential. V06-V10 attack the report and table machinery.
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

CC = "apps/cli/cli_contract.go"
MJ = "apps/cli/main.go"
VB = "apps/cli/cli_verbs.go"
CK = "tests/runtime/cli_contract/main.go"
V2T = "apps/cli/cli_v2.go"
DS = "apps/desktop/main/lib/v2.js"

MUTANTS = [
    {"name": "V01-doctor-case-unreachable", "file": MJ, "reviewer_counterexample": "R02",
     "expected": ["W0503-DOCTOR-NOT-FOUND-REFUSES", "W0503-DOCTOR-DOWN-EXIT-4", "W0503-DOCTOR-UP-COMPLETES",
                  "W0503-TABLE-ROWS-ALL-PROVEN"],
     "edits": [('case "doctor":', 'case "doctorX":')]},
    {"name": "V02-settled-run-condition-removed", "file": CC, "reviewer_counterexample": "R04",
     "expected": ["W0503-MODEL-CHANGE-NEEDS-SETTLED-RUN-RECORDED"],
     "edits": [('if strings.TrimSpace(c.ConfirmedRun) == "" {', 'if false {')]},
    {"name": "V03-verbs-discard-their-arguments", "file": VB, "reviewer_counterexample": "P-R1-1",
     "expected": ["W0503-GOAL-SENDS-GOAL-START", "W0503-CANCEL-SENDS-SESSION-CONTROL",
                  "W0503-RESUME-SENDS-SESSION-ATTACH"],
     "edits": [('func verbRequest(name string, args []string, ctx *v2Context, cfg cliConfig) (method string, payload map[string]any, refusal string, detail string) {\n\tswitch name {',
                'func verbRequest(name string, args []string, ctx *v2Context, cfg cliConfig) (method string, payload map[string]any, refusal string, detail string) {\n\treturn "host.status", map[string]any{}, "", ""\n\tswitch name {')]},
    {"name": "V04-host-refusal-exits-zero", "file": VB, "reviewer_counterexample": "P-R1-1",
     "expected": ["W0503-STATUS-EXIT-FOLLOWS-THE-HOST-REPLY", "W0503-HOST-NOT-IMPLEMENTED-IS-NOT-EXIT-ZERO",
                  "W0503-MALFORMED-HOST-REPLY-FAILS", "W0503-HOST-HTTP-500-IS-NOT-A-COMPLETION"],
     "edits": [('if code != exitCompleted {\n\t\tfail(name, code, orDefault(reason, "HOST_REFUSED_WITHOUT_CODE"), replyView(reply))',
                'if false {\n\t\tfail(name, code, orDefault(reason, "HOST_REFUSED_WITHOUT_CODE"), replyView(reply))')]},
    {"name": "V05-credential-invented-when-absent", "file": VB, "reviewer_counterexample": "P-R1-1",
     "expected": ["W0503-NO-CREDENTIAL-REFUSES-WITHOUT-PRETENDING"],
     "edits": [('credential: os.Getenv("RESEARCHOS_CLI_CREDENTIAL")',
                'credential: cliEnv("RESEARCHOS_CLI_CREDENTIAL", "invented-token")')]},
    {"name": "V06-table-stops-naming-its-probes", "file": CC, "reviewer_counterexample": "P-R1-3",
     "expected": ["W0503-TABLE-ROWS-ALL-PROVEN", "W0503-COMMANDS-ALL-HANDLED"],
     "edits": [('"proven_by": c.proven,', '"proven_by": []string{},')]},
    {"name": "V07-protocol-table-drifts-from-schema", "file": V2T, "reviewer_counterexample": "new",
     "expected": ["W0503-CLI-METHOD-TABLE-MATCHES-THE-FROZEN-SCHEMA"],
     "edits": [('{"ControlPayload", "ControlResult", []string{"action", "target_id", "reason"}}',
               '{"ControlPayload", "ControlResult", []string{"action", "target_id"}}')]},
    {"name": "V08-desktop-and-cli-tables-diverge", "file": DS, "reviewer_counterexample": "new",
     "expected": ["W0503-CLI-TABLE-AND-DESKTOP-V2-AGREE"],
     "edits": [("  'session.control': { payload: 'ControlPayload', result: 'ControlResult', required: ['action', 'target_id', 'reason'] },",
                "  'session.control': { payload: 'ControlCommandPayload', result: 'ControlResult', required: ['action', 'target_id', 'reason'] },")]},
    {"name": "V09-help-drops-a-registered-command", "file": CC, "reviewer_counterexample": "R03",
     "expected": ["W0503-HELP-LISTS-EVERY-REGISTERED-COMMAND"],
     "edits": [('names = append(names, e.(map[string]any)["command"].(string))',
                'if len(names) > 0 {\n\t\t\t\tcontinue\n\t\t\t}\n\t\t\t\tnames = append(names, e.(map[string]any)["command"].(string))') for _ in [0]]},
    {"name": "V10-verb-probes-health-again", "file": VB, "reviewer_counterexample": "P-R1-1",
     "expected": ["W0503-STATUS-IS-NOT-A-HEALTH-PROBE"],
     "edits": [("stop := interruptGuard(name)",
                "_, _, _ = hostGet(ctx.baseURL + \"/healthz\")\n\tstop := interruptGuard(name)")]},
    {"name": "V11-config-written-before-the-host-answers", "file": CC,
     "reviewer_counterexample": "found by the remediation run, not by the review",
     "expected": ["W0503-REFUSED-SWITCH-LEAVES-THE-PREVIOUS-MODEL"],
     "edits": [("""		fail(command, code, orDefault(reason, "HOST_CONFIGURE_REFUSED"), replyView(cfgReply))""",
                """		c.Model = model
		c.ConfigRevision = c.ConfigRevision + 1
		_ = writeConfig(c)
		fail(command, code, orDefault(reason, "HOST_CONFIGURE_REFUSED"), replyView(cfgReply))""")]},
    {"name": "V12-interactive-adopts-any-session-id", "file": VB, "reviewer_counterexample": "P-R1-1",
     "expected": ["W0503-INTERACTIVE-SENDS-LIST-CREATE-SEND"],
     "edits": [('isMap && ctx.sessionID == "" && s.method == "session.create"', 'isMap && ctx.sessionID == ""')]},
    {"name": "V13-flag-value-swallows-the-next-flag", "file": CC, "reviewer_counterexample": "P-R1-2",
     "expected": ["W0503-MODEL-CHANGE-NEEDS-SETTLED-FLAG", "W0503-MODEL-CHANGE-REFUSES-WITHOUT-ENDPOINT-OR-CREDENTIAL",
                  "W0503-SETTLED-MODEL-CHANGE-SENDS-HOST-CONFIGURE"],
     "edits": [('if a == "--"+name && i+1 < len(args) && !strings.HasPrefix(args[i+1], "--") {',
                'if a == "--"+name && i+1 < len(args) {')]},
    {"name": "V14-doctor-keeps-the-uncanonical-code", "file": MJ, "reviewer_counterexample": "P-R1-9",
     "expected": ["W0503-DOCTOR-DOWN-EXIT-1"],
     "edits": [('"exit_code": map[string]any{"UP": 0, "DOWN": 1}[status]',
                 '"exit_code": map[string]any{"UP": 0, "DOWN": 4}[status]'),
                ('\t\tif status != "UP" {\n\t\t\tos.Exit(1)\n\t\t}',
                 '\t\tif status != "UP" {\n\t\t\tos.Exit(4)\n\t\t}')]},
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
        entry = {"mutant": m["name"], "file": m["file"], "reviewer_counterexample": m["reviewer_counterexample"],
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
            print(entry["mutant"], "anchor-missing", entry["anchor_counts"], file=sys.stderr)
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
        elif build_broke and rep.get("status") == "NO-REPORT":
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
    out = {"card": "W05-03", "round": 5,
           "purpose": "re-run the review's counterexamples as mutants against the remediated code",
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
           "survivors": [r["mutant"] for r in results if r["classification"] == "survived"],
           "carried_from_round4": "V11 and V12 survived because no probe reached the branch each one corrupts; W0503-HOST-REFUSED-SWITCH-LEAVES-THE-PREVIOUS-MODEL and W0503-INTERACTIVE-NEVER-SUBSTITUTES-THE-CREATED-SESSION were added before this run, and V07 named the wrong file (apps/cli/cli_contract.go instead of apps/cli/cli_v2.go).",
           "completeness_claim": "This lists every mutant attempted in this round. It is not a claim that all "
                                 "reachable branches are covered; the branches left untested are in not_reached.",
           "not_reached": [
               "The real control host's own replies: every host here is a loopback stub that speaks the published "
               "protocol statuses. A LIVE host (case A04) is not exercised by this card.",
               "Non-Windows builds: cancel_run_windows.go is behind a windows tag, and the distribution candidate "
               "returns early on other platforms.",
               "The interactive TUI, which stays refused; and the accepted verbs' internal failure paths, which "
               "belong to W05-01/W05-02.",
           ],
           "scope": "CONSTRUCTION_CHECK_MUTATION_MATRIX_NOT_PRODUCT_ACCEPTANCE",
           "executor_id": "qoder-desktop:/root/construction"}
    path = os.path.join(REPO, ".local", "w0503_mutation_round5.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"counts": out["counts"], "survivors": out["survivors"],
                      "restore": out["restore_verification"]}, ensure_ascii=False))


main()
