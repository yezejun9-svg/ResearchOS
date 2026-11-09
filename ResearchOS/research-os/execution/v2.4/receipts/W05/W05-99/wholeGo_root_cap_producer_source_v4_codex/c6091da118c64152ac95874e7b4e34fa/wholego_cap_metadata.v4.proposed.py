"""Root-only, finite whole-Go metadata producer. Source proposal; no execution authority.

Future usage: PinnedPython -I -S -X utf8 this.py attest|scope|arm|close INPUT OUTDIR INPUT_SHA256
All inputs must be immutable byte pins supplied by Root. This module never runs Go,
starts a child, creates a grant, or promotes a source candidate to qualification.
"""

from datetime import datetime, timezone
import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
HEAD = "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7"
LOCAL_LANES = {"BUILD_ONLY_NO_TOP_TEST", "STATIC_NO_RESOURCE_SIGNAL_REVIEW",
               "LOCAL_HTTP_FIXTURE_REVIEW", "CONDITIONAL_SKIP_REVIEW",
               "LOCAL_NATIVE_CHILD", "LOCAL_NODE_MU_TLS"}
SELECTED = ROOT / "execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_configuration_sync_source_preparation_codex/4a8dca58606d4a4db695aa6dc9f082cb"
SELECTED_REFS = {
    "execution_contract_ref": ("whole58-execution.contract.rev4.proposed.json",
                               "f19830d3ac484412d9a99219aa9358d4d688c9fab836afabbb68293a61727a20", 3571),
    "runner_ref": ("whole58_finite_runner.rev9.proposed.py",
                   "d79f1258fc0fe4b98844da81ab4633a337029253abd155d89269ee6de6a149fa", 24460),
    "gate_ref": ("whole58_gate.rev4.proposed.py",
                 "9fef074899ffba00c4a18d8774d60c01268d30f260becfe9f83ecc13e6bebac6", 24591),
}
FIXED_FINITE_SHA = "52828991f4f23d6957a3f7aa6343b50d8840efbe0ca42121871aa6bc8ce8c904"
FIXED_FINITE_BYTES = 275734
CHECKPOINT_PATH = ROOT / "execution/v2.4/checkpoint.json"


def require(ok, code):
    if not ok:
        raise ValueError(code)


def unique_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def canonical(path):
    require(isinstance(path, str), "PATH_TYPE")
    p = Path(path)
    require(p.is_absolute(), "ABSOLUTE_PATH_REQUIRED")
    for part in (p, *p.parents):
        if not part.exists():
            continue
        info = part.lstat()
        require(not part.is_symlink() and not getattr(part, "is_junction", lambda: False)()
                and not getattr(info, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400), "REPARSE_PATH_DENIED")
    resolved = p.resolve(strict=True)
    require(str(resolved).casefold() == str(p).casefold(), "ALIAS_PATH_DENIED")
    return p


def pin_file(path):
    p = canonical(str(path))
    info = p.lstat()
    require(stat.S_ISREG(info.st_mode), "REGULAR_FILE_REQUIRED")
    raw = p.read_bytes()
    require(len(raw) == info.st_size, "FILE_CHANGED_WHILE_PINNING")
    return {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def verified_raw(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"}, "PIN_SHAPE")
    p = canonical(ref["path"])
    info = p.lstat()
    require(stat.S_ISREG(info.st_mode), "PIN_NOT_REGULAR_FILE")
    raw = p.read_bytes()
    require(len(raw) == info.st_size == ref["bytes"] and
            hashlib.sha256(raw).hexdigest() == ref["sha256"] and
            canonical(ref["path"]) == p, "PIN_DRIFT")
    return raw


def verified_json(ref):
    return unique_json(verified_raw(ref))


def fixed_selected(source, key):
    name, digest, size = SELECTED_REFS[key]
    ref = source[key]
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256", "bytes"} and
            canonical(ref["path"]) == canonical(str(SELECTED / name)) and
            ref["sha256"] == digest and ref["bytes"] == size, "SELECTED_SOURCE_DRIFT:" + key)
    verified_raw(ref)


def observed_windows_process(pid):
    """Observe PID, creation and liveness at this query instant; controller proves job ID."""
    require(os.name == "nt" and type(pid) is int and pid > 0, "WINDOWS_TARGET_PID_REQUIRED")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    class FILETIME(ctypes.Structure):
        _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
    kernel.GetExitCodeProcess.restype = ctypes.c_int
    handle = kernel.OpenProcess(0x1000, 0, pid)
    require(bool(handle), "ROOT_RUNNER_PROCESS_NOT_LIVE")
    try:
        created, exited, kernel_time, user_time = FILETIME(), FILETIME(), FILETIME(), FILETIME()
        ok = kernel.GetProcessTimes(ctypes.c_void_p(handle), ctypes.byref(created),
                                    ctypes.byref(exited), ctypes.byref(kernel_time),
                                    ctypes.byref(user_time))
        member = ctypes.c_int(0)
        ok_job = kernel.IsProcessInJob(ctypes.c_void_p(handle), None, ctypes.byref(member))
        require(ok != 0 and ok_job != 0 and member.value == 1,
                "ROOT_RUNNER_PROCESS_NOT_IN_WINDOWS_JOB")
        exit_code = ctypes.c_uint32()
        ok_exit = kernel.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(exit_code))
        require(ok_exit != 0 and exit_code.value == 259 and
                exited.low == 0 and exited.high == 0,
                "ROOT_RUNNER_PROCESS_ALREADY_EXITED_OR_UNOBSERVED")
        return (created.high << 32) | created.low
    finally:
        kernel.CloseHandle(ctypes.c_void_p(handle))


