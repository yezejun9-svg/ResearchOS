import ast, datetime, hashlib, io, json, os, re, subprocess, sys
ROOT = os.getcwd(); RD = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01")
MAIN = os.path.join(ROOT, "tests", "ui", "check", "main.py")
STAGED = os.path.join(ROOT, ".local", "prepare_w1301_mutants_round3.py")
rec = json.load(io.open(os.path.join(RD, "receipt.json"), encoding="utf-8-sig")); emitted = sorted(set(rec["check_results"]["assertion_ids"]))
base = json.load(io.open(os.path.join(RD, "mutation_selfcheck_w1301.json"), encoding="utf-8-sig"))
prev = sorted({k for r in base["results"] for k in (r.get("killed") or [])})
def run_check():
    p = subprocess.run([sys.executable, MAIN, "--check-id", "W13-01"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
    t = ((p.stdout or "") + (p.stderr or "")).strip(); ln = [l for l in t.splitlines() if l.strip().startswith("{")]
    d = json.loads(ln[-1]) if ln else {}
    return d.get("status"), sorted(d.get("assertion_ids") or []), sorted(f.get("id", "?") for f in (d.get("failures") or []))
# reuse the staged definitions verbatim so nothing is retyped and no marker drifts
src = io.open(STAGED, encoding="utf-8").read()
consts = {}
for m in re.finditer(r"^([A-Z_]+)\s*=\s*(.+?)$", src, re.M):
    try: consts[m.group(1)] = ast.literal_eval(m.group(2))
    except Exception:
        try: consts[m.group(1)] = eval(m.group(2), {"os": os, "REPO": ROOT, "RD": RD, "__file__": STAGED}, consts)
        except Exception: pass
i = src.index("CASES = [")
lit = src[i + len("CASES = "):]
depth = 0
for j, ch in enumerate(lit):
    if ch == "[": depth += 1
    elif ch == "]":
        depth -= 1
        if depth == 0: lit = lit[:j + 1]; break
staged_cases = eval(lit, {"os": os, "__builtins__": {}}, dict(consts))
missing_consts = sorted({c["file"] for c in staged_cases} - {v for v in consts.values() if isinstance(v, str)})
if any(not os.path.isabs(c["file"]) for c in staged_cases):
    print("note: some staged case files are relative and are resolved against the repository root")
want = {"M27", "M28", "M29"}
picked = [c for c in staged_cases if any(c.get("id", "").startswith(w + "-") for w in want)]
print("staged cases parsed:", len(staged_cases), "| picking:", [c["id"] for c in picked])
plan = []
for c in picked:
    path = c["file"] if os.path.isabs(c["file"]) else os.path.join(ROOT, c["file"])
    plan.append((c["id"], path, c["marker"], c["body"], c.get("kills", "")))
L = io.open(MAIN, encoding="utf-8").read().split("\n")
plan.append(("I1-node-hash-mismatch-accepted", MAIN, '    if digest != tools.get("sha256"):', "    if False:", "W1301-TOOLCHAIN-NODE-FROM-LOCKED-TABLE"))
plan.append(("I2-node-version-mismatch-accepted", MAIN, "    if r.returncode != 0 or version != tools.get(\"version_output\"):", "    if False:", "W1301-TOOLCHAIN-NODE-FROM-LOCKED-TABLE"))
out = []
for mid, path, marker, body, kills in plan:
    if not os.path.isfile(path):
        out.append({"id": mid, "bucket": "file-absent"}); print("%-34s file-absent" % mid); continue
    text = io.open(path, encoding="utf-8").read(); orig = text.encode("utf-8"); d0 = hashlib.sha256(orig).hexdigest()
    n = text.count(marker)
    if n != 1:
        out.append({"id": mid, "bucket": "anchor-count-%d" % n, "marker_head": marker[:60]})
        print("%-34s anchor %d" % (mid, n)); continue
    try:
        io.open(path, "w", encoding="utf-8", newline="\n").write(text.replace(marker, body, 1)); st, ids, failed = run_check()
    finally:
        io.open(path, "wb").write(orig)
    alive = "W1301-DRIVER-RAN" in ids
    lost = sorted(set(emitted) - set(ids)); newly = sorted(r for r in lost if r not in prev)
    bucket = "caught-new" if alive and newly else "caught-already-covered" if alive and lost else "crashed" if not alive else "survived"
    out.append({"id": mid, "file": os.path.relpath(path, ROOT).replace(os.sep, "/"), "bucket": bucket, "run_status": st,
                "driver_alive": alive, "stated_target": kills, "rows_lost": lost, "rows_new": newly,
                "restored_byte_identical": hashlib.sha256(open(path, "rb").read()).hexdigest() == d0})
    print("%-34s %-22s alive=%s new=%s lost=%s restored=%s" % (mid, bucket, alive, newly, lost, out[-1]["restored_byte_identical"]))
adj = json.load(io.open(os.path.join(RD, "mutation_addendum_w1301.json"), encoding="utf-8-sig"))
adj["mutants"] = (adj.get("mutants") or []) + out
newc = sorted({r for x in out for r in (x.get("rows_new") or [])})
disp = dict(adj.get("per_row_disposition") or {})
for r in newc:
    who = [x["id"] for x in out if r in (x.get("rows_new") or [])]
    disp[r] = ("killed by filed addendum mutant %s (marker taken verbatim from the staged definition, "
               "transient edit restored byte-identically)" % ", ".join(who))
adj["per_row_disposition"] = disp
adj["rows_newly_discriminated"] = sorted(set(adj.get("rows_newly_discriminated") or []) | set(newc))
adj["rows_still_without_a_mutant"] = sorted(set(emitted) - set(prev) - set(adj["rows_newly_discriminated"]))
adj["disposition_counts"] = {"killed_or_measured": len([k for k, v in disp.items() if not v.startswith(("OWED", "UNCLASSIFIED"))]),
                             "owed": len([k for k, v in disp.items() if v.startswith("OWED")]),
                             "unclassified": len([k for k, v in disp.items() if v.startswith("UNCLASSIFIED")])}
adj["count_reconciliation"]["rows_no_filed_mutant_kills"] = len(adj["rows_still_without_a_mutant"])
adj["pass9"] = {"credited_new": newc, "staged_cases_reused": [c["id"] for c in picked]}
adj["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("pass9 new:", newc, "| counts:", adj["disposition_counts"], "| still no filed mutant:", adj["count_reconciliation"]["rows_no_filed_mutant_kills"])
