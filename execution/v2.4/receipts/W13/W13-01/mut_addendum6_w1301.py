import datetime, hashlib, io, json, os, subprocess, sys
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
    return d.get("status"), sorted(d.get("assertion_ids") or (d.get("checks") or {}).get("assertion_ids") or [])
MUT = [
 ("F1-auth-required-becomes-success", "if (st === 'AUTH_REQUIRED') return { ok: false, reason: 'AUTH_REQUIRED' };",
  "if (st === 'AUTH_REQUIRED') return { ok: true, reason: 'AUTH_REQUIRED' };", ["W1301-AUTH-RATELIMIT-UNSUPPORTED-ARE-FAILURES"]),
 ("F2-rate-limited-becomes-success", "if (st === 'RATE_LIMITED') return { ok: false, reason: 'RATE_LIMITED' };",
  "if (st === 'RATE_LIMITED') return { ok: true, reason: 'RATE_LIMITED' };", ["W1301-AUTH-RATELIMIT-UNSUPPORTED-ARE-FAILURES"]),
 ("F3-unsupported-becomes-success", "if (st === 'UNSUPPORTED') return { ok: false, reason: 'UNSUPPORTED_MODEL' };",
  "if (st === 'UNSUPPORTED') return { ok: true, reason: 'UNSUPPORTED_MODEL' };", ["W1301-AUTH-RATELIMIT-UNSUPPORTED-ARE-FAILURES"]),
 ("F4-no-reply-becomes-success", "if (!result || typeof result !== 'object') return { ok: false, reason: 'NO_REPLY' };",
  "if (!result || typeof result !== 'object') return { ok: true, reason: 'NO_REPLY' };", ["W1301-TRANSPORT-AND-SILENCE-ARE-FAILURES"]),
 ("F5-transport-error-becomes-success", "if (result.error) return { ok: false, reason: 'TRANSPORT', detail: String(result.error) };",
  "if (result.error) return { ok: true, reason: 'TRANSPORT', detail: String(result.error) };", ["W1301-TRANSPORT-AND-SILENCE-ARE-FAILURES"]),
 ("F6-degraded-becomes-success", "if (st === 'OK' && result.degraded === true) return { ok: false, reason: 'DEGRADED_NOT_SUCCESS' };",
  "if (st === 'OK' && result.degraded === true) return { ok: true, reason: 'DEGRADED_NOT_SUCCESS' };", ["W1301-PROVIDER-OK-IS-SUCCESS"]),
]
out = []
for mid, old, new, targets in MUT:
    text = io.open(HOST, encoding="utf-8").read(); orig = text.encode("utf-8"); d0 = hashlib.sha256(orig).hexdigest()
    if text.count(old) != 1:
        out.append({"id": mid, "bucket": "anchor-count-%d" % text.count(old)}); print("%-38s anchor %d" % (mid, text.count(old))); continue
    try:
        io.open(HOST, "w", encoding="utf-8", newline="\n").write(text.replace(old, new, 1)); st, ids = run_check()
    finally:
        open(HOST, "wb").write(orig)
    alive = "W1301-DRIVER-RAN" in ids; lost = sorted(set(emitted) - set(ids))
    cred = sorted(r for r in lost if r not in prev) if alive else []
    hit = sorted(set(targets) & set(cred))
    bucket = "caught" if hit else ("crashed" if not alive else ("partly" if cred else "survived"))
    out.append({"id": mid, "file": "apps/desktop/main/lib/host.js", "bucket": bucket, "run_status": st, "driver_alive": alive,
                "targets": targets, "rows_lost_while_driver_alive": cred, "targets_hit": hit,
                "restored_byte_identical": hashlib.sha256(open(HOST, "rb").read()).hexdigest() == d0})
    print("%-38s %-8s alive=%s credited=%s" % (mid, bucket, alive, cred))
adj = json.load(io.open(os.path.join(RD, "mutation_addendum_w1301.json"), encoding="utf-8-sig"))
newc = sorted({r for x in out for r in (x.get("rows_lost_while_driver_alive") or [])})
disp = dict(adj.get("per_row_disposition") or {})
for r in newc:
    who = [x["id"] for x in out if r in (x.get("rows_lost_while_driver_alive") or [])]
    disp[r] = ("killed by filed addendum mutants %s (provider failure branches answering ok:true; driver alive; "
               "host.js restored byte-identically)" % ", ".join(who))
adj["mutants"] = (adj.get("mutants") or []) + out
adj["per_row_disposition"] = disp
adj["rows_newly_discriminated"] = sorted(set(adj.get("rows_newly_discriminated") or []) | set(newc))
adj["rows_still_without_a_mutant"] = sorted(set(emitted) - set(prev) - set(adj["rows_newly_discriminated"]))
adj["disposition_counts"] = {"killed_or_measured": len([k for k, v in disp.items() if not v.startswith(("OWED", "UNCLASSIFIED"))]),
                             "owed": len([k for k, v in disp.items() if v.startswith("OWED")]),
                             "unclassified": len([k for k, v in disp.items() if v.startswith("UNCLASSIFIED")])}
adj["pass6"] = {"credited": newc, "survived": [x["id"] for x in out if x.get("bucket") == "survived"]}
adj["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("pass6 credited:", newc, "| counts:", adj["disposition_counts"], "| survivors:", adj["pass6"]["survived"])
