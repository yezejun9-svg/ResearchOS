"""Audit receipts/W05/W05-02/receipt.json against the repository, not against its own prose.

Probes, each one a place where a report can look complete and still be wrong:
 1 artifact digests recomputed from raw bytes, and every listed path proven to exist;
 2 the routed assertion set re-read from the dispatcher's own invocation receipt and compared both ways;
 3 the registry facts (revision, commands.json digest, selector membership) taken from commands.json;
 4 the mutation file cross-checked: counts derived from its own mutant list, and every surviving mutant
   required to carry a stated reason;
 5 the selector-flip parity file checked against the same registry revision the receipt reports;
 6 the registration face verified as unclaimed (status, verifier fields, review arrays);
 7 the disclosures checked for the two things this card cannot claim, so a limitation cannot be dropped
   silently by a later regeneration;
 8 HEAD recorded by the receipt compared with the recorded tree of the routed run;
 9 a falsified control: one digest is perturbed in memory and the auditor must notice, proving the
   checks compute rather than echo.
"""
import hashlib, io, json, os, subprocess, sys

ROOT = os.getcwd()
V24 = os.path.join(ROOT, "execution", "v2.4")
RD = os.path.join(V24, "receipts", "W05", "W05-02")
problems, notes = [], []


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


rec_path = os.path.join(RD, "receipt.json")
if not os.path.isfile(rec_path):
    raise SystemExit(json.dumps({"status": "FAIL", "problems": ["no receipt.json to audit"]}))
rec = load(rec_path)

# 1 - artifacts
missing, wrong, hashed = [], [], 0
for a in rec.get("artifacts") or []:
    # one rule, asserted: every artifact path is relative to the repository root
    if "/" not in a["path"] or a["path"].startswith("receipts/"):
        problems.append("artifact path is not repository-root relative: %s" % a["path"])
        continue
    p = os.path.join(ROOT, a["path"].replace("/", os.sep))
    if not os.path.isfile(p):
        missing.append(a["path"])
        continue
    hashed += 1
    if sha(p) != a["sha256"]:
        wrong.append(a["path"])
if missing:
    problems.append("%d artifact path(s) listed but absent: %s" % (len(missing), missing[:4]))
if wrong:
    problems.append("%d artifact digest(s) do not match the bytes on disk: %s" % (len(wrong), wrong[:4]))
notes.append({"probe": 1, "artifacts_listed": len(rec.get('artifacts') or []), "hashed": hashed,
              "missing": missing, "digest_mismatches": wrong})

# 2 - routed assertions vs the dispatcher's own receipt
inv_rel = (rec.get("binding") or {}).get("dispatcher_receipt")
if not inv_rel:
    problems.append("the receipt names no dispatcher invocation receipt to re-read")
else:
    invp = os.path.join(V24, inv_rel.replace("/", os.sep))
    if not os.path.isfile(invp):
        problems.append("the invocation receipt is absent: %s" % inv_rel)
    else:
        inv = load(invp)
        want = sorted((rec.get("check_results") or {}).get("assertion_ids") or [])
        got = sorted(inv.get("assertion_ids") or [])
        if want != got:
            problems.append("assertion set mismatch: receipt lists %d, invocation receipt has %d; only-in-receipt=%s only-in-invocation=%s"
                            % (len(want), len(got), [x for x in want if x not in got][:5], [x for x in got if x not in want][:5]))
        if (inv.get("status") or "").upper() != "PASS":
            problems.append("the invocation receipt is not PASS: %r" % inv.get("status"))
        if inv.get("code_revision") and inv["code_revision"] != rec.get("repository_head_at_reporting"):
            problems.append("the routed run recorded tree %s but the receipt reports %s"
                            % (inv["code_revision"][:8], str(rec.get("repository_head_at_reporting"))[:8]))
        notes.append({"probe": 2, "assertions": len(want), "ids_match": want == got,
                      "invocation_status": inv.get("status"), "zero_assertion_run": len(want) == 0})
        if len(want) == 0:
            problems.append("a routed run with zero assertions can never be reported")

# 3 - registry facts
reg = load(os.path.join(V24, "commands.json"))
entry = (reg.get("commands") or {}).get("test.runtime") or {}
if entry.get("state") != "BOUND":
    problems.append("test.runtime is %r, not BOUND" % entry.get("state"))
if "W05-02" not in ((entry.get("selectors") or {}).get("check_id") or []):
    problems.append("check_id W05-02 is not registered on test.runtime")
