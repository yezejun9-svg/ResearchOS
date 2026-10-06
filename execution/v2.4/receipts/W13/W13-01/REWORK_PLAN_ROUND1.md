# W13-01 — round 1 verdict REJECT: what I measured and what the rework is

Verdict: `independent_review_round1.json` by `qoder-desktop:/root/w1301_verifier_r1`, verdict REJECT, 3 blocking
issues. The card stays EXECUTION_REPORTED and unregistered: 17 of 71 cards accepted, 0 of 22 parents, 0 of 42
formal cases. All three blockers were reproduced by the executor in this round before anything was written here.
None of them is a claim that the product does not work; all three are defects in my record.

**B1 — toolchain provenance is not what the record says (reproduced).** `tests/ui/check/main.py` never reads
`RESEARCHOS_NODE`, so the `PASS 29` report's `"environment": {"node": "v26.7.0"}` comes from whatever PATH holds,
while the locked table pins node `v24.9.0`. The same class of defect sits on the python side: the receipt
discloses that the forwarded branch resolves python via PATH, but the generator runs `sys.executable`.
Rework: resolve node (and python) from the locked table / `RESEARCHOS_NODE`, following the `RESEARCHOS_GO`
precedent, assert the identity as a named row, correct the disclosure sentence to match the code that really
runs, and re-measure the binding runs at HEAD so the environment rows agree with each other.

**B2 — a disclosure row states a reason the file refutes (reproduced).** `not_verified[1]` claims "main.js still
loads a single status view". `git show 085945dc:apps/desktop/main/main.js` contains
`win.loadFile(path.join(__dirname, 'workbench.html'))` at line 71. The blocked property itself — an installed
launch from the package, Start menu and the U01 first-use gate — is genuinely blocked by
`Windows_desktop_session`; the *reason* was stale, copied from an earlier round's state instead of re-measured
against the current file. This is the standing rule for disclosure rows and this card broke it.

**B3 — the census digests do not verify (reproduced, and it indicts the auditor too).** Recomputing every row's
`stdout_sha256` / `stderr_sha256` from the raw bytes of `execution/invocations/<id>/stdout.txt` and `stderr.txt`
matches 20 of 40 — and the 20 that match are exactly the empty streams. The builder hashed decoded,
newline-normalised text rather than the bytes on disk. Rework: hash `open(p, "rb").read()`, keep the CRLF-vs-LF
difference visible instead of normalising it away, and add a probe to `audit_receipt_w1301.py` that recomputes
those digests. The second half is the more serious finding: the auditor currently exits 0 without ever checking
that field, so a green self-audit proved less than it appeared to, and "0 inconsistencies" was read by me as
stronger than it is.

Also open from the reviewer's reservations: 11 assertion rows have neither a mutant nor a stated reason.

Order of work for the next round, chosen so the weakest link is fixed first:
1. census writer → raw bytes; 2. auditor probe that recomputes those digests, plus a positive control that makes
   the probe fail when a digest is edited; 3. B1 toolchain identity read + named assertion and the corrected
   disclosure sentence; 4. B2 reason re-measured against the file; 5. regenerate the receipt — the card is
   unregistered, so regeneration is legitimate here and needs no erratum, unlike an accepted card — re-run
   `mut_w1301.py` and the three parity shapes at the new HEAD, re-run `.local/pin_audit.py` and
   `.local/test_register_guards_w1301.py`; 6. request round 2 from a fresh identity, and answer the 11
   reservation rows explicitly rather than quietly.
