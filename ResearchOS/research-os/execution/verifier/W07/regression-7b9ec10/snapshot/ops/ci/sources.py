#!/usr/bin/env python3
"""W07 fixture and real public-source construction probes; no acceptance self-signing."""
import hashlib
import json
import os
import signal
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "TestW07GitHubReleaseBodyAndCommit",
    "TestW07GitHubRateLimitAndUnsafeQuery",
    "TestW07GitHubFaultsDoNotCompleteWindow",
    "TestW07GitHubRejectsForeignRedirectBeforeRequest",
    "TestW07GitHubEmptyAuthAndTimeoutAreDistinct",
    "TestW07GitHubCursorKeepsPageSizeAndRejectsNull",
    "TestW07GitHubReadmePinnedPrimaryBody",
    "TestW07ArxivFullPDFAndVersion",
    "TestW07ArxivMetadataCannotPassForFullText",
    "TestW07ArxivChunkedPDFPrefixCannotPass",
    "TestW07ArxivRejectsForeignRedirectBeforeRequest",
    "TestW07ArxivErrorPageIsNotValidEmptyFeed",
    "TestW07XOnlyPublicPostAndNoFalseComplete",
    "TestW07XExpandedBodyRequired",
    "TestW07XVisibleEmptyDiffersFromUnrendered",
    "TestW07EvidenceNeedsSealedLiveSnapshotAndAllowedOrigin",
    "TestW07CursorDoesNotAdvanceFailedOrUnpersistedWindow",
    "TestW07HTTPSourceEvidenceAndDurableEmptyWindow",
    "TestW07RetryAfterPreventsPrematureSourceRequest",
    "TestW07Provider429PersistsRetryBeforeAnotherFetch",
    "TestW07MissingAuthorizedXChannelDoesNotFetch",
    "TestW07XVisibleEmptySealsObservationWithoutCoverage",
}
SOURCE_FILES = [
    "adapters/sources/sources.go", "adapters/sources/github.go",
    "adapters/sources/github_readme.go", "adapters/sources/arxiv.go", "adapters/sources/x.go",
    "internal/domain/sources.go", "tests/sources/live/main.go",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def run_process(command, evidence, stem, *, env=None, timeout=180):
    stdout, stderr = evidence / (stem + ".stdout"), evidence / (stem + ".stderr")
    opts = {"cwd": ROOT, "env": env, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if os.name == "nt":
        opts["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        opts["start_new_session"] = True
    try:
        process = subprocess.Popen(command, **opts)
    except OSError as exc:
        stdout.write_bytes(b"")
        stderr.write_text(str(exc) + "\n", encoding="utf-8")
        return -2, stdout, stderr, False
    timed_out = False
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as timeout_error:
        timed_out = True
        # Kill only this command's process tree (including a child BrowserAct
        # CLI), then retain whatever output was produced before timeout.
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=10, check=False)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        try:
            out, err = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = process.communicate()
        out = out or timeout_error.stdout or b""
        err = err or timeout_error.stderr or b""
    stdout.write_bytes(out)
    stderr.write_bytes(err)
    return (-1 if timed_out else process.returncode), stdout, stderr, timed_out


def fixture(go, evidence):
    command = [go, "test", "-count=1", "-json", "-run", "^TestW07", "./adapters/sources", "./internal/domain"]
    code, out, err, timed_out = run_process(command, evidence, "fixture")
    passed = set()
    for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("Action") == "pass" and event.get("Test") in EXPECTED:
            passed.add(event["Test"])
    return {
        "command": command, "exit_code": code, "timed_out": timed_out, "passed": sorted(passed),
        "missing": sorted(EXPECTED - passed),
        "raw": [str(out.relative_to(ROOT)), str(err.relative_to(ROOT))],
    }


def x_public_only(report):
    db = sqlite3.connect(ROOT / report["db_path"])
    try:
        artifact_id = report["raw_page"]["artifact_id"]
        raw = db.execute(
            "SELECT u.bytes FROM domain_objects d JOIN uploaded_content u "
            "ON u.storage_key=json_extract(d.body,'$.storage_key') "
            "WHERE d.kind='Artifact' AND d.id=?", (artifact_id,)
        ).fetchone()
        if not raw:
            return False, False
        page = json.loads(raw[0])
        public_keys = set(page) <= {"url", "items", "empty"} and all(
            set(item) <= {"url", "published_at", "text", "author"}
            for item in page.get("items", [])
        )
        item_id = report["items"][0]["evidence_id"]
        evidence = db.execute("SELECT body FROM domain_objects WHERE kind='Evidence' AND id=?", (item_id,)).fetchone()
        if not evidence:
            return public_keys, False
        evidence = json.loads(evidence[0])
        unverified = (evidence.get("stance") == "CONTEXT" and
                      evidence.get("verification_status") == "UNVERIFIED" and
                      evidence.get("origin_evidence_id") is None)
        return public_keys, unverified
    finally:
        db.close()


def x_claim_has_primary_lineage(report):
    """Check the sealed product graph and both bodies, not another source's item count."""
    linked = report.get("claim_check") or {}
    if not linked or linked.get("conclusion") != "SUPPORTED_NARROW_SCOPE" or linked.get("adoption_authority") is not False:
        return False
    db = sqlite3.connect(ROOT / report["db_path"])
    try:
        project = report["project_id"]

        def object_ref(ref, kind):
            if not isinstance(ref, dict) or ref.get("entity_type") != kind:
                raise ValueError("typed reference missing")
            row = db.execute("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?",
                             (project, kind, ref.get("id"))).fetchone()
            if row is None:
                raise ValueError("referenced object missing")
            body = json.loads(row[0])
            if body["revision"] != ref.get("revision") or body.get("content_hash") != ref.get("content_hash"):
                raise ValueError("reference revision or hash mismatch")
            return body

        def artifact_bytes(ref):
            artifact = object_ref(ref, "Artifact")
            row = db.execute("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=?",
                             (project, artifact["storage_key"])).fetchone()
            if row is None or "sha256:" + hashlib.sha256(row[0]).hexdigest() != ref["content_hash"]:
                raise ValueError("sealed content mismatch")
            return artifact, row[0]

        manifest_artifact, raw = artifact_bytes(linked["artifact_ref"])
        manifest = json.loads(raw)
        x_ref, primary_ref = manifest["x_evidence_ref"], manifest["primary_evidence_ref"]
        x = object_ref(x_ref, "Evidence")
        primary = object_ref(primary_ref, "Evidence")
        if {ref.get("id") for ref in manifest_artifact["source_refs"]} != {x_ref["id"], primary_ref["id"]}:
            return False
        if {ref.get("id") for ref in manifest_artifact["input_refs"]} != {x_ref["id"], primary_ref["id"]}:
            return False
        if x_ref["id"] != report["items"][0]["evidence_id"] or x["source_kind"] != "X" or primary["source_kind"] != "GITHUB":
            return False
        if x["origin_evidence_id"] is not None or primary["origin_evidence_id"] is not None:
            return False
        if x["stance"] != "CONTEXT" or x["verification_status"] != "UNVERIFIED":
            return False
        _, x_body = artifact_bytes(x["snapshot_artifact_ref"])
        _, primary_body = artifact_bytes(primary["snapshot_artifact_ref"])
        if b"paperclipai/paperclip" not in x_body.lower() or b"agent management" not in x_body.lower():
            return False
        excerpt = manifest["primary_excerpt"]
        if excerpt != "manage AI agents for work" or excerpt.casefold() not in primary_body.decode("utf-8").casefold():
            return False
        commit = manifest["primary_commit"]
        if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
            return False
        if manifest["primary_url"] != primary["canonical_url"] or not manifest["primary_url"].endswith("/blob/" + commit + "/README.md") or primary["upstream_revision"] != commit:
            return False
        if manifest["primary_snapshot_ref"] != primary["snapshot_artifact_ref"]:
            return False
        if manifest["adoption_authority"] is not False or not any("stars" in claim for claim in manifest["unverified_claims"]):
            return False
        return linked.get("artifact_ref") == manifest_artifact_ref(manifest_artifact)
    finally:
        db.close()


def manifest_artifact_ref(artifact):
    return {"entity_type": "Artifact", "id": artifact["id"],
            "revision": artifact["revision"], "content_hash": artifact["content_hash"]}


def live(go, evidence, fixture_result):
    reports, raw_refs, commands = {}, [], {}
    browser_act = os.getenv("RESEARCHOS_BROWSER_ACT", "")
    browser_id = os.getenv("RESEARCHOS_BROWSER_ID", "")
    if not browser_act or not Path(browser_act).is_file() or not browser_id:
        return {"status": "BLOCKED", "reason": "authorized BrowserAct tool/browser ID unavailable",
                "reports": reports, "raw": raw_refs, "commands": commands}
    binary = evidence / ("w07-live.exe" if os.name == "nt" else "w07-live")
    build_command = [go, "build", "-o", str(binary), "./tests/sources/live"]
    code, out, err, timed_out = run_process(build_command, evidence, "build", timeout=180)
    commands["BUILD"] = {"argv": build_command, "exit_code": code, "timed_out": timed_out}
    raw_refs.extend([str(out.relative_to(ROOT)), str(err.relative_to(ROOT))])
    if code != 0 or not binary.is_file():
        binary.unlink(missing_ok=True)
        return {"status": "FAIL", "reason": "live probe binary build failed",
                "reports": reports, "raw": raw_refs, "commands": commands}
    binary_hash = sha256(binary)
    try:
        for kind in ("GITHUB", "PAPER", "X"):
            env = os.environ.copy()
            env.update({"RESEARCHOS_SOURCE_KIND": kind,
                        "RESEARCHOS_SOURCE_OUTPUT_DIR": str(evidence)})
            command = [str(binary)]
            code, out, err, timed_out = run_process(command, evidence, kind.lower(), env=env, timeout=180)
            commands[kind] = {"argv": command, "exit_code": code, "timed_out": timed_out}
            raw_refs.extend([str(out.relative_to(ROOT)), str(err.relative_to(ROOT))])
            report_path = evidence / ("report-" + kind + ".json")
            if report_path.is_file():
                report = json.loads(report_path.read_text(encoding="utf-8"))
                reports[kind] = report
                raw_refs.append(str(report_path.relative_to(ROOT)))
            if code != 0 or kind not in reports or reports[kind].get("status") != "PASS":
                return {"status": "FAIL", "reason": kind + " live product capture failed",
                        "reports": reports, "raw": raw_refs, "commands": commands,
                        "live_binary_sha256": binary_hash}
    finally:
        binary.unlink(missing_ok=True)
    required = ("url", "author", "published_at", "retrieved_at", "upstream_revision",
                "body_sha256", "artifact_ref", "evidence_id")
    real_items = all(
        r.get("scope") == "LIVE_SERVICE" and r.get("cursor_id") and
        r.get("window_from") and r.get("window_to") and r.get("fetched_at") and
        r.get("request_urls") and r.get("final_urls") and r.get("manifest") and
        r.get("raw_page") and r.get("items") and
        all(item.get(field) for field in required for item in r["items"])
        for r in reports.values()
    )
    try:
        x_public, x_unverified = x_public_only(reports["X"])
        x_linked = x_claim_has_primary_lineage(reports["X"])
    except (OSError, sqlite3.Error, ValueError, KeyError) as exc:
        return {"status": "FAIL", "reason": "sealed X receipt inspection failed: " + str(exc),
                "reports": reports, "raw": raw_refs, "commands": commands,
                "live_binary_sha256": binary_hash}
    faults = fixture_result["exit_code"] == 0 and not fixture_result["missing"]
    assertions = {
        "A05-01": bool(real_items),
        "A05-02": bool(x_unverified and x_linked),
        "A05-03": bool(faults),
        "A05-04": bool(x_public and browser_act and browser_id),
    }
    for kind, r in reports.items():
        db_path = ROOT / r["db_path"]
        r["db_sha256"] = sha256(db_path) if db_path.is_file() else None
        r["item_count"] = len(r["items"])
        # Final summary is compact; full public metadata stays in report-KIND.json.
        r["items"] = r["items"][:1]
    return {"status": "PASS" if all(assertions.values()) else "FAIL",
            "assertions": assertions, "reports": reports, "raw": raw_refs,
            "commands": commands, "live_binary_sha256": binary_hash,
            "x_primary_context_url": reports["X"].get("claim_check", {}).get("primary_url"),
            "x_claim_narrowly_supported": bool(x_linked), "x_adoption_authority": False}


def main():
    task, check, case = (os.getenv("RESEARCHOS_TASK_ID", "W07"),
                         os.getenv("RESEARCHOS_CHECK_ID", ""),
                         os.getenv("RESEARCHOS_CASE_ID", ""))
    mode = os.getenv("RESEARCHOS_SOURCE_MODE", "")
    if task != "W07" or check not in {"W07-G01", "W07-G02", ""} or case not in {"", "A05"}:
        raise NotImplementedError("unbound W07 selection")
    if mode == "fixture":
        if check != "W07-G01" or case:
            raise NotImplementedError("fixture command requires W07-G01")
    elif mode == "live":
        if check not in {"", "W07-G02"} or (not check and case != "A05"):
            raise NotImplementedError("live command requires W07-G02 or A05")
    else:
        raise NotImplementedError("registered W07 source mode required")
    go = os.getenv("RESEARCHOS_GO") or json.loads(
        (ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8")
    )["tools"]["go"]["path"]
    if not Path(go).is_file():
        raise FileNotFoundError("pinned Go executable unavailable")
    before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    evidence = ROOT / "execution/receipts/W07" / ("run-" + uuid.uuid4().hex)
    evidence.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    fr = fixture(go, evidence)
    selected_live = mode == "live"
    result = live(go, evidence, fr) if selected_live and not fr["missing"] and fr["exit_code"] == 0 else None
    if selected_live:
        ids = [k for k, value in (result or {}).get("assertions", {}).items() if value]
        status = (result or {}).get("status", "FAIL")
    else:
        ids = fr["passed"]
        status = "PASS" if fr["exit_code"] == 0 and not fr["missing"] else "FAIL"
    report = {
        "status": status, "scope": "LIVE_SERVICE" if selected_live else "FIXTURE",
        "task_id": task, "check_id": check or None, "case_id": case or None,
        "assertions": len(ids), "assertion_ids": sorted(ids), "expected_assertion_ids":
            ["A05-01", "A05-02", "A05-03", "A05-04"] if selected_live else sorted(EXPECTED),
        "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(),
        "execution_head": before, "dirty_before": dirty,
        "source_hashes": {name: sha256(ROOT / name) for name in SOURCE_FILES},
        "browser_act_sha256": sha256(os.getenv("RESEARCHOS_BROWSER_ACT"))
            if selected_live and os.getenv("RESEARCHOS_BROWSER_ACT") and Path(os.getenv("RESEARCHOS_BROWSER_ACT")).is_file() else None,
        "fixture": fr, "live": result, "owned_acceptance_ids": ["A05"] if selected_live else [],
        "formal_product_acceptance": "PENDING_INDEPENDENT_REVIEW" if selected_live else "NOT_RUN",
        "raw_evidence_references": fr["raw"] + ((result or {}).get("raw", [])),
    }
    (evidence / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        outcome = main()
    except Exception as exc:
        outcome = {"status": "NOT_IMPLEMENTED" if isinstance(exc, NotImplementedError) else "FAIL",
                   "assertions": 0, "assertion_ids": [], "error": str(exc)}
    print(json.dumps(outcome, ensure_ascii=False))
    sys.exit(0 if outcome["status"] == "PASS" and outcome["assertions"] > 0 else 1)
