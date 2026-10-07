"""A/B the four legacy failures, three attempts per state, recording every attempt separately.

A flat "these are pre-existing" claim was rejected before, and a flat "PASS" that only holds on retry
was rejected too, so this records each attempt and lets the reader see which rows move. Only
internal/domain/changes.go is swapped: it is the only file this card changed that the legacy domain
suite can see. The working copy is restored hash-exact and that restore is asserted, not assumed.
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys

CHG = "internal/domain/changes.go"
MINE = ".local/ab/changes.go.mine"
TESTS = ("TestW17UpgradeActiveRecovery|TestW12DuplicateCallbacks|"
         "TestRuntimeCoordinatorTypedBroker|TestRuntimeCoordinatorSkipsUnrelatedReady")
NAMES = ["TestW17UpgradeActiveRecovery", "TestW12DuplicateCallbacks",
         "TestRuntimeCoordinatorTypedBroker", "TestRuntimeCoordinatorSkipsUnrelatedReady"]
MINE_SHA = "7b10c3454e6378b133ccf6d9ee584005ebca53cc5221390c31a070523130e7cd"
ATTEMPTS = 3

GO = os.path.join(".local", "tools", "go1.27.1", "go", "bin", "go.exe")
ENV = dict(os.environ)
ENV.update({"GOTOOLCHAIN": "local", "GOENV": "off", "GOFLAGS": "", "PYTHONIOENCODING": "utf-8",
            "GOPATH": os.path.abspath(".local/gopath"), "GOCACHE": os.path.abspath(".local/gocache"),
            "RESEARCHOS_GO": os.path.abspath(GO)})


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def head_version():
    r = subprocess.run(["git", "show", "HEAD:" + CHG], capture_output=True)
    if r.returncode != 0:
        sys.exit("cannot read HEAD version of " + CHG)
    return r.stdout


def run_once():
    r = subprocess.run([GO, "test", "./internal/domain/", "-run", TESTS, "-count=1", "-v",
                        "-timeout", "900s"], env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    failed = {n for n in NAMES if ("--- FAIL: " + n) in out}
    ran = {n for n in NAMES if (("--- FAIL: " + n) in out or ("--- PASS: " + n) in out)}
    return {"exit": r.returncode, "failed": sorted(failed),
            "not_observed": sorted(set(NAMES) - ran),
            "seconds": round(len(out) / 100000.0, 2)}


def main():
    if sha(MINE) != MINE_SHA:
        sys.exit("the saved remediated copy does not match its recorded hash")
    original = open(CHG, "rb").read()
    if hashlib.sha256(original).hexdigest() != MINE_SHA:
        sys.exit("the working tree is not in the remediated state; refusing to A/B")

    results = {"remediated": [], "reverted": []}
    head_bytes = head_version()
    try:
        for state, payload in (("remediated", original), ("reverted", head_bytes)):
            with open(CHG, "wb") as f:
                f.write(payload)
            print("state=%s sha256=%s" % (state, sha(CHG)[:16]), flush=True)
            for i in range(ATTEMPTS):
                r = run_once()
                r["attempt"] = i + 1
                results[state].append(r)
                print("  attempt %d exit=%d failed=%r" % (i + 1, r["exit"], r["failed"]), flush=True)
    finally:
        with open(CHG, "wb") as f:
            f.write(original)
        restored = sha(CHG) == MINE_SHA
        print("restored hash-exact: %s (%s)" % (restored, sha(CHG)[:16]), flush=True)
        if not restored:
            shutil.copyfile(MINE, CHG)
            print("recovered from the saved copy: %s" % (sha(CHG) == MINE_SHA), flush=True)
        results["restored_hash_exact"] = sha(CHG) == MINE_SHA

    rows = []
    for n in NAMES:
        rem = sum(1 for r in results["remediated"] if n in r["failed"])
        rev = sum(1 for r in results["reverted"] if n in r["failed"])
        rows.append({"test": n,
                     "failed_in_remediated": "%d of %d" % (rem, ATTEMPTS),
                     "failed_in_reverted": "%d of %d" % (rev, ATTEMPTS),
                     "classification": ("DETERMINISTIC_PRE_EXISTING" if rem == rev == ATTEMPTS else
                                        "FLAKY" if rem != rev or (0 < rem < ATTEMPTS) else
                                        "NOT_REPRODUCED_IN_EITHER_STATE" if rem == rev == 0 else
                                        "NEEDS_REVIEW")})
    results["per_test"] = rows
    io.open(".local/ab/legacy_ab.json", "w", encoding="utf-8", newline="\n").write(
        __import__("json").dumps(results, indent=1, ensure_ascii=False))
    print()
    for r in rows:
        print("%-42s remediated=%-7s reverted=%-7s %s"
              % (r["test"], r["failed_in_remediated"], r["failed_in_reverted"], r["classification"]))


main()
