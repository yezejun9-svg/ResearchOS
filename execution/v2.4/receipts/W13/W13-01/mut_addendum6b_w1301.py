import datetime, hashlib, io, json, os, subprocess, sys
ROOT = os.getcwd(); RD = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01")
HOST = os.path.join(ROOT, "apps", "desktop", "main", "lib", "host.js")
rec = json.load(io.open(os.path.join(RD, "receipt.json"), encoding="utf-8-sig")); emitted = sorted(set(rec["check_results"]["assertion_ids"]))
base = json.load(io.open(os.path.join(RD, "mutation_selfcheck_w1301.json"), encoding="utf-8-sig"))
prev = sorted({k for r in base["results"] for k in (r.get("killed") or [])})
OLD = "if (st === 'OK' && result.degraded === true) return { ok: false, reason: 'DEGRADED_NOT_SUCCESS' };"
NEW = OLD.replace("ok: false", "ok: true")
text = io.open(HOST, encoding="utf-8").read(); orig = text.encode("utf-8")
assert text.count(OLD) == 1
io.open(HOST, "w", encoding="utf-8", newline="\n").write(text.replace(OLD, NEW, 1))
try:
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "ui", "check", "main.py"), "--check-id", "W13-01"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
finally:
    open(HOST, "wb").write(orig)
t = ((p.stdout or "") + (p.stderr or "")).strip(); ln = [l for l in t.splitlines() if l.strip().startswith("{")]
d = json.loads(ln[-1]) if ln else {}; ids = sorted(d.get("assertion_ids") or [])
lost = sorted(set(emitted) - set(ids)); failed = sorted(f.get("id", "?") for f in (d.get("failures") or []))
adj = json.load(io.open(os.path.join(RD, "mutation_addendum_w1301.json"), encoding="utf-8-sig"))
for x in adj["mutants"]:
    if x.get("id") == "F6-degraded-becomes-success":
        x["re_measured"] = {"run_status": d.get("status"), "driver_alive": "W1301-DRIVER-RAN" in ids,
                            "rows_lost": lost, "rows_failed": failed,
                            "all_lost_already_covered": bool(lost) and all(r in prev for r in lost),
                            "classification_fix": ("earlier bucket compared only rows not already covered, so a mutant that "
                                                   "failed only already-covered rows was mislabelled survived; this run records "
                                                   "the full lost/failed sets so the distinction is visible")}
        if lost or failed: x["bucket"] = "caught"
adj["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("F6 re-measured: status=%s lost=%s failed=%s restored=%s" % (d.get("status"), lost, failed[:3], hashlib.sha256(open(HOST,"rb").read()).hexdigest()==hashlib.sha256(orig).hexdigest()))
print("counts:", adj["disposition_counts"], "| owed rows:", len(adj["rows_still_without_a_mutant"]))
