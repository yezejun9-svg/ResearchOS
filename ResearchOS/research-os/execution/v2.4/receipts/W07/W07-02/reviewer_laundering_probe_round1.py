"""Reviewer round-1 anti-laundering probe for W07-02's own check program.

The card's green run reports PASS with 20 assertions. The question this answers is not 'is it green' but
'is there a path where a kind that never read still contributes to a PASS'. Three injected states are driven
through a byte-for-byte copy of tests/sources/check/main_w0702.py whose only edits are the constants that name
the X backend and the pinned go, plus the evidence root (redirected to .local so no product evidence directory
is written):

  B  browser-act executable missing   -> the X kind cannot read at all
  A  browser id not registered         -> X fails at the browser CLI (the executor's own disclosed mistake)
  C  pinned go missing                 -> the probe never builds, so no kind is observed

Expected for all three: status FAIL, the X rows red, and no assertion silently dropped from the roster. A PASS
under any of these would be the laundering the card's NEGATIVE check forbids.

Usage: python execution/v2.4/receipts/W07/W07-02/reviewer_laundering_probe_round1.py
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
SRC = os.path.join(ROOT, "tests", "sources", "check", "main_w0702.py")
WORK = os.path.join(ROOT, ".local", "rw0702")

VARIANTS = {
    "B_browser_act_missing": [(r'BROWSER_ACT = r"C:/Users/yqyyds/.local/bin/browser-act.exe"',
                              'BROWSER_ACT = r"C:/no/such/browser-act-for-reviewer-test.exe"')],
    "A_bogus_browser_id": [(r'X_BROWSER_ID = "direct_local_120993884286222444"',
                            'X_BROWSER_ID = "reviewer-nonexistent-browser-id"')],
    "C_pinned_go_missing": [(r'GO = os.path.join(ROOT, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")',
                            'GO = os.path.join(ROOT, ".local", "no-such-go-for-reviewer-test.exe")')],
}


def build_copy(name):
    text = io.open(SRC, encoding="utf-8").read()
    ed = list(VARIANTS[name])
    # ROOT is derived from the script's own location, and this copy lives outside the product tree, so it must be
    # pinned to the real repository or every variant dies at the build step instead of at the injected state.
    old_root_src = 'ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))'
    assert text.count(old_root_src) == 1, "ROOT anchor moved"
    ed.insert(0, (old_root_src, 'ROOT = %r' % ROOT))
    for old, new in ed:
        assert text.count(old) == 1, "anchor not unique for %s: %s" % (name, old[:60])
        text = text.replace(old, new, 1)
    # redirect the evidence root out of the product evidence tree
    old_root = 'os.path.join(ROOT, "qualification", "v2.4", "evidence", "w0702",'
    assert text.count(old_root) == 1, "evidence root anchor moved"
    text = text.replace(old_root, 'os.path.join(%r, "launder",' % WORK, 1)
    p = os.path.join(WORK, "launder_main_%s.py" % name)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
    return p


def main():
    os.makedirs(WORK, exist_ok=True)
    out = {"artifact": "reviewer_anti_laundering_round1.json",
           "reviewer_id": "qoder-desktop:/root/w0702_verifier_r1", "step_id": "W07-02",
           "source_under_test": "tests/sources/check/main_w0702.py", "variants": {}}
    for name in VARIANTS:
        script = build_copy(name)
        try:
            p = subprocess.run([sys.executable, "-X", "utf8", script], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=ROOT, timeout=2400)
            rc, so, se = p.returncode, p.stdout or "", p.stderr or ""
        except subprocess.TimeoutExpired:
            rc, so, se = 124, "", "timeout after 2400s"
        lines = [l for l in so.splitlines() if l.strip().startswith("{")]
        rep = json.loads(lines[-1]) if lines else None
        rowmap = {r["id"]: r["result"] for r in (rep or {}).get("rows", [])}
        x_rows = {k: v for k, v in rowmap.items() if "-X-" in k}
        verdict = {
            "child_rc": rc,
            "status": (rep or {}).get("status"),
            "assertions": (rep or {}).get("assertions"),
            "n_rows": len(rowmap),
            "x_rows": x_rows,
            "x_rows_red": sorted(k for k, v in x_rows.items() if v != "PASS"),
            "failure_ids": [f["id"] for f in (rep or {}).get("failures", [])],
            "failures_detail_sample": [str(f["detail"])[:220] for f in (rep or {}).get("failures", [])][:6],
            "stderr_tail": se[-200:],
            "laundered_pass": (rep or {}).get("status") == "PASS",
        }
        # the roster must not shrink either: 20 rows in every variant that reached the grading stage
        if name != "C_pinned_go_missing":
            verdict["roster_complete"] = len(rowmap) == 20
        out["variants"][name] = verdict
    blob = json.dumps(out, ensure_ascii=False, indent=1)
    io.open(os.path.join(WORK, "reviewer_anti_laundering_round1.json"), "w", encoding="utf-8", newline="\n").write(blob)
    print(blob)


if __name__ == "__main__":
    main()
