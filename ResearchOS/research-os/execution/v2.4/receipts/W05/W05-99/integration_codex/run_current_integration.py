"""Capture bounded, current-source Go execution without issuing acceptance."""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import uuid


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, choices=["./apps/cli", "./internal/domain", "./internal/api", "./internal/host"])
    parser.add_argument("--selector", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[6]
    assert (root / "execution/project_identity.json").is_file()
    locked = json.loads((root / "execution/toolchains/locked.json").read_bytes())
    go = locked["tools"]["go"]
    assert digest(Path(go["path"])) == go["sha256"], "Go toolchain drift"
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    run = Path(__file__).parent / "current_runs" / run_id
    run.mkdir(parents=True)
    tracked = subprocess.check_output(["git", "ls-files", "-z", "apps", "internal", "adapters", "contracts", "evaluation", "migrations", "spec", "tests", "third_party", "go.mod", "go.sum"], cwd=root).split(b"\0")
    inputs = []
    missing = []
    for name in tracked:
        if not name:
            continue
        relative = name.decode("utf-8")
        path = root / relative
        if not path.is_file():
            missing.append(relative)
            continue
        inputs.append({"path": relative, "sha256": digest(path), "bytes": path.stat().st_size})
        if relative.startswith(("apps/cli/", "internal/domain/client_protocol", "internal/domain/runtime_goal", "internal/domain/runtime_session", "internal/domain/runtime_tools", "internal/domain/runtime_permission", "internal/domain/runtime_broker")):
            target = run / "source_snapshot" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    env = dict(os.environ)
    env.update(GOTOOLCHAIN="local", GOENV="off", GOROOT=str(Path(go["path"]).parents[1]),
               GOPATH=str(root / ".local/gopath"), GOCACHE=str(root / ".local/gocache"), RESEARCHOS_GO=go["path"],
               RESEARCHOS_NODE=locked["tools"]["node"]["path"])
    bundle = root / ".local/w1401-mu-worker/mu-worker.mjs"
    if bundle.is_file():
        env["RESEARCHOS_MU_BUNDLE"] = str(bundle)
    argv = [go["path"], "test", "-json", "-count=1", args.package, "-run", args.selector, "-timeout", str(args.timeout) + "s"]
    manifest = {"schema": "researchos.w05.current-integration-input.v1", "mode": "FIXTURE_AND_LOCAL_WINDOWS_HOST_NOT_LIVE_PROVIDER", "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "argv": argv, "cwd": str(root), "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                "tracked_dirty": subprocess.check_output(["git", "status", "--porcelain", "-uno"], cwd=root, text=True).splitlines(),
                "source_inputs": inputs, "sparse_missing": missing, "runner_sha256": digest(Path(__file__)), "locked_tool": go,
                "mu_bundle": {"path": str(bundle), "sha256": digest(bundle)} if bundle.is_file() else None,
                "fixed_environment": {k: env[k] for k in ["GOTOOLCHAIN", "GOENV", "GOROOT", "GOPATH", "GOCACHE", "RESEARCHOS_GO", "RESEARCHOS_NODE"]},
                "provider_calls_expected": 0, "acceptance_issued": False}
    (run / "inputs.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (run / "stdout.jsonl").open("wb") as out, (run / "stderr.raw").open("wb") as err:
        try:
            process = subprocess.run(argv, cwd=root, env=env, stdout=out, stderr=err, timeout=args.timeout + 30)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            exit_code = 124
    rows = []
    parse_errors = []
    for index, line in enumerate((run / "stdout.jsonl").read_bytes().splitlines(), 1):
        try:
            rows.append(json.loads(line))
        except (ValueError, UnicodeError) as error:
            parse_errors.append({"line": index, "error": type(error).__name__})
    started = {r["Test"] for r in rows if r.get("Action") == "run" and r.get("Test")}
    finished = [r["Test"] for r in rows if r.get("Action") in ["pass", "fail", "skip"] and r.get("Test")]
    passed = [r["Test"] for r in rows if r.get("Action") == "pass" and r.get("Test")]
    failed = [r["Test"] for r in rows if r.get("Action") == "fail" and r.get("Test")]
    skipped = [r["Test"] for r in rows if r.get("Action") == "skip" and r.get("Test")]
    changed = [r["path"] for r in inputs if not (root / r["path"]).is_file() or digest(root / r["path"]) != r["sha256"]]
    package_pass = any(r.get("Action") == "pass" and not r.get("Test") for r in rows)
    valid = exit_code == 0 and bool(started) and package_pass and not failed and not skipped and not parse_errors and not changed and started == set(finished) and len(finished) == len(set(finished))
    result = {"schema": "researchos.w05.current-integration-result.v1", "started_at": manifest["started_at"], "ended_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "mode": manifest["mode"], "argv": argv, "exit_code": exit_code, "evidence_valid": valid, "test_pass": passed, "test_fail": failed, "test_skip": skipped,
              "unfinished": sorted(started - set(finished)), "duplicate_terminal": len(finished) - len(set(finished)), "parse_errors": parse_errors,
              "package_pass": package_pass, "source_changed_during_run": changed, "inputs_sha256": digest(run / "inputs.json"),
              "stdout_sha256": digest(run / "stdout.jsonl"), "stderr_sha256": digest(run / "stderr.raw"), "formal_case_count_delta": 0, "acceptance_issued": False}
    (run / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": str(run), "exit_code": exit_code, "evidence_valid": valid, "passed": len(passed), "failed": failed, "skipped": skipped, "source_changed": changed}, ensure_ascii=True))
    if not valid:
        print((run / "stderr.raw").read_text(encoding="utf-8", errors="replace")[-1500:])
        print("".join(r.get("Output", "") for r in rows)[-4000:])
    return 0 if valid else (exit_code or 2)


if __name__ == "__main__":
    sys.exit(main())
