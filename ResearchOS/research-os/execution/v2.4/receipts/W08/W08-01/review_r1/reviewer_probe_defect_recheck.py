#!/usr/bin/env python3
"""Round-1 reviewer, pass 3: the two mid-card defects, measured instead of read.

(a) The seal helper that once rolled back its own transaction. It cannot be mutated cheaply, so it is
    settled by a positive control already in the roster: W0801-RECORD-PROMOTES and
    W0801-PRODUCT-ARTIFACTS-SEALED only pass if a sealed artifact is still readable by a LATER
    transaction, which a rolled-back seal cannot survive. Pass 1 confirmed the two negative record
    assertions also fire on their own guard (R1-M27), so the positives are not resting on the same
    accident the negatives check for.

(b) The probe that once counted "no parsable report" as a refusal. R1-M35 re-creates that input
    exactly: the probe child is made to print no report at all. If the old lenient condition were
    still in place the assertion would go GREEN on this mutant; the delivered condition requires
    status FAIL with an assertion count of exactly 0, so it must go RED. Measured clean -> mutant ->
    restore -> clean, same digest gates as passes 1 and 2.
"""
import hashlib
import importlib.util
import json
import os

REPO = "D:/作品集/ResearchOS/research-os"
spec = importlib.util.spec_from_file_location(
    "m", os.path.join(REPO, "execution/v2.4/receipts/W08/W08-01/review_r1/reviewer_mutation_matrix.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CHECK, DIGESTS = m.CHECK, m.DIGESTS
EVDIR = m.EVDIR

OLD = ('func report(status string) {\n\tout, _ := json.Marshal(')
NEW = ('func report(status string) {\n\tif os.Getenv("W0801_PROBE_CHILD") == "1" {\n\t\treturn\n\t}\n'
       '\tout, _ := json.Marshal(')

orig = open(os.path.join(REPO, CHECK), "rb").read()
assert hashlib.sha256(orig).hexdigest() == DIGESTS[CHECK]
out = {}
cb = m.run("R1-M35/clean-before")
out["clean_before"] = {k: cb.get(k) for k in ("status", "n_ids", "rc", "procs_sample")}
print("clean-before", out["clean_before"], flush=True)
assert cb.get("status") == "PASS" and cb.get("n_ids") == 64

text = orig.decode("utf-8")
assert text.count(OLD) == 1, text.count(OLD)
open(os.path.join(REPO, CHECK), "wb").write(text.replace(OLD, NEW).encode("utf-8"))
mut = m.run("R1-M35/mutated")
open(os.path.join(REPO, CHECK), "wb").write(orig)
rest = hashlib.sha256(open(os.path.join(REPO, CHECK), "rb").read()).hexdigest() == DIGESTS[CHECK]
ca = m.run("R1-M35/clean-after")
out["mutated"] = {k: mut.get(k) for k in ("status", "n_ids", "rc", "procs_sample")}
out["mutated_failures"] = mut.get("failures")
out["restored_digest_ok"] = rest
out["clean_after"] = {k: ca.get(k) for k in ("status", "n_ids", "rc")}
out["classification"] = ("caught" if m.PROBE in (mut.get("failures") or [])
                         else "survived (no-parsable-report still counted as a refusal)")
print("R1-M35", out["classification"], "mut", out["mutated"], "failures", out["mutated_failures"],
      "restore", rest, "after", out["clean_after"], flush=True)
with open(os.path.join(REPO, EVDIR, "probe_defect_recheck_r1.json"), "wb") as fh:
    fh.write(json.dumps({"reviewer_id": "qoder-desktop:/root/w0801_verifier_r1",
                         "mutant": "R1-M35 probe child emits no parsable report",
                         "predicts": "the delivered condition must refuse to read this as a refusal",
                         **out}, ensure_ascii=False, indent=1).encode("utf-8"))
for f in (m.ADOPT, CHECK):
    print("final digest ok:", f,
          hashlib.sha256(open(os.path.join(REPO, f), "rb").read()).hexdigest() == DIGESTS[f])
