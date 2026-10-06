"""Round-2 reviewer mutation matrix for W05-03.

Independent of the executor's rounds 4/5/7: every mutant here is new and targets the
protocol client's local precondition mirrors, the table-closure mechanism, and the two
disclosed limits. Each mutant is applied by exact string replacement, the card's own
construction check is re-run, and the file is restored with
`git checkout -- <exact path>` and verified clean.

Reviewer scratch tool.
"""
import json, os, subprocess, sys, time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GO = r"D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe"
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "GOTOOLCHAIN": "local", "GOENV": "off",
       "GOPATH": r"D:\作品集\ResearchOS\research-os\.local\gopath",
       "GOCACHE": r"D:\作品集\ResearchOS\research-os\.local\gocache",
       "RESEARCHOS_GO": GO}
FLAKE = ("HOST_UNREACHABLE", "UNKNOWN_STATUS:<absent>", "connection attempt failed",
         "context deadline exceeded")

MUTANTS = [
 {"id": "R2-M1-session-get-leg-always-skipped", "file": "apps/cli/cli_verbs.go",
  "old": '\t\t\tsteps = append(steps, v2Step{"session.get", map[string]any{}, ""})',
  "new": '\t\t\tsteps = append(steps, v2Step{method: "session.get", skipped: "R2M1"})',
  "expected": ["W0503-STATUS-SENDS-HOST-STATUS", "W0503-SLASH-STATUS-SENDS-HOST-STATUS"],
  "claim": "status really sends session.get when a session is known"},
 {"id": "R2-M2-in-progress-becomes-a-failure", "file": "apps/cli/cli_v2.go",
  "old": '\tcase "IN_PROGRESS":\n\t\treturn reply, "", exitCompleted',
  "new": '\tcase "IN_PROGRESS":\n\t\treturn reply, "", exitFailed',
  "expected": ["W0503-STATUS-EXIT-FOLLOWS-THE-HOST-REPLY"],
  "claim": "the five protocol statuses are each mapped to a graded exit code"},
 {"id": "R2-M3-host-configure-carries-the-epoch", "file": "apps/cli/cli_v2.go",
  "old": '\t"goal.start": true, "project.bootstrap": true}',
  "new": '\t"goal.start": true, "project.bootstrap": true, "host.configure": true}',
  "expected": ["W0503-SETTLED-MODEL-CHANGE-SENDS-HOST-CONFIGURE"],
  "claim": "the host.configure envelope the CLI sends satisfies the protocol's epoch rule"},
 {"id": "R2-M4-table-claims-a-method-the-code-never-sends", "file": "apps/cli/cli_contract.go",
  "old": '"session.attach + session.control", []string{"W0503-RESUME-SENDS-SESSION-ATTACH"',
  "new": '"session.attach + session.control + session.handoff", []string{"W0503-RESUME-SENDS-SESSION-ATTACH"',
  "expected": ["W0503-TABLE-ROWS-ALL-PROVEN", "W0503-COMMANDS-ALL-HANDLED"],
  "claim": "the command table's method column is checked against what the CLI actually sent"},
 {"id": "R2-M5-proven-by-pointed-at-an-unrelated-emitted-row", "file": "apps/cli/cli_contract.go",
  "old": '''"init":     {"cliInit", "W0503-COMMANDS-ALL-HANDLED", "workspace path + host", "W05-03", "project.bootstrap", []string{"W0503-INIT-ACCEPTS-CHINESE-AND-SPACE-PATH", "W0503-INIT-WITHOUT-WORKSPACE-IS-USAGE-ERROR", "W0503-INIT-MISSING-DIRECTORY-FAILS"}},''',
  "new": '''"init":     {"cliInit", "W0503-COMMANDS-ALL-HANDLED", "workspace path + host", "W05-03", "project.bootstrap", []string{"W0503-CLI-BUILDS", "W0503-HEAD-RECORDED"}},''',
  "expected": ["W0503-TABLE-ROWS-ALL-PROVEN"],
  "claim": "a row's proven_by must name probes that actually drive that row"},
 {"id": "R2-M6-proven-by-emptied", "file": "apps/cli/cli_contract.go",
  "old": '"goal":     {"cliHostCommand", "W0503-COMMANDS-ALL-HANDLED", "host + objective", "W05-03", "goal.start", []string{"W0503-GOAL-SENDS-GOAL-START", "W0503-GOAL-WITHOUT-OBJECTIVE-IS-USAGE-ERROR"}},',
  "new": '"goal":     {"cliHostCommand", "W0503-COMMANDS-ALL-HANDLED", "host + objective", "W05-03", "goal.start", []string{}},',
  "expected": ["W0503-COMMANDS-ALL-HANDLED", "W0503-TABLE-ROWS-ALL-PROVEN"],
  "claim": "a row that names no probe cannot support the deliverable"},
 {"id": "R2-M7-delete-a-doctor-probe", "file": "tests/runtime/cli_contract/v2verbs.go",
  "old": '''\tup := call(base(), "doctor")\n\tok("W0503-DOCTOR-UP-COMPLETES", up.code == 0 && str(jsonOf(up)["health"]) == "UP" &&\n\t\tstr(jsonOf(up)["status"]) == "COMPLETED", "code", up.code, jsonOf(up))''',
  "new": '\tup := call(base(), "doctor")\n\t_ = up',
  "expected": ["W0503-TABLE-ROWS-ALL-PROVEN"],
  "claim": "deleting a probe a table row relies on goes red"},
 {"id": "R2-M8-os-exec-hidden-in-a-sibling-delivered-file", "file": "apps/cli/cli_v2.go",
  "old": 'import (\n\t"bytes"\n\t"encoding/json"\n\t"io"\n\t"net/http"\n\t"os"\n\t"regexp"\n\t"strings"\n\t"time"\n)',
  "new": 'import (\n\t"bytes"\n\t"encoding/json"\n\t"io"\n\t"net/http"\n\t"os"\n\t"os/exec"\n\t"regexp"\n\t"strings"\n\t"time"\n)\n\nvar r2VendorAlias = exec.Command',
  "expected": ["W0503-NO-PROCESS-DELEGATION"],
  "claim": "the command surface never shells out to another program"},
 {"id": "R2-M9-candidate-launches-the-build-tree-binary", "file": "ops/cli_distribution/main.go",
  "old": '\tcode, stdout, stderr, err := installed(exe, "version")',
  "new": '\texe = filepath.Join(*repo, ".local", "w0503_cli.exe")\n\tcode, stdout, stderr, err := installed(exe, "version")',
  "expected": ["W0503-DISTRIBUTION-SELFREPORT-DIGEST-MATCHES-INDEPENDENT-LAUNCH",
               "DIST-INSTALLED-LAUNCHES"],
  "claim": "the published digest proves the installed file was the one launched"},
]


