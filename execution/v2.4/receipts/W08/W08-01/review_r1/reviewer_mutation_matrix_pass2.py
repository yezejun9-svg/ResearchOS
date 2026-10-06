#!/usr/bin/env python3
"""Round-1 reviewer matrix, pass 2.

Two purposes.

(a) Fix two of my own pass-1 mutants that proved nothing and re-measure them honestly:
    R1-M16b was a comment-only edit, so it was a no-op, not a survivor.
    R1-M30 called tx.Commit() and discarded its error, so the write still persisted; it never
    removed the commit. R1-M30b drops the commit outright.

(b) Ask the question pass 1 cannot answer. Six pass-1 mutants were "unguarded" against the BOUND
    command (test.research.fixture). This card also ships three in-package Go test files, so a
    guard the roster does not name may still be named by `go test ./internal/domain -run W0801`.
    Each pass-1 non-caught mutant is re-measured against that second oracle.

Same clean -> mutate -> measure -> restore -> clean protocol and the same digest gates as pass 1.
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import time

REPO = "D:/作品集/ResearchOS/research-os"
spec = importlib.util.spec_from_file_location(
    "m", os.path.join(REPO, "execution/v2.4/receipts/W08/W08-01/review_r1/reviewer_mutation_matrix.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ADOPT, CHECK, DIGESTS, ENV, GO = m.ADOPT, m.CHECK, m.DIGESTS, m.ENV, m.GO
EVDIR = m.EVDIR

# pass-1 ids whose "not caught" verdict must be re-tested against the Go-test oracle
RETEST = {
    "R1-M08": "decision enum membership (out-of-enum decision kind)",
    "R1-M09": "adoption_decision_ref entity_type leg",
    "R1-M10": "input_revision must be a positive integer",
    "R1-M17": "RESEARCH=FAILED refused by the no-skip gate (third named form)",
    "R1-M21": "ReuseJevGate receipt must carry status/selected/signals",
    "R1-M28": "adoption_decision_ref effectiveness check (s.effective)",
    "R1-M32": "probe depth cap alone removed (check-program only; go test cannot see it)",
}
PASS2 = [
    ("R1-M16c", m.ADOPT,
     '\tcase StageNotStarted:\n\t\tswitch stage {\n\t\tcase StageResearch:\n\t\t\treturn "run a research cycle over the declared sources"',
     '\tcase StageNotStarted:\n\t\tswitch stage {\n\t\tcase StageResearch + "-x":\n\t\t\treturn "run a research cycle over the declared sources"',
     "every NOT_STARTED stage collapses onto the generic reader action (per-stage wording lost)",
     "fixture"),
    ("R1-M30b", m.ADOPT,
     '\treturn out, tx.Commit()',
     '\treturn out, nil',
     "the durable write never commits",
     "fixture"),
]

by_id = {r[0]: r for r in m.M}


def go_test(pattern="W0801"):
    t = time.time()
    p = subprocess.run([GO, "test", "./internal/domain", "-count=1", "-run", pattern, "-v"],
                       capture_output=True, cwd=REPO, env=ENV, timeout=1800)
    out = p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")
    fails = sorted({ln.split()[2] for ln in out.splitlines() if ln.startswith("--- FAIL")})
    passed = sorted({ln.split()[2] for ln in out.splitlines() if ln.startswith("--- PASS") and "0." in ln
                     or (ln.startswith("--- PASS") and len(ln.split()) > 2)})
    subs = sorted({ln.strip().split()[1] for ln in out.splitlines()
                   if ln.strip().startswith("--- FAIL") and ln.strip().split()[1].startswith("Test")})
    top = sorted({ln.split()[2] for ln in out.splitlines()
                  if ln.startswith("--- FAIL") and len(ln.split()) > 2 and "/" not in ln.split()[2]})
    return {"rc": p.returncode, "seconds": round(time.time() - t, 2), "failed_top_level": top,
            "failed_any": sorted(set(top) | set(subs)),
            "tail": out.strip().splitlines()[-6:]}


def apply(path, old, new):
    p = os.path.join(REPO, path)
    b = open(p, "rb").read().decode("utf-8")
    if b.count(old) != 1:
        raise RuntimeError("anchor count %d" % b.count(old))
    open(p, "wb").write(b.replace(old, new).encode("utf-8"))


def restore(path, original):
    open(os.path.join(REPO, path), "wb").write(original)
    return hashlib.sha256(open(os.path.join(REPO, path), "rb").read()).hexdigest() == DIGESTS[path]


def main():
    orig = {f: open(os.path.join(REPO, f), "rb").read() for f in (ADOPT, CHECK)}
    results = []
    retest_only = "--retest-only" in os.sys.argv
    corrected_only = "--corrected-only" in os.sys.argv
    outfile = ("mutation_matrix_reviewer_r1_pass2b.json" if retest_only else
               "mutation_matrix_reviewer_r1_pass2a.json" if corrected_only else
               "mutation_matrix_reviewer_r1_pass2.json")
    for mid, path, old, new, desc, _ in ([] if retest_only else PASS2):
        entry = {"id": mid, "guard": desc, "file": path, "kind": "reviewer-corrected-mutant",
                 "must_red_anchors": ["W0801-PROJ-READER-ACTION-EVERY-INCOMPLETE"] if mid == "R1-M16c"
                 else ["W0801-RECORD-STAGE-ROW-WRITTEN"]}
        cb = m.run(mid + "/clean-before")
        entry["clean_before"] = {k: cb.get(k) for k in ("status", "n_ids", "rc")}
        if cb.get("status") != "PASS" or cb.get("n_ids") != 64:
            entry["classification"] = "BASELINE-RED"
            results.append(entry)
            print(mid, "BASELINE-RED", flush=True)
            continue
        apply(path, old, new)
        mut = m.run(mid + "/mutated")
        gt = go_test()
        rest = restore(path, orig[path])
        ca = m.run(mid + "/clean-after")
        entry["mutated"] = {k: mut.get(k) for k in ("status", "n_ids", "rc", "procs_sample")}
        entry["mutated_failures"] = mut.get("failures")
        entry["gotest"] = {k: gt.get(k) for k in ("rc", "failed_top_level", "failed_any")}
        entry["restored_digest_ok"] = rest
        entry["clean_after"] = {k: ca.get(k) for k in ("status", "n_ids", "rc")}
        ids_now, fails_now = set(mut.get("ids") or []), set(mut.get("failures") or [])
        a = entry["must_red_anchors"][0]
        if not rest:
            entry["classification"] = "RESTORE-FAILED"
        elif a in fails_now:
            entry["classification"] = "caught"
        elif a in ids_now:
            entry["classification"] = "survived"
        else:
            entry["classification"] = "anchor-missing"
        entry["collateral_reds"] = sorted(x for x in fails_now if x != a)
        results.append(entry)
        print("%-8s %-22s fx=%s/%s red=%d gotest_rc=%s restore=%s after=%s/%s procs=%s" % (
            mid, entry["classification"], mut.get("status"), mut.get("n_ids"), len(fails_now),
            gt.get("rc"), rest, ca.get("status"), ca.get("n_ids"),
            entry["mutated"].get("procs_sample")), flush=True)
        for f in (ADOPT, CHECK):
            assert hashlib.sha256(open(os.path.join(REPO, f), "rb").read()).hexdigest() == DIGESTS[f]

    # ---- (b) re-test pass-1 non-caught mutants against the go-test oracle ----
    for id_, guard in ({} if corrected_only else RETEST).items():
        _, path, old, new, _ = by_id[id_][1], by_id[id_][2], by_id[id_][3], by_id[id_][4], by_id[id_][5]
        entry = {"id": id_ + "/gotest", "guard": guard, "file": path, "kind": "pass-1 re-measure",
                 "pass1_verdict": "not caught by the bound fixture command"}
        cb = m.run(id_ + "/clean-before")
        gt0 = go_test()
        entry["clean"] = {"fixture": {k: cb.get(k) for k in ("status", "n_ids")},
                          "gotest_rc": gt0["rc"], "gotest_failed": gt0["failed_any"]}
        if cb.get("status") != "PASS" or cb.get("n_ids") != 64 or gt0["rc"] != 0:
            entry["classification"] = "BASELINE-RED"
            results.append(entry)
            print(id_, "BASELINE-RED", entry["clean"], flush=True)
            continue
        apply(path, old, new)
        mut = m.run(id_ + "/mut-fixture")
        gt = go_test()
        rest = restore(path, orig[path])
        ca = m.run(id_ + "/clean-after")
        entry["mutated"] = {"fixture_status": mut.get("status"), "fixture_ids": mut.get("n_ids"),
                            "fixture_failures": mut.get("failures")}
        entry["gotest"] = {k: gt.get(k) for k in ("rc", "failed_top_level", "failed_any", "tail")}
        entry["restored_digest_ok"] = rest
        entry["clean_after"] = {k: ca.get(k) for k in ("status", "n_ids")}
        if not rest:
            entry["classification"] = "RESTORE-FAILED"
        elif gt["rc"] != 0:
            entry["classification"] = "guarded by the in-package go test (not by the bound command)"
        elif mut.get("failures"):
            entry["classification"] = "caught by the bound command after all"
        else:
            entry["classification"] = "SURVIVED BOTH ORACLES"
        results.append(entry)
        print("%-8s %-58s gotest_rc=%s failing=%s fx_failures=%d restore=%s" % (
            id_, entry["classification"], gt.get("rc"), gt.get("failed_top_level"),
            len(mut.get("failures") or []), rest), flush=True)
        for f in (ADOPT, CHECK):
            assert hashlib.sha256(open(os.path.join(REPO, f), "rb").read()).hexdigest() == DIGESTS[f]

    with open(os.path.join(REPO, EVDIR, outfile), "wb") as fh:
        fh.write(json.dumps({"reviewer_id": "qoder-desktop:/root/w0801_verifier_r1",
                             "purpose": "corrected mutants of my own + second oracle (in-package go test) "
                                        "for the pass-1 non-caught set",
                             "results": results}, ensure_ascii=False, indent=1).encode("utf-8"))
    for f in (ADOPT, CHECK):
        print("final digest", f,
              hashlib.sha256(open(os.path.join(REPO, f), "rb").read()).hexdigest() == DIGESTS[f])


if __name__ == "__main__":
    main()
