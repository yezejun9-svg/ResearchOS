"""Import and verify the immutable specification; never certify product tests."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(argv, cwd, evidence, name):
    started = now()
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=120)
    evidence.mkdir(parents=True, exist_ok=True)
    out, err = evidence / f"{name}.stdout.txt", evidence / f"{name}.stderr.txt"
    out.write_bytes(result.stdout)
    err.write_bytes(result.stderr)
    record = {"argv": argv, "cwd": str(cwd), "started_at": started, "ended_at": now(),
              "exit_code": result.returncode, "environment_variable_names": [],
              "stdout": {"path": str(out.relative_to(ROOT)), "sha256": digest(out)},
              "stderr": {"path": str(err.relative_to(ROOT)), "sha256": digest(err)}}
    write(evidence / f"{name}.command.json", record)
    return record


def isolation_check():
    # File-import identity fixture only; this is not the product isolation gate C02.
    with tempfile.TemporaryDirectory(prefix="researchos-import-") as temp:
        root = Path(temp)
        records = []
        for content in ("first source", "second source"):
            project_id = str(uuid.uuid4())
            target = root / project_id
            target.mkdir()
            (target / "source.txt").write_text(content, encoding="utf-8")
            records.append({"project_id": project_id, "display_name": "ResearchOS",
                            "directory": project_id, "source_sha256": digest(target / "source.txt")})
        assert records[0]["project_id"] != records[1]["project_id"]
        assert records[0]["source_sha256"] != records[1]["source_sha256"]
        assert all((root / x["directory"]).name == x["project_id"] for x in records)
        return {"mode": "FIXTURE", "status": "PASS", "assertion_ids": ["W00-G03"],
                "records": records, "C02": "NOT_RUN"}


def check():
    imported = json.loads((ROOT / "execution/import_manifest.json").read_text(encoding="utf-8"))
    identity = json.loads((ROOT / "execution/project_identity.json").read_text(encoding="utf-8"))
    assert str(uuid.UUID(identity["project_id"])) == identity["project_id"]
    assert Path(identity["repository_root"]).resolve() == ROOT
    assert identity["imported_projects"] == [identity["project_id"]]
    for item in imported["files"]:
        target = ROOT / item["target"]
        assert target.is_file() and digest(target) == item["sha256"], item["target"]
        assert not (target.stat().st_mode & stat.S_IWRITE), item["target"]
    snapshot = ROOT / "spec/v2.0"
    assert {p.relative_to(ROOT).as_posix() for p in snapshot.rglob("*") if p.is_file()} == {x["target"] for x in imported["files"]}
    assert subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True, encoding="utf-8").strip().replace("\\", "/") == ROOT.as_posix()
    fixture = isolation_check()
    return {"status": "PASS", "scope": "W00_CONSTRUCTION_ONLY", "files": len(imported["files"]),
            "assertion_ids": ["W00-G01", "W00-G02", "W00-G03"], "isolation": fixture,
            "product_tests": "NOT_RUN"}


def initialize(source):
    source = source.resolve(strict=True)
    target = ROOT / "spec/v2.0"
    if target.exists() or (ROOT / ".git").exists():
        raise SystemExit("Already initialized; use --check. Existing work was preserved.")
    started, run_id, project_id = now(), str(uuid.uuid4()), str(uuid.uuid4())
    evidence = ROOT / "execution/receipts/W00" / run_id
    sources = sorted(p for p in source.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    before = {p.relative_to(source).as_posix(): digest(p) for p in sources}
    validation = run([sys.executable, "tools/validate_package.py"], source, evidence, "package-validate")
    if validation["exit_code"] != 0:
        raise SystemExit("Specification validator failed; inspect preserved evidence.")
    files = []
    for src in sources:
        relative = src.relative_to(source)
        dst = target / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        assert digest(dst) == before[relative.as_posix()] == digest(src)
        dst.chmod(stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
        files.append({"source": str(src), "target": dst.relative_to(ROOT).as_posix(),
                      "sha256": digest(dst), "size_bytes": dst.stat().st_size})
    write(ROOT / "execution/import_manifest.json", {"status": "IMPORTED", "source_root": str(source),
          "project_id": project_id, "created_at": now(), "failed_imports": [], "files": files})
    spec_hash = digest(target / "PACKAGE_MANIFEST.json")
    write(ROOT / "execution/project_identity.json", {"project_id": project_id, "name": "ResearchOS",
          "created_at": now(), "repository_root": str(ROOT), "spec_manifest_sha256": spec_hash,
          "imported_projects": [project_id], "other_project_access": "NOT_AUTHORIZED"})
    initialization = run(["git", "init", "-b", "main"], ROOT, evidence, "git-init")
    assert initialization["exit_code"] == 0
    environment = {"os": platform.platform(), "machine": platform.machine(), "python": sys.version,
                   "shell": "PowerShell", "timezone": str(dt.datetime.now().astimezone().tzinfo),
                   "initial_repository": "ABSENT", "initial_paths": ["AGENTS.md", ".gitignore", "bootstrap/bootstrap.py"],
                   "tools": {name: shutil.which(name) for name in ("python", "git", "node", "npm", "pnpm", "go", "codex", "gh")}}
    write(ROOT / "execution/environment.json", environment)
    write(evidence / "import-isolation.json", isolation_check())
    task_contract = json.loads((target / "contracts/tasks.json").read_text(encoding="utf-8"))
    frozen = {"project_id": project_id, "spec_manifest_sha256": spec_hash,
              "tasks_sha256": digest(target / "contracts/tasks.json"), "acceptance_sha256": digest(target / "contracts/acceptance.json"),
              "executor_identity": "codex:/root", "verifier_identity": "codex:/root/bootstrap_verifier",
              "w00_contract": task_contract["tasks"][0], "created_at": now()}
    write(ROOT / "execution/frozen_context.json", frozen)
    ledger = json.loads((target / "examples/bootstrap_ledger.template.json").read_text(encoding="utf-8"))
    ledger.update({"artifact_kind": "CONSTRUCTION_LEDGER_NOT_PRODUCT_STATE", "status": "IN_PROGRESS",
                   "project_identity_ref": "execution/project_identity.json", "repository_root": str(ROOT),
                   "spec_manifest_sha256": spec_hash, "active_tasks": [{"task_id": "W00", "owner": "codex:/root", "run_id": run_id}],
                   "tasks": {t["task_id"]: {"status": "EXECUTION_REPORTED" if t["task_id"] == "W00" else "NOT_STARTED"} for t in task_contract["tasks"]},
                   "checkpoint_ref": "execution/checkpoint.json", "next_ready": [], "updated_at": now()})
    ledger["task_receipt_refs"] = [f"execution/receipts/W00/{run_id}/receipt.json"]
    write(ROOT / "execution/bootstrap_ledger.json", ledger)
    write(ROOT / "execution/acceptance_status.json", {"baseline_sha256": digest(target / "contracts/acceptance.json"),
          "cases": {case["id"]: {"status": "NOT_RUN", "evidence": []} for case in json.loads((target / "contracts/acceptance.json").read_text(encoding="utf-8"))["cases"]}})
    write(ROOT / "execution/agent_policy.json", {"revision": 1, "max_active_construction_tasks": 2,
          "user_authorized_model_selection": True, "model_policy": {"architecture_security": "gpt-6-astra/high",
          "implementation_verification": "gpt-6-sol/high", "mechanical_low_risk": "gpt-6-luna/high"},
          "assignments": [{"agent": "codex:/root/bootstrap_verifier", "task": "W00 independent verification", "model": "gpt-6-sol", "reasoning": "high", "reason": "Bounded evidence audit against four fixed bootstrap gates"}]})
    write(ROOT / "execution/checkpoint.json", {"updated_at": now(), "project_id": project_id,
          "current": "W00 awaiting independent construction verification", "next": "W01 bounded Paperclip qualification",
          "processes": [], "pending_side_effects": [], "cost": {"actual": None, "in_flight": None, "cap": None},
          "resume": ["AGENTS.md", "execution/project_identity.json", "execution/bootstrap_ledger.json", "spec/v2.0/00_START_HERE.md"]})
    finalize()


def finalize():
    target = ROOT / "spec/v2.0"
    ledger = json.loads((ROOT / "execution/bootstrap_ledger.json").read_text(encoding="utf-8"))
    identity = json.loads((ROOT / "execution/project_identity.json").read_text(encoding="utf-8"))
    assert ledger["tasks"]["W00"]["status"] == "EXECUTION_REPORTED"
    run_id = ledger["active_tasks"][0]["run_id"]
    evidence = ROOT / "execution/receipts/W00" / run_id
    if (evidence / "receipt.json").exists():
        raise SystemExit("Finalized receipt exists; use --check. Evidence preserved.")
    task_contract = json.loads((target / "contracts/tasks.json").read_text(encoding="utf-8"))
    validation = json.loads((evidence / "package-validate.command.json").read_text(encoding="utf-8"))
    project_id, spec_hash, started = identity["project_id"], identity["spec_manifest_sha256"], identity["created_at"]
    files = json.loads((ROOT / "execution/import_manifest.json").read_text(encoding="utf-8"))["files"]
    result = check()
    write(evidence / "bootstrap-check.json", result)
    artifacts = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p != evidence / "receipt.json"]
    artifact_manifest = [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)} for p in artifacts]
    write(evidence / "artifact-manifest.json", artifact_manifest)
    receipt = {key: None for key in task_contract["receipt_required_fields"]}
    receipt.update({"task_id": "W00", "run_id": run_id, "project_id": project_id, "owner_role": "platform",
                    "executor_identity": "codex:/root", "verifier_identity": "codex:/root/bootstrap_verifier",
                    "status": "EXECUTION_REPORTED", "base_revision": "EMPTY_REPOSITORY", "input_manifest_hash": spec_hash,
                    "rubric_revision": digest(target / "contracts/tasks.json"), "artifact_manifest_hash": digest(evidence / "artifact-manifest.json"),
                    "route_revision": "NOT_SELECTED", "code_revision": "UNCOMMITTED_BOOTSTRAP", "changed_paths": [a["path"] for a in artifact_manifest],
                    "verification_results": [{"command_key": "package.validate", "registered_command_revision": "W00_DIRECT",
                    "actual_invocation_reference": str((evidence / "package-validate.command.json").relative_to(ROOT)),
                    "mode": "DEVELOPMENT", "status": "PASS", "started_at": validation["started_at"], "ended_at": validation["ended_at"],
                    "exit_code": 0, "assertion_ids": ["W00-G01"], "artifact_versions": {"spec_manifest_sha256": spec_hash},
                    "stdout_reference": validation["stdout"]["path"], "stderr_reference": validation["stderr"]["path"],
                    "raw_evidence_references": [validation["stdout"]]}], "open_blockers": [], "resource_request_ids": [],
                    "side_effects": ["Created isolated local repository and immutable specification copy"],
                    "rollback_reference": "Preserve repository; no existing user files changed",
                    "next_action": "Independent W00 verification, then W01", "started_at": started, "ended_at": now(),
                    "product_acceptance": "NOT_RUN", "phase_gate_results": result,
                    "external_verifier": {"status": "NOT_RUN", "evidence_ref": None}})
    receipt["receipt_hash"] = hashlib.sha256(json.dumps(receipt, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    write(evidence / "receipt.json", receipt)
    print(json.dumps({"status": "EXECUTION_REPORTED", "project_id": project_id, "run_id": run_id,
                      "spec_manifest_sha256": spec_hash, "file_count": len(files), "product_tests": "NOT_RUN"}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--resume-bootstrap", action="store_true")
    args = parser.parse_args()
    if args.check:
        print(json.dumps(check(), ensure_ascii=False, indent=2))
    elif args.resume_bootstrap:
        finalize()
    elif args.source:
        initialize(args.source)
    else:
        parser.error("Specify --source or --check")