def put_new(path, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as out:
        out.write(raw)
    return pin_file(path)


def allocated_paths(source, stage, output_dir):
    allocation = verified_json(source["root_allocation_ref"])
    allocation_review = verified_json(source["root_allocation_review_ref"])
    uuid = source["run_uuid"]
    base = canonical(str(ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex"))
    reg = canonical(allocation.get("registration_dir"))
    require(reg.parent == base and reg.name.endswith(uuid), "ROOT_ALLOCATION_NAMESPACE_OPEN")
    run_output = canonical(allocation.get("run_output_root"))
    require(run_output == reg / "run-output", "ROOT_RUN_OUTPUT_NOT_ALLOCATED")
    stage_root = canonical(str(output_dir))
    require(stage_root == reg / "cap-producer" / stage and stage_root.is_dir() and
            not list(stage_root.iterdir()), "ROOT_STAGE_OUTPUT_NOT_FRESH")
    require(allocation.get("schema") == "researchos.current58-whole-go-root-allocation.v1" and
            allocation.get("actor_id") == "codex:/root" and
            allocation.get("run_uuid") == uuid and
            allocation.get("source_commit") == HEAD and
            allocation.get("stage_output_roots", {}).get(stage) == str(stage_root) and
            allocation.get("run_output_root") == str(run_output), "ROOT_ALLOCATION_DRIFT")
    require(allocation_review.get("schema") == "researchos.current58-whole-go-root-allocation-review.v1" and
            allocation_review.get("decision") == "ALLOCATED_PATHS_REVIEWED" and
            allocation_review.get("actor_id") not in (None, "", "codex:/root", source.get("owner")) and
            allocation_review.get("allocation_ref") == source["root_allocation_ref"] and
            allocation_review.get("run_uuid") == uuid, "ROOT_ALLOCATION_REVIEW_OPEN")
    return allocation


def identity(source, stage, output_dir):
    require(source.get("schema") == "researchos.whole-go-root-cap-input.v1" and
            source.get("source_commit") == HEAD and source.get("actor_id") == "codex:/root" and
            isinstance(source.get("run_uuid"), str) and len(source["run_uuid"]) == 32 and
            all(c in "0123456789abcdef" for c in source["run_uuid"]), "ROOT_IDENTITY_OPEN")
    require(canonical(source["worktree"]) == ROOT and Path.cwd() == ROOT,
            "ROOT_WORKTREE_AND_CWD_NOT_CURRENT")
    allocated_paths(source, stage, output_dir)


def reviewed_limits(source):
    limits = verified_json(source["root_limits_ref"])
    review = verified_json(source["cap_plan_review_ref"])
    require(limits.get("schema") == "researchos.current58-whole-go-root-limits.v1" and
            limits.get("actor_id") == "codex:/root" and
            limits.get("run_uuid") == source["run_uuid"] and
            limits.get("source_commit") == HEAD and
            limits.get("worktree") == str(ROOT), "ROOT_LIMITS_NOT_ACTUAL")
    require(review.get("schema") == "researchos.current58-whole-go-cap-plan-review.v1" and
            review.get("decision") == "CAP_PLAN_REVIEWED" and
            review.get("actor_id") not in (None, "", "codex:/root", source.get("owner")) and
            review.get("run_uuid") == source["run_uuid"] and
            review.get("root_limits_ref") == source["root_limits_ref"],
            "NON_AUTHOR_CAP_PLAN_REVIEW_OPEN")
    fixed_selected(source, "execution_contract_ref")
    execution = verified_json(source["execution_contract_ref"])
    require(execution.get("schema") == "researchos.current58-whole-go-execution-contract.v2",
            "EXECUTION_CONTRACT_CHANGED")
    keys = execution["numeric_budget_keys"]
    budgets = limits.get("budgets")
    require(isinstance(keys, list) and len(keys) == 13 and len(set(keys)) == 13 and
            isinstance(budgets, dict) and set(budgets) == set(keys), "THIRTEEN_BUDGET_KEYS_OPEN")
    for key in keys:
        require(type(budgets[key]) is int and
                (budgets[key] == 0 if key == "max_model_requests" else budgets[key] > 0),
                "ROOT_NUMERIC_BOUND_OPEN:" + key)
    require(budgets["total_wall_seconds"] >
            budgets["cleanup_reserve_seconds"] + budgets["finalization_reserve_seconds"] +
            budgets["io_reserve_seconds"], "RESERVES_EXHAUST_TOTAL")
    require(limits.get("selected_lanes") and
            len(limits["selected_lanes"]) == len(set(limits["selected_lanes"])) and
            set(limits["selected_lanes"]) <= LOCAL_LANES and
            "REAL_MODEL_B01_HOLD" not in limits["selected_lanes"], "PAID_LANE_NOT_HELD")
    return limits, execution, budgets


def finite_plan(finite, lanes, go_executable):
    calls = []
    packages = finite.get("packages")
    require(isinstance(packages, list) and len(packages) == 58, "FINITE_58_PACKAGES_CHANGED")
    for package in packages:
        name = package["directory"]
        arg = package["import_arg"]
        require(arg == "./" + name and ".." not in Path(name).parts, "FINITE_IMPORT_ARG_CHANGED")
        calls.append({"kind": "list", "package": name, "lane": None,
                      "argv_template": [go_executable, "test", "-list", ".", arg]})
        for lane in lanes:
            entry = package["lanes"].get(lane)
            if entry is None or (not entry["windows_candidate_names"] and lane != "BUILD_ONLY_NO_TOP_TEST"):
                continue
            names = entry["windows_candidate_names"]
            regex = "^(?:" + "|".join(names) + ")$" if names else "^$"
            require(entry["exact_top_regex"] == regex, "FINITE_LANE_REGEX_CHANGED")
            calls.append({"kind": "lane", "package": name, "lane": lane, "selected": names,
                          "argv_template": [go_executable, "test", "-json", "-count=1", "-run",
                                            regex, "-timeout", "<BOUNDED_DURATION>", arg]})
    return calls


def attest(source):
    tree = verified_json(source["go_tree_ref"])
    native = verified_json(source["native_result_ref"])
    go_ref = source["go_executable_ref"]
    verified_json(source["locked_toolchain_ref"])
    verified_raw(source["implementation_ref"])
    require(tree.get("schema") == "researchos.current58-frozen-go-toolchain-tree.v1" and
            tree.get("selection") == "runtime_check_windows.go/checkTree:curatedGo" and
            tree.get("root_path") == source["go_root"] and
            tree.get("member_count") == len(tree.get("members", [])) and
            isinstance(tree.get("frozen_go_tree_hash"), str), "GO_TREE_NOT_TYPED")
    require(pin_file(Path(source["go_root"]) / "bin" / "go.exe") == go_ref,
            "GO_EXE_NOT_IN_TREE")
    go_entry = next((x for x in tree["members"] if x.get("path") == "bin/go.exe"), None)
    require(go_entry is not None and go_entry["sha256"] == "sha256:" + go_ref["sha256"],
            "GO_BUILD_HASH_NOT_TREE_MEMBER")
    require(native.get("schema") == "researchos.current58-frozen-go-native-result.v1" and
            native.get("run_uuid") == source["run_uuid"] and native.get("actual_exit") == 0 and
            native.get("go_executable_ref") == go_ref and
            native.get("tree_hash") == tree["frozen_go_tree_hash"] and
            native.get("build_hash") == go_entry["sha256"] and
            native.get("implementation_ref") == source["implementation_ref"],
            "NATIVE_GO_HASH_RESULT_OPEN")
    selection = json.dumps(tree["members"], ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return {"schema": "researchos.current58-frozen-go-hash-attestation.v2",
            "run_uuid": source["run_uuid"], "root_path": source["go_root"],
            "go_tree_ref": source["go_tree_ref"], "go_executable_ref": go_ref,
            "locked_toolchain_ref": source["locked_toolchain_ref"],
            "selection_members_sha256": hashlib.sha256(selection).hexdigest(),
            "build_hash": go_entry["sha256"], "tree_hash": tree["frozen_go_tree_hash"],
            "implementation_ref": source["implementation_ref"],
            "producer": "ROOT_ACTUAL_FROZEN_GO_TOOLCHAIN_HASH", "actor_id": "codex:/root",
            "native_result_ref": source["native_result_ref"]}


def scope(source, require_fresh=True):
    limits, execution, budgets = reviewed_limits(source)
    require(source["finite_contract_ref"]["sha256"] == FIXED_FINITE_SHA and
            source["finite_contract_ref"]["bytes"] == FIXED_FINITE_BYTES,
            "SELECTED_FINITE_CONTRACT_DRIFT")
    finite = verified_json(source["finite_contract_ref"])
    attestation = verified_json(source["go_tree_attestation_ref"])
    go_review = verified_json(source["go_tree_attestation_review_ref"])
    require(attestation == attest({**source, "native_result_ref": attestation["native_result_ref"]}),
            "GO_ATTESTATION_NOT_DERIVED_FROM_NATIVE")
    require(go_review.get("schema") == execution["go_attestation_review_schema"] and
            go_review.get("decision") == "PASS" and
            go_review.get("run_uuid") == source["run_uuid"] and
            go_review.get("attestation_ref") == source["go_tree_attestation_ref"] and
            go_review.get("native_result_ref") == attestation["native_result_ref"] and
            go_review.get("go_tree_ref") == source["go_tree_ref"] and
            go_review.get("actor_id") not in (None, "", "codex:/root"),
            "NON_AUTHOR_GO_ATTESTATION_REVIEW_OPEN")
    require(finite.get("source_commit") == HEAD and
            finite.get("public_source_catalog_ref") == source["public_catalog_ref"] and
            len(finite.get("packages", [])) == 58, "FINITE_CONTRACT_OR_PUBLIC_CATALOG_DRIFT")
    verified_json(source["public_catalog_ref"])
    verified_json(source["runtime_catalog_ref"])
    source_manifest = verified_json(source["source_manifest_ref"])
    fixed_selected(source, "runner_ref")
    fixed_selected(source, "gate_ref")
    member_pins = source_manifest.get("members", [])
    require(isinstance(member_pins, list) and
            all(any(member == ref for member in member_pins) for ref in
                (source["runner_ref"], source["gate_ref"], source["execution_contract_ref"],
                 source["finite_contract_ref"])), "SELECTED_SOURCE_MEMBERS_NOT_CLOSED")
    env = limits.get("environment")
    require(isinstance(env, dict) and env.get("GOTOOLCHAIN") == "local" and
            env.get("GOPROXY") == "off" and env.get("GOSUMDB") == "off" and
            env.get("GOOS") == "windows" and env.get("GOARCH") == "amd64" and
            all(env.get(k) for k in ("PATH", "TEMP", "TMP", "GOCACHE", "GOMODCACHE", "GOTMPDIR")),
            "ROOT_LOCAL_ENVIRONMENT_OPEN")
    calls = finite_plan(finite, limits["selected_lanes"], source["go_executable_ref"]["path"])
    require(budgets["max_primary_go_calls"] >= len(calls) and
            limits.get("planned_invocations") == calls, "FINITE_PLAN_OR_CALL_CAP_OPEN")
    require(limits.get("output_root") == source.get("output_root") and
            limits.get("owner") == source.get("owner") and
            limits.get("source_manifest_ref") == source["source_manifest_ref"] and
            limits.get("finite_contract_ref") == source["finite_contract_ref"],
            "ROOT_LIMIT_SCOPE_IDENTITY_MISMATCH")
    output = canonical(source["output_root"])
    allocation = verified_json(source["root_allocation_ref"])
    require(output == canonical(allocation["run_output_root"]) and output.is_dir() and
            (not require_fresh or not list(output.iterdir())), "OUTPUT_ROOT_NOT_FRESH_OR_ALLOCATED")
    return {"schema": execution["scope_schema"], "run_uuid": source["run_uuid"],
            "project_id": source["project_id"], "source_commit": HEAD,
            "target_os": "windows", "target_arch": "amd64", "owner": source["owner"],
            "worktree": str(ROOT), "source_manifest_ref": source["source_manifest_ref"],
            "finite_contract_ref": source["finite_contract_ref"], "runner_ref": source["runner_ref"],
            "gate_ref": source["gate_ref"], "execution_contract_ref": source["execution_contract_ref"],
            "public_catalog_ref": source["public_catalog_ref"],
            "runtime_catalog_ref": source["runtime_catalog_ref"],
            "go_tree_ref": source["go_tree_ref"],
            "go_tree_attestation_ref": source["go_tree_attestation_ref"],
            "go_tree_attestation_review_ref": source["go_tree_attestation_review_ref"],
            "pinned_go_ref": source["go_executable_ref"],
            "selected_lanes": limits["selected_lanes"], "planned_invocations": calls,
            "budgets": budgets, "environment": env, "output_root": str(output)}


def arm(source):
    limits, execution, budgets = reviewed_limits(source)
    current_scope = verified_json(source["scope_ref"])
    registration = verified_json(source["registration_ref"])
    grant = verified_json(source["grant_ref"])
    review = verified_json(source["source_review_ref"])
    lease = verified_json(source["owner_lease_ref"])
    checkpoint = verified_json(source["checkpoint_ref"])
    outer = verified_json(source["outer_job_ref"])
    meter = verified_json(source["meter_ref"])
    paths = verified_json(source["path_authority_ref"])
    os_probe = verified_json(source["os_probe_ref"])
    controller_review = verified_json(source["controller_review_ref"])
    controller_source = source["controller_source_ref"]
    verified_raw(controller_source)
    controller_actual = verified_json(source["controller_actual_receipt_ref"])
    controller_actual_review = verified_json(source["controller_actual_review_ref"])
    require(current_scope == scope(source), "SCOPE_NOT_CURRENT_FROM_REVIEWED_LIMITS")
    uuid = source["run_uuid"]
    require(canonical(source["checkpoint_ref"]["path"]) == canonical(str(CHECKPOINT_PATH)),
            "CANONICAL_CHECKPOINT_REQUIRED")
    allocation = verified_json(source["root_allocation_ref"])
    require(registration.get("schema") == execution["root_registration_schema"] and
            registration.get("actor_id") == "codex:/root" and
            registration.get("run_uuid") == uuid and
            registration.get("scope_path") == source["scope_ref"]["path"] and
            registration.get("source_commit") == HEAD and
            registration.get("planned_invocations") == current_scope["planned_invocations"] and
            registration.get("worktree") == str(ROOT) and registration.get("cwd") == str(ROOT) and
            registration.get("owner") == source["owner"] and
            registration.get("output_root") == source["output_root"] and
            registration.get("source_manifest_ref") == source["source_manifest_ref"] and
            registration.get("go_tree_attestation_review_ref") == source["go_tree_attestation_review_ref"] and
            registration.get("root_allocation_ref") == source["root_allocation_ref"] and
            registration.get("registration_dir") == allocation["registration_dir"],
            "ROOT_REGISTRATION_MISMATCH")
    require(review.get("schema") == execution["non_author_review_schema"] and
            review.get("decision") == "SOURCE_AND_PLAN_REVIEWED" and
            review.get("actor_id") not in (None, "", "codex:/root", source["owner"]) and
            review.get("registration_ref") == source["registration_ref"] and
            review.get("scope_ref") == source["scope_ref"] and
            review.get("source_manifest_ref") == source["source_manifest_ref"] and
            review.get("finite_contract_ref") == source["finite_contract_ref"] and
            review.get("go_tree_attestation_review_ref") == source["go_tree_attestation_review_ref"],
            "SOURCE_PLAN_REVIEW_OPEN")
    require(grant.get("schema") == execution["root_grant_schema"] and
            grant.get("actor_id") == "codex:/root" and grant.get("decision") == "ALLOW_LOCAL_GO_ONLY" and
            grant.get("run_uuid") == uuid and grant.get("scope_ref") == source["scope_ref"] and
            grant.get("registration_ref") == source["registration_ref"] and
            grant.get("source_review_ref") == source["source_review_ref"] and
            grant.get("budgets") == budgets and grant.get("selected_lanes") == current_scope["selected_lanes"] and
            grant.get("planned_invocations") == current_scope["planned_invocations"] and
            grant.get("environment") == current_scope["environment"] and
            grant.get("runtime_catalog_ref") == source["runtime_catalog_ref"] and
            grant.get("source_manifest_ref") == source["source_manifest_ref"] and
            grant.get("go_tree_attestation_ref") == source["go_tree_attestation_ref"] and
            grant.get("go_tree_attestation_review_ref") == source["go_tree_attestation_review_ref"] and
            grant.get("worktree") == str(ROOT) and grant.get("cwd") == str(ROOT) and
            grant.get("allow_model_requests") is False and
            grant.get("root_allocation_ref") == source["root_allocation_ref"] and
            grant.get("controller_source_ref") == controller_source and
            grant.get("controller_review_ref") == source["controller_review_ref"],
            "ROOT_GRANT_NOT_EXACT")
    require(lease.get("schema") == execution["owner_lease_schema"] and
            lease.get("state") == "ACTIVE" and lease.get("run_uuid") == uuid and
            lease.get("owner") == source["owner"] and lease.get("worktree") == str(ROOT) and
            datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00")) > datetime.now(timezone.utc),
            "OWNER_LEASE_NOT_ACTIVE")
    wip = checkpoint.get("work_in_progress", {})
    require(checkpoint.get("head") == HEAD and
            wip.get("whole58_active_run_uuid") == uuid and
            wip.get("whole58_registration_ref") == source["registration_ref"] and
            wip.get("whole58_owner_lease_ref") == source["owner_lease_ref"] and
            any(row.get("step_id") == "W05-99" and row.get("slice_id") == "WHOLE58_GO" and
                row.get("owner") == source["owner"] and row.get("scope_ref") == source["scope_ref"] and
                row.get("lease_ref") == source["owner_lease_ref"] for row in checkpoint.get("workers", [])),
            "CHECKPOINT_NOT_ACTUAL_ACTIVE_WORKER")
    require(outer.get("schema") == execution["outer_job_schema"] and
            outer.get("run_uuid") == uuid and outer.get("kill_on_close") is True and
            outer.get("deadline_enforced") is True and
            type(outer.get("runner_pid")) is int and outer["runner_pid"] > 0 and
            outer.get("max_child_processes") == budgets["max_child_processes"],
            "OUTER_JOB_ACTUAL_FACT_OPEN")
    require(meter.get("schema") == execution["meter_schema"] and
            meter.get("run_uuid") == uuid and meter.get("active") is True and
            meter.get("max_child_processes") == budgets["max_child_processes"] and
            meter.get("max_local_http_requests") == budgets["max_local_http_requests"] and
            meter.get("max_model_requests") == 0 and
            meter.get("egress_policy") == "LOOPBACK_ONLY_BLOCK_NONLOCAL", "ACTIVE_METER_FACT_OPEN")
    require(paths.get("schema") == execution["path_authority_schema"] and
            paths.get("run_uuid") == uuid and paths.get("environment") == current_scope["environment"] and
            paths.get("output_root") == source["output_root"] and
            paths.get("worktree") == str(ROOT) and paths.get("cwd") == str(ROOT),
            "PATH_AUTHORITY_NOT_ACTUAL")
    require(os_probe.get("schema") == "researchos.current58-whole-go-os-job-probe.v1" and
            os_probe.get("run_uuid") == uuid and os_probe.get("runner_pid") == outer["runner_pid"] and
            os_probe.get("job_controller_ref") == controller_source and
            os_probe.get("member_of_expected_job") is True and
            os_probe.get("kill_on_close_observed") is True, "ROOT_OS_JOB_PROBE_OPEN")
    require(controller_review.get("schema") == "researchos.current58-whole-go-cap-controller-review.v1" and
            controller_review.get("decision") == "CAP_CONTROLLER_REVIEWED" and
            controller_review.get("actor_id") not in (None, "", "codex:/root", source["owner"]) and
            controller_review.get("run_uuid") == uuid and
            controller_review.get("controller_source_ref") == controller_source and
            controller_review.get("os_probe_ref") == source["os_probe_ref"] and
            controller_review.get("outer_job_ref") == source["outer_job_ref"] and
            controller_review.get("meter_ref") == source["meter_ref"],
            "NON_AUTHOR_ACTUAL_CAP_REVIEW_OPEN")
    creation = observed_windows_process(outer["runner_pid"])
    require(controller_actual.get("schema") == "researchos.current58-whole-go-controller-actual.v1" and
            controller_actual.get("run_uuid") == uuid and
            controller_actual.get("runner_pid") == outer["runner_pid"] and
            type(controller_actual.get("pid_creation_filetime_100ns")) is int and
            controller_actual["pid_creation_filetime_100ns"] == creation and
            controller_actual.get("job_id") == outer.get("job_id") == os_probe.get("job_id") and
            isinstance(controller_actual.get("job_id"), str) and
            controller_actual.get("expected_job_membership_verified") is True and
            controller_actual.get("os_probe_ref") == source["os_probe_ref"] and
            controller_actual.get("controller_review_ref") == source["controller_review_ref"] and
            controller_actual.get("controller_source_ref") == controller_source and
            controller_actual.get("scope_ref") == source["scope_ref"] and
            controller_actual.get("registration_ref") == source["registration_ref"] and
            controller_actual.get("grant_ref") == source["grant_ref"] and
            controller_actual.get("absolute_deadline_monotonic") == outer.get("absolute_deadline_monotonic"),
            "ROOT_CONTROLLER_ACTUAL_OR_PROCESS_IDENTITY_OPEN")
    require(controller_actual_review.get("schema") ==
            "researchos.current58-whole-go-controller-actual-review.v1" and
            controller_actual_review.get("decision") == "ACTUAL_CONTROLLER_RECEIPT_REVIEWED" and
            controller_actual_review.get("actor_id") not in (None, "", "codex:/root", source["owner"]) and
            controller_actual_review.get("run_uuid") == uuid and
            controller_actual_review.get("controller_actual_receipt_ref") ==
            source["controller_actual_receipt_ref"] and
            controller_actual_review.get("controller_source_ref") == controller_source and
            controller_actual_review.get("pid_creation_filetime_100ns") == creation,
            "NON_AUTHOR_ACTUAL_CONTROLLER_REVIEW_OPEN")
    heartbeat_path = canonical(meter["heartbeat_path"])
    require(ROOT in heartbeat_path.parents, "METER_HEARTBEAT_FOREIGN")
    heartbeat_raw = heartbeat_path.read_bytes()
    heartbeat_ref = {"path": str(heartbeat_path), "sha256": hashlib.sha256(heartbeat_raw).hexdigest(),
                     "bytes": len(heartbeat_raw)}
    heartbeat = unique_json(heartbeat_raw)
    require(heartbeat.get("schema") == "researchos.current58-whole-go-meter-heartbeat.v1" and
            heartbeat.get("run_uuid") == uuid and heartbeat.get("active") is True and
            type(heartbeat.get("monotonic_tick")) in (int, float) and
            heartbeat.get("runner_pid") == outer["runner_pid"] and
            heartbeat.get("pid_creation_filetime_100ns") == creation and
            controller_actual.get("heartbeat_ref") == heartbeat_ref and
            type(controller_actual.get("observed_monotonic")) in (int, float) and
            0 <= time.monotonic() - controller_actual["observed_monotonic"] <= 5,
            "ACTIVE_HEARTBEAT_OPEN")
    age = time.monotonic() - heartbeat["monotonic_tick"]
    require(0 <= age <= 5, "METER_HEARTBEAT_STALE")
    observed = {
        "root_budget_values": {key: {"value": budgets[key], "source_ref": source["root_limits_ref"],
                                     "evidence_class": "DECLARED_ROOT_LIMIT"}
                               for key in execution["numeric_budget_keys"]},
        "runtime_cap_values": {
            "runner_pid": {"value": outer["runner_pid"], "source_ref": source["controller_actual_receipt_ref"],
                           "evidence_class": "OBSERVED_LIVE_PID_AND_CREATION"},
            "outer_max_child_processes": {"value": outer["max_child_processes"], "source_ref": source["outer_job_ref"],
                                          "evidence_class": "CONTROLLER_PREFLIGHT_LIMIT"},
            "meter_max_child_processes": {"value": meter["max_child_processes"], "source_ref": source["meter_ref"],
                                          "evidence_class": "METER_PREFLIGHT_LIMIT"},
            "meter_max_local_http_requests": {"value": meter["max_local_http_requests"], "source_ref": source["meter_ref"],
                                              "evidence_class": "METER_PREFLIGHT_LIMIT"},
            "meter_max_model_requests": {"value": meter["max_model_requests"], "source_ref": source["meter_ref"],
                                         "evidence_class": "METER_PREFLIGHT_LIMIT"},
            "heartbeat_age_seconds": {"value": age, "source_ref": heartbeat_ref,
                                      "evidence_class": "OBSERVED_RAW_HEARTBEAT_AGE"},
        },
    }
    require(len(observed["root_budget_values"]) + len(observed["runtime_cap_values"]) == 19,
            "NINETEEN_CAP_NUMBERS_NOT_DERIVED")
    bundle = {"schema": execution["authority_bundle_schema"], "run_uuid": uuid,
              "runner_pid": outer["runner_pid"],
              "pid_creation_filetime_100ns": creation,
              "absolute_deadline_monotonic": outer["absolute_deadline_monotonic"],
              "checkpoint_ref": source["checkpoint_ref"],
              "registration_ref": source["registration_ref"], "grant_ref": source["grant_ref"],
              "owner_lease_ref": source["owner_lease_ref"],
              "source_review_ref": source["source_review_ref"],
              "outer_job_ref": source["outer_job_ref"], "meter_ref": source["meter_ref"],
              "controller_actual_receipt_ref": source["controller_actual_receipt_ref"],
              "controller_actual_review_ref": source["controller_actual_review_ref"],
              "heartbeat_ref": heartbeat_ref,
              "path_authority_ref": source["path_authority_ref"],
              "scope_ref": source["scope_ref"]}
    return observed, bundle


def close(source):
    current_scope = verified_json(source["scope_ref"])
    require(current_scope == scope(source, require_fresh=False), "POSTRUN_SCOPE_NOT_CURRENT")
    run_output = canonical(current_scope["output_root"])
    runner_ref, terminal_ref = source.get("runner_report_ref"), source.get("runner_terminal_ref")
    require(runner_ref is None or canonical(runner_ref["path"]) == run_output / "report.json",
            "RUNNER_REPORT_NOT_FROM_THIS_OUTPUT")
    require(terminal_ref is None or canonical(terminal_ref["path"]) == run_output / "terminal.json",
            "RUNNER_TERMINAL_NOT_FROM_THIS_OUTPUT")
    runner = verified_json(runner_ref) if runner_ref is not None else {}
    terminal = verified_json(terminal_ref) if terminal_ref is not None else {}
    bundle = verified_json(source["authority_bundle_ref"])
    outer = verified_json(source["outer_job_final_ref"])
    meter = verified_json(source["meter_final_ref"])
    invocation = verified_json(source["root_invocation_ref"])
    require(bundle.get("schema") == "researchos.current58-whole-go-authority-bundle.v1" and
            bundle.get("run_uuid") == source["run_uuid"] and
            bundle.get("scope_ref") == source["scope_ref"] and
            bundle.get("registration_ref") == source["registration_ref"] and
            bundle.get("grant_ref") == source["grant_ref"] and
            bundle.get("checkpoint_ref") == source["checkpoint_ref"] and
            bundle.get("owner_lease_ref") == source["owner_lease_ref"] and
            bundle.get("outer_job_ref") == source["outer_job_ref"] and
            bundle.get("meter_ref") == source["meter_ref"], "POSTRUN_AUTHORITY_NOT_THIS_RUN")
    require(not runner or
            (runner.get("schema") == "researchos.current58-go-run-facts.v2" and
             runner.get("scope_ref") == source["scope_ref"] and
             runner.get("authority_ref") == source["authority_bundle_ref"]),
            "POSTRUN_RUNNER_REPORT_FOREIGN")
    require(not terminal or
            terminal.get("schema") == "researchos.current58-whole-go-provisional-terminal.v1",
            "POSTRUN_TERMINAL_SCHEMA_CHANGED")
    require(outer.get("schema") == "researchos.current58-whole-go-outer-job-final.v1" and
            meter.get("schema") == "researchos.current58-whole-go-meter-final.v1" and
            outer.get("run_uuid") == meter.get("run_uuid") == source["run_uuid"] and
            outer.get("preflight_ref") == source["outer_job_ref"] and
            meter.get("preflight_ref") == source["meter_ref"] and
            outer.get("runner_pid") == meter.get("runner_pid") == bundle.get("runner_pid") and
            outer.get("pid_creation_filetime_100ns") ==
            meter.get("pid_creation_filetime_100ns") ==
            bundle.get("pid_creation_filetime_100ns"),
            "POSTRUN_FINAL_RESOURCE_ORIGINS_FOREIGN")
    require(invocation.get("schema") == "researchos.current58-whole-go-root-once-invocation.v1" and
            invocation.get("run_uuid") == source["run_uuid"] and
            invocation.get("scope_ref") == source["scope_ref"] and
            invocation.get("authority_bundle_ref") == source["authority_bundle_ref"] and
            invocation.get("runner_report_ref") == runner_ref and
            invocation.get("runner_terminal_ref") == terminal_ref and
            invocation.get("outer_job_final_ref") == source["outer_job_final_ref"] and
            invocation.get("meter_final_ref") == source["meter_final_ref"] and
            invocation.get("automatic_retry") is False and
            invocation.get("counter_reset") is False, "ROOT_ONCE_PROVENANCE_OPEN")
    def nonnegative_int(value):
        return type(value) is int and value >= 0
    primary = runner.get("actual_primary_go_calls")
    outer_exit = invocation.get("actual_outer_exit")
    require((not runner or nonnegative_int(primary)) and
            (outer_exit is None or type(outer_exit) is int) and
            all(nonnegative_int(value) for value in
                (meter.get("model_request_count"), meter.get("local_http_request_count"),
                 outer.get("owned_process_count"), outer.get("owned_handle_count"))),
            "POSTRUN_COUNT_OR_EXIT_TYPE_INVALID")
    deadline = outer.get("absolute_deadline_monotonic")
    started, ended = invocation.get("started_monotonic"), invocation.get("ended_monotonic")
    report_end = runner.get("phase_ended_monotonic")
    terminal_tick = terminal.get("after_report_monotonic")
    cleanup_tick = outer.get("cleanup_ended_monotonic")
    require(all(type(tick) in (int, float) for tick in (deadline, started, ended, cleanup_tick)) and
            started <= ended <= cleanup_tick and
            outer.get("absolute_deadline_monotonic") == meter.get("absolute_deadline_monotonic") ==
            invocation.get("absolute_deadline_monotonic") ==
            bundle.get("absolute_deadline_monotonic"),
            "POSTRUN_DEADLINE_OR_TIME_ORIGIN_INVALID")
    for name in ("stdout_ref", "stderr_ref"):
        if invocation.get(name) is not None:
            verified_raw(invocation[name])
    terminal_typed = (not terminal or
                      (type(report_end) in (int, float) and type(terminal_tick) in (int, float) and
                       started <= report_end <= terminal_tick <= ended))
    require(terminal_typed, "POSTRUN_REPORT_TERMINAL_ORDER_INVALID")
    closed = (bool(runner) and bool(terminal) and
              type(primary) is int and primary <= current_scope["budgets"]["max_primary_go_calls"] and
              terminal.get("report_written") is True and
              terminal.get("within_absolute_deadline") is True and
              outer.get("all_owned_processes_exited") is True and
              outer.get("cleanup_completed") is True and
              outer["owned_process_count"] == outer["owned_handle_count"] == 0 and
              meter.get("process_count_over_cap") is False and
              meter.get("http_count_over_cap") is False and
              meter["model_request_count"] == 0 and
              ended <= cleanup_tick < deadline)
    return {"schema": "researchos.current58-whole-go-cap-close-observation.v1",
            "run_uuid": source["run_uuid"], "scope_ref": source["scope_ref"],
            "authority_bundle_ref": source["authority_bundle_ref"],
            "runner_report_ref": runner_ref, "runner_terminal_ref": terminal_ref,
            "root_invocation_ref": source["root_invocation_ref"],
            "outer_job_final_ref": source["outer_job_final_ref"],
            "meter_final_ref": source["meter_final_ref"],
            "actual_root_outer_exit": outer_exit,
            "actual_go_invocations": primary, "resource_lifecycle_closed": closed,
            "runner_report_written": terminal.get("report_written") if terminal else None,
            "within_absolute_deadline": terminal.get("within_absolute_deadline") if terminal else None,
            "first_cause": runner.get("first_cause") or invocation.get("first_cause"),
            "secondary_causes": runner.get("secondary_causes", []) + invocation.get("secondary_causes", []),
            "cost_usd": None, "cost_basis": "UNKNOWN", "source_acceptance": False,
            "whole_suite_qualified": False, "formal_case_accepted_delta": 0}


def main():
    require(len(sys.argv) == 5 and sys.argv[1] in {"attest", "scope", "arm", "close"},
            "USAGE_ATTEST_SCOPE_ARM_CLOSE")
    stage, input_path, output_dir = sys.argv[1], canonical(sys.argv[2]), canonical(sys.argv[3])
    require(output_dir.is_dir() and not list(output_dir.iterdir()), "FRESH_EMPTY_OUTPUT_DIRECTORY_REQUIRED")
    source_raw = input_path.read_bytes()
    require(hashlib.sha256(source_raw).hexdigest() == sys.argv[4], "ROOT_INPUT_RAW_SHA_DRIFT")
    source = unique_json(source_raw)
    identity(source, stage, output_dir)
    if stage == "attest":
        output = {"attestation.json": attest(source)}
    elif stage == "scope":
        output = {"scope.json": scope(source)}
    elif stage == "arm":
        numbers, bundle = arm(source)
        output = {"cap-observation.json": {"schema": "researchos.current58-whole-go-cap-observation.v1",
                "run_uuid": source["run_uuid"], "numeric_provenance": numbers,
                "actual_os_cap_qualification": False, "source_acceptance": False},
                  "authority-bundle.json": bundle}
    else:
        output = {"postrun-observation.json": close(source)}
    refs = {name: put_new(output_dir / name, value) for name, value in output.items()}
    print(json.dumps({"stage": stage, "source_only": True, "produced_refs": refs,
                      "authority_granted_by_producer": False}, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
