"""W13-01 mutation addendum: cover the rows the shipped matrix left undiscriminated.

Why this exists: the shipped matrix hashes 10 cases and its own no_mutant_rows field lists 7 rows,
while the emitted set minus the union of killed rows is 19. Both numbers are in the frozen artifact;
neither is edited here. This script writes NEW files only, because mutation_selfcheck_w1301.json and
the other 13 artifacts are pinned by an accepted receipt and must not change by one byte.

Method per mutant: take a file the row actually reads, apply the smallest edit that makes the
behaviour the row names wrong, run the card's own check program the same way the shipped runner runs
it, record which assertion ids disappeared or failed, then restore and require the file to come back
byte-identical. A mutant that crashes the whole run is reported as crashed, not as killed.
"""
import datetime, hashlib, io, json, os, subprocess, sys

ROOT = os.getcwd()
RD = os.path.join(ROOT, "execution", "v2.4", "receipts", "W13", "W13-01")
PY = sys.executable
HOSTJS = os.path.join(ROOT, "apps", "desktop", "main", "lib", "host.js")
IPCJS = os.path.join(ROOT, "apps", "desktop", "main", "lib", "ipc.js")
PRELOAD = os.path.join(ROOT, "apps", "desktop", "main", "lib", "preload.js")
WORKBENCH = os.path.join(ROOT, "apps", "desktop", "renderer", "workbench.html")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    return open(p, "rb").read().decode("utf-8")


def run_check():
    p = subprocess.run([PY, os.path.join(ROOT, "tests", "ui", "check", "main.py"), "--check-id", "W13-01"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=1800)
    txt = ((p.stdout or "") + (p.stderr or "")).strip()
    line = [l for l in txt.splitlines() if l.strip().startswith("{")]
    d = json.loads(line[-1]) if line else {}
    checks = d.get("checks") or {}
    return {"rc": p.returncode, "status": d.get("status"),
            "ids": sorted(d.get("assertion_ids") or checks.get("assertion_ids") or []),
            "failures": sorted(f.get("id", "?") for f in (d.get("failures") or [])),
            "raw_tail": txt[-200:]}


rec = json.load(io.open(os.path.join(RD, "receipt.json"), encoding="utf-8-sig"))
emitted = sorted(set(rec["check_results"]["assertion_ids"]))
base = json.load(io.open(os.path.join(RD, "mutation_selfcheck_w1301.json"), encoding="utf-8-sig"))
previously_killed = sorted({k for r in base["results"] for k in (r.get("killed") or [])})
uncovered = sorted(set(emitted) - set(previously_killed))

# each mutant: id, file, marker (must occur exactly once), replacement, plus what it should take down
MUTANTS = [
    {"id": "A1-preload-drops-a-registered-channel", "file": PRELOAD, "kind": "drop-line-containing",
     "needle": "session.send", "targets": ["W1301-PRELOAD-MATCHES-REGISTERED-CHANNELS"],
     "why": "a channel the registry exposes but the preload no longer bridges must be caught"},
    {"id": "A2-ipc-drops-a-route", "file": IPCJS, "kind": "drop-line-containing",
     "needle": "workspacePickDirectory", "targets": ["W1301-FIRST-RUN-METHODS-ALL-ROUTED",
                                                     "W1301-ALL-CLIENT-CHANNELS-REGISTERED"],
     "why": "the first-run walkthrough needs every method routed; removing one must break it"},
    {"id": "A3-ipc-drops-a-client", "file": IPCJS, "kind": "drop-line-containing",
     "needle": "statusHealth", "targets": ["W1301-FOUR-NATIVE-CLIENTS-ROUTED",
                                           "W1301-WORKBENCH-COVERS-FOUR-CLIENTS"],
     "why": "the shell claims four native clients; dropping one channel must be visible"},
    {"id": "A4-workbench-tells-the-user-to-use-a-terminal", "file": WORKBENCH, "kind": "append",
     "needle": "</body>", "text": "<p>Open a terminal and run the command there.</p>\n</body>",
     "targets": ["W1301-WORKBENCH-TELLS-NOBODY-TO-USE-A-TERMINAL"],
     "why": "the card's own promise is that nobody has to leave the window"},
    {"id": "A5-host-refuses-unknown-clients-anyway", "file": HOSTJS, "kind": "disable-guard",
     "needle": "UNKNOWN_CLIENT", "targets": ["W1301-UNKNOWN-CLIENT-AND-METHOD-REFUSED"],
     "why": "the staged M24 disabled this guard and crashed the run; a narrower edit should discriminate the row instead of the driver"},
    {"id": "A6-provider-catch-all-branch-returns-success", "file": HOSTJS, "kind": "catchall-ok",
     "needle": "PROVIDER_", "targets": ["W1301-AUTH-RATELIMIT-UNSUPPORTED-ARE-FAILURES",
                                        "W1301-PROVIDER-OK-IS-SUCCESS"],
     "why": "the round-3 reviewer reproduced this survival; it is filed again here so the addendum does not pretend it was fixed"},
]

results = []
for m in MUTANTS:
    path = m["file"]
    if not os.path.isfile(path):
        results.append({"id": m["id"], "bucket": "file-absent", "note": path})
        continue
    original = open(path, "rb").read()
    digest = sha(original)
    text = original.decode("utf-8")
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if m["needle"] in l]
    if not hits:
        results.append({"id": m["id"], "bucket": "anchor-missing", "note": "no line contains %r" % m["needle"]})
        continue
    mutated = None
    if m["kind"] == "drop-line-containing":
        mutated = "\n".join(lines[:hits[0]] + ["// MUTANT %s: dropped %s" % (m["id"], m["needle"])] + lines[hits[0] + 1:])
    elif m["kind"] == "append":
        mutated = text.replace(m["needle"], m["text"], 1)
    elif m["kind"] == "disable-guard":
        i = hits[0]
        mutated = "\n".join(lines[:i] + [lines[i].replace("if (!routes)", "if (false && !routes)").replace("if (!r)", "if (false && !r)")] + lines[i + 1:])
    elif m["kind"] == "catchall-ok":
        i = hits[0]
        mutated = "\n".join(lines[:i] + [lines[i].replace("ok: false", "ok: true")] + lines[i + 1:])
    if mutated is None or mutated == text:
        results.append({"id": m["id"], "bucket": "no-op-mutant", "note": "the edit did not change the file"})
        continue
    try:
        open(path, "wb").write(mutated.encode("utf-8"))
        got = run_check()
    finally:
        open(path, "wb").write(original)
    restored = sha(open(path, "rb").read()) == digest
    lost = sorted(set(emitted) - set(got["ids"]))
    newly = sorted(set(lost) - set(previously_killed))
    hit_targets = sorted(set(m["targets"]) & set(lost))
    driver_alive = "W1301-DRIVER-RAN" not in lost and got["status"] in ("PASS", "FAIL")
    bucket = ("caught" if hit_targets and driver_alive else
              "crashed" if not driver_alive else "survived")
    results.append({"id": m["id"], "file": os.path.relpath(path, ROOT).replace(os.sep, "/"), "bucket": bucket,
                    "run_status": got["status"], "assertions_after": len(got["ids"]),
                    "targets_hit": hit_targets, "rows_newly_discriminated": newly,
                    "restored_byte_identical": restored})
    print("%-46s %-9s newly-covered=%s restored=%s" % (m["id"], bucket, newly, restored))

