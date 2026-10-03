"""Self-audit of execution/v2.4/receipts/W13/W13-01/receipt.json against the files it cites.

Read-only. Every check recomputes from disk; a green run here proves the receipt is internally
consistent with its sources, not that the product works - an independent identity must still re-run
the binding command and the matrix. Aborts nothing: it collects inconsistencies and prints them.
"""
import glob, hashlib, io, json, os, re, subprocess, sys

NL = chr(10)


def _find_repo(start):
    d = start
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal", "domain")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
RD = os.path.join("execution", "v2.4", "receipts", "W13", "W13-01")


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


R = load(os.path.join(RD, "receipt.json"))
bad = []


def chk(cond, msg):
    if not cond:
        bad.append(msg)


# 1 - it is a report, not an acceptance
chk(R["verifier_id"] is None, "verifier_id is filled by the executor")
chk(R["status"] == "EXECUTION_REPORTED", "status is %s, not a report" % R["status"])
chk(R["independent_review"] in (None, {}) and not R["independent_reviews"], "an executor receipt carries a review")

# 2 - every artifact hash recomputes
for a in R["artifacts"]:
    chk(os.path.exists(a["path"]), "artifact path absent: %s" % a["path"])
    if os.path.exists(a["path"]):
        chk(sha(a["path"]) == a["sha256"], "artifact hash drifts: %s" % a["path"])

# 3 - the header still describes the tree it was written against
head_full = os.popen("git rev-parse HEAD").read().strip()
head = head_full[:8]
chk(R["repository_head_at_reporting"] in (head, head_full) or 0 == subprocess.call(
    ["git", "merge-base", "--is-ancestor", R["repository_head_at_reporting"], head]),
    "the tree the receipt describes is not an ancestor of the live HEAD")
tracked = [l for l in os.popen("git status --porcelain").read().splitlines()
           if l.strip() and not l.startswith("?? ")]
for l in tracked:
    if "self_audit_run.json" in l:
        continue  # this auditor's own output cannot have been disclosed by a receipt written before it ran
    chk(l in (R["uncommitted_source_files_at_reporting"] or []),
        "a tracked modification is not disclosed: %s" % l)

# 4 - cited invocation ids exist and carry the status quoted
for c in R["commands"]:
    r = c.get("result")
    if isinstance(r, dict) and r.get("invocation_id"):
        hits = glob.glob(os.path.join("execution", "invocations", r["invocation_id"] + "*", "receipt.json"))
        chk(bool(hits), "command row cites invocation %s which is not on disk" % r["invocation_id"])
        if hits:
            inv = load(hits[0])
            chk(inv["status"] == r["status"],
                "command row says %s but invocation %s says %s" % (r["status"], r["invocation_id"][:8], inv["status"]))
            chk(inv["code_revision"] == R["repository_head_at_reporting"],
        "command row's invocation %s ran at %s but the receipt reports the tree at %s"
        % (r["invocation_id"][:8], inv["code_revision"][:8], R["repository_head_at_reporting"][:8]))
            if isinstance(r.get("assertions"), int):
                chk(len(inv.get("assertion_ids") or []) == r["assertions"],
                    "row claims %d assertions, invocation emitted %d" % (r["assertions"], len(inv.get("assertion_ids") or [])))
    if isinstance(r, str):
        src = c.get("derived_from", "")
        chk(bool(src) and os.path.exists(os.path.join(RD, src)),
            "command row quotes a string result with no captured source: %s" % src)
        if src and os.path.exists(os.path.join(RD, src)):
            log = load(os.path.join(RD, src))
            chk(log.get("exit_code") == c.get("exit_code"), "row exit_code disagrees with the log %s" % src)
            chk(log.get("code_revision") == R["repository_head_at_reporting"],
                "log %s was captured at %s, not the tree the receipt reports (%s)"
                % (src, (log.get("code_revision") or "")[:8], R["repository_head_at_reporting"][:8]))
            chk(str(log.get("status", "")) in r,
                "the log's own status %s is not visible in the quoted result for %s" % (log.get("status"), src))

# 5 - every W1301-* name the receipt uses must exist somewhere measured.
# The vocabulary is the binding invocation's own stdout (authoritative), plus the disclosure rows
# and the mutant kills the matrix file records. The prefix histogram is excluded because its keys
# are prefixes by construction, not assertion ids.
bi = (R["commands"][0]["result"].get("invocation_id") or "")
stdout_ids, stdout_nv = [], []
sp = os.path.join("execution", "invocations", bi, "stdout.txt")
if os.path.exists(sp):
    for l in io.open(sp, encoding="utf-8", errors="replace"):
        if l.strip().startswith("{"):
            rep = json.loads(l)
            stdout_ids = rep.get("assertion_ids") or []
            stdout_nv = rep.get("not_verified") or []
chk(len(stdout_ids) == R["check_results"]["assertions"],
    "check_results claims %d assertions but the binding invocation emitted %d"
    % (R["check_results"]["assertions"], len(stdout_ids)))
chk(sorted(stdout_ids) == sorted(R["check_results"].get("assertion_ids") or []),
    "the receipt's inline id list is not the binding invocation's id list")
matrix_ids = set()
for r in load(os.path.join(RD, "mutation_selfcheck_w1301.json"))["results"]:
    matrix_ids |= set(r.get("killed") or [])
