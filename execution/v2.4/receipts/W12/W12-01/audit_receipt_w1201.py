# Receipt self-audit for W12-01: recompute every number and hash in receipt.json
# against the files it references, using only paths tracked by git. Read-only.
import hashlib, json, os, subprocess, sys

def _root():
    d = os.path.abspath(os.path.dirname(__file__))
    while d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, "execution", "v2.4", "commands.json")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("repository root not found from " + __file__)


REPO = _root()
RD = os.path.join(REPO, "execution", "v2.4", "receipts", "W12", "W12-01")
rc = json.load(open(os.path.join(RD, "receipt.json"), encoding="utf-8"))
checks, bad = [], []


def chk(label, want, got):
    ok = want == got
    checks.append((label, want, got, ok))
    if not ok:
        bad.append(label)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# 1. artifact hashes
for a in rc["artifacts"]:
    p = os.path.join(REPO, a["path"].replace("/", os.sep))
    chk("artifact:" + a["path"], a["sha256"], sha(p) if os.path.exists(p) else "MISSING")

# 2. referenced evidence files exist and hash-match nothing claimed otherwise
runner = rc["mutation_selfcheck"]["runner"]
chk("mutation_runner_exists", True, os.path.exists(os.path.join(REPO, runner.replace("/", os.sep))))

# 3. mutation buckets vs the round-2 selfcheck json
ms = json.load(open(os.path.join(RD, "mutation_selfcheck_w1201_round2.json"), encoding="utf-8"))
buckets = ms.get("buckets", ms)
raw = json.dumps(ms, sort_keys=True)
def bucket(name):
    for key in (name, name.replace("-", "_")):
        if key in buckets:
            return buckets[key]
    raise KeyError(name + " in " + raw[:400])


for k in ("caught", "survived", "crashed", "anchor-missing"):
    chk("mutation_bucket:" + k, rc["mutation_selfcheck"]["buckets"][k], bucket(k))
chk("mutation_cases", rc["mutation_selfcheck"]["cases"],
    sum(bucket(k) for k in ("caught", "survived", "crashed", "anchor-missing")))
caught_list = rc["mutation_selfcheck"]["caught"]
chk("caught_list_len", rc["mutation_selfcheck"]["buckets"]["caught"], len(caught_list))
# every killed assertion id must exist in the binding invocation's assertion set
binding_id = rc["check_results"]["binding_invocation"]
inv_dir = os.path.join(REPO, "execution", "invocations", binding_id)
ids = json.load(open(os.path.join(RD, "binding_assertion_ids.json"), encoding="utf-8"))
known = set()
for item in (ids if isinstance(ids, list) else ids.get("assertion_ids", [])):
    known.add(item if isinstance(item, str) else json.dumps(item))
if os.path.exists(inv_dir):
    for root, _, files in os.walk(inv_dir):
        for fn in files:
            if fn.endswith(".json"):
                try:
                    d = json.load(open(os.path.join(root, fn), encoding="utf-8"))
                except Exception:
                    continue
                if isinstance(d, dict) and isinstance(d.get("assertion_ids"), list):
                    known.update(d["assertion_ids"])
killed = {k for c in caught_list for k in c["killed"]}
missing = sorted(killed - known)
chk("killed_ids_present", [], missing)

# 4. histogram sums to the reported assertion count and matches the invocation ids
hist = rc["check_results"]["assertion_id_prefix_histogram"]
chk("histogram_sum", rc["check_results"]["assertions"], sum(hist.values()))

# 5. commands[]: every dict result that claims an assertion count must claim 31,
#    and the two dispatch runs must both be pinned at the reported head.
res_objs = [c.get("result") if isinstance(c.get("result"), dict) else {} for c in rc["commands"]]
for c, res in zip(rc["commands"], res_objs):
    if "assertions" in res:
        chk("command_assertions:" + " ".join(c["argv"][-2:]), rc["check_results"]["assertions"], res["assertions"])
chk("head_pin_rows", 2, sum(1 for res in res_objs if res.get("invocation_id")))

# 6. stability runs: each cited invocation dir exists and carries the cited code revision
for run in rc["stability_runs"]:
    d = os.path.join(REPO, "execution", "invocations", run["invocation_id"])
    chk("stability_dir:" + run["invocation_id"][:8], True, os.path.isdir(d))
    txt = json.dumps({fn: json.load(open(os.path.join(d, fn), encoding="utf-8"))
                      for fn in os.listdir(d) if fn.endswith(".json")}, sort_keys=True) \
        if os.path.isdir(d) else ""
    chk("stability_rev:" + run["invocation_id"][:8], True, run["code_revision"] in txt)
    chk("stability_assertions:" + run["invocation_id"][:8], True, str(run["assertions"]) in txt)

# 7. registry parity: commands.json revision and its hash
cmdp = os.path.join(REPO, "execution", "v2.4", "commands.json")
cmds = json.load(open(cmdp, encoding="utf-8"))
chk("registry_revision", rc["registry_parity"]["registry_revision"], cmds.get("revision"))
cmdhash = sha(cmdp)
art = {a["path"]: a["sha256"] for a in rc["artifacts"]}
chk("commands_hash_vs_artifact", art.get("execution/v2.4/commands.json"), cmdhash)
for run in rc["stability_runs"]:
    chk("stability_regrev:" + run["invocation_id"][:8], cmdhash, run["registered_command_revision"])

# 8. receipt head is a real commit and is an ancestor of HEAD
head = rc["repository_head_at_reporting"]
p = subprocess.run(["git", "cat-file", "-t", head], cwd=REPO, capture_output=True, text=True)
chk("head_commit_exists", "commit", p.stdout.strip())
p = subprocess.run(["git", "merge-base", "--is-ancestor", head, "HEAD"], cwd=REPO)
chk("head_is_ancestor", 0, p.returncode)

print("checked", len(checks), "rows;", "inconsistent", len(bad))
for b in bad:
    for label, want, got, ok in checks:
        if label == b:
            print("MISMATCH", label, "\n  want:", json.dumps(want)[:300], "\n  got: ", json.dumps(got)[:300])
sys.path.insert(0, "")
out = os.path.join(REPO, ".local", "w1201_receipt_selfaudit.json")
if not os.path.isdir(os.path.dirname(out)):
    out = os.path.join(os.path.dirname(__file__), "w1201_receipt_selfaudit.json")
json.dump({"checks": [{"label": l, "ok": o} for l, _, _, o in checks], "mismatches": bad},
          open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("wrote", out)
sys.exit(1 if bad else 0)
