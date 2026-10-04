"""Reviewer round-1 mutation re-measurement for W07-02 (independent of the executor's driver).

Three questions the executor's record does not answer by itself:

1. Do the executor's two mutants really kill the named tests on THIS tree? (re-run their driver's exact
   substitutions, from bytes I captured myself, restored and proven by sha256 + clean re-run)
2. Would the two new tests pass against the TRUE pre-fix product bytes (commit 2e69022e)? A test that only fails
   against a hand-picked regex mutant proves less than one that fails against the real previous behaviour, so the
   whole pre-fix file is restored from git and the named test run against it.
3. Is the fix pinned on every site it was applied to? The adapter has FOUR gap sites (two DETAIL_UNAVAILABLE,
   two INCOMPLETE_ITEM). The executor's M1 only rewrote the two INCOMPLETE_ITEM sites, and the domain's
   "nothing complete still seals nothing" half was never mutated. Those are measured here as reviewer-added
   mutants M3/M4; a survivor means the claim is only partly pinned.

Usage: python execution/v2.4/receipts/W07/W07-02/reviewer_mut_w0702_round1.py [--out PATH]
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
GO = os.path.join(ROOT, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
X_FILE = os.path.join(ROOT, "adapters", "sources", "x.go")
D_FILE = os.path.join(ROOT, "internal", "domain", "sources.go")
PRE = "2e69022e"  # last commit before the card's product fix


def sub(pattern, replacement, text):
    return re.subn(pattern, replacement, text)


MUTANTS = [
    {
        "id": "W0702-M1-adapter-gap-returns-without-cursor",
        "kind": "executor-replay",
        "file": X_FILE,
        "pattern": r'(p\.Failure = "INCOMPLETE_ITEM"\n(\s*))break',
        "replacement": r"\1return p, nil",
        "expect": 2,
        "test": "./adapters/sources",
        "run": "TestW0702XGapKeepsPrefixAndResumeCursor",
        "claim": "a page that stops at a gap still reports how far the window was observed",
    },
    {
        "id": "W0702-M2-domain-discards-partial-prefix",
        "kind": "executor-replay",
        "file": D_FILE,
        "pattern": r'if e != nil \|\| \(page\.Failure != "" && len\(page\.Items\) == 0\) \{',
        "replacement": 'if e != nil || page.Failure != "" {',
        "expect": 1,
        "test": "./internal/domain",
        "run": "TestW0702PartialPageSealsItsVerifiedPrefix",
        "claim": "a partially rendered page still seals its verified prefix",
    },
    {
        "id": "REVIEW-M3-adapter-detail-unavailable-aborts-page",
        "kind": "reviewer-added",
        "file": X_FILE,
        "pattern": r'(p\.Failure = "DETAIL_UNAVAILABLE"\n(\s*))break',
        "replacement": r"\1return p, nil",
        "expect": 2,
        "test": "./adapters/sources",
        "run": "TestW0702",
        "claim": "every gap site (not just INCOMPLETE_ITEM) keeps the verified prefix",
    },
    {
        "id": "REVIEW-M4-domain-seals-a-page-with-nothing-complete",
        "kind": "reviewer-added",
        "file": D_FILE,
        "pattern": r'if e != nil \|\| \(page\.Failure != "" && len\(page\.Items\) == 0\) \{',
        "replacement": 'if e != nil {',
        "expect": 1,
        "test": "./internal/domain",
        "run": "TestW0702",
        "claim": "a failure with nothing complete still seals nothing (the negative half of the new contract)",
    },
]


def go(test, run):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", GOFLAGS="-mod=mod", RESEARCHOS_GO=GO)
    p = subprocess.run([GO, "test", "-count=1", test, "-run", run], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT, env=env, timeout=1500)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def detail(log, limit=3):
    out = []
    for line in log.splitlines():
        if "test.go:" in line or line.startswith("--- FAIL") or "cannot use" in line or "undefined" in line \
                or "declared and not used" in line or "syntax error" in line:
            out.append(line.strip()[:220])
            if len(out) >= limit:
                break
    if not out:
        out = [(l.strip()[:220]) for l in log.strip().splitlines()[-2:]]
    return out


def git_show(path, rev):
    p = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, path)], capture_output=True)
    return p.stdout


def main():
    assert os.path.isfile(GO), "locked go toolchain missing"
    out_path = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    results = []
    originals = {f: open(f, "rb").read() for f in (X_FILE, D_FILE)}
    orig_sha = {f: hashlib.sha256(b).hexdigest() for f, b in originals.items()}
    baseline = subprocess.run(["git", "-C", ROOT, "status", "--porcelain=v1", "--untracked-files=no"],
                              capture_output=True, text=True).stdout.strip()

    def restore(f):
        io.open(f, "wb").write(originals[f])
        return hashlib.sha256(open(f, "rb").read()).hexdigest() == orig_sha[f]

    for m in MUTANTS:
        text = io.open(m["file"], encoding="utf-8").read()
        mutated, n = sub(m["pattern"], m["replacement"], text)
        if n != m["expect"]:
            results.append({"id": m["id"], "kind": m["kind"], "class": "anchor-missing",
                            "occurrences": n, "expected": m["expect"]})
            continue
        io.open(m["file"], "w", encoding="utf-8", newline="\n").write(mutated)
        rc, log = go(m["test"], m["run"])
        ok_restore = restore(m["file"])
        rc_clean, log_clean = go(m["test"], m["run"])
        results.append({
            "id": m["id"], "kind": m["kind"], "file": os.path.relpath(m["file"], ROOT).replace("\\", "/"),
            "occurrences": n, "claim": m["claim"], "mutated_rc": rc, "mutated_detail": detail(log),
            "clean_rc": rc_clean, "clean_detail": detail(log_clean) if rc_clean else [],
            "restored_sha256_matches": ok_restore,
            "class": "caught" if (rc != 0 and rc_clean == 0 and ok_restore) else
                     ("unrestored" if not ok_restore else "SURVIVED"),
        })

    # question 2: the TRUE pre-fix product bytes, whole-file restore from git, both new tests run against them
    prefix = []
    for f, rel in ((X_FILE, "adapters/sources/x.go"), (D_FILE, "internal/domain/sources.go")):
        pre_bytes = git_show(rel, PRE)
        assert pre_bytes and b"package " in pre_bytes[:40], "could not read pre-fix bytes for " + rel
        io.open(f, "wb").write(pre_bytes)
    tests = [("./adapters/sources", "TestW0702XGapKeepsPrefixAndResumeCursor"),
             ("./adapters/sources", "TestW0702XGapOnFirstArticleSealsNothingButStillReports"),
             ("./internal/domain", "TestW0702PartialPageSealsItsVerifiedPrefix"),
             ("./internal/domain", "TestW0702FailedPageWithNothingCompleteStillSealsNothing")]
    for test, run in tests:
        rc, log = go(test, run)
        prefix.append({"run": run, "test": test, "rc": rc, "detail": detail(log, 2)})
    ok_all = all([restore(X_FILE), restore(D_FILE)])
    rc_pair = {}
    for test, run in tests:
        rc_pair[run], _ = go(test, run)
    after = subprocess.run(["git", "-C", ROOT, "status", "--porcelain=v1", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()

    summary = {
        "artifact": "reviewer_mutation_round1.json",
        "reviewer_id": "qoder-desktop:/root/w0702_verifier_r1",
        "step_id": "W07-02",
        "repository_head": subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                          capture_output=True, text=True).stdout.strip(),
        "pre_fix_bytes_taken_from": PRE,
        "file_sha_before_run": orig_sha,
        "mutants": results,
        "buckets": {k: sum(1 for r in results if r["class"] == k)
                    for k in ("caught", "SURVIVED", "anchor-missing", "unrestored")},
        "new_tests_against_true_pre_fix_bytes": {"all_restored": ok_all, "runs": prefix,
                                                 "clean_recheck_rc": rc_pair},
        "git_status_identical_to_baseline": after == baseline,
        "git_status_baseline": baseline,
        "git_status_after": after,
    }
    blob = json.dumps(summary, ensure_ascii=False, indent=1)
    if out_path:
        io.open(out_path, "w", encoding="utf-8", newline="\n").write(blob)
    print(blob)


if __name__ == "__main__":
    main()
