"""Apply only the mutant whose anchor missed, merge its result into the matrix, and recompute the
counts so the file cannot disagree with its own mutant list.

The first pass reported an anchor problem because the CLI validates -repairs together with
-observe-after on one line; the anchor is taken from the file as it actually reads, and the run still
has to leave the tree byte-identical.
"""
import datetime, hashlib, io, json, os, subprocess, time

ROOT = os.getcwd()
V24 = os.path.join(ROOT, "execution", "v2.4")
MATRIX = os.path.join(V24, "receipts", "W05", "W05-02", "mutation_selfcheck_w0502.json")
LOCK = json.load(io.open(os.path.join(ROOT, "execution", "toolchains", "locked.json"), encoding="utf-8-sig"))
GO = LOCK["tools"]["go"]["path"]
PATH = "apps/cli/coding_task.go"
OLD = "\tif *repairs < 0 {"
NEW = "\tif false {"
EXPECT = "the budget row must fail when the CLI stops refusing a negative budget"

m = json.load(io.open(MATRIX, encoding="utf-8-sig"))
text = io.open(os.path.join(ROOT, PATH), encoding="utf-8").read()
if text.count(OLD) != 1:
    raise SystemExit("anchor count in %s is %d, not 1" % (PATH, text.count(OLD)))
digest = hashlib.sha256(text.encode("utf-8")).hexdigest()


def suite():
    env = dict(os.environ)
    env["RESEARCHOS_TASK_ID"] = "W05"
    env["RESEARCHOS_CHECK_ID"] = "W05-02"
    r = subprocess.run([GO, "run", "./tests/runtime/check"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT, env=env, timeout=1800)
    lines = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("{")]
    d = json.loads(lines[-1]) if lines else {}
    ids = sorted(d.get("assertion_ids") or [])
    return {"status": d.get("status"), "ids": ids, "rc": r.returncode,
            "failed": sorted(f.get("id", "?") for f in (d.get("failures") or []))}


baseline = set(m["baseline_ids"])
try:
    io.open(os.path.join(ROOT, PATH), "w", encoding="utf-8", newline="\n").write(text.replace(OLD, NEW, 1))
    got = suite()
finally:
    io.open(os.path.join(ROOT, PATH), "w", encoding="utf-8", newline="\n").write(text)
restored = hashlib.sha256(io.open(os.path.join(ROOT, PATH), encoding="utf-8").read().encode("utf-8")).hexdigest() == digest
lost = sorted(baseline - set(got["ids"]))
killed = got["status"] != "PASS" or bool(lost) or got["rc"] != 0
row = {"mutant": "Q5-negative-budget-accepted", "file": PATH, "expectation": EXPECT,
       "killed": killed, "run_status": got["status"], "run_rc": got["rc"],
       "assertions_reported": len(got["ids"]), "ids_lost": lost, "failed_ids": got["failed"],
       "restored_byte_identical": restored, "note": "re-applied after the first pass reported an anchor problem"}
print("Q5:", "KILLED" if killed else "SURVIVED", got["status"], "lost", len(lost), "failed", got["failed"][:3],
      "| restored byte-identical:", restored)
m["mutants"] = [x for x in m["mutants"] if not (x.get("mutant", "").startswith("Q5"))] + [row]
m["mutants"].sort(key=lambda x: x.get("mutant", ""))
applied = [x for x in m["mutants"] if "killed" in x]
surv = [x for x in applied if not x.get("killed")]
m["counts"] = {"applied": len(applied), "killed": len([x for x in applied if x.get("killed")]),
               "survived": len(surv)}
m["survivors"] = [x["mutant"] for x in surv]
m["survivors_with_stated_reason"] = [x["mutant"] for x in surv if "EXPECTED TO SURVIVE" in x.get("expectation", "")]
m["survivors_without_reason"] = [x for x in m["survivors"] if x not in m["survivors_with_stated_reason"]]
m["recomputed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
m["tree_clean_after_restores"] = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                                                capture_output=True, text=True, cwd=ROOT).stdout.strip() == ""
json.dump(m, io.open(MATRIX, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("counts:", m["counts"], "| survivors:", m["survivors"], "| unexplained:", m["survivors_without_reason"],
      "| tree clean:", m["tree_clean_after_restores"])