def read(p):
    return open(os.path.join(REPO, p), encoding="utf-8", errors="replace").read()


def porcelain(p):
    r = subprocess.run(["git", "status", "--porcelain", "--", p], cwd=REPO, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip()


def run_check():
    t0 = time.time()
    r = subprocess.run([GO, "run", "./tests/runtime/cli_contract"], cwd=REPO, env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    line = (r.stdout or "").strip().splitlines()
    payload = None
    for l in reversed(line):
        if l.startswith("{"):
            payload = json.loads(l)
            break
    if payload is None:
        return {"compile_error": True, "stderr": (r.stderr or "")[-1500:], "exit": r.returncode,
                "seconds": round(time.time() - t0, 1)}
    payload["exit"] = r.returncode
    payload["seconds"] = round(time.time() - t0, 1)
    payload["compile_error"] = False
    return payload


def flake_only(payload):
    if payload["status"] == "PASS":
        return False
    for f in payload["failures"]:
        if not any(k in f["detail"] for k in FLAKE):
            return False
    return True


def main():
    only = sys.argv[1:]
    out = {"program": "reviewer round-2 mutation matrix", "reviewer_id":
           "qoder-desktop:/root/w0503_verifier_r2", "matrix": []}
    for m in MUTANTS:
        if only and m["id"] not in only:
            continue
        path = m["file"]
        src = read(path)
        n = src.count(m["old"])
        rec = {"mutant": m["id"], "file": path, "attack_claim": m["claim"],
               "expected_rows": m["expected"]}
        if n != 1:
            rec["classification"] = "anchor-missing"
            rec["anchor_occurrences"] = n
            out["matrix"].append(rec)
            print("%s ANCHOR-MISSING (%d)" % (m["id"], n))
            continue
        open(os.path.join(REPO, path), "w", encoding="utf-8", newline="").write(
            src.replace(m["old"], m["new"], 1))
        p = run_check()
        if p.get("compile_error"):
            rec.update({"classification": "crashed-mutant-ill-formed", "stderr": p["stderr"]})
            print("%s CRASHED" % m["id"])
        elif flake_only(p):
            p2 = run_check()
            rec["flake_retry"] = {"first_failures": [f["id"] for f in p["failures"]],
                                  "second_status": p2["status"],
                                  "second_failures": [f["id"] for f in p2["failures"]]}
            p = p2
        if not p.get("compile_error") and not rec.get("classification"):
            red = sorted(f["id"] for f in p["failures"])
            hit = [x for x in m["expected"] if x in red]
            rec.update({"status": p["status"], "assertions": p["assertions"],
                        "red_rows": red, "not_verified": p["not_verified"]})
            if not red:
                rec["classification"] = "survived"
            elif hit:
                rec["classification"] = "caught-by-card-id"
            else:
                rec["classification"] = "caught-by-gate-id-only"
            print("%-46s %-24s red=%s" % (m["id"], rec["classification"], red[:4]))
        subprocess.run(["git", "checkout", "--", path], cwd=REPO, env=ENV)
        rec["restored_clean"] = (porcelain(path) == "")
        rec["restored_sha_matches_baseline"] = (read(path) == src)
        out["matrix"].append(rec)
        with open(os.path.join(REPO, ".local", "r2", "reviewer_mutants_r2a.json"), "w",
                  encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    print("wrote .local/r2/reviewer_mutants_r2a.json")


if __name__ == "__main__":
    main()
