"""Reviewer measurement for W07-01 claims 3 and 4.

Runs the card's own check program directly (same argv the registry stores, same selector env the dispatcher
forwards) up to three times, recording EVERY attempt, then independently re-reads the winning run's SQLite
database and evidence directory: the cursor is taken out of domain_objects / domain_versions by this script,
not out of the probe's report, and the sealed bytes are re-digested here.
Nothing is smoothed: a refused or timed-out kind is reported as it measured.
"""
import hashlib
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

REPO = r"D:/作品集/ResearchOS/research-os"
CHECK = os.path.join("tests", "sources", "check", "main.py")
REQUIRED = ("url", "author", "published_at", "retrieved_at", "upstream_revision",
            "body_sha256", "artifact_ref", "evidence_id", "locator")


def run_check():
    env = dict(os.environ, RESEARCHOS_TASK_ID="W07", RESEARCHOS_CHECK_ID="W07-01", RESEARCHOS_CASE_ID="",
               PYTHONUTF8="1", GOTOOLCHAIN="local", GOENV="off")
    env.pop("RESEARCHOS_SOURCE_KIND", None)
    started = time.time()
    p = subprocess.run([sys.executable, "-X", "utf8", CHECK], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=REPO, env=env, timeout=1500)
    lines = [l.strip() for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    rep = json.loads(lines[-1]) if lines else None
    return {"rc": p.returncode, "seconds": round(time.time() - started, 1), "report": rep,
            "stderr_tail": (p.stderr or "")[-500:]}


def probe_reports(run_dir):
    """Every report file the run produced, by attempt directory."""
    out = {}
    root = os.path.join(REPO, run_dir) if not os.path.isabs(run_dir) else run_dir
    if not os.path.isdir(root):
        return out
    for d in sorted(os.listdir(root)):
        sub = os.path.join(root, d)
        if not os.path.isdir(sub):
            continue
        for f in sorted(os.listdir(sub)):
            if f.startswith("report-") and f.endswith(".json"):
                out[d + "/" + f] = json.loads(io.open(os.path.join(sub, f), encoding="utf-8").read())
    return out


def read_back_cursor(db_path, cursor_id):
    con = sqlite3.connect("file:" + db_path.replace("\\", "/") + "?mode=ro", uri=True)
    try:
        cur = con.execute("SELECT kind, revision, body FROM domain_objects WHERE id=?", (cursor_id,)).fetchone()
        body = json.loads(cur[2]) if cur else {}
        hist = con.execute("SELECT revision, body FROM domain_versions WHERE id=? ORDER BY revision",
                           (cursor_id,)).fetchall()
        return {
            "kind": cur[0] if cur else None,
            "revision": cur[1] if cur else None,
            "covered_until": body.get("covered_until"),
            "pending_window_from": body.get("pending_window_from"),
            "pending_window_to": body.get("pending_window_to"),
            "opaque_cursor": body.get("opaque_cursor"),
            "versions": [{"revision": r,
                          "covered_until": json.loads(b).get("covered_until"),
                          "pending_window_from": json.loads(b).get("pending_window_from"),
                          "opaque_cursor": json.loads(b).get("opaque_cursor")} for r, b in hist],
        }
    finally:
        con.close()


def verify_artifacts(db_path, items):
    con = sqlite3.connect("file:" + db_path.replace("\\", "/") + "?mode=ro", uri=True)
    rows = []
    try:
        for it in items:
            ref = it.get("artifact_ref") or {}
            key = ref.get("id") if isinstance(ref, dict) else ref
            r = con.execute("SELECT content_hash, sealed, length(bytes), substr(bytes,1,40) "
                            "FROM uploaded_content WHERE storage_key=?", (key,)).fetchone()
            full = con.execute("SELECT bytes FROM uploaded_content WHERE storage_key=?", (key,)).fetchone()
            rows.append({
                "storage_key": str(key),
                "claimed_body_sha256": it.get("body_sha256"),
                "row_found": bool(r),
                "stored_content_hash": r[0] if r else None,
                "sealed_flag": r[1] if r else None,
                "byte_len": r[2] if r else None,
                "reviewer_recomputed": ("sha256:" + hashlib.sha256(bytes(full[0])).hexdigest()) if full else None,
            })
    finally:
        con.close()
    return rows


def main():
    attempts = []
    winner = None
    for i in range(1, 4):
        res = run_check()
        rep = res["report"] or {}
        attempts.append({
            "attempt": i, "rc": res["rc"], "seconds": res["seconds"],
            "status": rep.get("status"), "assertions": rep.get("assertions"),
            "failures": [{"id": f["id"], "detail": f["detail"][:300]} for f in rep.get("failures", [])],
            "blocked_kinds": rep.get("blocked_kinds"),
            "captures": rep.get("captures"),
            "evidence_run_dir": rep.get("evidence_run_dir"),
            "stderr_tail": res["stderr_tail"][:200],
        })
        if rep.get("status") == "PASS":
            winner = rep
            break
        time.sleep(2)

    result = {"attempts": attempts, "clean_run_obtained": bool(winner)}
    if winner:
        run_dir = winner["evidence_run_dir"]
        reports = probe_reports(run_dir)
        detail = {}
        for path, rep in reports.items():
            kind = rep.get("source")
            dbp = rep.get("db_path") or ""
            db_abs = dbp if os.path.isabs(dbp) else os.path.join(REPO, dbp)
            items = rep.get("items") or []
            d = {
                "status": rep.get("status"), "scope": rep.get("scope"),
                "page_complete": rep.get("page_complete"),
                "item_count": len(items),
                "items_missing_fields": {k: [i for i, it in enumerate(items) if not it.get(k)]
                                         for k in REQUIRED},
                "request_urls": rep.get("request_urls"),
                "final_urls": rep.get("final_urls"),
                "request_equals_final": (rep.get("request_urls") or []) == (rep.get("final_urls") or [])
                                        and bool(rep.get("request_urls")),
                "raw_page": rep.get("raw_page"),
                "manifest": rep.get("manifest"),
                "db_exists": os.path.isfile(db_abs),
                "reviewer_cursor_read_back": read_back_cursor(db_abs, rep.get("cursor_id"))
                                             if os.path.isfile(db_abs) else None,
                "reviewer_sealed_recompute": verify_artifacts(db_abs, items)
                                             if os.path.isfile(db_abs) else None,
                "upstream_revisions": [i.get("upstream_revision") for i in items],
                "urls": [i.get("url") for i in items],
                "published_at": [i.get("published_at") for i in items],
                "retrieved_at": [i.get("retrieved_at") for i in items],
                "authors": [i.get("author") for i in items],
                "locators": [i.get("locator") for i in items],
                "body_bytes": [i.get("body_bytes") for i in items],
            }
            detail[path] = d
        result["reviewer_independent_readback"] = detail
        result["invariant_rows"] = {
            "window_rows_as_reported": [x for x in (winner.get("diagnostics") or [])
                                        if x.get("probe", "").startswith("cursor-branch")],
            "captures": winner.get("captures"),
        }
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
