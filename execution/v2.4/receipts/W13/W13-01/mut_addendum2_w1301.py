"""W13-01 addendum pass 2: the same four rows, now anchored to the files that really exist.

Pass 1 reported four mutants as anchor-missing. The cause was checked rather than patched around: this
card's own registered artifact list names apps/desktop/preload/preload.js and apps/desktop/main/
workbench.html, whereas pass 1 searched main/lib/preload.js and renderer/workbench.html, which are not
in the tree. Rows are credited only when they vanish while W1301-DRIVER-RAN survives; a crash credits
nothing. The disposition table is then rebuilt from both passes, so a row moves out of OWED only when a
filed mutant actually took it down.
"""
import datetime, hashlib, io, json, os, subprocess, sys

ROOT = os.getcwd()
RD = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01")
PY = sys.executable
IPCJS = os.path.join(ROOT, "apps", "desktop", "main", "lib", "ipc.js")
PRELOAD = os.path.join(ROOT, "apps", "desktop", "preload", "preload.js")
WORKBENCH = os.path.join(ROOT, "apps", "desktop", "main", "workbench.html")

rec = json.load(io.open(os.path.join(RD, "receipt.json"), encoding="utf-8-sig"))
emitted = sorted(set(rec["check_results"]["assertion_ids"]))
base = json.load(io.open(os.path.join(RD, "mutation_selfcheck_w1301.json"), encoding="utf-8-sig"))
previously = sorted({k for r in base["results"] for k in (r.get("killed") or [])})
adj1 = json.load(io.open(os.path.join(RD, "mutation_addendum_w1301.json"), encoding="utf-8-sig"))


def sha(b):
    return hashlib.sha256(b).decode() if isinstance(b, str) else hashlib.sha256(b).hexdigest()


def digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def run_check():
    p = subprocess.run([PY, os.path.join(ROOT, "tests", "ui", "check", "main.py"), "--check-id", "W13-01"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
    txt = ((p.stdout or "") + (p.stderr or "")).strip()
    line = [l for l in txt.splitlines() if l.strip().startswith("{")]
    d = json.loads(line[-1]) if line else {}
    ids = sorted(d.get("assertion_ids") or (d.get("checks") or {}).get("assertion_ids") or [])
    return {"status": d.get("status"), "ids": ids, "tail": txt[-160:]}


MUTANTS = [
    {"id": "B1-preload-loses-a-bridged-channel", "file": PRELOAD, "kind": "token-remove",
     "needle": "session.send",
     "targets": ["W1301-PRELOAD-MATCHES-REGISTERED-CHANNELS"],
     "why": "a channel the registry exposes but the preload stops bridging must be caught"},
    {"id": "B2-ipc-drops-the-directory-picker-route", "file": IPCJS, "kind": "line-delete",
     "needle": "workspacePickDirectory: ['workspace', 'pick_directory']",
     "targets": ["W1301-FIRST-RUN-METHODS-ALL-ROUTED"],
     "why": "the first-run walkthrough needs every method routed"},
    {"id": "B3-ipc-drops-the-status-health-route", "file": IPCJS, "kind": "line-delete",
     "needle": "statusHealth: ['status', 'health']",
     "targets": ["W1301-FOUR-NATIVE-CLIENTS-ROUTED"],
     "why": "the shell claims four native clients, each with its routes"},
    {"id": "B4-workbench-tells-the-user-to-open-a-terminal", "file": WORKBENCH, "kind": "insert-before",
     "needle": "</body>", "insert": "<p>Open a terminal and run the command there.</p>\n",
     "targets": ["W1301-WORKBENCH-TELLS-NOBODY-TO-USE-A-TERMINAL"],
     "why": "the promise is that nobody has to leave the window"},
    {"id": "B5-workbench-loses-the-provider-panel", "file": WORKBENCH, "kind": "token-remove",
     "needle": "provider", "targets": ["W1301-WORKBENCH-COVERS-FOUR-CLIENTS"],
     "why": "four clients means four surfaces in the workbench"},
]

results = []
for m in MUTANTS:
    path = m["file"]
    if not os.path.isfile(path):
        results.append({"id": m["id"], "bucket": "file-absent", "file": os.path.relpath(path, ROOT).replace(os.sep, "/")})
        print("%-46s file-absent" % m["id"])
        continue
    original = open(path, "rb").read()
    d0 = hashlib.sha256(original).hexdigest()
    text = original.decode("utf-8")
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if m["needle"] in l]
    if not hits:
        results.append({"id": m["id"], "bucket": "anchor-missing",
                        "file": os.path.relpath(path, ROOT).replace(os.sep, "/"),
                        "note": "no line contains %r" % m["needle"]})
        print("%-46s anchor-missing (%d lines searched)" % (m["id"], len(lines)))
        continue
    if m["kind"] == "line-delete":
        mutated = "\n".join(lines[:hits[0]] + ["// MUTANT %s: route removed" % m["id"]] + lines[hits[0] + 1:])
    elif m["kind"] == "token-remove":
        mutated = text.replace(m["needle"], "__removed_by_mutant__", 1)
    elif m["kind"] == "insert-before":
        mutated = text.replace(m["needle"], m["insert"] + m["needle"], 1)
    else:
        mutated = text
    if mutated == text:
        results.append({"id": m["id"], "bucket": "no-op-mutant"})
        print("%-46s no-op" % m["id"])
        continue
    try:
        open(path, "wb").write(mutated.encode("utf-8"))
        got = run_check()
    finally:
        open(path, "wb").write(original)
    alive = "W1301-DRIVER-RAN" in got["ids"]
    lost = sorted(set(emitted) - set(got["ids"]))
    credited = [r for r in lost if r not in previously] if alive else []
    bucket = ("caught" if alive and set(credited) & set(m["targets"]) else
              "crashed" if not alive else "survived")
    restored = hashlib.sha256(open(path, "rb").read()).hexdigest() == d0
    results.append({"id": m["id"], "file": os.path.relpath(path, ROOT).replace(os.sep, "/"), "bucket": bucket,
                    "run_status": got["status"], "assertions_after": len(got["ids"]),
                    "driver_alive": alive, "targets": m["targets"],
                    "rows_lost_while_driver_alive": sorted(credited),
                    "targets_hit": sorted(set(m["targets"]) & set(credited)),
                    "credits_nothing_if_crash": sorted(lost) if not alive else [],
                    "restored_byte_identical": restored, "expectation": m["why"]})
    print("%-46s %-9s credited=%s restored=%s" % (m["id"], bucket, credited, restored))

new_covered = sorted({r for x in results for r in (x.get("rows_lost_while_driver_alive") or [])})
all_mutants = (adj1.get("mutants") or []) + results
disposition = dict(adj1.get("per_row_disposition") or {})
for row in new_covered:
    who = [x["id"] for x in results if row in (x.get("rows_lost_while_driver_alive") or [])]
    disposition[row] = ("killed by filed addendum mutant %s in pass 2 (driver alive, file restored "
                        "byte-identically); the shipped matrix is untouched because its artifact is pinned"
                        % ", ".join(who))
open_rows = sorted(set(emitted) - set(previously) - set(new_covered))
doc2 = {"record": "W13-01 mutation addendum pass 2 - corrected file anchors",
        "why_pass_one_missed": ("pass 1 searched apps/desktop/main/lib/preload.js and "
                                "apps/desktop/renderer/workbench.html; the card's own artifact list names "
                                "apps/desktop/preload/preload.js and apps/desktop/main/workbench.html, so "
                                "the four anchor-missing results were wrong paths, not absent code"),
        "mutants": results, "rows_newly_discriminated": new_covered,
        "attribution_rule": adj1["attribution_rule"],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
json.dump(doc2, io.open(os.path.join(RD, "mutation_addendum2_w1301.json"), "w", encoding="utf-8", newline="\n"),
          indent=1, ensure_ascii=False)
adj1["mutants"] = all_mutants
adj1["per_row_disposition"] = disposition
adj1["rows_newly_discriminated"] = sorted(set(adj1.get("rows_newly_discriminated") or []) | set(new_covered))
adj1["rows_still_without_a_mutant"] = open_rows
adj1["disposition_counts"] = {
    "killed_or_measured": len([k for k, v in disposition.items() if not v.startswith(("OWED", "UNCLASSIFIED"))]),
    "owed": len([k for k, v in disposition.items() if v.startswith("OWED")]),
    "unclassified": len([k for k, v in disposition.items() if v.startswith("UNCLASSIFIED")])}
adj1["pass2"] = "mutation_addendum2_w1301.json"
adj1["finalised_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(adj1, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"),
          indent=1, ensure_ascii=False)
print("pass2 credited:", new_covered)
print("still owed:", len(open_rows), "| counts:", adj1["disposition_counts"])
print("tree clean:", subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", "apps", "tests"],
                                    capture_output=True, text=True, cwd=ROOT).stdout.strip() == "")
