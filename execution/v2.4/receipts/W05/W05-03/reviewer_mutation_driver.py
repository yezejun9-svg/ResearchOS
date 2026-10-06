"""Reviewer's own mutation matrix for W05-03. Independent of the executor's two rounds.

Each mutant is one byte-exact edit with an anchor asserted to occur exactly once. The question asked is always:
does a NAMED assertion id of the construction check go red for the reason this edit introduces?

Files are restored with `git checkout -- <that one file>` and the restore is verified by sha256 against the
digest the executor registered, plus `git status --porcelain` for that path.
"""
import hashlib
import json
import os
import subprocess
import sys

REPO = r"D:\作品集\ResearchOS\research-os"
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
ENV = dict(os.environ, GOTOOLCHAIN="local", GOENV="off",
           GOPATH=os.path.join(REPO, ".local", "gopath"),
           GOCACHE=os.path.join(REPO, ".local", "gocache"),
           RESEARCHOS_GO=GO, PYTHONIOENCODING="utf-8")

CC = "apps/cli/cli_contract.go"
MJ = "apps/cli/main.go"
DS = "ops/cli_distribution/main.go"
CK = "tests/runtime/cli_contract/main.go"
CH = "apps/cli/cli_http.go"

BASELINE_SHA = {
    CC: "f850c16f2e1e3468b9717eac0cfc896781ebaf79f999cc78e4908b583dee708c",
    MJ: "6d04c558dfd83914f46ee73aad79ec1d888cdea6385b5f2b2d2bd4e80effead6",
    DS: "23921fd0e8328b734bedbc2f29aab9a9c86c1c15e83d4eb091397c69f25a7543",
    CK: "f9c3b480936823e737744b9501a45aa682e6d3af323f6d43418f7c8acaa92e71",
    CH: "c0dcbca7261d0eab673c4d6c41e887856fb1f936b4d9e28bd77ef346285c5425",
}

MUTANTS = [
    {
        "name": "R01-take-guard-removed-alone",
        "file": CC,
        "why": "the executor never tested the second registration guard on its own; with registeredHere intact "
               "no W05-03-owned verb is already taken, so this should be an equivalent mutant",
        "expected": ["W0503-ACCEPTED-VERBS-NOT-SHADOWED"],
        "edits": [("\t\tif _, taken := commandHandlers[name]; taken {\n\t\t\tcontinue\n\t\t}\n", "")],
    },
    {
        "name": "R02-doctor-verb-removed-from-surface",
        "file": MJ,
        "why": "product.contract lists doctor as a required command; no W0503 row invokes it, so deleting the "
               "branch should leave the 46 ids green",
        "expected": [],
        "edits": [('case "doctor":', 'case "doctor-removed-by-reviewer":')],
    },
    {
        "name": "R03-help-command-list-replaced-by-junk-names",
        "file": CC,
        "why": "W0503-HELP-COVERS-EVERY-COMMAND only measures len(commands) >= 15",
        "expected": ["W0503-HELP-COVERS-EVERY-COMMAND"],
        "edits": [("\tnames := make([]string, 0, len(entries))\n\tfor _, e := range entries {\n\t\tnames = append(names, e.(map[string]any)[\"command\"].(string))\n\t}\n",
                   "\tnames := []string{\"a1\", \"a2\", \"a3\", \"a4\", \"a5\", \"a6\", \"a7\", \"a8\", \"a9\", \"b1\", \"b2\", \"b3\", \"b4\", \"b5\", \"b6\", \"b7\"}\n")],
    },
    {
        "name": "R04-settled-run-confirmation-dropped",
        "file": CC,
        "why": "action 3 needs a settled confirmation; the named row only omits --settled, so dropping the "
               "ConfirmedRun requirement should survive",
        "expected": ["W0503-MODEL-CHANGE-NEEDS-SETTLED-CONFIRMATION"],
        "edits": [('if !flagBool(args, "settled") || strings.TrimSpace(c.ConfirmedRun) == "" {',
                   'if !flagBool(args, "settled") {')],
    },
    {
        "name": "R05-revision-equality-gate-removed",
        "file": CC,
        "why": "the stale-revision comparison itself (M04 only removed the presence check)",
        "expected": ["W0503-STALE-CONFIG-REVISION-REFUSED"],
        "edits": [("\tif rev != strconv.Itoa(c.ConfigRevision) {", "\tif false {")],
    },
    {
        "name": "R06-unknown-verb-stdout-record-removed",
        "file": MJ,
        "why": "W0503-UNKNOWN-VERB-KEEPS-STDOUT-JSONL-ONLY accepts empty stdout by its own condition",
        "expected": ["W0503-UNKNOWN-VERB-KEEPS-STDOUT-JSONL-ONLY"],
        "edits": [('\t\toutJSON(map[string]any{"command": cmd, "status": "REJECTED", "exit_code": 3,\n\t\t\t"reason": "NOT_IMPLEMENTED", "detail": cmd + " is registered to a later card; no silent success"})\n', "")],
    },
    {
        "name": "R07-delegation-hidden-in-a-sibling-file",
        "file": CH,
        "why": "W0503-NO-PROCESS-DELEGATION reads only apps/cli/cli_contract.go, so shelling out from a sibling "
               "file of the same package should survive",
        "expected": ["W0503-NO-PROCESS-DELEGATION"],
        "edits": [('import (\n\t"io"\n', 'import (\n\t"io"\n\t"os/exec"\n'),
                  ("func hostGet(", "var reviewerDelegation = exec.Command\n\nfunc hostGet(")],
    },
    {
        "name": "R08-distribution-launches-build-tree-copy-not-the-install",
        "file": DS,
        "why": "the digest cross-check compares bytes; two builds of one source emit byte-identical version records",
        "expected": ["W0503-DISTRIBUTION-SELFREPORT-DIGEST-MATCHES-INDEPENDENT-LAUNCH"],
        "edits": [('code, stdout, stderr, err := installed(exe, "version")',
                   'code, stdout, stderr, err := installed(filepath.Join(*repo, ".local", "w0503_cli.exe"), "version")')],
    },
    {
        "name": "R09-ascii-distribution-target",
        "file": CK,
        "why": "does the Chinese/space path condition actually gate the run, or is it only claimed",
        "expected": ["W0503-DISTRIBUTION-CANDIDATE-PASSES"],
        "edits": [('target := filepath.Join(repo, ".local", "w0503 分发 target")',
                   'target := filepath.Join(repo, ".local", "w0503_target")')],
    },
    {
        "name": "R10-cancel-and-status-share-one-body",
        "file": CC,
        "why": "action 1 says implement each command; cancel/goal/go/status/resume all run the same health probe. "
               "Rename the reported command to prove the rows key off the name, not the operation",
        "expected": ["W0503-RESUME-GOES-THROUGH-THE-HOST"],
        "edits": [('\toutJSON(map[string]any{"command": name, "status": "HOST_ANSWERED", "exit_code": exitCompleted,',
                   '\toutJSON(map[string]any{"command": "status", "status": "HOST_ANSWERED", "exit_code": exitCompleted,')],
    },
]


