"""Finite current58 Go runner source candidate; never called in this proposal.

Requires a fresh Root registration/grant and a separately reviewed scope JSON.
It emits candidate facts only. Source acceptance belongs to an independent owner.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[7]
CONTRACT = Path(__file__).with_name("whole58-finite.contract.proposed.json")
LOCAL_LANES = {"BUILD_ONLY_NO_TOP_TEST", "STATIC_NO_RESOURCE_SIGNAL_REVIEW",
               "LOCAL_HTTP_FIXTURE_REVIEW", "CONDITIONAL_SKIP_REVIEW",
               "LOCAL_NATIVE_CHILD", "LOCAL_NODE_MU_TLS"}
ALLOWED_ENV = {"SystemRoot", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP",
               "GOTOOLCHAIN", "GOPROXY", "GOSUMDB", "GOMODCACHE", "GOCACHE", "GOTMPDIR",
               "GOOS", "GOARCH", "CGO_ENABLED", "GOROOT", "GOPATH",
               "RESEARCHOS_NODE", "RESEARCHOS_MU_BUNDLE", "W14_GO_TOOLCHAIN"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": sha(data), "bytes": len(data)}


def pinned_file(claim):
    if not isinstance(claim, dict) or set(claim) != {"path", "sha256", "bytes"}:
        raise ValueError("MALFORMED_PIN")
    path = Path(claim["path"])
    if not path.is_absolute() or not path.is_file() or path.is_symlink():
        raise ValueError("PIN_PATH_NOT_ABSOLUTE_REGULAR")
    actual = pin(path)
    if actual != claim:
        raise ValueError("PIN_DRIFT")
    return path


def source_closure(contract, catalog):
    if catalog.get("commit") != contract["source_commit"] or catalog.get("file_count") != 639:
        raise ValueError("SOURCE_CATALOG_TUPLE_CHANGED")
    files = catalog.get("files")
    if not isinstance(files, list) or len(files) != 639:
        raise ValueError("PUBLIC_SOURCE_MEMBERSHIP_CHANGED")
    seen = set()
    for entry in files:
        relative = entry["path"]
        path = (ROOT / relative).resolve(strict=True)
        if ROOT not in path.parents or relative in seen or not path.is_file() or path.is_symlink():
            raise ValueError("SOURCE_FOREIGN_OR_DUPLICATE")
        seen.add(relative)
        data = path.read_bytes()
        if sha(data) != entry["sha256"] or len(data) != entry["bytes"]:
            raise ValueError("SOURCE_BYTES_CHANGED")
    return len(seen)


def validate_scope(scope, contract):
    if scope.get("schema") != "researchos.current58-whole-go-run-scope.v1" or scope.get("execution_authorized") is not True:
        raise ValueError("NO_ROOT_EXECUTION_GRANT")
    if scope.get("source_commit") != contract["source_commit"] or scope.get("target_os") != "windows" or scope.get("target_arch") != "amd64":
        raise ValueError("SCOPE_SOURCE_OR_HOST_MISMATCH")
    if os.name != "nt":
        raise ValueError("WINDOWS_TARGET_REQUIRED")
    for name in ("root_registration_ref", "grant_ref", "current_authority_ref", "public_catalog_ref",
                 "complete_runtime_resource_catalog_ref", "git_head_ref", "git_dirty_ref",
                 "outer_os_job_ref", "nested_process_meter_ref", "local_http_meter_ref",
                 "path_authority_ref"):
        pinned_file(scope[name])
    if scope["public_catalog_ref"] != contract["public_source_catalog_ref"]:
        raise ValueError("PUBLIC_CATALOG_NOT_FROZEN")
    runtime = json.loads(pinned_file(scope["complete_runtime_resource_catalog_ref"]).read_text(encoding="utf-8"))
    members = runtime.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("RUNTIME_RESOURCE_CATALOG_EMPTY")
    for row in members: pinned_file(row)
    go_path = pinned_file(scope["pinned_go_ref"])
    if go_path not in {Path(row["path"]) for row in members}:
        raise ValueError("GO_NOT_IN_RUNTIME_CATALOG")
    budgets = scope.get("budgets")
    fields = ("per_invocation_wall_seconds", "total_wall_seconds", "stdout_bytes",
              "stderr_bytes", "max_child_processes", "max_local_http_requests")
    if not isinstance(budgets, dict) or any(type(budgets.get(name)) is not int or budgets[name] <= 0 for name in fields):
        raise ValueError("NUMERIC_BUDGETS_NOT_FROZEN")
    if budgets["max_child_processes"] != 1:
        raise ValueError("RUNNER_ONLY_SUPPORTS_ONE_CHILD_AT_A_TIME")
    lanes = scope.get("selected_lanes")
    if not isinstance(lanes, list) or len(lanes) != len(set(lanes)) or not set(lanes) <= LOCAL_LANES:
        raise ValueError("UNAUTHORIZED_OR_PAID_MODEL_LANE")
    if not lanes:
        raise ValueError("ZERO_LANE_SCOPE")
    env = scope.get("environment")
    if not isinstance(env, dict) or not set(env) <= ALLOWED_ENV or any(not isinstance(v, str) for v in env.values()):
        raise ValueError("ENVIRONMENT_NOT_PINNED_OR_SECRET_BEARING")
    if env.get("GOPROXY") != "off" or env.get("GOSUMDB") != "off" or env.get("GOTOOLCHAIN") != "local":
        raise ValueError("GO_NETWORK_MUST_BE_OFF")
    if env.get("GOOS") != "windows" or env.get("GOARCH") != "amd64":
        raise ValueError("TARGET_GOOS_GOARCH_NOT_LOCKED")
    for name in ("GOMODCACHE", "GOCACHE", "GOTMPDIR", "TEMP", "TMP", "PATH"):
        if not env.get(name): raise ValueError("GO_PATH_OR_CACHE_ENV_MISSING")
    for name in ("RESEARCHOS_NODE", "RESEARCHOS_MU_BUNDLE", "W14_GO_TOOLCHAIN"):
        if name in env and Path(env[name]) not in {Path(row["path"]) for row in members}:
            raise ValueError("ENV_TOOL_NOT_PINNED")
    if "LOCAL_NODE_MU_TLS" in lanes and not all(env.get(name) for name in ("RESEARCHOS_NODE", "RESEARCHOS_MU_BUNDLE")):
        raise ValueError("LOCAL_NODE_MU_RESOURCES_MISSING")
    if "LOCAL_NATIVE_CHILD" in lanes and not env.get("W14_GO_TOOLCHAIN"):
        raise ValueError("NATIVE_GO_PROBE_TOOLCHAIN_MISSING")
    output = Path(scope["output_root"])
    if not output.is_absolute() or not output.is_dir() or output.is_symlink() or list(output.iterdir()):
        raise ValueError("OUTPUT_ROOT_NOT_FRESH")
    return go_path, output, budgets, env, lanes


def run_one(argv, cwd, env, out_dir, wall, stdout_cap, stderr_cap):
    """No retry. Raw bytes land on disk before any output parsing."""
    out_dir.mkdir(parents=True, exist_ok=False)
    stdout = out_dir / "stdout.raw"
    stderr = out_dir / "stderr.raw"
    started = time.time()
    flags = {"stdout_overflow": False, "stderr_overflow": False, "timed_out": False,
             "drain_error": None}
    process = subprocess.Popen(argv, cwd=cwd, env=env, shell=False,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    def drain(pipe, target, cap, key):
        size = 0
        try:
            with target.open("xb") as stream:
                while True:
                    chunk = os.read(pipe.fileno(), 65536)
                    if not chunk: break
                    keep = max(0, min(len(chunk), cap - size))
                    if keep: stream.write(chunk[:keep]); size += keep
                    if keep != len(chunk):
                        flags[key] = True
                        try: process.kill()
                        except OSError: pass
        except OSError as exc:
            flags["drain_error"] = repr(exc)
            try: process.kill()
            except OSError: pass
    workers = [threading.Thread(target=drain, args=(process.stdout, stdout, stdout_cap, "stdout_overflow")),
               threading.Thread(target=drain, args=(process.stderr, stderr, stderr_cap, "stderr_overflow"))]
    for worker in workers: worker.start()
    try:
        process.wait(timeout=wall)
    except subprocess.TimeoutExpired:
        flags["timed_out"] = True
        process.kill()
        process.wait(timeout=10)
    for worker in workers: worker.join(timeout=10)
    if any(worker.is_alive() for worker in workers):
        flags["drain_incomplete"] = True
        (out_dir / "invocation.partial.json").write_text(json.dumps({"argv": argv,
            "actual_exit": process.returncode, "timed_out": flags["timed_out"],
            "drain_incomplete": True, "stdout_path": str(stdout), "stderr_path": str(stderr),
            "raw_hashes": None, "outer_os_job_required": True}, ensure_ascii=False) + "\n", encoding="utf-8")
        raise RuntimeError("DRAIN_INCOMPLETE_OUTER_JOB_REQUIRED")
    receipt = {"argv": argv, "cwd": str(cwd), "env_names": sorted(env),
               "actual_exit": process.returncode, "started_epoch": started,
               "ended_epoch": time.time(), "stdout": pin(stdout), "stderr": pin(stderr),
               **flags, "automatic_retry": False, "counter_reset": False,
               "os_child_tree_lifecycle_qualification": False}
    (out_dir / "invocation.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def test_events(path):
    events = []
    for line in path.read_bytes().splitlines():
        try: value = json.loads(line)
        except json.JSONDecodeError: continue
        if isinstance(value, dict) and value.get("Action"): events.append(value)
    return events


def evaluate_run(receipt, selected, build_only):
    stdout_path = Path(receipt["stdout"]["path"])
    events = test_events(stdout_path)
    terminal = {}
    skipped = []
    for event in events:
        name, action = event.get("Test"), event.get("Action")
        if name and action in ("pass", "fail", "skip"):
            terminal[name] = action
            if action == "skip": skipped.append(name)
    top = {name: status for name, status in terminal.items() if "/" not in name}
    package_pass = any(event.get("Action") == "pass" and not event.get("Test") for event in events)
    if build_only and not package_pass:
        package_pass = b"[no test files]" in stdout_path.read_bytes() and not terminal
    unexpected = sorted(set(top) - set(selected))
    missing = sorted(set(selected) - set(top))
    passed = sorted(name for name in selected if top.get(name) == "pass")
    okay = (receipt["actual_exit"] == 0 and not any(receipt.get(key) for key in
            ("stdout_overflow", "stderr_overflow", "timed_out", "drain_incomplete", "drain_error"))
            and package_pass and not skipped and not unexpected and not missing
            and len(passed) == len(selected))
    if build_only and (selected or terminal):
        okay = False
    return {"candidate_pass": okay, "selected": selected, "passed": passed,
            "missing": missing, "unexpected": unexpected, "skipped": skipped,
            "package_pass": package_pass, "build_only": build_only,
            "actual_exit": receipt["actual_exit"]}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: whole58_finite_runner.proposed.py SCOPE_JSON SCOPE_SHA256")
    scope_path = Path(argv[1])
    scope_raw = scope_path.read_bytes()
    if not scope_path.is_absolute() or sha(scope_raw) != argv[2]:
        raise SystemExit("SCOPE_PIN_MISMATCH")
    scope = json.loads(scope_raw)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if len(contract["packages"]) != 58 or contract["all_platform_top_tests"] != 745:
        raise SystemExit("FINITE_CONTRACT_SHAPE_CHANGED")
    go_path, output, budgets, env_literal, lanes = validate_scope(scope, contract)
    catalog = json.loads(pinned_file(contract["public_source_catalog_ref"]).read_text(encoding="utf-8"))
    source_closure(contract, catalog)
    env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update(env_literal)
    deadline = time.monotonic() + budgets["total_wall_seconds"]
    report = {"schema": "researchos.current58-go-run-facts.v1", "scope_ref": pin(scope_path),
              "source_commit": contract["source_commit"], "packages": [], "qualified": False,
              "source_acceptance": False, "formal_case_accepted_delta": 0,
              "selected_lanes": lanes,
              "model_lane_executed": False, "model_cost_usd": None,
              "os_child_tree_lifecycle_qualification": False,
              "nested_process_and_http_cap_qualification": False,
              "outer_cap_receipts_pending_independent_verification": True}
    for package in contract["packages"]:
        package_out = output / package["directory"].replace("/", "__")
        package_out.mkdir(parents=True, exist_ok=False)
        expected = sorted({name for lane in package["lanes"].values() for name in lane["windows_candidate_names"]})
        if time.monotonic() >= deadline: raise RuntimeError("TOTAL_WALL_DEADLINE")
        listed = run_one([str(go_path), "test", "-list", ".", package["import_arg"]],
                         ROOT, env, package_out / "list", budgets["per_invocation_wall_seconds"],
                         budgets["stdout_bytes"], budgets["stderr_bytes"])
        raw_names = {line.strip() for line in Path(listed["stdout"]["path"]).read_text(encoding="utf-8", errors="replace").splitlines()
                     if re.fullmatch(r"Test\w+", line.strip())}
        roster_ok = (listed["actual_exit"] == 0 and raw_names == set(expected)
                     and not listed["timed_out"] and not listed["stdout_overflow"] and not listed["stderr_overflow"])
        package_report = {"package": package["directory"], "list_invocation": listed,
                          "expected_windows_source_names": expected, "actual_listed_names": sorted(raw_names),
                          "roster_reconciled": roster_ok, "lanes": []}
        report["packages"].append(package_report)
        if not roster_ok: break
        for lane in lanes:
            entry = package["lanes"].get(lane)
            if not entry: continue
            selected = entry["windows_candidate_names"]
            if not selected and lane != "BUILD_ONLY_NO_TOP_TEST": continue
            if time.monotonic() >= deadline: raise RuntimeError("TOTAL_WALL_DEADLINE")
            regex = entry["exact_top_regex"]
            invocation = run_one([str(go_path), "test", "-json", "-count=1", "-run", regex,
                                  "-timeout", str(budgets["per_invocation_wall_seconds"]) + "s",
                                  package["import_arg"]], ROOT, env, package_out / lane,
                                 budgets["per_invocation_wall_seconds"], budgets["stdout_bytes"], budgets["stderr_bytes"])
            outcome = evaluate_run(invocation, selected, lane == "BUILD_ONLY_NO_TOP_TEST")
            package_report["lanes"].append({"lane": lane, "invocation": invocation, "outcome": outcome})
            if not outcome["candidate_pass"]: break
        if any(not item["outcome"]["candidate_pass"] for item in package_report["lanes"]): break
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(p["roster_reconciled"] and all(l["outcome"]["candidate_pass"] for l in p["lanes"])
                    for p in report["packages"]) and len(report["packages"]) == 58 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
