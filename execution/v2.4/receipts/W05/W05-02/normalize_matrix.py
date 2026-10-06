import datetime, hashlib, io, json, os, subprocess
ROOT = os.getcwd(); V24 = os.path.join(ROOT, "execution", "v2.4")
P = os.path.join(V24, "receipts", "W05", "W05-02", "mutation_selfcheck_w0502.json")
m = json.load(io.open(P, encoding="utf-8-sig"))
rows = []
for x in m["mutants"]:
    if x.get("mutant") == "control-clean-run":
        x = {k: v for k, v in x.items() if k != "killed"}
        x["role"] = "control, not a mutant"
    rows.append(x)
applied = [x for x in rows if "killed" in x]
surv = [x for x in applied if x["killed"] is False]
m["mutants"] = sorted(rows, key=lambda y: y.get("mutant", ""))
m["counts"] = {"applied": len(applied), "killed": len([x for x in applied if x["killed"] is True]),
               "survived": len(surv)}
m["survivors"] = [x["mutant"] for x in surv]
m["survivors_with_stated_reason"] = [x["mutant"] for x in surv if "EXPECTED TO SURVIVE" in x.get("expectation", "")]
m["survivors_without_reason"] = [x for x in m["survivors"] if x not in m["survivors_with_stated_reason"]]
m["normalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(m, io.open(P, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
print("counts", m["counts"], "| survivors", m["survivors"], "| unexplained", m["survivors_without_reason"])