covered_now = sorted({r for x in results for r in x.get("rows_newly_discriminated") or []})
still_open = sorted(set(uncovered) - set(covered_now))
doc = {"record": "W13-01 mutation addendum; the shipped matrix and its 14 pinned artifacts are unchanged",
       "computed_from": {"emitted_assertions": len(emitted),
                         "killed_by_shipped_matrix": len(previously_killed),
                         "rows_without_a_mutant_before_this_addendum": len(uncovered),
                         "shipped_no_mutant_rows_field_says": len(base.get("no_mutant_rows") or [])},
       "discrepancy": ("the shipped artifact's no_mutant_rows lists %d rows while emitted-minus-killed is %d; "
                       "both numbers stay in the frozen file, and this addendum works from the computed %d"
                       % (len(base.get("no_mutant_rows") or []), len(uncovered), len(uncovered))),
       "mutants": results,
       "rows_newly_discriminated": covered_now,
       "rows_still_without_a_mutant": still_open,
       "how_to_reproduce": "python execution/v2.4/receipts/W13/W13-01/mut_addendum_w1301.py",
       "generated_by": "qoder-desktop:/root/construction",
       "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "repository_head": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip(),
       "tree_clean_after_restores": subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", "apps", "tests"],
                                                   capture_output=True, text=True, cwd=ROOT).stdout.strip() == ""}
json.dump(doc, io.open(os.path.join(RD, "mutation_addendum_w1301.json"), "w", encoding="utf-8", newline="\n"),
          indent=1, ensure_ascii=False)
print("covered now:", len(covered_now), "| still without a mutant:", len(still_open))
for s in still_open:
    print("   -", s)
print("tree clean after restores:", doc["tree_clean_after_restores"])
