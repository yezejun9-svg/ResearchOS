"""Exact W13-03 Electron observations; unresolved card gates remain explicit."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
RECEIPTS = ROOT / "execution/v2.4/receipts/W13/W13-03"
STAGES = [
    ("matrix", "run.py", "matrix.json", 660),
    ("preview", "preview_run.py", "preview.json", 360),
    ("workspace", "workspace_run.py", "workspace.json", 300),
    ("permission", "permission_run.py", None, 300),
    ("accessibility", "accessibility_run.py", "accessibility.json", 360),
    ("transcript", "transcript_run.py", "electron-transcript.json", 360),
]

# Other observation drivers are not executed by a stage; shared fixture/production inputs remain pinned.
STAGE_DRIVER_FILES = {
    "matrix": {"run.py", "matrix.cjs"},
    "preview": {"preview_run.py", "preview.cjs"},
    "workspace": {"workspace_run.py", "workspace.cjs"},
    "permission": {"permission_run.py", "permission.cjs"},
    "accessibility": {"accessibility_run.py", "accessibility.cjs"},
    "transcript": {"transcript_run.py", "transcript.cjs"},
}


def stage_inputs(stage, fingerprint):
    unused = {"tests/ui/w1303/check.py"}
    unused.update("tests/ui/w1303/" + name for other, names in STAGE_DRIVER_FILES.items()
                  if other != stage for name in names)
    return {name: value for name, value in fingerprint.items() if name not in unused}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_hashes():
    hashes = {}
    for folder in ["apps/web/src", "apps/desktop/main", "apps/desktop/preload",
                   "apps/control", "apps/cli", "internal", "adapters", "migrations/sqlite", "tests/ui/w1303",
                   "tests/ui/provision", "tests/ui"]:
        for path in sorted((ROOT / folder).rglob("*")):
            if path.is_file() and path.suffix in {".go", ".js", ".jsx", ".cjs", ".mjs", ".css", ".py", ".sql", ".html", ".json"}:
                hashes[path.relative_to(ROOT).as_posix()] = digest(path)
    for name in ["go.mod", "go.sum", "execution/toolchains/locked.json",
                 "apps/web/package.json", "apps/web/package-lock.json", "apps/web/index.html",
                 "apps/desktop/package.json", "apps/desktop/package-lock.json",
                 "tests/ui/browser_smoke.py"]:
        hashes[name] = digest(ROOT / name)
    locked = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8-sig"))["tools"]
    for tool in ["go", "node", "python"]:
        hashes["runtime_tool_" + tool] = digest(Path(locked[tool]["path"]))
    hashes["runtime_tool_electron"] = digest(ROOT / "apps/desktop/node_modules/electron/dist/electron.exe")
    bundle = Path(os.environ.get("RESEARCHOS_MU_BUNDLE") or ROOT / ".local/w1401-mu-worker/mu-worker.mjs")
    hashes["runtime_bundle"] = digest(bundle) if bundle.is_file() else "UNAVAILABLE"
    return hashes


def source_review(filename):
    path = RECEIPTS / filename
    record = json.loads(path.read_text(encoding="utf-8-sig"))
    source = record.get("source_hashes") or record["candidate"]["source_hashes"]
    if isinstance(source, list):
        source = {row["path"]: row.get("main_sha256") or row["sha256"] for row in source}
    changed = [name for name, expected in source.items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != expected.removeprefix("sha256:")]
    return {"status": record["status"] if not changed else "SOURCE_CHANGED_PENDING_REVIEW",
            "historical_status": record["status"], "source_drift": changed,
            "evidence": {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)},
            "scope": record.get("scope", "Only the specific independent review; no whole card acceptance."),
            "prior_runtime_evidence": record.get("prior_runtime_evidence", record.get("prior_runtime_scope")),
            "new_runtime_executions": record.get("new_runtime_executions")}


def observed_checks(parent, child_name):
    meta = json.loads(parent.read_text(encoding="utf-8-sig"))
    if child_name:
        child = parent.parent / child_name
        value = json.loads(child.read_text(encoding="utf-8-sig"))
        checks = value.get("checks", [])
        if meta.get("schema") == "researchos.desktop-transcript-observation.v1":
            checks = [{"id": "HARNESS-" + name, "status": "PASS" if okay else "FAIL"}
                      for name, okay in meta.get("checks", {}).items()] + checks
        return meta, checks, [child]
    checks, children = [], []
    for case in meta.get("cases", []):
        child = parent.parent / case["decision"].lower() / "permission.json"
        value = json.loads(child.read_text(encoding="utf-8-sig"))
        checks.extend(dict(row, decision=case["decision"]) for row in value.get("checks", []))
        children.append(child)
    return meta, checks, children


def prior_stage(stage, fingerprint):
    # Pin all production, shared fixture, build/toolchain and this stage's driver inputs.
    # A change confined to a different driver or this orchestration wrapper does not
    # change an existing observation. Preserve the original complete fingerprint and raw refs.
    for report_path in sorted(RECEIPTS.glob("registered-*/report.json"), reverse=True):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8-sig"))
            old_inputs = report.get("source_hashes", {})
            if not old_inputs or stage_inputs(stage, old_inputs) != stage_inputs(stage, fingerprint):
                continue
            for row in report.get("stages", []):
                if row["stage"] == stage and row["status"] == "PASS" and row.get("checks"):
                    if all(digest(ROOT / ref["path"]) == ref["sha256"] for ref in row["evidence"]):
                        return dict(row, reused=True, reuse_source_report={
                            "path": report_path.relative_to(ROOT).as_posix(), "sha256": digest(report_path)},
                            ignored_source_changes=[name for name in sorted(set(old_inputs) | set(fingerprint))
                                                    if old_inputs.get(name) != fingerprint.get(name)],
                            reuse_rule="All production/shared fixture/build inputs and current stage drivers match; unrelated observation drivers and orchestration wrapper excluded.")
        except (OSError, ValueError, KeyError):
            continue
    return None


def run_stage(stage, script, child_name, timeout, out, fingerprint):
    cached = prior_stage(stage, fingerprint)
    if cached:
        return cached
    argv = [sys.executable, "-B", "-X", "utf8", str(ROOT / "tests/ui/w1303" / script)]
    try:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout)
        stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, exit_code = exc.stdout or b"", exc.stderr or b"", 124
    stdout_path, stderr_path = out / (stage + ".stdout.txt"), out / (stage + ".stderr.txt")
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    row = {"stage": stage, "argv": argv, "exit_code": exit_code,
           "status": "FAIL", "checks": [], "reused": False, "evidence": []}
    evidence = [stdout_path, stderr_path]
    try:
        summary = json.loads(stdout.decode("utf-8").strip().splitlines()[-1])
        parent = Path(summary["receipt"]).resolve()
        if not parent.is_relative_to(RECEIPTS.resolve()):
            raise ValueError("observation receipt outside the W13 directory")
        meta, checks, children = observed_checks(parent, child_name)
        evidence += [parent, *children]
        row["checks"] = checks
        row["observation_receipt"] = parent.relative_to(ROOT).as_posix()
        if exit_code == 0 and meta.get("status") == "PASS" and checks and all(c["status"] == "PASS" for c in checks):
            row["status"] = "PASS"
    except (OSError, ValueError, KeyError, IndexError):
        row["error"] = "Observation failed or did not provide nonempty raw checks; inspect its preserved logs."
    row["evidence"] = [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)} for p in evidence]
    return row


def main():
    task, check, case = (os.environ.get(k, "") for k in
                         ["RESEARCHOS_TASK_ID", "RESEARCHOS_CHECK_ID", "RESEARCHOS_CASE_ID"])
    if task == "W13" and ((check == "W13-G02" and not case) or (case == "C24" and not check)):
        return subprocess.call([sys.executable, "ops/ci/ui.py", "--phase", "core"], cwd=ROOT)
    if task != "W13" or check != "W13-03" or case:
        print(json.dumps({"status": "NOT_IMPLEMENTED", "assertion_ids": [], "scope": "W13-03 exact selector required"}))
        return 3
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    out = RECEIPTS / ("registered-" + run_id)
    out.mkdir(parents=True, exist_ok=False)
    before = source_hashes()
    stages = [run_stage(*args, out, before) for args in STAGES]
    rows = [{"assertion_id": f"W13-03-{s['stage'].upper()}-{i:04d}-{c['id']}",
             "status": c["status"], "observation": c, "receipt": s.get("observation_receipt"),
             "reused": s["reused"]}
            for s in stages for i, c in enumerate(s["checks"], 1)]
    after = source_hashes()
    drift = [p for p, h in before.items() if after.get(p) != h]
    blockers = [
        {"gate": "SCREEN_READER", "status": "BLOCKED_OS_FOREGROUND",
         "evidence": "execution/v2.4/receipts/W13/W13-03/screen_reader_observation_codex.json"},
        {"gate": "WORKSPACE_INDEPENDENT_REVIEW", "status": "BLOCKED_PLATFORM_POLICY",
         "evidence": "execution/v2.4/receipts/W13/W13-03/workspace_review_round2_interruption_codex.json"},
    ]
    for blocker in blockers:
        path = ROOT / blocker["evidence"]
        blocker["sha256"] = digest(path) if path.is_file() else None
    status = "PARTIAL" if rows and all(s["status"] == "PASS" for s in stages) and not drift else "FAIL"
    report = {"schema": "researchos.w1303-registered-observation.v1", "step_id": "W13-03",
              "status": status, "source_hashes": before, "source_drift": drift,
              "stages": stages, "assertion_rows": rows, "assertion_ids": [r["assertion_id"] for r in rows],
              "blockers": blockers,
              "independent_permission_review": source_review("independent_permission_review_round4_codex.json"),
              "independent_transcript_review": source_review("independent_transcript_review_round1_codex.json"),
              "card_accepted": False, "formal_cases_accepted": [], "provider_calls": 0,
              "scope": "Actual Windows Electron observations with explicit FIXTURE inputs; unresolved card gates remain blocked.",
              "finished_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    save(out / "report.json", report)
    print(json.dumps({"status": status, "assertions": len(rows), "assertion_ids": report["assertion_ids"],
                      "scope": report["scope"], "receipt": str(out / "report.json")}, ensure_ascii=False))
    # A nonzero result prevents the dispatcher from accepting partial card evidence.
    return 4 if status == "PARTIAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
