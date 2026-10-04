"""Reviewer attacks on claim 5: is there ANY remaining path where a missing live read still ends in PASS?

Four probes, each a whole run of the card's registered check program, none of which edits any tracked file:

  1. only ONE kind is starved: HTTPS_PROXY points at a dead port but NO_PROXY lets arXiv through, so GITHUB
     cannot be read while PAPER can. (The mirror case - PAPER starved, GITHUB fine - was already measured by the
     reviewer's first dispatcher run, which failed with four named PAPER rows.)
  2. the live probe BINARY cannot be built: GOTMPDIR points at a directory that does not exist, so `go build`
     fails. This is the branch whose four rows are `skip()`-ped rather than failed.
  3. RESEARCHOS_SOURCE_KIND set to a value that is not a kind this card owns, to prove the outer environment
     cannot redirect the graded kinds or make the capture loop run zero kinds.
  4. RESEARCHOS_SOURCE_OUTPUT_DIR pre-set by the caller, to prove the run still gets its own fresh directory and
     a stale output directory cannot be inherited.

Every attempt is recorded as measured, including the environment's own refusals.
"""
import json
import os
import subprocess
import sys
import time

REPO = r"D:/作品集/ResearchOS/research-os"
CHECK = os.path.join("tests", "sources", "check", "main.py")


def run(label, extra_env, drop=()):
    env = dict(os.environ, RESEARCHOS_TASK_ID="W07", RESEARCHOS_CHECK_ID="W07-01", RESEARCHOS_CASE_ID="",
               PYTHONUTF8="1", GOTOOLCHAIN="local", GOENV="off")
    env.pop("RESEARCHOS_SOURCE_KIND", None)
    env.pop("RESEARCHOS_SOURCE_OUTPUT_DIR", None)
    for k in drop:
        env.pop(k, None)
    env.update(extra_env)
    for k, v in list(extra_env.items()):
        if v is None:
            env.pop(k, None)
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", CHECK], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=REPO, env=env, timeout=900)
        rc, out, err = p.returncode, p.stdout or "", p.stderr or ""
    except subprocess.TimeoutExpired as exc:
        return {"probe": label, "rc": "TIMEOUT", "seconds": round(time.time() - t0, 1),
                "status": "NOT_PASSED(timeout)", "note": str(exc)[:200]}
    lines = [l.strip() for l in out.splitlines() if l.strip().startswith("{")]
    rep = None
    if lines:
        try:
            rep = json.loads(lines[-1])
        except ValueError:
            rep = {"status": "UNPARSEABLE_REPORT"}
    return {
        "probe": label, "env_change": {k: v for k, v in extra_env.items() if k not in ("PYTHONUTF8",)},
        "rc": rc, "seconds": round(time.time() - t0, 1),
        "status": (rep or {}).get("status", "NO_REPORT"),
        "assertions": (rep or {}).get("assertions"),
        "failed_rows": [f["id"] for f in (rep or {}).get("failures", [])],
        "failure_details_head": [f["detail"][:180] for f in (rep or {}).get("failures", [])][:3],
        "blocked_kinds": [b[0] if isinstance(b, list) else b for b in (rep or {}).get("blocked_kinds", [])],
        "captures": (rep or {}).get("captures"),
        "ends_in_PASS": (rep or {}).get("status") == "PASS" and rc == 0,
        "stderr_tail": (err or "")[-200:],
    }


def main():
    dead = "http://127.0.0.1:9"
    res = []
    res.append(run("1_only_GITHUB_starved", {
        "HTTPS_PROXY": dead, "https_proxy": dead, "HTTP_PROXY": dead, "http_proxy": dead,
        "NO_PROXY": "arxiv.org,export.arxiv.org,localhost,127.0.0.1", "no_proxy": "arxiv.org,export.arxiv.org"}))
    res.append(run("2_live_probe_binary_cannot_build", {
        "GOTMPDIR": os.path.join(REPO, ".local", "definitely-not-a-directory-%d" % os.getpid())}))
    res.append(run("3_source_kind_set_to_a_foreign_value", {"RESEARCHOS_SOURCE_KIND": "X"}))
    res.append(run("4_caller_pre_sets_output_dir", {
        "RESEARCHOS_SOURCE_OUTPUT_DIR": os.path.join(REPO, ".local", "reviewer_stale_output_dir")}))
    summary = {
        "probes": res,
        "any_probe_ended_in_PASS_with_a_missing_live_read": [
            r["probe"] for r in res
            if r.get("ends_in_PASS") and (not r.get("captures")
                                          or any((v or {}).get("status") != "PASS"
                                                 for v in (r.get("captures") or {}).values())
                                          or len(r.get("captures") or {}) < 2)],
        "all_probes": {r["probe"]: r.get("status") for r in res},
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
