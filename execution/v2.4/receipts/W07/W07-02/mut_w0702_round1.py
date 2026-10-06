"""W07-02 mutation driver: prove the new gap tests fail for the stated reason, not incidentally.

Each mutant rewrites one guard back to the pre-card behaviour, runs the named test, and restores the file from the
bytes captured at the top of the run. The restore is verified by sha256 equality and a clean re-run, so a surviving
mutant can never leave a modified product file behind.

Usage: python execution/v2.4/receipts/W07/W07-02/mut_w0702_round1.py [--out PATH]
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

# repo/execution/v2.4/receipts/W07/W07-02/script.py -> five levels up is the repository root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
GO = os.path.join(ROOT, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
X_FILE = os.path.join(ROOT, "adapters", "sources", "x.go")
D_FILE = os.path.join(ROOT, "internal", "domain", "sources.go")

MUTANTS = [
    {
        "id": "W0702-M1-adapter-gap-returns-without-cursor",
        "file": X_FILE,
        "pattern": re.compile(r'(p\.Failure = "INCOMPLETE_ITEM"\n(\s*))break'),
        "replacement": r"\1return p, nil",
        "expect_occurrences": 2,
        "test": "./adapters/sources",
        "run": "TestW0702XGapKeepsPrefixAndResumeCursor",
        "claim_under_test": "a page that stops at a gap still reports how far the window was observed",
    },
    {
        "id": "W0702-M2-domain-discards-partial-prefix",
        "file": D_FILE,
        "pattern": re.compile(r'if e != nil \|\| \(page\.Failure != "" && len\(page\.Items\) == 0\) \{'),
        "replacement": 'if e != nil || page.Failure != "" {',
        "expect_occurrences": 1,
        "test": "./internal/domain",
        "run": "TestW0702PartialPageSealsItsVerifiedPrefix",
        "claim_under_test": "a partially rendered page still seals its verified prefix",
    },
]


def go(test, run):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", GOFLAGS="-mod=mod", RESEARCHOS_GO=GO)
    p = subprocess.run([GO, "test", test, "-run", run], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT, env=env, timeout=900)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def failure_line(log):
    for line in log.splitlines():
        if "test.go:" in line or line.startswith("--- FAIL"):
            return line.strip()[:240]
    return (log.strip().splitlines() or [""])[-1][:240]


def main():
    assert os.path.isdir(os.path.join(ROOT, "execution", "v2.4")), "ROOT resolved outside the repository: " + ROOT
    assert os.path.isfile(GO), "locked go toolchain missing: " + GO
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    results, problems = [], []
    originals = {m["file"]: open(m["file"], "rb").read() for m in MUTANTS}
    baseline = subprocess.run(["git", "-C", ROOT, "status", "--porcelain=v1", "--untracked-files=no"], capture_output=True, text=True).stdout.strip()
    for m in MUTANTS:
        text = io.open(m["file"], encoding="utf-8").read()
        mutated, n = m["pattern"].subn(m["replacement"], text)
        if n != m["expect_occurrences"]:
            problems.append("%s: anchor matched %d times, expected %d - this mutant did not run"
                            % (m["id"], n, m["expect_occurrences"]))
            results.append({"id": m["id"], "class": "anchor-missing", "occurrences": n})
            continue
        io.open(m["file"], "w", encoding="utf-8", newline="\n").write(mutated)
        rc, log = go(m["test"], m["run"])
        # restore, then prove the bytes are exactly what they were before this mutant
        io.open(m["file"], "wb").write(originals[m["file"]])
        restored = hashlib.sha256(open(m["file"], "rb").read()).hexdigest()
        expected = hashlib.sha256(originals[m["file"]]).hexdigest()
        rc_clean, log_clean = go(m["test"], m["run"])
        results.append({
            "id": m["id"],
            "file": os.path.relpath(m["file"], ROOT).replace("\\", "/"),
            "occurrences": n,
            "claim_under_test": m["claim_under_test"],
            "mutated_rc": rc,
            "mutated_failure_line": failure_line(log),
            "restored_sha256_matches": restored == expected,
            "clean_recheck_rc": rc_clean,
            "class": "caught" if rc != 0 and rc_clean == 0 and restored == expected else "survived-or-unrestored",
        })
    summary = {
        "artifact": "mutation_selfcheck_round1.json",
        "step_id": "W07-02",
        "run_by": "qoder-desktop:/root/construction",
        "repository_head": subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                                          text=True).stdout.strip(),
        "method": "one mutant per named guard, each restored from bytes captured at start and re-verified by sha256 "
                  "plus a clean re-run of the same test",
        "mutants": results,
        "problems": problems,
        "buckets": {k: sum(1 for r in results if r["class"] == k) for k in ("caught", "survived-or-unrestored")},
        "anchor_missing": len(problems),
        "note": "A mutant that cannot be anchored is reported as anchor-missing, which is an UNTESTED guard, not a "
                "pass. Survivors here would mean the new tests do not actually watch the behaviour they claim.",
    }
    blob = json.dumps(summary, ensure_ascii=False, indent=1)
    if out_path:
        io.open(out_path, "w", encoding="utf-8", newline="\n").write(blob)
    print(blob)
    after = subprocess.run(["git", "-C", ROOT, "status", "--porcelain=v1", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()
    print("git status identical to the pre-mutant baseline:", after == baseline)
    if after != baseline:
        print("BASELINE:", baseline)
        print("AFTER   :", after)
    summary["tree_matches_pre_mutant_baseline"] = after == baseline
    blob2 = json.dumps(summary, ensure_ascii=False, indent=1)
    if out_path:
        io.open(out_path, "w", encoding="utf-8", newline="\n").write(blob2)
    print(blob2)


if __name__ == "__main__":
    main()
