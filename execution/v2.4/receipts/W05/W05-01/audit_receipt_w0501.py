"""Independent self-audit of execution/v2.4/receipts/W05/W05-01/receipt.json, written before the reviewer.

This recomputes every figure the receipt carries from the frozen files on disk instead of re-reading the
receipt's own prose, and it reports the numbers that are NOT reachable that way. The check worth the most
is the last one: every W0501-* identifier quoted anywhere in the receipt must exist in the frozen
assertion id set, because a receipt that cites an assertion nobody runs is worse than one that cites none.
Exit 1 with a list of findings; exit 0 only when every probe below passes.
"""
import glob, hashlib, io, json, os, re, subprocess, sys

def _find_repo(start):
    d = start
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal", "domain")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
RD = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01")
findings, passed = [], []


def ok(name, detail=""):
    passed.append(name + (": " + detail if detail else ""))


def bad(name, detail):
    findings.append({"probe": name, "detail": detail})


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


receipt = load(os.path.join(RD, "receipt.json"))
head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

# 1. the receipt must remain a report
if receipt.get("status") != "EXECUTION_REPORTED":
    bad("status", receipt.get("status"))
elif receipt.get("verifier_id") is not None or receipt.get("independent_review") or receipt.get("independent_reviews"):
    bad("self_signing", "verifier or review content present in an executor receipt")
else:
    ok("report_shape", "EXECUTION_REPORTED with no verifier field")
text = json.dumps(receipt, ensure_ascii=False)
# assertion ids legitimately contain the word ACCEPTED (W0501-ADAPTER-CURRENT-EPOCH-RENEWAL-ACCEPTED), so
# the acceptance-vocabulary probe reads prose with id-shaped tokens removed, not the raw serialization
if re.search(r"\bACCEPT(ED|_WITH)\b", re.sub(r"W0501-[A-Z0-9]+(?:-[A-Z0-9]+)*", "", text)):
    bad("acceptance_wording", "the receipt uses acceptance vocabulary")
else:
    ok("no_acceptance_wording")

# 2. artifacts re-hashed from disk
rows = {a["path"]: a["sha256"] for a in receipt["artifacts"]}
mismatch = []
for p, h in rows.items():
    if not os.path.exists(p):
        mismatch.append([p, "absent"])
    elif hashlib.sha256(open(p, "rb").read()).hexdigest() != h:
        mismatch.append([p, "hash differs"])
bad("artifact_hashes", mismatch) if mismatch else ok("artifact_hashes", "%d files re-hashed" % len(rows))

