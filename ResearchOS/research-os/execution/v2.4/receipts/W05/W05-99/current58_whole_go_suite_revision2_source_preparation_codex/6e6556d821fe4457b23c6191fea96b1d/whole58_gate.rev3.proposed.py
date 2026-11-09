"""Proposed pre-execution Root gate for the finite current58 Go plan.

The Root producer must create and independently review all authority inputs.
This module validates them before any Go child is started. Merely writing the
proposed JSON schemas does not authorize execution.
"""
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import time

FROZEN_FINITE_SHA = "52828991f4f23d6957a3f7aa6343b50d8840efbe0ca42121871aa6bc8ce8c904"
FROZEN_FINITE_BYTES = 275734
LOCAL_LANES = {"BUILD_ONLY_NO_TOP_TEST", "STATIC_NO_RESOURCE_SIGNAL_REVIEW",
               "LOCAL_HTTP_FIXTURE_REVIEW", "CONDITIONAL_SKIP_REVIEW",
               "LOCAL_NATIVE_CHILD", "LOCAL_NODE_MU_TLS"}
ENV_KEYS = {"SystemRoot", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP",
            "GOTOOLCHAIN", "GOPROXY", "GOSUMDB", "GOMODCACHE", "GOCACHE", "GOTMPDIR",
            "GOOS", "GOARCH", "CGO_ENABLED", "GOROOT", "GOPATH",
            "RESEARCHOS_NODE", "RESEARCHOS_MU_BUNDLE", "W14_GO_TOOLCHAIN"}


def require(ok, code):
    if not ok:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "DUPLICATE_JSON_KEY")
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=unique)


def _not_reparse(path):
    info = path.lstat()
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    require(not path.is_symlink() and not getattr(os.path, "isjunction", lambda _: False)(path)
            and not (getattr(info, "st_file_attributes", 0) & flag), "REPARSE_RESOURCE_DENIED")
    return info


def absolute(path):
    require(isinstance(path, str) and Path(path).is_absolute(), "ABSOLUTE_PATH_REQUIRED")
    original = Path(path)
    _not_reparse(original)
    resolved = original.resolve(strict=True)
    require(str(resolved).casefold() == str(original).casefold(), "ALIAS_RESOURCE_DENIED")
    return resolved


def pin_file(path):
    info = _not_reparse(path)
    require(stat.S_ISREG(info.st_mode), "REGULAR_FILE_REQUIRED")
    raw = path.read_bytes()
    require(len(raw) == info.st_size, "FILE_CHANGED_WHILE_PINNING")
    return {"path": str(path), "sha256": sha(raw), "bytes": len(raw)}


def check_pin(claim, expected=None):
    require(isinstance(claim, dict) and set(claim) == {"path", "sha256", "bytes"}, "PIN_SHAPE")
    path = absolute(claim["path"])
    if expected is not None:
        require(path == expected, "PIN_PATH_NOT_EXPECTED")
    require(pin_file(path) == claim, "PIN_DRIFT")
    return path


def read_pin(claim, expected=None):
    path = check_pin(claim, expected)
    return path, strict_json(path.read_bytes())


def pin_matches(claim, path):
    require(claim == pin_file(path), "SOURCE_CODE_OR_CONTRACT_DRIFT")


def curated_go_tree(root):
    """Mirror runtime_check_windows.go/checkTree curatedGo selection, not a file-only API."""
    info = _not_reparse(root)
    require(stat.S_ISDIR(info.st_mode) and root == root.resolve(strict=True), "GO_ROOT_DIRECTORY_REQUIRED")
    members = []
    total = 0

    def walk(directory, rel_prefix):
        nonlocal total
        for entry in sorted(os.scandir(directory), key=lambda item: item.name):
            rel = (rel_prefix + "/" + entry.name).lstrip("/")
            if not rel_prefix:
                if entry.is_dir(follow_symlinks=False) and entry.name not in {"bin", "pkg", "lib", "src"}:
                    continue
                if entry.is_file(follow_symlinks=False) and entry.name not in {"VERSION", "go.env"}:
                    continue
            if rel in {"src/cmd", "src/testdata"} and entry.is_dir(follow_symlinks=False):
                continue
            if rel_prefix == "src" and entry.is_file(follow_symlinks=False) and rel not in {"src/go.mod", "src/go.sum"}:
                continue
            path = Path(entry.path)
            item = _not_reparse(path)
            if stat.S_ISDIR(item.st_mode):
                walk(path, rel)
                continue
            require(stat.S_ISREG(item.st_mode), "NONREGULAR_GO_TREE_MEMBER")
            require(len(members) < 25000 and item.st_size <= (768 << 20) - total,
                    "GO_TREE_STAGING_LIMIT")
            raw = path.read_bytes()
            require(len(raw) == item.st_size, "GO_TREE_CHANGED_DURING_READ")
            total += len(raw)
            members.append({"path": rel, "sha256": "sha256:" + sha(raw), "size_bytes": len(raw)})

    walk(root, "")
    require(any(row["path"] == "bin/go.exe" for row in members), "GO_TREE_EXECUTABLE_MISSING")
    return members, total


