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
from pathlib import Path, PurePosixPath, PureWindowsPath

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
    "TestW07OfflineXPrimaryClaimSealsProductLineage",
    "TestW07HealthForgedReportCannotCompleteWindow",
    "TestW07HealthPublicIngressCannotForgeCapturedSource",
    "TestW07HealthH07ProductionFaultMatrix",
    "TestW07HealthDetailPrecedesSuccessfulEnvelope",
    "TestW07HealthEmptyProofAndIndexReadLevel",
    "TestW07HealthUnavailableClassification",
    "TestW07PRDetailStatesAndIndexRejection",
    "TestW07HealthDurableFaultsExactWindowAndReplay",
    "TestW07HealthPartialPrefixNoProviderCursorAndNoFalseComplete",
    "TestW07HealthCASAndUnconfiguredResourceDedup",
    "TestW07HealthRealCyclePartialProgressAndIndependentSources",
    "TestW07HealthBoundPartialEffectRemainsConfirmed",
    "TestW07HealthFailureBeforeCommitStaysUnresolved",
    "TestW07XUncorroboratedDispositionSealed",

}
SOURCE_FILES = [
    "adapters/sources/sources.go", "adapters/sources/github.go",
    "adapters/sources/github_readme.go", "adapters/sources/arxiv.go", "adapters/sources/x.go",
    "internal/domain/sources.go", "tests/sources/live/main.go", "tests/sources/live/main_test.go",
    "adapters/sources/health.go", "adapters/sources/github_pr.go", "internal/domain/sources_health.go",
    "internal/domain/research.go", "internal/domain/research_acceptance.go", "internal/domain/research_source_windows.go",
    "ops/ci/sources.py", "tests/sources/check/main.py",
]

# Include the full compiled source packages and gates, including their tests.
SOURCE_FILES = sorted(set(SOURCE_FILES) | {
    str(p.relative_to(ROOT)).replace("\\", "/")
    for pattern in ("adapters/sources/*.go", "internal/domain/*.go", "tests/sources/live/*.go", "tests/sources/check/*.py", "internal/store/*.go", "migrations/sqlite/*.sql", "spec/v2.0/contracts/*", "go.mod", "go.sum")
    for p in ROOT.glob(pattern)
})


def fixture_ok(result):
    return result.get("exit_code") == 0 and not result.get("timed_out") and not result.get("missing") and set(result.get("passed", [])) == EXPECTED



def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def prepare_go_environment():
    # Native dispatch filters inherited cache variables. Both collection modes
    # must therefore derive the same project-owned defaults before Go runs.
    for name, directory in (("GOPATH", "gopath"), ("GOCACHE", "gocache")):
        if not os.environ.get(name):
            os.environ[name] = str(ROOT / ".local" / directory)


def run_process(command, evidence, stem, *, env=None, timeout=180):
    started = datetime.now(timezone.utc).isoformat()
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
    code = -1 if timed_out else process.returncode
    invocation = {"actualargv": command, "cwd": str(ROOT), "exit_code": code,
                  "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(), "timed_out": timed_out,
                  "stdout_ref": file_ref(stdout), "stderr_ref": file_ref(stderr)}
    (evidence / (stem + ".invocation.json")).write_text(json.dumps(invocation, indent=2) + "\n", encoding="utf-8")
    return code, stdout, stderr, timed_out


