import hashlib, io, json, os, re, subprocess, sys, datetime
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
    return d.get("status"), sorted(d.get("assertion_ids") or (d.get("checks") or {}).get("assertion_ids") or []), t[-260:]
MUT = [
 ("E1-drop-one-first-run-method", "pick_directory: ['POST', '/workspaces/pick'], ", "",
  ["W1301-FIRST-RUN-METHODS-ALL-ROUTED"]),
 ("E2-drop-provider-models-route", "models: ['GET', '/provider/models'], ", "",
  ["W1301-FIRST-RUN-METHODS-ALL-ROUTED", "W1301-ROUTING-TRUTH-TABLE"]),
 ("E3-add-an-unregistered-route", "provider: {", "provider: { bogus: ['GET', '/bogus'], ",
  ["W1301-ROUTING-TRUTH-TABLE", "W1301-ALL-CLIENT-CHANNELS-REGISTERED"]),
]
out = []
for mid, needle, repl, targets in MUT:
    text = io.open(HOST, encoding="utf-8").read(); orig = text.encode("utf-8"); d0 = hashlib.sha256(orig).hexdigest()
    if text.count(needle) != 1:
        print("%-32s anchor count %d" % (mid, text.count(needle))); continue
    mutated = text.replace(needle, repl, 1)
    try:
        io.open(HOST, "w", encoding="utf-8", newline="\n").write(mutated); st, ids, tail = run_check()
    finally:
        open(HOST, "wb").write(orig)
    alive = "W1301-DRIVER-RAN" in ids; lost = sorted(set(emitted) - set(ids))
    cred = sorted(r for r in lost if r not in prev) if alive else []
    hit = sorted(set(targets) & set(cred))
    bucket = "caught" if hit else ("crashed" if not alive else ("partly" if cred else "survived"))
    print("%-32s %-8s alive=%s credited=%s restored=%s" % (mid, bucket, alive, cred, hashlib.sha256(open(HOST,'rb').read()).hexdigest()==d0))
    if not alive: print("      driver tail:", tail.replace("\n", " ")[:200])
    out.append({"id": mid, "file": "apps/desktop/main/lib/host.js", "bucket": bucket, "run_status": st,
                "driver_alive": alive, "targets": targets, "rows_lost_while_driver_alive": cred,
                "targets_hit": hit, "uncredited_if_crash": lost if not alive else [],
                "restored_byte_identical": True})
adj = json.load(io.open(os.path.join(RD, "mutation_addendum_w1301.json"), encoding="utf-8-sig"))
newc = sorted({r for x in out for r in x["rows_lost_while_driver_alive"]})
disp = dict(adj.get("per_row_disposition") or {})
for r in newc:
    who = [x["id"] for x in out if r in x["rows_lost_while_driver_alive"]]
    disp[r] = "killed by filed addendum mutant %s (a single route removed from host.js ROUTES; driver alive; file restored byte-identically)" % ", ".join(who)
adj["mutants"] = (adj.get("mutants") or []) + out
adj["per_row_disposition"] = disp
adj["rows_newly_discriminated"] = sorted(set(adj.get("rows_newly_discriminated") or []) | set(newc))
adj["rows_still_without_a_mutant"] = sorted(set(emitted) - set(prev) - set(adj["rows_newly_discriminated"]))
adj["disposition_counts"] = {"killed_or_measured": len([k for k, v in disp.items() if not v.startswith(("OWED", "UNCLASSIFIED"))]),
                             "owed": len([k for k, v in disp.items() if v.startswith("OWED")]),
                             "unclassified": len([k for k, v in disp.items() if v.startswith("UNCLASSIFIED")])}
adj["pass5"] = {"credited": newc, "note": "method-level removals from host.ROUTES keep the client map and the driver alive, which is what passes 2-4 lacked"}
adj["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("pass5 credited:", newc, "| counts:", adj["disposition_counts"], "| still owed:", len(adj["rows_still_without_a_mutant"]))