# relaxations, each of which is a property of the field rather than of the claim:
#  - not_verified rows are written as "ID: reason", so the id is the part before the colon;
#  - the refusal selector shape emits W1301-SELECTORS-REQUIRED from a different invocation, so every
#    invocation the receipt cites contributes its emitted ids;
#  - two fields are excluded because they hold clipped quotations and derived prefixes, not claims:
#    commands[].result strings (a truncated stdout tail) and the prefix histogram keys.
extra_ids = set()
for c in R["commands"]:
    r = c.get("result")
    if isinstance(r, dict) and r.get("invocation_id"):
        sp2 = os.path.join("execution", "invocations", r["invocation_id"], "receipt.json")
        if os.path.exists(sp2):
            extra_ids |= set(load(sp2).get("assertion_ids") or [])
        sp3 = os.path.join("execution", "invocations", r["invocation_id"], "stdout.txt")
        if os.path.exists(sp3):
            for l in io.open(sp3, encoding="utf-8", errors="replace"):
                if l.strip().startswith("{"):
                    rep2 = json.loads(l)
                    extra_ids |= set(rep2.get("assertion_ids") or [])
                    extra_ids |= {f.get("id") for f in (rep2.get("failures") or []) if isinstance(f, dict)}
cr = R["check_results"]
nv_prefixes = {row.split(":")[0].strip() for row in R["check_results"]["not_verified"]}
matrix_ids |= extra_ids
vocabulary = set(stdout_ids) | set(stdout_nv) | set(cr["not_verified"]) | matrix_ids | nv_prefixes | extra_ids
claims = json.dumps({k: v for k, v in R.items()
                     if k not in ("commands", "check_results")}, ensure_ascii=False)          + json.dumps([cr["not_verified"]], ensure_ascii=False)          + json.dumps({k: v for k, v in cr.items() if k != "assertion_id_prefix_histogram"}, ensure_ascii=False)          + json.dumps(R["mutation_selfcheck"], ensure_ascii=False)
for i in sorted(set(re.findall(r"W1301-[A-Z0-9]+(?:-[A-Z0-9]+)*", claims))):
    chk(i in vocabulary, "receipt cites %s which is neither an assertion, a disclosure row nor a mutant kill" % i)

# 6 - disclosure rows are disclosed, not counted as assertions
cr = R["check_results"]
chk(not (set(cr["not_verified"]) & set(stdout_ids)),
    "a not_verified row also appears as an assertion id")
chk(cr["assertions"] == len(stdout_ids),
    "check_results.assertions %s vs the binding invocation %s" % (cr["assertions"], len(stdout_ids)))
inv_rep = load(os.path.join("execution", "invocations", bi, "receipt.json"))
chk(inv_rep["status"] == cr["status"], "check_results.status %s vs invocation %s" % (cr["status"], inv_rep["status"]))
chk(sorted(inv_rep.get("assertion_ids") or []) == sorted(cr.get("assertion_ids") or []),
    "the receipt's inline ids are not the invocation's ids")

# 7 - the matrix buckets and the census
m = R["mutation_selfcheck"]
mx = load(os.path.join(RD, "mutation_selfcheck_w1301.json"))
chk(m["cases"] == mx["cases"], "matrix case count differs from the file")
chk(m["buckets"] == mx["buckets"], "matrix buckets differ from the file")
chk(len(m["caught"]) == mx["buckets"]["caught"], "caught rows do not match the caught bucket")
for row in m["caught"]:
    src = [r for r in mx["results"] if r["id"] == row["case"]]
    chk(bool(src) and sorted(src[0].get("killed") or []) == sorted(row["killed"]),
        "caught row %s does not match the matrix file" % row.get("case"))
cs = R["registry_parity"]["c23_forwarded_history"]
cen = load(os.path.join(RD, "c23_forwarded_flake_census.json"))
chk(cs["runs"] == cen["runs"] == len(cen["rows"]), "census run count differs between receipt and file")
chk(cs["statuses"] == cen["statuses"], "census status counts differ between receipt and file")
chk(sum(cen["cause_counts"].values()) == cen["runs"], "census causes do not account for every run")
chk(not any("unclassified" in r["cause"] for r in cen["rows"]), "a census row is unexplained")

# 8 - registry rows the receipt claims
reg = load(os.path.join("execution", "v2.4", "commands.json"))
chk(R["registry_parity"]["registry_revision"] == reg["revision"], "registry revision stale in the receipt")
chk(reg["commands"]["test.ui.routes"].get("owner_card", "").startswith("W13-01"), "test.ui.routes is not owned by W13-01")
own = load(os.path.join("execution", "v2.4", "path_ownership.json"))
aliases = {}
for k, v in (own.get("aliases") or own.get("map") or {}).items():
    aliases[k.upper()] = v
for c in R["input"]["write_scope"]:
    first = c.split("/")[0].strip()
    entry = aliases.get(first.upper(" ") if False else first.upper())
    candidates = [re.sub(r"\s*\(.*?\)\s*", "", x).strip() for x in (entry or {}).get("paths", [first])]         if entry else [first]
    ok = [x for x in candidates if x and os.path.isdir(x)]
    chk(bool(ok), "write_scope entry %s resolves to %s and none of it is a directory" % (c, candidates))

print(json.dumps({"receipt": os.path.relpath(os.path.join(RD, "receipt.json"), REPO).replace("\\", "/"),
                  "receipt_sha256": sha(os.path.join(RD, "receipt.json")),
                  "probes": 8, "artifacts": len(R["artifacts"]), "commands": len(R["commands"]),
                  "assertions": cr["assertions"], "disclosed": len(cr["not_verified"]),
                  "matrix_buckets": m["buckets"], "census_runs": cs["runs"],
                  "inconsistencies": bad}, indent=1, ensure_ascii=False))
sys.exit(1 if bad else 0)