# 3. the assertion set is derived from the frozen runs, not from the receipt
runs, ids = [], set()
for d in sorted(glob.glob(os.path.join(RD, "invocations", "*"))):
    rp = os.path.join(d, "receipt.json")
    if not os.path.isfile(rp):
        continue
    r = load(rp)
    if (r.get("code_revision") or "") == receipt["repository_head_at_reporting"]:
        sp = os.path.join(d, "stdout.txt")
        rep = {}
        for line in io.open(sp, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("{") and '"assertion_ids"' in line:
                rep = json.loads(line)
        runs.append({"dir": os.path.basename(d), "ids": sorted(r.get("assertion_ids") or []),
                     "report": rep, "status": r.get("status")})
        ids |= set(r.get("assertion_ids") or [])
if len(runs) < 2:
    bad("binding_runs", "only %d frozen runs at the receipt HEAD" % len(runs))
else:
    ok("binding_runs", "%d runs at %s" % (len(runs), receipt["repository_head_at_reporting"][:8]))
    if runs[0]["ids"] != runs[1]["ids"]:
        bad("run_agreement", "the two frozen runs list different id sets")
    else:
        ok("run_agreement", "%d ids identical" % len(runs[0]["ids"]))
    if receipt["check_results"]["assertions"] != len(runs[0]["ids"]):
        bad("assertion_count", "%s in the receipt, %d on disk"
            % (receipt["check_results"]["assertions"], len(runs[0]["ids"])))
    else:
        ok("assertion_count", str(len(runs[0]["ids"])))
    for rep in (r["report"] for r in runs):
        if sorted(rep.get("assertion_ids") or []) != runs[0]["ids"] or rep.get("status") != "PASS":
            bad("stdout_report", "a frozen stdout.txt disagrees with the invocation receipt")
            break
    else:
        ok("stdout_report", "each frozen stdout.txt repeats the same ids and PASS")
    if sorted(receipt["check_results"]["not_verified"]) != sorted(runs[0]["report"].get("not_verified") or []):
        bad("not_verified", "disclosure rows differ from the frozen report")
    else:
        ok("not_verified", "%d rows copied exactly from the report" % len(receipt["check_results"]["not_verified"]))

# 4. matrix counted from its own rows
matrix = load(os.path.join(RD, receipt["mutation_selfcheck"]["matrix_source"]))
counted = {}
for r in matrix["results"]:
    counted[r["bucket"]] = counted.get(r["bucket"], 0) + 1
for k in ("caught", "survived", "crashed", "anchor-missing"):
    counted.setdefault(k, 0)
if counted != matrix["buckets"]:
    bad("matrix_buckets", "%s counted vs %s recorded" % (counted, matrix["buckets"]))
elif matrix["buckets"] != receipt["mutation_selfcheck"]["buckets"]:
    bad("matrix_buckets", "the receipt and the matrix disagree")
else:
    ok("matrix_buckets", json.dumps(counted))
if matrix["cases"] != len(matrix["results"]):
    bad("matrix_cases", "cases=%s but %d rows" % (matrix["cases"], len(matrix["results"])))
else:
    ok("matrix_cases", "%d rows, equivalence probe kept outside (%d)"
       % (matrix["cases"], len(matrix["equivalence_probe"]["results"])))
unclean = [r["id"] for r in matrix["results"] if r["bucket"] == "caught" and not r.get("restored_byte_identical")]
no_kill = [r["id"] for r in matrix["results"] if r["bucket"] == "caught" and not r.get("killed")]
if unclean or no_kill:
    bad("matrix_rows", {"not_restored": unclean, "no_named_kill": no_kill})
else:
    ok("matrix_rows", "every caught case names at least one killed assertion and restored its file")
if not matrix.get("tree_clean_after_restore"):
    bad("matrix_tree", "the matrix did not leave the tree clean")
else:
    ok("matrix_tree")
for e in matrix["equivalence_probe"]["results"]:
    if e["bucket"] != "survived":
        bad("equivalence_probe", "%s was killed, so it is not an equivalence probe" % e["id"])
    elif e["expected"] != "survived":
        bad("equivalence_probe", "%s does not declare its expected bucket" % e["id"])
    else:
        ok("equivalence_probe", "%s survives as filed outside the matrix, with the stated reason" % e["id"])

# 5. every command row must be traceable to a captured artifact
untraceable = []
for c in receipt["commands"]:
    df = c.get("derived_from")
    r = c.get("result")
    if isinstance(r, dict):
        f = r.get("frozen_under")
        if not f or not os.path.isdir(os.path.join(RD, f)):
            untraceable.append(c["argv"][-1] if c.get("argv") else "?")
        continue
    if not df:
        untraceable.append(" ".join(c.get("argv") or []))
        continue
    p = os.path.join(RD, df) if not df.startswith("execution/") else df
    if not os.path.exists(p):
        untraceable.append(df)
        continue
    body = io.open(p, encoding="utf-8", errors="replace").read()
    if "stdout.txt" in df:
        rep = {}
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("{") and '"assertion_ids"' in line:
                rep = json.loads(line)
        if rep.get("status") != "PASS" or (runs and sorted(rep.get("assertion_ids") or []) != runs[0]["ids"]):
            untraceable.append(df + " (its frozen report is not a PASS over the same id set)")
    else:
        log = json.loads(body)
        if str(log.get("exit_code")) != str(c.get("exit_code")):
            untraceable.append(df + " (exit code differs)")
if untraceable:
    bad("command_provenance", untraceable)
else:
    ok("command_provenance", "%d rows, each pointing at a frozen invocation or captured log" % len(receipt["commands"]))

# 6. registry facts
registry = load(os.path.join("execution", "v2.4", "commands.json"))
if receipt["registry_parity"]["registry_revision"] != registry["revision"]:
    bad("registry_revision", "%s recorded, %s on disk"
        % (receipt["registry_parity"]["registry_revision"], registry["revision"]))
else:
    ok("registry_revision", str(registry["revision"]))
entry = registry["commands"]["test.runtime"]
if "W05-01" not in json.dumps(entry):
    bad("registry_owner", "test.runtime does not mention this card")
else:
    ok("registry_owner", "test.runtime carries W05-01 selectors")

# 7. quoted assertion ids must exist
quoted = sorted(set(re.findall(r"W0501-[A-Z0-9]+(?:-[A-Z0-9]+)*", text)))
# Three vocabularies are legal: rows the harness asserts, rows it discloses as not verified, and the
# prefix keys of its own histogram. Anything else would be a citation of an assertion nobody runs.
# A disclosure row is "ID: reason", so the id is the part before the first colon; the reason prose is not
# a vocabulary and must not be allowed to smuggle an unrelated token past this probe.
disclosed = sorted({row.split(":")[0].strip() for row in receipt["check_results"]["not_verified"]})
vocab = set(ids) | set(disclosed) | set(receipt["check_results"]["assertion_id_prefix_histogram"])
ghost = [q for q in quoted if q not in vocab]
if ghost:
    bad("quoted_assertion_ids", ghost)
else:
    ok("quoted_assertion_ids", "%d quoted ids all inside %d asserted + %d disclosed + %d prefix keys"
       % (len(quoted), len(ids), len(disclosed), len(receipt["check_results"]["assertion_id_prefix_histogram"])))
overlap = sorted(set(ids) & set(disclosed))
if overlap:
    bad("asserted_and_disclosed_overlap", overlap)
else:
    ok("disclosure_is_disjoint", "%d asserted rows and %d disclosed rows share no id" % (len(ids), len(disclosed)))
if len(disclosed) != len(receipt["check_results"]["not_verified"]):
    bad("disclosure_rows_unique", "%d rows name %d distinct ids"
        % (len(receipt["check_results"]["not_verified"]), len(disclosed)))
else:
    ok("disclosure_rows_unique", str(len(disclosed)))
missing_from_suite = sorted(i for i in ids if i not in quoted)
if missing_from_suite:
    ok("suite_ids_not_quoted", "%d asserted rows the receipt prose never names: %s"
       % (len(missing_from_suite), missing_from_suite))

out = {"auditor": "audit_receipt_w0501.py", "findings": findings, "passed": passed,
       "first_pass_findings_and_their_disposition": [
        {"finding": "acceptance_wording", "was": "the probe matched ACCEPTED inside the assertion id W0501-ADAPTER-CURRENT-EPOCH-RENEWAL-ACCEPTED",
         "disposition": "auditor scope error, fixed by reading prose with id-shaped tokens removed; the receipt still claims only EXECUTION_REPORTED",
         "how_to_reproduce": "revert the regex to search the raw serialization and the probe fires again"},
        {"finding": "command_provenance", "was": "the probe looked for the literal substring '\"status\": \"PASS\"' inside a frozen stdout report that is serialized without a space after the colon",
         "disposition": "auditor artifact; the probe now parses the report and requires PASS over the identical id set, which is the property that was meant to be checked",
         "how_to_reproduce": "grep the frozen stdout.txt for status and see the compact form"},
        {"finding": "quoted_assertion_ids", "was": "twelve W0501-* tokens were called ghost ids: the histogram prefix keys (W0501-ADAPTER, W0501-PROTOCOL, ...) and the three disclosed not-verified rows",
         "disposition": "auditor scope error; the vocabulary now covers asserted ids, disclosed ids and prefix keys, and a separate probe requires the asserted and disclosed sets to be disjoint so a skip cannot masquerade as an assertion",
         "how_to_reproduce": "the three disclosed ids are quoted verbatim from the frozen report's not_verified array, which the not_verified probe compares byte for byte"}],
       "receipt_head": receipt["repository_head_at_reporting"], "git_head_at_audit": head,
       "verdict": "CLEAN" if not findings else "FINDINGS"}
io.open(os.path.join(RD, "receipt_selfaudit.json"), "w", encoding="utf-8", newline="\n").write(
    json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps({"verdict": out["verdict"], "findings": len(findings), "passed": len(passed)}))
for f in findings:
    print("FINDING", f["probe"], json.dumps(f["detail"], ensure_ascii=False)[:300])
sys.exit(1 if findings else 0)
