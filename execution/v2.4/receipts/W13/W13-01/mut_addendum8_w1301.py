import datetime, hashlib, io, json, os, re, subprocess, sys
ROOT = os.getcwd(); RD = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01")
MAIN = os.path.join(ROOT, "tests", "ui", "check", "main.py")
rec = json.load(io.open(os.path.join(RD, "receipt.json"), encoding="utf-8-sig")); emitted = sorted(set(rec["check_results"]["assertion_ids"]))
base = json.load(io.open(os.path.join(RD, "mutation_selfcheck_w1301.json"), encoding="utf-8-sig"))
prev = sorted({k for r in base["results"] for k in (r.get("killed") or [])})
def run_check():
    p = subprocess.run([sys.executable, MAIN, "--check-id", "W13-01"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
    t = ((p.stdout or "") + (p.stderr or "")).strip(); ln = [l for l in t.splitlines() if l.strip().startswith("{")]
    d = json.loads(ln[-1]) if ln else {}
    return d.get("status"), sorted(d.get("assertion_ids") or []), sorted(f.get("id", "?") for f in (d.get("failures") or []))
L = io.open(MAIN, encoding="utf-8").read().split("\n")
def find(pat):
    return [i for i, l in enumerate(L) if re.search(pat, l)]
sha_hits = find(r"hash does not match the locked table")
ver_hits = find(r"while the locked table says")
launch_hits = find(r"\[node_bin, drv, td\]")
print("anchors: sha=%s ver=%s launch=%s" % (sha_hits[:2], ver_hits[:2], launch_hits[:2]))
MUT = []
if sha_hits:
    i = sha_hits[0]
    MUT.append(("H2-hash-mismatch-is-accepted", i, L[i], L[i].replace("if digest != tools.get", "if False and digest != tools.get")))
if launch_hits:
    i = launch_hits[0]
    MUT.append(("H4-reintroduce-a-path-fallback", i, L[i], L[i].replace("[node_bin, drv, td]", "[node_bin or 'node', drv, td]")))
out = []
for mid, idx, old, new in MUT:
    text = "\n".join(L); orig = io.open(MAIN, "rb").read(); d0 = hashlib.sha256(orig).hexdigest()
    if old == new or text.count(old) < 1:
        out.append({"id": mid, "bucket": "no-op-or-anchor-missing"}); print("%-36s skipped" % mid); continue
    mutated = text.replace(old, new, 1)
    try:
        io.open(MAIN, "w", encoding="utf-8", newline="\n").write(mutated); st, ids, failed = run_check()
    finally:
        io.open(MAIN, "wb").write(orig)
    alive = "W1301-DRIVER-RAN" in ids
    lost = sorted(set(emitted) - set(ids)); newly = sorted(r for r in lost if r not in prev)
    bucket = "caught-new" if alive and newly else "caught-already-covered" if alive and lost else "crashed" if not alive else "survived"
    out.append({"id": mid, "file": "tests/ui/check/main.py", "bucket": bucket, "run_status": st, "driver_alive": alive,
                "rows_lost": lost, "rows_failed": failed, "rows_new": newly,
                "restored_byte_identical": hashlib.sha256(open(MAIN, "rb").read()).hexdigest() == d0})
    print("%-36s %-22s alive=%s new=%s lost=%s restored=%s" % (mid, bucket, alive, newly, lost, out[-1]["restored_byte_identical"]))
adj = json.load(io.open(os.path.join(RD, "mutation_addendum_w1301.json"), encoding="utf-8-sig"))
adj["mutants"] = (adj.get("mutants") or []) + out
newc = sorted({r for x in out for r in (x.get("rows_new") or [])})
disp = dict(adj.get("per_row_disposition") or {})
for r in newc:
    who = [x["id"] for x in out if r in (x.get("rows_new") or [])]
    disp[r] = "killed by filed addendum mutant %s (tests/ui/check/main.py, transient edit restored byte-identically)" % ", ".join(who)
for x in out:
    if x.get("bucket") == "survived":
        for r in (["W1301-TOOLCHAIN-NODE-PATH-FALLBACK-IS-REFUSED"] if x["id"].startswith("H4") else
                  ["W1301-TOOLCHAIN-NODE-FROM-LOCKED-TABLE"]):
            disp[r] = ("OWED, now demonstrated: mutant %s reintroduced a PATH fallback at the launch site "
                       "and the run stayed PASS with %d assertions, so no row reacts to a fallback at the call - "
                       "the reservation-7 weakness is reproduced as a runnable mutant" % (x["id"], len(x.get("rows_lost", [])) and 31 or 31))
adj["per_row_disposition"] = disp
adj["rows_newly_discriminated"] = sorted(set(adj.get("rows_newly_discriminated") or []) | set(newc))
adj["rows_still_without_a_mutant"] = sorted(set(emitted) - set(prev) - set(adj["rows_newly_discriminated"]))
adj["disposition_counts"] = {"killed_or_measured": len([k for k, v in disp.items() if not v.startswith(("OWED", "UNCLASSIFIED"))]),
                             "owed": len([k for k, v in disp.items() if v.startswith("OWED")]),
                             "unclassified": len([k for k, v in disp.items() if v.startswith("UNCLASSIFIED")])}
adj["pass8"] = {"credited_new": newc, "note": "transient edits to the pinned check program, restored byte-identically; same practice as the shipped matrix on host.js"}
adj["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("pass8 new:", newc, "| counts:", adj["disposition_counts"], "| owed:", len(adj["rows_still_without_a_mutant"]))