def validate_go_tree(tree_ref, attestation_ref, attestation_review_ref,
                     go_ref, locked, root, run_uuid):
    _, tree = read_pin(tree_ref)
    require(tree.get("schema") == "researchos.current58-frozen-go-toolchain-tree.v1"
            and tree.get("selection") == "runtime_check_windows.go/checkTree:curatedGo",
            "GO_TREE_SCHEMA_OR_SELECTION")
    go_root = absolute(tree.get("root_path"))
    require(go_root.is_dir() and go_root != absolute(go_ref["path"]), "GO_TREE_NOT_DIRECTORY")
    members, total = curated_go_tree(go_root)
    require(tree.get("members") == members and tree.get("member_count") == len(members)
            and tree.get("total_bytes") == total, "GO_TREE_MEMBERSHIP_DRIFT")
    go_path = absolute(go_ref["path"])
    require(go_path == go_root / "bin" / "go.exe" and pin_file(go_path) == go_ref
            and go_ref["sha256"] == locked["tools"]["go"]["sha256"]
            and go_path == absolute(locked["tools"]["go"]["path"]), "GO_EXE_TREE_OR_LOCK_MISMATCH")
    go_entry = next(row for row in members if row["path"] == "bin/go.exe")
    require(go_entry["sha256"] == "sha256:" + go_ref["sha256"], "GO_BUILD_HASH_MISMATCH")
    _, attestation = read_pin(attestation_ref)
    selection_raw = json.dumps(members, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
    require(attestation.get("schema") == "researchos.current58-frozen-go-hash-attestation.v2"
            and attestation.get("run_uuid") == run_uuid
            and attestation.get("root_path") == str(go_root)
            and attestation.get("go_tree_ref") == tree_ref
            and attestation.get("go_executable_ref") == go_ref
            and attestation.get("locked_toolchain_ref") == pin_file(root / "execution/toolchains/locked.json")
            and attestation.get("selection_members_sha256") == sha(selection_raw)
            and attestation.get("build_hash") == go_entry["sha256"]
            and isinstance(tree.get("frozen_go_tree_hash"), str)
            and tree["frozen_go_tree_hash"].startswith("sha256:")
            and attestation.get("tree_hash") == tree["frozen_go_tree_hash"]
            and attestation.get("implementation_ref") == pin_file(root / "internal/host/runtime_check_windows.go")
            and attestation.get("producer") == "ROOT_ACTUAL_FROZEN_GO_TOOLCHAIN_HASH"
            and attestation.get("actor_id") == "codex:/root"
            and "independent_review_ref" not in attestation,
            "GO_NATIVE_TREE_ATTESTATION_OPEN")
    native_ref = attestation.get("native_result_ref")
    _, native = read_pin(native_ref)
    require(native.get("schema") == "researchos.current58-frozen-go-native-result.v1"
            and native.get("run_uuid") == run_uuid
            and native.get("actual_exit") == 0
            and native.get("go_executable_ref") == go_ref
            and native.get("tree_hash") == attestation["tree_hash"]
            and native.get("build_hash") == attestation["build_hash"]
            and native.get("implementation_ref") == attestation["implementation_ref"],
            "GO_NATIVE_HASH_RESULT_NOT_BOUND")
    _, review = read_pin(attestation_review_ref)
    require(review.get("schema") == "researchos.current58-frozen-go-independent-review.v1"
            and review.get("decision") == "PASS"
            and review.get("run_uuid") == run_uuid
            and review.get("attestation_ref") == attestation_ref
            and review.get("native_result_ref") == native_ref
            and review.get("go_tree_ref") == tree_ref
            and review.get("actor_id") not in (None, "", attestation["actor_id"]),
            "GO_TREE_ATTESTATION_NOT_REVIEWED")
    return go_root, go_path, tree


def plan(contract, selected_lanes, go_path):
    calls = []
    for package in contract["packages"]:
        name = package["directory"]
        arg = package["import_arg"]
        require(isinstance(name, str) and isinstance(arg, str)
                and arg == "./" + name and ".." not in Path(name).parts,
                "PACKAGE_IMPORT_ARG_CHANGED")
        calls.append({"kind": "list", "package": name, "lane": None,
                      "argv_template": [str(go_path), "test", "-list", ".", arg]})
        for lane in selected_lanes:
            entry = package["lanes"].get(lane)
            if entry is None or (not entry["windows_candidate_names"] and lane != "BUILD_ONLY_NO_TOP_TEST"):
                continue
            names = entry["windows_candidate_names"]
            regex = "^(?:" + "|".join(names) + ")$" if names else "^$"
            require(entry["exact_top_regex"] == regex, "LANE_REGEX_DRIFT")
            calls.append({"kind": "lane", "package": name, "lane": lane,
                          "selected": names,
                          "argv_template": [str(go_path), "test", "-json", "-count=1", "-run", regex,
                                            "-timeout", "<BOUNDED_DURATION>", arg]})
    return calls


def _in_current_windows_job():
    if os.name != "nt":
        return False
    kernel = ctypes.windll.kernel32
    assigned = ctypes.c_int(0)
    ok = kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(assigned))
    return bool(ok and assigned.value)


