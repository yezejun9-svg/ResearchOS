import datetime, hashlib, io, json, os, re, subprocess, sys
ROOT = os.getcwd(); RD = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01")
HOST = os.path.join(ROOT, "apps", "desktop", "main", "lib", "host.js")
rec = json.load(io.open(os.path.join(RD, "receipt.json"), encoding="utf-8-sig")); emitted = sorted(set(rec["check_results"]["assertion_ids"]))
base = json.load(io.open(os.path.join(RD, "mutation_selfcheck_w1301.json"), encoding="utf-8-sig"))
prev = sorted({k for r in base["results"] for k in (r.get("killed") or [])})
def run_check():
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "ui", "check", "main.py"), "--check-id", "W13-01"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
    t = ((p.stdout or "") + (p.stderr or "")).strip(); ln = [l for l in t.splitlines() if l.strip().startswith("{")]
    d = json.loads(ln[-1]) if ln else {}
    return d.get("status"), sorted(d.get("assertion_ids") or []), sorted(f.get("id", "?") for f in (d.get("failures") or []))
MUT = [("G1-empty-state-demands-a-terminal", "requires_terminal: false", "requires_terminal: true",
        ["W1301-WORKBENCH-TELLS-NOBODY-TO-USE-A-TERMINAL"]),
       ("G2-existing-project-poses-as-first-run", "return { kind: 'HAS_PROJECTS'", "return { kind: 'FIRST_RUN'",
        ["W1301-EXISTING-PROJECT-SKIPS-EMPTY-STATE"]),
       ("G3-drop-a-first-run-action", "'configure_provider', ", "", ["W1301-FIRST-RUN-METHODS-ALL-ROUTED", "W1301-EXISTING-PROJECT-SKIPS-EMPTY-STATE"])]
out = []
for mid, old, new, targets in MUT:
    text = io.open(HOST, encoding="utf-8").read(); orig = text.encode("utf-8"); d0 = hashlib.sha256(orig).hexdigest()
    n = text.count(old)
    if n < 1:
        out.append({"id": mid, "bucket": "anchor-missing", "occurrences": n}); print("%-40s anchor-missing" % mid); continue
    mutated = text.replace(old, new, 1)
    try:
        io.open(HOST, "w", encoding="utf-8", newline="\n").write(mutated); st, ids, failed = run_check()
    finally:
        open(HOST, "wb").write(orig)
    alive = "W1301-DRIVER-RAN" in ids
    lost = sorted(set(emitted) - set(ids)); newly = sorted(r for r in lost if r not in prev)
    hit = sorted(set(targets) & set(lost))
    bucket = "caught-new" if alive and newly else "caught-already-covered" if alive and lost else "crashed" if not alive else "survived"
    out.append({"id": mid, "file": "apps/desktop/main/lib/host.js", "bucket": bucket, "run_status": st,
                "driver_alive": alive, "targets": targets, "rows_lost": lost, "rows_failed": failed,
                "rows_new": newly, "targets_hit": hit, "occurrences": n,
                "restored_byte_identical": hashlib.sha256(open(HOST, "rb").read()).hexdigest() == d0})
    print("%-40s %-22s alive=%s new=%s lost=%s restored=%s" % (mid, bucket, alive, newly, lost, out[-1]["restored_byte_identical"]))
adj = json.load(io.open(os.path.join(RD, "mutation_addendum_w1301.json"), encoding="utf-8-sig"))
adj["mutants"] = (adj.get("mutants") or []) + out
newc = sorted({r for x in out for r in (x.get("rows_new") or [])})
disp = dict(adj.get("per_row_disposition") or {})
for r in newc:
    who = [x["id"] for x in out if r in (x.get("rows_new") or [])]
    disp[r] = "killed by filed addendum mutant %s (host.js %s; driver alive; file restored byte-identically)" % (", ".join(who), "empty-state behaviour")
adj["per_row_disposition"] = disp
adj["rows_newly_discriminated"] = sorted(set(adj.get("rows_newly_discriminated") or []) | set(newc))
adj["rows_still_without_a_mutant"] = sorted(set(emitted) - set(prev) - set(adj["rows_newly_discriminated"]))
adj["disposition_counts"] = {"killed_or_measured": len([k for k, v in disp.items() if not v.startswith(("OWED", "UNCLASSIFIED"))]),
                             "owed": len([k for k, v in disp.items() if v.startswith("OWED")]),
                             "unclassified": len([k for k, v in disp.items() if v.startswith("UNCLASSIFIED")])}
adj["bucket_rule_fixed"] = ("buckets are now caught-new / caught-already-covered / crashed / survived, decided on the "
                            "full lost set rather than only on rows never killed before, so a mutant that fails only "
                            "already-covered rows can no longer be printed as survived")
adj["pass7"] = {"credited_new": newc, "caught_already_covered": [x["id"] for x in out if x.get("bucket") == "caught-already-covered"]}
adj["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("pass7 new:", newc, "| counts:", adj["disposition_counts"], "| owed:", len(adj["rows_still_without_a_mutant"]))
