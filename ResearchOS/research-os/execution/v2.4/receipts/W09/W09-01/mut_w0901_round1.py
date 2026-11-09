"""W09-01 mutation matrix: one mutant per product guard leg, anchored on the delivered bytes.

Anchors below were taken by reading the files at HEAD 17e2ece8, not from memory, and every one is asserted to occur
exactly once before it is applied: a wrong anchor is reported as anchor-missing, never as a kill or a survival. Each
mutant disables ONE decision while keeping the package compiling (unused-variable mutants crash rather than measure).

Scope note for the reviewer: internal/domain/retrieval.go, retrieval_local.go and sources.go are outside W09-01's write
scope. They are edited transiently here - write, run, restore, digest-compare against the byte block captured at start -
which is the same measurement technique the accepted cards used, and nothing net changes on disk.

The handler's own guards (routing refusal, roster equality, locked-toolchain resolution) are covered by a second script,
because tests/evidence/check/main.py is inside this card's write scope and its mutants are written from its delivered text.
"""
import hashlib
import json
import os
import subprocess
import sys

REPO = os.getcwd()
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
ENV = dict(os.environ, GOTOOLCHAIN="local", GOPATH=os.path.join(REPO, ".local", "gopath"),
           GOCACHE=os.path.join(REPO, ".local", "gocache"), RESEARCHOS_GO=GO, PYTHONUTF8="1")
CMD = [sys.executable, "-X", "utf8", "tests/evidence/check/main.py"]

SOURCES = "internal/domain/sources.go"
ORIGIN = "internal/domain/evidence_origin.go"
RETRIEVAL = "internal/domain/retrieval.go"

MUTANTS = [
    ("N01-observed-kind-mismatch-unchecked", SOURCES,
     '\tif artifact["evidence_kind"] != b["evidence_kind"] {',
     '\tif false {',
     "W0901-OBSERVED-CLAIM-REFUSED-OVER-SIMULATED-SNAPSHOT"),
    ("N02-observed-requires-live-unchecked", SOURCES,
     '\tif b["evidence_kind"] == "OBSERVED" && artifact["measurement_mode"] != "LIVE" {',
     '\tif false && artifact["measurement_mode"] != "LIVE" {',
     "W0901-OBSERVED-CLAIM-REFUSED-OVER-FIXTURE-MODE-SNAPSHOT"),
    ("N03-snapshot-currency-leg-unread", SOURCES,
     '\tif artifact["validity"] != "CURRENT" || artifact["content_hash"] != artifactRef["content_hash"] {',
     '\tif false || artifact["content_hash"] != artifactRef["content_hash"] {',
     "W0901-CREATE-REFUSED-WHEN-SNAPSHOT-NOT-CURRENT"),
    # The hash half of the same compound is a different decision and needs its own mutant and its own input.
    ("N03b-snapshot-hash-leg-unread", SOURCES,
     '\tif artifact["validity"] != "CURRENT" || artifact["content_hash"] != artifactRef["content_hash"] {',
     '\tif artifact["validity"] != "CURRENT" || false {',
     "W0901-SUMMARY-BODY-CANNOT-BE-SWAPPED-FOR-SEALED-ORIGINAL"),
    ("N04-origin-must-be-current-observed", ORIGIN,
     '\tif ev["evidence_kind"] != "OBSERVED" || ev["validity"] != "CURRENT" {',
     '\tif ev["validity"] != "CURRENT" && false {',
     "W0901-SIMULATED-EVIDENCE-REFUSED-ORIGIN-REVIEW"),
    ("N05-origin-chain-citation-unread", ORIGIN,
     '\t\tif !strings.Contains(string(sourceBody), originURL) {',
     '\t\tif false && strings.Contains(string(sourceBody), originURL) {',
     "W0901-UNCITED-REPOST-CANNOT-BE-ATTACHED-TO-THE-ORIGIN"),
    ("N06-stale-origin-accepted", ORIGIN,
     '\t\tif origin["evidence_kind"] != "OBSERVED" || origin["validity"] != "CURRENT" {',
     '\t\tif origin["validity"] != "CURRENT" && false {',
     "W0901-STALE-ORIGIN-CANNOT-ANCHOR-A-NEW-DOWNSTREAM"),
    ("N07-local-hit-hash-recheck-skipped", RETRIEVAL,
     '\t\t\tif data == nil || Digest(data) != a["content_hash"] {',
     '\t\t\tif data == nil && false {',
     "W0901-SEARCH-REVALIDATES-CURRENT-SOURCE-HASH-BEFORE-HIT"),
]


def digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_handler():
    env = dict(ENV, RESEARCHOS_TASK_ID="W09", RESEARCHOS_CHECK_ID="W09-01")
    p = subprocess.run(CMD, capture_output=True, text=True, env=env, timeout=1800, cwd=REPO,
                       encoding="utf-8", errors="replace")
    lines = [l for l in (p.stdout or "").strip().splitlines() if l.strip()]
    if not lines:
        return "crashed", [], (p.stderr or "")[-300:]
    try:
        report = json.loads(lines[-1])
    except Exception:
        return "crashed", [], "no parsable final report"
    failed = [f["id"] for f in (report.get("failures") or [])]
    # `red` is what a mutant must achieve; `green` is what the clean tree must show. Naming them by exit status, not by
    # "caught"/"survived", is what keeps the clean precondition from contradicting itself: a green run has no failures,
    # which an earlier version of this script read as a survivor and refused to measure at all.
    status = report.get("status")
    if status == "PASS" and not failed and p.returncode == 0:
        return "green", [], ""
    if failed and p.returncode != 0:
        return "red", failed, ""
    return "unexpected", failed, "status=%s rc=%s" % (status, p.returncode)


def main():
    originals = {p: (open(p, "rb").read(), digest(p)) for p in {m[1] for m in MUTANTS}}
    cls, clean_failed, note = run_handler()
    if cls != "green" or clean_failed:
        raise SystemExit("clean run is not green: %s %s %s" % (cls, clean_failed, note))
    clean = json.loads(subprocess.run(CMD, capture_output=True, text=True, env=dict(ENV, RESEARCHOS_TASK_ID="W09",
                RESEARCHOS_CHECK_ID="W09-01"), cwd=REPO, timeout=1800, encoding="utf-8").stdout.strip().split("\n")[-1])
    roster = set(clean.get("assertion_ids") or [])

    rows = []
    for name, path, old, new, expect in MUTANTS:
        row = {"mutant": name, "file": path, "expected_assertion": expect}
        if expect not in roster:
            row["classification"] = "expected-assertion-not-in-roster"
            rows.append(row)
            print("%-40s expected id not emitted: %s" % (name, expect))
            continue
        text = originals[path][0].decode("utf-8")
        count = text.count(old)
        if count != 1:
            row["classification"] = "anchor-missing"
            row["anchor_occurrences"] = count
            rows.append(row)
            print("%-40s anchor-missing (%d)" % (name, count))
            continue
        open(path, "w", encoding="utf-8", newline="").write(text.replace(old, new, 1))
        try:
            cls, failed, note = run_handler()
            row["assertions_that_went_red"] = failed
            row["expected_in_red"] = expect in failed
            if cls in ("crashed", "unexpected"):
                row["classification"] = "crashed"
                row["note"] = note or "run did not produce a comparable report"
            elif cls == "green":
                row["classification"] = "survived"
            else:
                row["classification"] = "caught" if expect in failed else "survived"
        finally:
            open(path, "wb").write(originals[path][0])
            if digest(path) != originals[path][1]:
                row["restore_verified"] = False
                json.dump({"rows": rows, "aborted": "restore failed for " + path},
                          open(".local/mutation_selfcheck_w0901_round1.json", "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                raise SystemExit("RESTORE FAILED for %s" % path)
            row["restore_verified"] = True
        rows.append(row)
        print("%-40s %-12s red=%-3d expected=%s" % (name, row["classification"],
                                                     len(row.get("assertions_that_went_red", [])),
                                                     row.get("expected_in_red")))

    summary = {}
    for r in rows:
        summary[r["classification"]] = summary.get(r["classification"], 0) + 1
    json.dump({"total": len(MUTANTS), "summary": summary, "rows": rows, "clean_roster_count": len(roster)},
              open(".local/mutation_selfcheck_w0901_round1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
