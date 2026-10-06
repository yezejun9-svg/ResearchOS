"""Second pass over the W09-01 survivors: is a surviving leg unasserted BY THIS CARD, or
unasserted by the repository entirely?

For each surviving single-leg mutant, the whole `./internal/domain` package test suite is run
(without the -run filter). If some other accepted test catches the mutant, the leg is covered
elsewhere and this card's silence is not a hole; if the whole package still passes, the leg is
unasserted anywhere in the build.

Same discipline as the primary battery: one leg, exact-once anchor, go build must succeed,
digest captured before and byte-verified after.
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path("D:/作品集/ResearchOS/research-os").resolve()
GO = str(ROOT / ".local/tools/go1.27.1/go/bin/go.exe")
OUT = ROOT / "execution/v2.4/receipts/W09/W09-01/verifier_survivor_scope_r1.json"

sys.path.insert(0, str(ROOT / "execution/v2.4/receipts/W09/W09-01"))
drv = (ROOT / "execution/v2.4/receipts/W09/W09-01/verifier_mutation_r1.py").read_text(encoding="utf-8")
NS = {"__name__": "__driver__"}
exec(drv.split("print(\"baselines:\", json.dumps(BASELINES, indent=1))")[0], NS)
MUTANTS = NS["MUTANTS"]
sha, BASELINES = NS["sha"], NS["BASELINES"]
env_base = NS["env_base"]
TOUCHED = sorted({rel for m in MUTANTS for rel, _, _ in m["edits"]})
BASE = {rel: sha(ROOT / rel) for rel in TOUCHED}

SURVIVORS = ["O02", "O04", "O06", "O07", "O08", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09",
             "L01", "L02", "A01", "A02", "A03"]

rows = []
for m in MUTANTS:
    if not any(m["name"].startswith(s + "-") for s in SURVIVORS):
        continue
    rels = sorted({rel for rel, _, _ in m["edits"]})
    originals = {rel: (ROOT / rel).read_bytes() for rel in rels}
    row = {"mutant": m["name"], "files": rels,
           "digests_before": {rel: hashlib.sha256(originals[rel]).hexdigest() for rel in rels}}
    mutated, bad = dict(originals), []
    for rel, o, nw in m["edits"]:
        raw = mutated[rel]
        crlf = b"\r\n" in raw
        ob = o.replace("\n", "\r\n").encode("utf-8") if crlf else o.encode("utf-8")
        nb = nw.replace("\n", "\r\n").encode("utf-8") if crlf else nw.encode("utf-8")
        if raw.count(ob) != 1:
            bad.append([rel, o[:60], raw.count(ob)])
        else:
            mutated[rel] = raw.replace(ob, nb, 1)
    if bad:
        row.update(classification="anchor-missing", anchor_problems=bad)
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("mutant", "classification")}))
        continue
    for rel in rels:
        (ROOT / rel).write_bytes(mutated[rel])
    try:
        b = subprocess.run([GO, "build", "./internal/domain", "./adapters/retrieval"], cwd=str(ROOT),
                           env=env_base(), capture_output=True, timeout=300)
        if b.returncode != 0:
            row["classification"] = "crashed"
            row["build_error"] = b.stderr.decode("utf-8", "replace")[-400:]
        else:
            t0 = time.time()
            try:
                c = subprocess.run([GO, "test", "-count=1", "-timeout", "900s", "./internal/domain"],
                                   cwd=str(ROOT), env=env_base(), capture_output=True, timeout=1200)
                out = (c.stdout + c.stderr).decode("utf-8", "replace")
                row["full_suite_rc"] = c.returncode
                row["seconds"] = round(time.time() - t0, 1)
                row["failing_tests"] = sorted({ln.split("--- FAIL: ")[1].split(" ")[0]
                                               for ln in out.splitlines() if "--- FAIL: " in ln})
                row["output_tail"] = out[-500:]
                row["classification"] = ("caught_by_another_test_in_the_package"
                                         if c.returncode != 0 else "unasserted_anywhere_in_the_build")
            except subprocess.TimeoutExpired:
                row["classification"] = "full-suite-timeout"
    finally:
        for rel in rels:
            (ROOT / rel).write_bytes(originals[rel])
        row["restored_verified"] = all(sha(ROOT / rel) == row["digests_before"][rel] for rel in rels)
    rows.append(row)
    print(json.dumps({k: row.get(k) for k in ("mutant", "classification", "restored_verified")}))

FINAL = {rel: sha(ROOT / rel) for rel in TOUCHED}
report = {"verifier_id": "qoder-desktop:/root/w0901_verifier_r1", "step_id": "W09-01",
          "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
          "question": "does a leg that survives this card's 41-assertion roster survive the whole package too?",
          "baselines": BASE, "final": FINAL, "all_restored_identical": BASE == FINAL,
          "summary": {c: sum(1 for r in rows if r["classification"] == c) for c in
                      ("caught_by_another_test_in_the_package", "unasserted_anywhere_in_the_build",
                       "crashed", "anchor-missing", "full-suite-timeout")},
          "rows": rows}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"summary": report["summary"], "all_restored_identical": report["all_restored_identical"]}))