def _heartbeat(root, meter):
    path = absolute(meter["heartbeat_path"])
    require(root in path.parents, "METER_HEARTBEAT_FOREIGN")
    raw = strict_json(path.read_bytes())
    require(raw.get("schema") == "researchos.current58-whole-go-meter-heartbeat.v1"
            and raw.get("run_uuid") == meter["run_uuid"] and raw.get("active") is True
            and isinstance(raw.get("monotonic_tick"), (int, float))
            and 0 <= time.monotonic() - raw["monotonic_tick"] <= 5,
            "OUTER_METER_NOT_LIVE")


def validate(root, runner_path, gate_path, finite_path, execution_path,
             scope_ref, authorization_ref, phase_started):
    """Return only a validated local execution plan; every missing future fact is OPEN."""
    scope_path, scope = read_pin(scope_ref)
    auth_path, auth = read_pin(authorization_ref)
    finite_raw = finite_path.read_bytes()
    require(sha(finite_raw) == FROZEN_FINITE_SHA and len(finite_raw) == FROZEN_FINITE_BYTES,
            "REVIEWED_FINITE_CONTRACT_DRIFT")
    finite = strict_json(finite_raw)
    _, execution = read_pin(scope.get("execution_contract_ref"), execution_path)
    require(execution.get("schema") == "researchos.current58-whole-go-execution-contract.v2"
            and execution["frozen_finite_contract"]["sha256"] == FROZEN_FINITE_SHA,
            "EXECUTION_CONTRACT_NOT_REVIEWED")
    require(root == root.resolve(strict=True)
            and Path.cwd().resolve(strict=True) == root
            and scope.get("worktree") == str(root)
            and absolute(scope["worktree"]) == root,
            "ACTUAL_ROOT_WORKTREE_CWD_NOT_BOUND")
    require(scope.get("schema") == execution["scope_schema"]
            and auth.get("schema") == execution["authority_bundle_schema"]
            and scope.get("source_commit") == finite["source_commit"]
            and scope.get("target_os") == "windows" and scope.get("target_arch") == "amd64"
            and os.name == "nt", "SCOPE_SOURCE_OR_HOST_MISMATCH")
    require(scope.get("finite_contract_ref") == pin_file(finite_path)
            and scope.get("runner_ref") == pin_file(runner_path)
            and scope.get("gate_ref") == pin_file(gate_path), "RUNNER_GATE_CONTRACT_NOT_PINNED")
    _, source_manifest = read_pin(scope.get("source_manifest_ref"))
    require(source_manifest.get("schema") == "researchos.current58-whole-go-source-preparation-manifest.v1"
            and all(pin_file(path) in source_manifest.get("members", [])
                    for path in (runner_path, gate_path, execution_path, finite_path)),
            "CURRENT_SOURCE_MANIFEST_NOT_CLOSED")
    require(auth.get("scope_ref") == scope_ref and auth.get("run_uuid") == scope.get("run_uuid"),
            "AUTH_SCOPE_NOT_CURRENT")
    uuid = scope["run_uuid"]
    require(isinstance(uuid, str) and len(uuid) == 32 and all(c in "0123456789abcdef" for c in uuid),
            "RUN_UUID_SHAPE")
    lanes = scope.get("selected_lanes")
    require(isinstance(lanes, list) and lanes and len(lanes) == len(set(lanes))
            and set(lanes) <= LOCAL_LANES and "REAL_MODEL_B01_HOLD" not in lanes,
            "SELECTED_LANES_NOT_LOCAL")
    budgets = scope.get("budgets")
    keys = execution["numeric_budget_keys"]
    require(isinstance(budgets, dict) and set(budgets) == set(keys)
            and all(type(budgets[k]) is int and budgets[k] > 0 for k in keys if k != "max_model_requests")
            and budgets.get("max_model_requests") == 0 and budgets["max_child_processes"] >= 1
            and budgets["total_wall_seconds"] > budgets["cleanup_reserve_seconds"]
            + budgets["finalization_reserve_seconds"] + budgets["io_reserve_seconds"],
            "NUMERIC_BUDGET_OR_RESERVE_OPEN")
    env = scope.get("environment")
    require(isinstance(env, dict) and set(env) <= ENV_KEYS
            and all(isinstance(v, str) for v in env.values()), "ENVIRONMENT_SHAPE")
    require(set(env) <= ENV_KEYS and all(isinstance(v, str) for v in env.values())
            and env.get("GOTOOLCHAIN") == "local" and env.get("GOPROXY") == "off"
            and env.get("GOSUMDB") == "off" and env.get("GOOS") == "windows"
            and env.get("GOARCH") == "amd64"
            and all(env.get(k) for k in ("PATH", "TEMP", "TMP", "GOCACHE", "GOMODCACHE", "GOTMPDIR")),
            "GO_ENV_NOT_OFFLINE_OR_FROZEN")
    locked = strict_json((root / "execution/toolchains/locked.json").read_bytes())
    _, runtime = read_pin(scope.get("runtime_catalog_ref"))
    require(runtime.get("schema") == "researchos.current58-whole-go-runtime-resources.v2"
            and isinstance(runtime.get("file_members"), list), "RUNTIME_CATALOG_SHAPE")
    file_members = runtime["file_members"]
    require(file_members and len({x["path"].casefold() for x in file_members}) == len(file_members),
            "RUNTIME_FILE_DUPLICATE")
    for row in file_members:
        check_pin(row)
    go_tree_ref = scope.get("go_tree_ref")
    require(runtime.get("go_tree_ref") == go_tree_ref, "RUNTIME_GO_TREE_REF_MISMATCH")
    go_root, go_path, tree = validate_go_tree(
        go_tree_ref, scope.get("go_tree_attestation_ref"),
        scope.get("go_tree_attestation_review_ref"), scope.get("pinned_go_ref"),
        locked, root, uuid)
    require(env.get("W14_GO_TOOLCHAIN") == str(go_root) if "LOCAL_NATIVE_CHILD" in lanes else
            env.get("W14_GO_TOOLCHAIN", "") in ("", str(go_root)), "W14_DIRECTORY_ABI_OR_SKIP")
    for key in ("RESEARCHOS_NODE", "RESEARCHOS_MU_BUNDLE"):
        if key in env:
            require(env[key] in {row["path"] for row in file_members}, "ENV_FILE_TOOL_NOT_PINNED")
    require("LOCAL_NODE_MU_TLS" not in lanes or all(env.get(k) for k in
            ("RESEARCHOS_NODE", "RESEARCHOS_MU_BUNDLE")), "NODE_MU_RESOURCES_OPEN")
    calls = plan(finite, lanes, go_path)
    require(scope.get("planned_invocations") == calls
            and budgets["max_primary_go_calls"] >= len(calls), "FINITE_PLAN_NOT_EXACT")
    require(scope.get("public_catalog_ref") == finite["public_source_catalog_ref"],
            "PUBLIC_SOURCE_CATALOG_NOT_FIXED")
    check_pin(scope["public_catalog_ref"])
    output = absolute(scope.get("output_root"))
    require(output.is_dir() and not list(output.iterdir()), "OUTPUT_ROOT_NOT_FRESH")
    for cache_key in ("GOCACHE", "GOMODCACHE", "GOTMPDIR", "TEMP", "TMP"):
        cache_path = absolute(env[cache_key])
        require(cache_path.is_dir() and cache_path != output
                and output not in cache_path.parents and cache_path not in output.parents,
                "CACHE_OR_TEMP_ROOT_OVERLAPS_OUTPUT")
    cp_path = root / "execution/v2.4/checkpoint.json"
    _, cp = read_pin(auth.get("checkpoint_ref"), cp_path)
    require(cp.get("head") == finite["source_commit"] and cp.get("project_id") == scope.get("project_id"),
            "CHECKPOINT_SOURCE_OR_IDENTITY_CHANGED")
    wip = cp.get("work_in_progress", {})
    require(wip.get("whole58_active_run_uuid") == uuid
            and wip.get("whole58_registration_ref") == auth.get("registration_ref")
            and wip.get("whole58_owner_lease_ref") == auth.get("owner_lease_ref"),
            "CHECKPOINT_HAS_NO_ACTUAL_WHOLE58_REGISTRATION")
    _, registration = read_pin(auth.get("registration_ref"))
    _, grant = read_pin(auth.get("grant_ref"))
    _, lease = read_pin(auth.get("owner_lease_ref"))
    _, review = read_pin(auth.get("source_review_ref"))
    require(registration.get("schema") == execution["root_registration_schema"]
            and registration.get("actor_id") == "codex:/root"
            and registration.get("run_uuid") == uuid
            and registration.get("scope_path") == str(scope_path)
            and registration.get("source_commit") == finite["source_commit"]
            and registration.get("planned_invocations") == calls
            and registration.get("output_root") == str(output)
            and registration.get("owner") == scope.get("owner")
            and registration.get("worktree") == str(root)
            and registration.get("cwd") == str(root)
            and registration.get("source_manifest_ref") == scope["source_manifest_ref"]
            and registration.get("go_tree_attestation_review_ref") ==
                scope["go_tree_attestation_review_ref"],
            "ACTUAL_ROOT_REGISTRATION_MISMATCH")
    require(review.get("schema") == execution["non_author_review_schema"]
            and review.get("decision") == "SOURCE_AND_PLAN_REVIEWED"
            and review.get("actor_id") not in (None, "", registration["actor_id"], scope["owner"])
            and review.get("registration_ref") == auth["registration_ref"]
            and review.get("scope_ref") == scope_ref
            and review.get("finite_contract_ref") == scope["finite_contract_ref"]
            and review.get("source_manifest_ref") == scope["source_manifest_ref"]
            and review.get("go_tree_attestation_review_ref") ==
                scope["go_tree_attestation_review_ref"],
            "NON_AUTHOR_SOURCE_REVIEW_OPEN")
    require(grant.get("schema") == execution["root_grant_schema"]
            and grant.get("actor_id") == "codex:/root"
            and grant.get("decision") == "ALLOW_LOCAL_GO_ONLY"
            and grant.get("run_uuid") == uuid
            and grant.get("scope_ref") == scope_ref
            and grant.get("registration_ref") == auth["registration_ref"]
            and grant.get("source_review_ref") == auth["source_review_ref"]
            and grant.get("selected_lanes") == lanes
            and grant.get("budgets") == budgets
            and grant.get("environment") == env
            and grant.get("worktree") == str(root)
            and grant.get("cwd") == str(root)
            and grant.get("planned_invocations") == calls
            and grant.get("runtime_catalog_ref") == scope["runtime_catalog_ref"]
            and grant.get("source_manifest_ref") == scope["source_manifest_ref"]
            and grant.get("go_tree_attestation_ref") == scope["go_tree_attestation_ref"]
            and grant.get("go_tree_attestation_review_ref") ==
                scope["go_tree_attestation_review_ref"]
            and grant.get("allow_model_requests") is False, "ROOT_GRANT_NOT_CURRENT_OR_BOUNDED")
    until = lease.get("expires_at_utc")
    require(lease.get("schema") == execution["owner_lease_schema"]
            and lease.get("state") == "ACTIVE"
            and lease.get("run_uuid") == uuid and lease.get("owner") == scope["owner"]
            and lease.get("worktree") == scope.get("worktree") == str(root)
            and isinstance(until, str)
            and datetime.fromisoformat(until.replace("Z", "+00:00")) > datetime.now(timezone.utc),
            "OWNER_WORKTREE_LEASE_NOT_ACTIVE")
    require(any(row.get("step_id") == "W05-99" and row.get("slice_id") == "WHOLE58_GO"
                and row.get("owner") == scope["owner"] and row.get("scope_ref") == scope_ref
                and row.get("lease_ref") == auth["owner_lease_ref"]
                for row in cp.get("workers", [])), "CHECKPOINT_WORKER_LEASE_MISMATCH")
    _, outer = read_pin(auth.get("outer_job_ref"))
    _, meter = read_pin(auth.get("meter_ref"))
    _, paths = read_pin(auth.get("path_authority_ref"))
    require(outer.get("schema") == execution["outer_job_schema"]
            and outer.get("run_uuid") == uuid and outer.get("runner_pid") == os.getpid()
            and outer.get("kill_on_close") is True
            and outer.get("deadline_enforced") is True
            and outer.get("max_child_processes") == budgets["max_child_processes"]
            and _in_current_windows_job(), "ACTUAL_OUTER_JOB_NOT_ASSIGNED")
    require(meter.get("schema") == execution["meter_schema"]
            and meter.get("run_uuid") == uuid and meter.get("active") is True
            and meter.get("max_child_processes") == budgets["max_child_processes"]
            and meter.get("max_local_http_requests") == budgets["max_local_http_requests"]
            and meter.get("max_model_requests") == 0
            and meter.get("egress_policy") == "LOOPBACK_ONLY_BLOCK_NONLOCAL"
            and paths.get("schema") == execution["path_authority_schema"]
            and paths.get("run_uuid") == uuid and paths.get("environment") == env
            and paths.get("output_root") == str(output)
            and paths.get("worktree") == str(root)
            and paths.get("cwd") == str(root), "ACTIVE_METERS_OR_PATH_AUTHORITY_OPEN")
    _heartbeat(root, meter)
    require(time.monotonic() - phase_started < budgets["total_wall_seconds"]
            - budgets["cleanup_reserve_seconds"] - budgets["finalization_reserve_seconds"]
            - budgets["io_reserve_seconds"], "PREFLIGHT_EXHAUSTED_TOTAL_DEADLINE")
    return {"scope_ref": scope_ref, "authorization_ref": authorization_ref,
            "checkpoint_ref": auth["checkpoint_ref"], "lease_ref": auth["owner_lease_ref"],
            "meter": meter, "go_path": go_path, "go_root": go_root,
            "output": output, "env": env, "lanes": lanes, "budgets": budgets,
            "planned_invocations": calls, "finite": finite, "scope": scope,
            "source_catalog_ref": scope["public_catalog_ref"], "registration_ref": auth["registration_ref"],
            "grant_ref": auth["grant_ref"], "tree": tree,
            "source_manifest_ref": scope["source_manifest_ref"],
            "go_tree_attestation_ref": scope["go_tree_attestation_ref"],
            "go_tree_attestation_review_ref": scope["go_tree_attestation_review_ref"],
            "outer_job_ref": auth["outer_job_ref"], "meter_ref": auth["meter_ref"],
            "path_authority_ref": auth["path_authority_ref"]}


def recheck_before_launch(root, authority):
    """Fail closed if canonical authority changed or the live meter stopped."""
    read_pin(authority["checkpoint_ref"], root / "execution/v2.4/checkpoint.json")
    _, lease = read_pin(authority["lease_ref"])
    require(lease.get("state") == "ACTIVE" and
            datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00")) > datetime.now(timezone.utc),
            "OWNER_LEASE_EXPIRED_DURING_RUN")
    for name in ("outer_job_ref", "meter_ref", "path_authority_ref", "registration_ref",
                 "grant_ref", "source_manifest_ref", "go_tree_attestation_ref",
                 "go_tree_attestation_review_ref"):
        check_pin(authority[name])
    _heartbeat(root, authority["meter"])
    require(Path.cwd().resolve(strict=True) == root
            and authority["scope"].get("worktree") == str(root)
            and _in_current_windows_job(), "RUNNER_LEFT_OUTER_JOB_OR_CWD")