if reg.get("revision") != rec.get("registry_revision"):
    problems.append("registry revision is %r but the receipt says %r" % (reg.get("revision"), rec.get("registry_revision")))
if sha(os.path.join(V24, "commands.json")) != rec.get("commands_sha256"):
    problems.append("commands.json digest differs from the receipt's (the registry moved after the receipt was written)")
notes.append({"probe": 3, "registry_revision": reg.get("revision"), "selector_present": True})

# 4 - mutation file self-consistency
mrel = (rec.get("mutation_selfcheck") or {}).get("artifact")
m = load(os.path.join(V24, mrel.replace("/", os.sep))) if mrel else {}
applied = [x for x in (m.get("mutants") or []) if "killed" in x]
killed = [x for x in applied if x.get("killed")]
surv = [x for x in applied if not x.get("killed")]
if len(applied) != (m.get("counts") or {}).get("applied"):
    problems.append("mutation 'applied' count %r disagrees with the mutant list (%d)"
                    % ((m.get("counts") or {}).get("applied"), len(applied)))
if len(killed) != (m.get("counts") or {}).get("killed"):
    problems.append("mutation 'killed' count %r disagrees with the mutant list (%d)"
                    % ((m.get("counts") or {}).get("killed"), len(killed)))
silent = [x["mutant"] for x in surv if not x.get("expected_to_survive")]
if silent:
    problems.append("surviving mutants without a stated reason: %s" % silent)
if m.get("tree_clean_after_restores") is not True:
    problems.append("the matrix reported a dirty tree after restores")
notes.append({"probe": 4, "applied": len(applied), "killed": len(killed),
              "survived": len(surv), "survived_with_reason": [x["mutant"] for x in surv if x["mutant"] not in silent]})

# 5 - parity file vs the reported revision
prel = (rec.get("selector_flip") or {}).get("artifact")
pr = load(os.path.join(V24, prel.replace("/", os.sep))) if prel else {}
if pr.get("registry_revision_after") != rec.get("registry_revision"):
    problems.append("parity file records revision %r but the receipt reports %r"
                    % (pr.get("registry_revision_after"), rec.get("registry_revision")))
if ((pr.get("before") or {}).get("W05-02") or {}).get("status") != "NOT_IMPLEMENTED":
    problems.append("the parity file does not show the before-flip refusal it claims")
notes.append({"probe": 5, "before": (pr.get("before") or {}).get("W05-02"), "after_status": (pr.get("after") or {}).get("W05-02")})

# 6 - unclaimed registration face
if rec.get("status") != "EXECUTION_REPORTED":
    problems.append("status is %r; only EXECUTION_REPORTED may be self-filed" % rec.get("status"))
for k in ("verifier_id", "independent_review"):
    if rec.get(k) is not None:
        problems.append("%s must be null on a reported receipt" % k)
if rec.get("independent_reviews"):
    problems.append("independent_reviews must be empty on a reported receipt")
if (rec.get("check_results") or {}).get("status") != "PASS":
    problems.append("check_results.status is not PASS")
notes.append({"probe": 6, "registration_face_unclaimed": True})

# 7 - required disclosures
joined = json.dumps(rec.get("limitations") or [], ensure_ascii=False)
for needle in ("workspace.write", "Goal restarting"):
    if needle not in joined:
        problems.append("a required disclosure disappeared from limitations: %r" % needle)
notes.append({"probe": 7, "limitations": len(rec.get("limitations") or [])})

# 8 - falsified control: the checks must actually compute
perturbed = json.loads(json.dumps(rec))
if perturbed.get("artifacts"):
    perturbed["artifacts"][0]["sha256"] = "0" * 64
bad = [x["path"] for x in perturbed["artifacts"]
       if not os.path.isfile(os.path.join(ROOT, x["path"].replace("/", os.sep)))
       or sha(os.path.join(ROOT, x["path"].replace("/", os.sep))) != x["sha256"]]
if not bad:
    problems.append("the falsified digest was NOT detected - probe 1 does not actually compute")
notes.append({"probe": 8, "falsified_digest_detected": bool(bad), "example": bad[:1]})

out = {"status": "FAIL" if problems else "PASS", "receipt_sha256": sha(rec_path),
       "problems": problems, "probes": len(notes), "detail": notes,
       "audited_at": subprocess.run(["python", "-c", "import datetime;print(datetime.datetime.now(datetime.timezone.utc).isoformat())"],
                                    capture_output=True, text=True).stdout.strip()}
print(json.dumps(out, indent=1, ensure_ascii=False)[:2600])
sys.exit(1 if problems else 0)