def sha(p):
    return hashlib.sha256(open(os.path.join(REPO, p), "rb").read()).hexdigest()


def apply(m):
    p = os.path.join(REPO, m["file"])
    raw = open(p, "rb").read().decode("utf-8")
    for old, new in m["edits"]:
        ob = old
        if raw.count(ob) != 1:
            return "anchor-missing(count=%d)" % raw.count(ob)
        raw = raw.replace(ob, new)
    open(p, "wb").write(raw.encode("utf-8"))
    return None


def restore(m):
    subprocess.run(["git", "checkout", "--", m["file"],], cwd=REPO, env=ENV, capture_output=True)
    por = subprocess.run(["git", "status", "--porcelain", m["file"]], cwd=REPO, env=ENV,
                         capture_output=True, encoding="utf-8", errors="replace").stdout
    return sha(m["file"]) == BASELINE_SHA[m["file"]] and por.strip() == ""


def run_check():
    pr = subprocess.run([GO, "run", "./tests/runtime/cli_contract"], cwd=REPO, env=ENV,
                        capture_output=True, encoding="utf-8", errors="replace")
    lines = [l.strip() for l in (pr.stdout or "").replace("\r\n", "\n").split("\n") if l.strip()]
    if not lines:
        return {"status": "NO-REPORT", "exit": pr.returncode, "red": [], "ids": [],
                "detail": (pr.stderr or "")[-400:]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "exit": pr.returncode,
            "red": sorted([f.get("id") for f in d.get("failures") or []]),
            "ids": sorted(d.get("assertion_ids") or []),
            "not_verified": d.get("not_verified"), "assertions": d.get("assertions")}


def main():
    results = []
    for m in MUTANTS:
        ent = {"mutant": m["name"], "file": m["file"], "why": m["why"],
               "expected_rows": m["expected"]}
        aerr = apply(m)
        if aerr:
            ent["classification"] = "anchor-missing"
            ent["anchor_error"] = aerr
            results.append(ent)
            print("%s ANCHOR-MISSING" % m["name"], file=sys.stderr)
            continue
        r = run_check()
        ent["report_status"] = r["status"]
        ent["red_rows"] = r["red"]
        ent["assertions_green"] = r.get("assertions")
        if r["status"] == "NO-REPORT":
            ent["classification"] = "crashed-mutant-ill-formed"
            ent["detail"] = r["detail"]
        elif r["status"] == "PASS":
            ent["classification"] = "survived"
        else:
            hit = [x for x in r["red"] if x in m["expected"]]
            if m["expected"] and hit:
                ent["classification"] = "caught-by-named-id"
                ent["killed_by"] = sorted(hit)
                ent["extra_red_rows"] = [x for x in r["red"] if x not in hit]
            else:
                ent["classification"] = "caught-by-gate-id-only"
                ent["killed_by"] = []
                ent["extra_red_rows"] = r["red"]
        ent["restored_byte_exact"] = restore(m)
        results.append(ent)
        print("%s -> %s (red=%d)" % (m["name"], ent["classification"], len(r["red"])), file=sys.stderr)
    counts = {}
    for e in results:
        counts[e["classification"]] = counts.get(e["classification"], 0) + 1
    out = {"card": "W05-03", "round": "verifier-round-1", "reviewer_id": "qoder-desktop:/root/w0503_verifier_r1",
           "tool": "tests/runtime/cli_contract (go run)", "baseline": {"status": "PASS", "assertions": 46},
           "mutants": results, "counts": counts,
           "restore_policy": "git checkout -- <the one mutated file>, verified by sha256 against the digest the "
                             "executor registered in execution/v2.4/step_state.json plus empty git status --porcelain",
           "scope": "REVIEWER_MUTATION_MATRIX_NOT_PRODUCT_ACCEPTANCE"}
    with open(os.path.join(REPO, "execution", "v2.4", "receipts", "W05", "W05-03",
                           "mutation_selfcheck_verifier_round1.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