def fixture(go, evidence):
    command = [go, "test", "-count=1", "-json", "-run", "^TestW07", "./adapters/sources", "./internal/domain", "./tests/sources/live"]
    code, out, err, timed_out = run_process(command, evidence, "fixture", env=dict(os.environ, W07_EVIDENCE_DIR=str(evidence / "h07-db")))
    passed = set()
    for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("Action") == "pass" and event.get("Test") in EXPECTED:
            passed.add(event["Test"])
    parent_command = [sys.executable, "-B", "-X", "utf8", "tests/sources/check/parent_gate_test.py"]
    parent_code, parent_out, parent_err, parent_timeout = run_process(parent_command, evidence, "parent-unit")
    return {
        "command": command, "exit_code": code if code else parent_code, "timed_out": timed_out or parent_timeout, "passed": sorted(passed),
        "missing": sorted(EXPECTED - passed), "parent_unit": {"measurement_mode": "FIXTURE", "actualargv": parent_command, "exit_code": parent_code},
        "raw": [str(out.relative_to(ROOT)), str(err.relative_to(ROOT)), str(parent_out.relative_to(ROOT)), str(parent_err.relative_to(ROOT))],
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
    if not linked or linked.get("conclusion") not in {"SUPPORTED_NARROW_SCOPE", "NOT_CORROBORATED"} or linked.get("adoption_authority") is not False:
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
        if manifest.get("conclusion") != linked.get("conclusion") or manifest.get("adoption_authority") is not False:
            return False
        if linked.get("x_evidence_ref") != manifest.get("x_evidence_ref") or linked.get("primary_evidence_ref") != manifest.get("primary_evidence_ref"):
            return False
        if manifest.get("conclusion") == "NOT_CORROBORATED":
            x_ref = manifest["x_evidence_ref"]
            x = object_ref(x_ref, "Evidence")
            _, body = artifact_bytes(x["snapshot_artifact_ref"])
            return bool(body and manifest.get("reason") and manifest.get("primary_evidence_ref") is None and
                        manifest.get("x_snapshot_ref") == x["snapshot_artifact_ref"] and
                        x_ref["id"] in {item["evidence_id"] for item in report["items"]} and
                        x.get("source_kind") == "X" and x.get("stance") == "CONTEXT" and
                        x.get("verification_status") == "UNVERIFIED" and
                        manifest_artifact["input_refs"] == [x_ref] and manifest_artifact["source_refs"] == [x_ref])
        x_ref, primary_ref = manifest["x_evidence_ref"], manifest["primary_evidence_ref"]
        x = object_ref(x_ref, "Evidence")
        primary = object_ref(primary_ref, "Evidence")
        if {ref.get("id") for ref in manifest_artifact["source_refs"]} != {x_ref["id"], primary_ref["id"]}:
            return False
        if {ref.get("id") for ref in manifest_artifact["input_refs"]} != {x_ref["id"], primary_ref["id"]}:
            return False
        if x_ref["id"] not in {item["evidence_id"] for item in report["items"]} or x["source_kind"] != "X" or primary["source_kind"] != "GITHUB":
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
        claims = manifest["unverified_claims"]
        fallback = "Any X growth, usage or effectiveness claim is unverified without its own primary source."
        if manifest["adoption_authority"] is not False or not isinstance(claims, list) or not claims or not all(
            isinstance(claim, str) and (claim in x_body.decode("utf-8") or claim == fallback) for claim in claims
        ):
            return False
        return linked.get("artifact_ref") == manifest_artifact_ref(manifest_artifact)
    finally:
        db.close()


def manifest_artifact_ref(artifact):
    return {"entity_type": "Artifact", "id": artifact["id"],
            "revision": artifact["revision"], "content_hash": artifact["content_hash"]}


def validate_source_report(report):
    """Read closed SQLite bytes and exact references; JSON presence is not proof."""
    try:
        if report.get("scope") != "LIVE_SERVICE" or not report.get("items"):
            return False
        db = sqlite3.connect("file:" + str((ROOT / report["db_path"]).resolve()).replace("\\", "/") + "?mode=ro", uri=True)
        try:
            project = report["project_id"]
            def obj(kind, id):
                row = db.execute("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?", (project, kind, id)).fetchone()
                if not row: raise ValueError("missing object")
                return json.loads(row[0])
            def body(a):
                row = db.execute("SELECT bytes,sealed FROM uploaded_content WHERE project=? AND storage_key=?", (project,a["storage_key"])).fetchone()
                if not row or row[1] != 1 or "sha256:" + hashlib.sha256(row[0]).hexdigest() != a["content_hash"]: raise ValueError("bad sealed bytes")
                return row[0]
            cursor = obj("SourceCursor",report["cursor_id"])
            if cursor["source_id"] != report["source_id"]: return False
            health_a = obj("Artifact",report["health_artifact_ref"]["id"])
            if manifest_artifact_ref(health_a) != report["health_artifact_ref"] or health_a["kind"] != "REPORT": return False
            health = json.loads(body(health_a))
            if health["schema"] != "researchos.source-health.v1" or health["source_id"] != report["source_id"] or health["query_hash"] != cursor["query_hash"] or health["health"] != report["health"]: return False
            page_a = obj("Artifact",report["manifest"]["artifact_id"])
            page = json.loads(body(page_a))
            if page_a["content_hash"] != report["manifest"]["sha256"] or page["source_id"] != report["source_id"] or page["query_hash"] != cursor["query_hash"] or page["window_from"] != report["window_from"] or page["window_to"] != report["window_to"]: return False
            raw_a = obj("Artifact",report["raw_page"]["artifact_id"]); body(raw_a)
            if raw_a["content_hash"] != report["raw_page"]["sha256"] or page["raw_artifact_ref"] != manifest_artifact_ref(raw_a): return False
            for item in report["items"]:
                ev = obj("Evidence",item["evidence_id"])
                if ev["source_kind"] != report["source"] or ev["canonical_url"] != item["url"] or ev["publisher"] != item["author"] or ev["upstream_revision"] != item["upstream_revision"] or ev["published_at"] != item["published_at"] or ev["snapshot_artifact_ref"] != item["artifact_ref"]: return False
                if domain_ref(ev,"Evidence") not in page["evidence_refs"]: return False
                if not any(meta.get("source_id")==report["source_id"] and meta.get("upstream_id")==item["upstream_id"] and meta.get("canonical_url")==item["url"] and meta.get("body_sha256")==item["body_sha256"] and meta.get("read_level")!="INDEX" for meta in page.get("item_metadata",[])): return False
                a = obj("Artifact",item["artifact_ref"]["id"]); b = body(a)
                if manifest_artifact_ref(a) != item["artifact_ref"] or not b or a["content_hash"] != item["body_sha256"]: return False
            if report["page_complete"] is not True and cursor["covered_until"] is not None: return False
            if report["health"]["full_read_count"] != len(report["items"]): return False
            return True
        finally: db.close()
    except (KeyError,ValueError,TypeError,OSError,sqlite3.Error):
        return False


def domain_ref(obj,kind):
    return {"entity_type":kind,"id":obj["id"],"revision":obj["revision"],"content_hash":obj.get("content_hash")}


def live(go, evidence, fixture_result):
    reports, raw_refs, commands = {}, [], {}
    browser_act = os.getenv("RESEARCHOS_BROWSER_ACT", "")
    browser_id = os.getenv("RESEARCHOS_BROWSER_ID", "")
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
    finally:
        binary_after = sha256(binary) if binary.is_file() else None
        # Retain the exact executed binary as immutable evidence.
    if binary_after != binary_hash:
        return {"status":"FAIL","reason":"live binary drift","reports":reports,"raw":raw_refs,"commands":commands}
    unavailable = [kind for kind in ("GITHUB", "PAPER", "X") if
                   commands.get(kind, {}).get("exit_code") != 0 or reports.get(kind, {}).get("status") != "PASS"]
    if unavailable:
        return {"status": "BLOCKED", "reason": "required source captures unavailable: " + ", ".join(unavailable),
                "reports": reports, "raw": raw_refs, "commands": commands, "live_binary_sha256": binary_hash,
                "assertions": {"A05-0" + str(n): False for n in range(1, 6)}}
    required = ("url", "author", "published_at", "retrieved_at", "upstream_revision",
                "body_sha256", "artifact_ref", "evidence_id")
    real_items = all(
        validate_source_report(r) and r.get("scope") == "LIVE_SERVICE" and r.get("cursor_id") and
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
    faults = fixture_ok(fixture_result) and verify_h07_evidence(evidence)
    assertions = {
        "A05-01": bool(real_items),
        "A05-02": bool(x_unverified and x_linked),
        "A05-03": bool(faults),
        "A05-04": bool(x_public and browser_act and browser_id),
        "A05-05": bool(faults and all(validate_source_report(r) for r in reports.values())),
    }
    for kind, r in reports.items():
        db_path = ROOT / r["db_path"]
        r["db_sha256"] = sha256(db_path) if db_path.is_file() else None
        r["item_count"] = len(r["items"])
        # Final summary is compact; full public metadata stays in report-KIND.json.
        # Preserve the complete selected-item graph; index zero is not special.
    return {"status": "PASS" if all(assertions.values()) else "FAIL",
            "assertions": assertions, "reports": reports, "raw": raw_refs,
            "commands": commands, "live_binary_sha256": binary_hash, "live_binary_sha256_after": binary_after, "live_binary_ref": file_ref(binary),
            "x_primary_context_url": reports["X"].get("claim_check", {}).get("primary_url"),
            "x_claim_narrowly_supported": bool(x_linked), "x_adoption_authority": False}


def file_ref(path):
    return {"path": str(Path(path).relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(path)}


def typed_h07_rows(evidence):
    # test2json may split one long stdout line across multiple Output events.
    streams={}
    for line in (evidence / "fixture.stdout").read_text(encoding="utf-8").splitlines():
        try:
            event=json.loads(line)
            key=(event.get("Package"),event.get("Test"))
            streams[key]=streams.get(key,"")+event.get("Output","")
        except (ValueError,TypeError): pass
    rows=[]
    for output in streams.values():
        for line in output.splitlines():
            if line.startswith("H07_ASSERTION "):
                try:
                    row=json.loads(line[len("H07_ASSERTION "):])
                    if row.get("db_snapshot_path"): rows.append(row)
                except ValueError: pass
    return rows


def h07_snapshot_paths(evidence, rows, proof):
    """Map recorded paths using one proof-bound invocation; never open its old cwd."""
    evidence = evidence.resolve()
    collection = evidence.relative_to(ROOT.resolve())
    invocations = proof["h07_invocations"]
    if len(invocations) != 1 or proof["run_id"] != evidence.name:
        raise ValueError("one H07 invocation for this collection required")
    invocation = invocations[0]
    if invocation.get("measurement_mode") != "INJECTED" or invocation.get("exit_code") != 0 or invocation.get("timed_out") is not False:
        raise ValueError("successful injected H07 invocation required")
    for field, name in (("stdout_ref", "fixture.stdout"), ("stderr_ref", "fixture.stderr"), ("assertions_ref", "h07-assertions.json")):
        if invocation[field] != file_ref(evidence / name):
            raise ValueError("H07 raw reference differs from this collection")
    if json.loads((evidence / "h07-assertions.json").read_text(encoding="utf-8")) != rows:
        raise ValueError("typed assertions differ from original stdout")
    cwd = invocation["cwd"]
    flavor = PureWindowsPath if PureWindowsPath(cwd).drive else PurePosixPath
    original_root = flavor(cwd)
    if not original_root.is_absolute() or ".." in original_root.parts:
        raise ValueError("absolute recorded invocation cwd required")
    original_collection = original_root.joinpath(*collection.parts)
    snapshots = {}
    for ref in invocation["db_snapshots"]:
        relative = PurePosixPath(ref["path"])
        if relative.is_absolute() or PureWindowsPath(ref["path"]).drive or ".." in relative.parts or "\\" in ref["path"]:
            raise ValueError("repository-relative snapshot reference required")
        target = (ROOT / Path(*relative.parts)).resolve()
        suffix = target.relative_to(evidence)
        if len(suffix.parts) != 2 or suffix.parts[0] != "h07-db" or target.suffix != ".sqlite" or target in snapshots:
            raise ValueError("duplicate or foreign H07 snapshot")
        if ref != file_ref(target):
            raise ValueError("H07 snapshot bytes changed")
        snapshots[target] = ref
    mapped = {}
    seen = set()
    for row in rows:
        recorded = flavor(row["db_snapshot_path"])
        if not recorded.is_absolute() or ".." in recorded.parts:
            raise ValueError("absolute captured snapshot path required")
        suffix = recorded.relative_to(original_collection)
        target = (evidence / Path(*suffix.parts)).resolve()
        if target not in snapshots or target in seen:
            raise ValueError("unlisted or duplicate captured snapshot")
        seen.add(target)
        mapped[row["id"]] = target
    if seen != set(snapshots):
        raise ValueError("H07 snapshot inventory is not closed")
    return mapped


def verify_h07_evidence(evidence, proof=None):
    expected={"not_configured":"NOT_CONFIGURED","429":"RATE_LIMITED","401_or_revoked":"UNAVAILABLE","timeout":"PARTIAL","empty_valid_result":"COMPLETE","visible_empty":"PARTIAL","index_only":"PARTIAL","pr_open":"COMPLETE","pr_closed_unmerged":"COMPLETE","pr_merged":"COMPLETE"}
    try:
        typed_rows = typed_h07_rows(evidence)
        rows = {r["id"]: r for r in typed_rows}
        if len(rows) != len(typed_rows) or set(rows) != set(expected)|{"cycle_partial","effect_confirmed","effect_unresolved"}: return False
        mapped = h07_snapshot_paths(evidence, typed_rows, proof) if proof is not None else None
        seen = set()
        for name,row in rows.items():
            if row.get("measurement_mode") != "INJECTED" or row.get("db_closed_or_vacuum_snapshot") is not True: return False
            path=mapped[name] if mapped is not None else Path(row["db_snapshot_path"]).resolve()
            if not path.is_relative_to((evidence / "h07-db").resolve()) or path in seen: return False
            seen.add(path)
            db=sqlite3.connect(path.as_uri()+"?mode=ro&immutable=1",uri=True)
            try:
                actual=row["actual"];project=row["project_id"]
                if name in expected:
                    ref=actual["health_artifact_ref"]
                    raw=db.execute("SELECT a.body,u.bytes FROM domain_objects a JOIN uploaded_content u ON u.project=a.project AND u.storage_key=json_extract(a.body,'$.storage_key') WHERE a.project=? AND a.kind='Artifact' AND a.id=? AND u.sealed=1",(project,ref["id"])).fetchone()
                    if raw is None or domain_ref(json.loads(raw[0]),"Artifact") != ref or "sha256:"+hashlib.sha256(raw[1]).hexdigest()!=ref["content_hash"]: return False
                    h=json.loads(raw[1])["health"]
                    if h!=actual["health"] or h["status"]!=expected[name]: return False
                    if name=="timeout" and (h["reason"]!="page_timeout" or h["provider_result"]!={"exit_code":0,"status":"ok","detail_errors":["page_timeout"]}): return False
                    if name in {"empty_valid_result","visible_empty","index_only"} and h["full_read_count"]!=0: return False
                    if name=="visible_empty" and h["exhaustive"] is not False: return False
                    c=json.loads(db.execute("SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor' AND id=?",(project,actual["cursor"]["id"])).fetchone()[0])
                    if c!=actual["cursor"] or c["covered_until"] is not None: return False
                    if name=="429" and not c["retry_after"]: return False
                elif name=="cycle_partial":
                    cycle=json.loads(db.execute("SELECT body FROM domain_objects WHERE project=? AND kind='ResearchCycle' AND id=?",(project,actual["cycle"]["id"])).fetchone()[0])
                    if cycle!=actual["cycle"] or cycle["status"]!="PARTIAL": return False
                elif name in {"effect_confirmed","effect_unresolved"}:
                    effect=json.loads(db.execute("SELECT body FROM resource_effects WHERE project=? AND effect_key=? ORDER BY sequence DESC LIMIT 1",(project,row["input"]["effect_key"])).fetchone()[0])
                    if effect!=actual["effect"] or effect["state"] != ("CONFIRMED" if name=="effect_confirmed" else "UNKNOWN"): return False
            finally: db.close()
        return True
    except (KeyError,ValueError,TypeError,OSError,sqlite3.Error): return False


def write_product_proof(evidence, report, go):
    h07 = typed_h07_rows(evidence)
    (evidence / "h07-assertions.json").write_text(json.dumps(h07, indent=2) + "\n", encoding="utf-8")
    inputs = ROOT / "execution/toolchains/locked.json"
    vector = {"spec": {}, "source": report["source_hashes"], "input": {},
              "lock": {str(inputs.relative_to(ROOT)): sha256(inputs)},
              "tool": {"go": {"path": go, "sha256": sha256(go)}}}
    spec = Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4")
    for name in ("contracts/acceptance.json", "contracts/tasks.json", "contracts/harness.contract.json", "tasks/steps/W07-99.md"):
        vector["spec"][name] = sha256(spec / name)
    browser = os.getenv("RESEARCHOS_BROWSER_ACT")
    if browser and Path(browser).is_file(): vector["tool"]["browser_act"] = {"path": browser, "sha256": sha256(browser)}
    live_result = report.get("live") or {}
    source_invocations = []
    for kind, source_report in live_result.get("reports", {}).items():
        invocation_path = evidence / (kind.lower() + ".invocation.json")
        if not invocation_path.is_file(): continue
        invocation = json.loads(invocation_path.read_text(encoding="utf-8"))
        request = {"source_id": source_report.get("source_id"), "kind": kind, "query": source_report.get("query"),
                   "window_from": source_report.get("window_from"), "window_to": source_report.get("window_to"),
                   "browser_id": os.getenv("RESEARCHOS_BROWSER_ID") if kind == "X" else None}
        request_path = evidence / (kind.lower() + "-inputs.json")
        request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
        vector["input"][str(request_path.relative_to(ROOT)).replace("\\", "/")] = sha256(request_path)
        invocation.update({"kind": kind, "measurement_mode": "LIVE_SERVICE", "report_ref": file_ref(evidence / ("report-" + kind + ".json")),
                           "db_snapshot_ref": file_ref(ROOT / source_report["db_path"]), "db_closed_or_vacuum_snapshot": True,
                           "request_inputs_ref": file_ref(request_path)})
        source_invocations.append(invocation)
    vector_path = evidence / "version-vector.json"
    vector_path.write_text(json.dumps(vector, indent=2) + "\n", encoding="utf-8")
    acceptance = json.loads((spec / "contracts/acceptance.json").read_text(encoding="utf-8"))
    def find_case(value):
        if isinstance(value, dict):
            if value.get("id") == "A05" and "assertions" in value: return value
            for v in value.values():
                result = find_case(v)
                if result: return result
        if isinstance(value, list):
            for v in value:
                result = find_case(v)
                if result: return result
    case = find_case(acceptance)
    assertion_rows = [{"id": a["id"], "expected": a["expected"], "actual": {"source_count": len(source_invocations), "source_reports": live_result.get("reports", {}), "h07_rows": h07},
                       "status": "PASS" if live_result.get("assertions", {}).get(a["id"]) is True else "BLOCKED",
                       "raw_evidence_refs": [dict(file_ref(evidence / "h07-assertions.json"), locator={"json_pointer": ""})] +
                           [dict(inv["report_ref"], locator={"json_pointer": ""}) for inv in source_invocations]} for a in case["assertions"]]
    fixture_invocation = json.loads((evidence / "fixture.invocation.json").read_text(encoding="utf-8"))
    fixture_invocation.update({"measurement_mode": "INJECTED", "assertions_ref": file_ref(evidence / "h07-assertions.json"),
                              "db_snapshots": [file_ref(Path(row["db_snapshot_path"])) for row in h07 if row.get("db_snapshot_path")]})
    proof = {"schema": "researchos.w07.product-proof.v1", "run_id": evidence.name, "task_id": "W07", "step_id": "W07-99",
             "executor_id": "codex:/root/sources_parent_impl", "mode": report["scope"], "started_at": report["started_at"], "ended_at": report["ended_at"],
             "version_vector_ref": file_ref(vector_path), "source_before_ref": file_ref(evidence / "source-before.json"),
             "source_after_ref": file_ref(evidence / "source-after.json"), "source_invocations": source_invocations, "compilation_inputs_ref": file_ref(evidence / "go-list.stdout"), "build_invocation_ref": file_ref(evidence / "build.invocation.json") if (evidence / "build.invocation.json").is_file() else None, "live_binary_ref": live_result.get("live_binary_ref"),
             "h07_invocations": [fixture_invocation], "assertion_rows": assertion_rows,
             "gate_rows": [{"id": "W07-G01", "status": "PASS" if fixture_ok(report["fixture"]) else "FAIL", "actual": report["fixture"]},
                           {"id": "W07-G02", "status": live_result.get("status", "NOT_RUN"), "actual": {"sources": len(source_invocations)}},
                           {"id": "W07-H07", "status": "PASS" if fixture_ok(report["fixture"]) and live_result.get("status") == "PASS" else "BLOCKED", "actual": {"typed_rows": len(h07)}}]}
    proof_path = evidence / "proof.json"
    proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["product_proof_ref"] = file_ref(proof_path)


def replay_product_proof(path, task, check, case):
    path=(ROOT / path).resolve()
    allowed=(ROOT / "execution/v2.4/receipts/W07/W07-99/source_executor_codex").resolve()
    if not path.is_relative_to(allowed): raise ValueError("proof must be within this task receipt namespace")
    proof=json.loads(path.read_text(encoding="utf-8"))
    if proof.get("schema")!="researchos.w07.product-proof.v1" or proof.get("task_id")!="W07" or proof.get("mode")!="LIVE_SERVICE": raise ValueError("current LIVE source proof required")
    def verify_refs(value):
        if isinstance(value,dict):
            if "path" in value and "sha256" in value:
                ref=(ROOT/value["path"]).resolve()
                if not ref.is_relative_to(ROOT) or not ref.is_file() or sha256(ref)!=value["sha256"]: raise ValueError("missing or changed proof reference: "+value["path"])
            for child in value.values(): verify_refs(child)
        elif isinstance(value,list):
            for child in value: verify_refs(child)
    verify_refs(proof)
    before=json.loads((ROOT/proof["source_before_ref"]["path"]).read_text(encoding="utf-8"))
    after=json.loads((ROOT/proof["source_after_ref"]["path"]).read_text(encoding="utf-8"))
    if before!=after or not set(SOURCE_FILES)<=set(before) or any(sha256(ROOT/name)!=digest for name,digest in before.items()): raise ValueError("proof product source drift")
    original=json.loads((path.parent/"report.json").read_text(encoding="utf-8"))
    if original.get("product_proof_ref")!=file_ref(path) or not fixture_ok(original.get("fixture",{})) or not verify_h07_evidence(path.parent, proof): raise ValueError("missing current fixture and typed H07 evidence")
    for name,digest in original["raw_hashes"].items():
        if sha256(ROOT/name)!=digest: raise ValueError("raw command output changed")
    vector=json.loads((ROOT/proof["version_vector_ref"]["path"]).read_text(encoding="utf-8"))
    for tool in vector["tool"].values():
        if sha256(tool["path"])!=tool["sha256"]: raise ValueError("pinned tool changed")
    reports={}
    for invocation in proof["source_invocations"]:
        if invocation["measurement_mode"]!="LIVE_SERVICE" or invocation["exit_code"]!=0 or not invocation["db_closed_or_vacuum_snapshot"]: raise ValueError("injected or failed positive")
        kind=invocation["kind"]
        if kind in reports: raise ValueError("duplicate source positive")
        r=json.loads((ROOT/invocation["report_ref"]["path"]).read_text(encoding="utf-8"))
        if not validate_source_report(r): raise ValueError("sealed source graph failed: "+kind)
        inputs=json.loads((ROOT/invocation["request_inputs_ref"]["path"]).read_text(encoding="utf-8"))
        if kind=="X" and inputs["browser_id"]!=os.getenv("RESEARCHOS_BROWSER_ID"): raise ValueError("authorized channel identity changed")
        reports[kind]=r
    if set(reports)!={"GITHUB","PAPER","X"}: raise ValueError("three independent source captures required")
    if not all(x_public_only(reports["X"])) or not x_claim_has_primary_lineage(reports["X"]): raise ValueError("X public withholding/provenance failed")
    if len(proof["assertion_rows"]) != 5 or {row["id"] for row in proof["assertion_rows"]}!={"A05-0"+str(n) for n in range(1,6)} or any(row["status"]!="PASS" for row in proof["assertion_rows"]): raise ValueError("all five current assertion rows required")
    ids=[check] if check else ["A05-0"+str(n) for n in range(1,6)]
    result={"status":"PASS","task_id":task,"check_id":check or None,"case_id":case or None,"scope":"LIVE_SERVICE","assertion_ids":ids,"expected_assertion_ids":ids,"assertions":len(ids),"product_proof_ref":file_ref(path),"replay":"READ_ONLY_CURRENT_PROOF","formal_product_acceptance":"PENDING_INDEPENDENT_REVIEW"}
    receipt=allowed/("selector-"+uuid.uuid4().hex+".json")
    receipt.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


def main():
    task, check, case = (os.getenv("RESEARCHOS_TASK_ID", "W07"),
                         os.getenv("RESEARCHOS_CHECK_ID", ""),
                         os.getenv("RESEARCHOS_CASE_ID", ""))
    mode = os.getenv("RESEARCHOS_SOURCE_MODE", "")
    if (check and case) or task != "W07" or check not in {"W07-G01", "W07-G02", "W07-H07", ""} or case not in {"", "A05"}:
        raise NotImplementedError("unbound W07 selection")
    if mode == "fixture":
        if check != "W07-G01" or case:
            raise NotImplementedError("fixture command requires W07-G01")
    elif mode == "live":
        if check not in {"", "W07-G02", "W07-H07"} or (not check and case != "A05"):
            raise NotImplementedError("live command requires W07-G02 or A05")
    else:
        raise NotImplementedError("registered W07 source mode required")
    if proof_path := os.getenv("RESEARCHOS_W07_PROOF_REF"):
        return replay_product_proof(proof_path, task, check, case)
    go = os.getenv("RESEARCHOS_GO") or json.loads(
        (ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8")
    )["tools"]["go"]["path"]
    if not Path(go).is_file():
        raise FileNotFoundError("pinned Go executable unavailable")
    prepare_go_environment()
    before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    evidence = ROOT / "execution/v2.4/receipts/W07/W07-99/source_executor_codex" / ("run-" + uuid.uuid4().hex)
    evidence.mkdir(parents=True, exist_ok=False)
    env_code, env_out, _, env_timeout = run_process(
        [go, "env", "-json", "GOPATH", "GOCACHE", "GOMODCACHE", "GOROOT", "GOTOOLCHAIN", "GOENV"], evidence, "go-env")
    if env_code != 0 or env_timeout: raise ValueError("cannot record actual Go environment")
    go_environment = json.loads(env_out.read_text(encoding="utf-8"))
    dep_command = [go, "list", "-deps", "-json", "./tests/sources/live"]
    dep_code, dep_out, dep_err, dep_timeout = run_process(dep_command, evidence, "go-list")
    if dep_code != 0 or dep_timeout: raise ValueError("cannot freeze actual compiled package dependencies")
    decoder = json.JSONDecoder(); data = dep_out.read_text(encoding="utf-8"); offset = 0; local_files = set()
    while offset < len(data):
        while offset < len(data) and data[offset].isspace(): offset += 1
        if offset >= len(data): break
        package, offset = decoder.raw_decode(data, offset)
        directory = Path(package.get("Dir", "")).resolve()
        if directory.is_relative_to(ROOT):
            for field in ("GoFiles", "CgoFiles", "EmbedFiles"):
                for name in package.get(field, []):
                    local_files.add(str((directory / name).relative_to(ROOT)).replace("\\", "/"))
            # Freeze every current project package source, including tests and
            # platform variants that this host's GoFiles selection excludes.
            if directory.relative_to(ROOT).parts[:1] != (".local",):
                local_files.update(path.relative_to(ROOT).as_posix()
                                   for path in directory.glob("*.go") if path.is_file())
    SOURCE_FILES[:] = sorted(set(SOURCE_FILES) | local_files)
    source_before = {name: sha256(ROOT / name) for name in SOURCE_FILES}
    tool_before = {"go": sha256(go), "browser_act": sha256(browser_act) if (browser_act := os.getenv("RESEARCHOS_BROWSER_ACT")) and Path(browser_act).is_file() else None}
    started = datetime.now(timezone.utc).isoformat()
    (evidence / "source-before.json").write_text(json.dumps(source_before, indent=2) + "\n", encoding="utf-8")
    fr = fixture(go, evidence)
    selected_live = mode == "live"
    result = live(go, evidence, fr) if selected_live and fixture_ok(fr) else None
    if selected_live:
        ids = [k for k, value in (result or {}).get("assertions", {}).items() if value]
        status = (result or {}).get("status", "FAIL")
    else:
        ids = fr["passed"]
        status = "PASS" if fixture_ok(fr) else "FAIL"
    report = {
        "status": status, "scope": "LIVE_SERVICE" if selected_live else "FIXTURE",
        "task_id": task, "check_id": check or None, "case_id": case or None,
        "assertions": len(ids), "assertion_ids": sorted(ids), "expected_assertion_ids":
            ["A05-01", "A05-02", "A05-03", "A05-04", "A05-05"] if selected_live else sorted(EXPECTED),
        "started_at": started, "ended_at": datetime.now(timezone.utc).isoformat(),
        "execution_head": before, "dirty_before": dirty,
        "go_environment": go_environment, "go_environment_ref": file_ref(env_out),
        "source_hashes": source_before,
        "source_hashes_after": {name: sha256(ROOT / name) for name in SOURCE_FILES},
        "tool_hashes_before": tool_before,
        "tool_hashes_after": {"go": sha256(go), "browser_act": sha256(browser_act) if browser_act and Path(browser_act).is_file() else None},
        "browser_act_sha256": sha256(os.getenv("RESEARCHOS_BROWSER_ACT"))
            if selected_live and os.getenv("RESEARCHOS_BROWSER_ACT") and Path(os.getenv("RESEARCHOS_BROWSER_ACT")).is_file() else None,
        "fixture": fr, "live": result, "owned_acceptance_ids": ["A05"] if selected_live else [],
        "formal_product_acceptance": "PENDING_INDEPENDENT_REVIEW" if selected_live else "NOT_RUN",
        "raw_evidence_references": fr["raw"] + ((result or {}).get("raw", [])),
    }
    report["raw_hashes"] = {name: sha256(ROOT / name) for name in report["raw_evidence_references"]}
    if report["source_hashes"] != report["source_hashes_after"] or report["tool_hashes_before"] != report["tool_hashes_after"]:
        report["status"] = "FAIL"
        report["reason"] = "source or tool drift during probe"
    report["executed_assertion_ids"] = list(report["assertion_ids"])
    if check and report["status"] == "PASS":
        report["assertion_ids"] = [check]
        report["expected_assertion_ids"] = [check]
        report["assertions"] = 1
    (evidence / "source-after.json").write_text(json.dumps(report["source_hashes_after"], indent=2) + "\n", encoding="utf-8")
    write_product_proof(evidence, report, go)
    (evidence / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if os.getenv("RESEARCHOS_TASK_ID") == "W08":
        import research
        sys.exit(research.main("test.sources.fixture"))
    try:
        outcome = main()
    except Exception as exc:
        outcome = {"status": "NOT_IMPLEMENTED" if isinstance(exc, NotImplementedError) else "FAIL",
                   "assertions": 0, "assertion_ids": [], "error": str(exc)}
    print(json.dumps(outcome, ensure_ascii=False))
    sys.exit(0 if outcome["status"] == "PASS" and outcome["assertions"] > 0 else 1)
