"""Re-measure the three test.ui.routes selector shapes at the current HEAD and freeze them.

binding_and_parity_rev15.json was measured at the commit that bound the entry (92d82df6) and its
local row carries 28 assertions, while the suite now reports 29. A receipt must not mix rows from
different trees, so this script runs each shape once at HEAD, reads back the dispatcher's own
invocation receipt (its stdout.txt is authoritative for status), and refuses to write unless every
row is at this HEAD. The older file stays on disk as provenance.
"""
import io, json, os, subprocess, sys

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
PY = sys.executable
DISPATCH = os.path.join("execution", "command_dispatcher", "dispatch.py")
OUT = os.path.join(RD, "binding_and_parity_rev15_at_head.json")

SHAPES = [("local_check_W13_01", ["test.ui.routes", "--task-id", "W13", "--check-id", "W13-01"]),
          ("forwarded_case_C23", ["test.ui.routes", "--task-id", "W13", "--case-id", "C23"]),
          ("bare_selector_refused", ["test.ui.routes"])]

head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
rows = {}
for key, argv in SHAPES:
    p = subprocess.run([PY, DISPATCH] + argv, cwd=REPO, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800)
    text = (p.stdout or "") + (p.stderr or "")
    rep = {}
    for l in text.splitlines():
        if l.strip().startswith("{"):
            rep = json.loads(l)
    inv = rep.get("invocation_id")
    rp = os.path.join("execution", "invocations", inv, "receipt.json") if inv else None
    frozen = json.load(io.open(rp, encoding="utf-8")) if rp and os.path.exists(rp) else {}
    rows[key] = {"status": frozen.get("status", rep.get("status")), "assertions": len(frozen.get("assertion_ids") or []),
                 "invocation_id": inv, "argv": argv, "exit_code": p.returncode,
                 "code_revision": frozen.get("code_revision"), "child_exit_code": frozen.get("child_exit_code"),
                 "registry_revision_observed": json.load(io.open(os.path.join("execution", "v2.4", "commands.json"),
                                                                 encoding="utf-8-sig"))["revision"]}
    print(key, rows[key]["status"], rows[key]["assertions"], (rows[key]["code_revision"] or "")[:8])

off_head = [k for k, v in rows.items() if v["code_revision"] != head]
if off_head:
    raise SystemExit("these rows did not run at HEAD %s: %s - refusing to freeze a mixed tree" % (head[:8], off_head))
out = {"record": "the three test.ui.routes selector shapes re-measured at the HEAD this receipt reports",
       "head": head, "supersedes_for_quoting": "binding_and_parity_rev15.json (measured at the binding commit)",
       "why": "the binding-commit parity file carries a 28-assertion local row while the suite now reports 29; "
              "quoting both would mix trees",
       "rows": rows,
       "expectation": "local_check_W13_01 PASS and non-zero assertions; forwarded_case_C23 PASS 6 or an honest "
                      "failure that c23_forwarded_flake_census.json classifies; bare_selector_refused a refusal "
                      "with zero assertions, never a PASS"}
io.open(OUT, "w", encoding="utf-8", newline=NL).write(json.dumps(out, indent=1, ensure_ascii=False))
print("wrote", OUT.replace("\\", "/"))
