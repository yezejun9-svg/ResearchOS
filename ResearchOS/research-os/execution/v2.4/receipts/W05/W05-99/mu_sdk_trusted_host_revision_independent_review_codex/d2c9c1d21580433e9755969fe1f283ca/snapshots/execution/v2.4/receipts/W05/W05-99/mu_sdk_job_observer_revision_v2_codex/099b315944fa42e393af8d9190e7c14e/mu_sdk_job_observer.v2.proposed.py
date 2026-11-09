"""Independent-source automated observer, called by Root before first ResumeThread.

Import defines functions only. It does not create processes, query Windows, issue
grants, or write receipts. Runtime observation uses Root's real process handles;
the program author is not represented as a human observing a separate tool call.
This is admission evidence only, never product acceptance or final cleanup.
"""

import ast
import ctypes
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import stat
import time
import types
from datetime import datetime, timezone

AUTHOR = "codex:/root/w05_merge_review"
ACTOR = "program:researchos.mu-sdk-job-observer.v1"
ROOT_ACTOR = "codex:/root"
SOURCE_COMMIT = "adc460c2138528f163f7fdab5e8d81dde157b7fb"
LIMITS = {"maximum_provider_requests": 3, "requested_output_tokens_total": 8192,
          "total_wall_seconds": 300}
PUBLIC_ENVIRONMENT_KEYS = ("SystemRoot", "WINDIR", "PATH", "USERPROFILE",
                           "LOCALAPPDATA", "APPDATA", "TEMP", "TMP")
RUNNER_REF = {
    "path": r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\mu_model_sdk_real_trial_v8_source_codex\8251b1ed21754f7cbd6c2f8e7ff574eb\mu_sdk_trial.v8.proposed.py",
    "sha256": "5b112a0824ab3bbbabb228416a9c2d0aa0be70ac2a45f29720138de350507fde", "bytes": 90096}
BASE_REF = {
    "path": "D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py",
    "sha256": "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad", "bytes": 18901}
SIGNATURE = "def run_owned(argv, cwd, env, stdout, stderr, timeout, stdin=None, creation_flags=0):"
ASSIGNED = "        cleanup['assigned_before_resume'] = True\n"
HOOK = """        if before_resume is not None:
            before_resume({
                'process_handle': int(pi.hProcess), 'thread_handle': int(pi.hThread),
                'job_handle': int(job), 'runner_pid': int(pi.dwProcessId),
                'creation_time_100ns': result['creation_time_100ns'],
                'started_monotonic': started, 'absolute_deadline_monotonic': started + timeout,
                'assigned_before_resume': cleanup['assigned_before_resume'],
                'kill_on_job_close_configured': cleanup['kill_on_job_close_configured'],
                'resumed': False,
            })
"""


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strict_json(raw):
    def unique(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError("nonfinite JSON constant " + value)
    result = json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)
    require(isinstance(result, dict), "JSON object required")
    return result


def checked_path(raw, directory=False):
    require(isinstance(raw, str) and Path(raw).is_absolute(), "absolute path required")
    path = Path(raw)
    require(path.exists(), "path absent: " + raw)
    for item in (path, *path.parents):
        info = item.lstat()
        require(not item.is_symlink() and
                not getattr(info, "st_file_attributes", 0) & 0x400,
                "reparse path: " + str(item))
    require(str(path.resolve(strict=True)).casefold() == str(path).casefold(),
            "noncanonical path")
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else
            stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
            "unexpected file type or hardlink")
    return path


def pin_bytes(pin):
    require(isinstance(pin, dict) and set(pin) == {"path", "sha256", "bytes"},
            "three-key pin required")
    require(type(pin["bytes"]) is int and pin["bytes"] >= 0 and
            isinstance(pin["sha256"], str) and len(pin["sha256"]) == 64,
            "pin value types")
    raw = checked_path(pin["path"]).read_bytes()
    require(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
            "file pin changed: " + pin["path"])
    return raw


def pin_json(pin):
    return strict_json(pin_bytes(pin))


def pin_of(path, raw):
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def validate_limits(doc, reg, job, now):
    require(all(type(doc.get(k)) is int and doc[k] == v for k, v in LIMITS.items()) and
            reg.get("limits") == LIMITS and job.get("wall_seconds") == 300,
            "finite limits changed")
    require(type(doc.get("qualification_requests")) is int and doc["qualification_requests"] == 1 and
            type(doc.get("ordinary_requests")) is int and doc["ordinary_requests"] == 2,
            "request partition changed")
    start, deadline = reg.get("started_monotonic"), reg.get("absolute_deadline_monotonic")
    require(all(type(v) in (int, float) and math.isfinite(v) for v in (start, deadline, now)) and
            0 < deadline - start <= 300 and start <= now < deadline and
            deadline == job.get("absolute_deadline_monotonic"), "deadline changed or exhausted")
    return start, deadline


def validate_public_environment(public_environment):
    require(isinstance(public_environment, dict) and
            set(public_environment) <= set(PUBLIC_ENVIRONMENT_KEYS) and
            all(type(k) is str and type(v) is str and "\x00" not in v
                for k, v in public_environment.items()), "public worker environment is not closed")
    require(public_environment.get("SystemRoot") == "C:/Windows" and
            public_environment.get("WINDIR") == "C:/Windows", "public Windows root changed")
    return dict(public_environment)


def phase_projection(doc, runner_raw, public_environment):
    tree = ast.parse(runner_raw)
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("PHASE_BASIS_KEYS", "PROVIDER", "MODEL", "BASE", "CREDENTIAL_REF"):
                constants[name] = ast.literal_eval(node.value)
    keys = constants["PHASE_BASIS_KEYS"]
    require(all(key in doc for key in keys), "incomplete immutable phase basis")
    cli = str(Path(doc["cli_binary"]["path"]))
    mode = doc["phase"]
    require(mode in ("bootstrap", "execute"), "phase unsupported")
    if mode == "bootstrap":
        argv = {"cli-init": [cli, "init", doc["workspace"]],
                "cli-goal": [cli, "goal", doc["goal_objective"], "--project", "<CLI_INIT_PROJECT_ID>", "--draft"]}
    else:
        argv = {"cli-config": [cli, "config", "set-model", "--model", constants["PROVIDER"] + "/" + constants["MODEL"],
                              "--base-url", constants["BASE"], "--config-revision", str(doc["config_revision"]),
                              "--credential-ref", constants["CREDENTIAL_REF"], "--default"],
                "cli-run": [cli, "run", doc["prompt"], "--project", doc["project_id"], "--output", "jsonl"]}
    env = validate_public_environment(public_environment)
    env.update(RESEARCHOS_CLI_DISCOVERY=doc["discovery_file"], RESEARCHOS_CLI_CONFIG=doc["cli_config_file"])
    return {"schema": "researchos.mu-sdk-trial-phase-basis.v1", "phase": mode,
            "run_uuid": doc["run_uuid"], "source_ref": RUNNER_REF,
            "consumed_input": {key: doc[key] for key in keys}, "child_argv": argv,
            "cwd": str(Path(doc["repository_root"])), "child_environment": env}


def validate_source_review(review, context):
    require(review.get("schema") == "researchos.mu-sdk-controller-observer-independent-source-review.v2" and
            review.get("decision") == "READY_SOURCE_ONLY" and
            review.get("actor_id") not in (None, "", ROOT_ACTOR, AUTHOR, ACTOR) and
            review.get("controller_source_ref") == context["controller_source"] and
            review.get("observer_source_ref") == context["observer_source"] and
            review.get("hooks_source_ref") == context["hooks_source"] and
            review.get("runner_source_ref") == RUNNER_REF and
            review.get("phase_worker_source_ref") == context["phase_worker_source"] and
            review.get("python_binary_ref") == context["python_binary"] and
            review.get("callback_contract") == "REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME" and
            review.get("formal_acceptance") is False,
            "independent source review missing or wrong source tuple")


def validate_launch_inputs(context, basis):
    """Use each checked byte buffer directly; no hash-then-second-read source load."""
    worker_raw = pin_bytes(context["phase_worker_source"])
    python_raw = pin_bytes(context["python_binary"])
    worker_path = Path(context["phase_worker_source"]["path"])
    python_path = Path(context["python_binary"]["path"])
    require(worker_path.suffix == ".py" and python_path.suffix.casefold() == ".exe",
            "reviewed worker or Python binary type")
    compile(worker_raw, str(worker_path), "exec", dont_inherit=True)
    public_env = validate_public_environment(context["public_environment"])
    frozen_env = dict(basis["child_environment"])
    doc = context["input_doc"]
    require(frozen_env.pop("RESEARCHOS_CLI_DISCOVERY", None) == doc["discovery_file"] and
            frozen_env.pop("RESEARCHOS_CLI_CONFIG", None) == doc["cli_config_file"] and
            frozen_env == public_env, "worker environment differs from complete frozen basis")
    phase_dir = Path(context["phase_dir"])
    input_path = phase_dir / "input.execute.json"
    require(not os.path.lexists(input_path), "phase input was already present before admission")
    return {"argv": [str(python_path), "-I", "-S", "-X", "utf8", str(worker_path), str(input_path)],
            "cwd": str(Path("D:/作品集/ResearchOS/research-os")), "public_environment": public_env,
            "phase_worker_source_ref": context["phase_worker_source"],
            "python_binary_ref": context["python_binary"],
            "worker_checked_bytes": len(worker_raw), "python_checked_bytes": len(python_raw)}


def validate_callback_launch(context, loc, state):
    launch = state["launch"]
    actual_env = validate_public_environment(loc["env"])
    require(type(loc["argv"]) is list and loc["argv"] == launch["argv"],
            "actual process argv differs from reviewed Python/worker/input vector")
    require(type(loc["cwd"]) is str and loc["cwd"] == launch["cwd"],
            "actual process cwd differs from canonical repository root")
    require(actual_env == launch["public_environment"] == context["public_environment"],
            "actual worker environment differs from frozen phase basis")
    return {"argv": list(loc["argv"]), "cwd": loc["cwd"],
            "phase_worker_source_ref": launch["phase_worker_source_ref"],
            "python_binary_ref": launch["python_binary_ref"],
            "public_environment_sha256": hashlib.sha256(json_bytes(actual_env)).hexdigest()}


def mode_public_pins(doc):
    require(doc.get("phase") in ("bootstrap", "execute"), "phase unsupported")
    if doc["phase"] == "bootstrap":
        require("runtime_profile" in doc and "public_route_manifest" in doc and
                doc["runtime_profile"] is None and doc["public_route_manifest"] is None,
                "bootstrap must explicitly preserve unqualified null public runtime refs")
        return ()
    keys = ("runtime_profile", "public_route_manifest", "cancel_fixture_receipt", "bootstrap_receipt")
    require(all(isinstance(doc.get(key), dict) and set(doc[key]) == {"path", "sha256", "bytes"}
                for key in keys), "execute requires all exact public/evidence pins")
    return keys


def validate_context(context, pid):
    doc = context["input_doc"]
    validate_public_environment(context["public_environment"])
    require(doc.get("schema") == "researchos.mu-sdk-trial.executable-input.v1" and
            doc.get("source_commit") == SOURCE_COMMIT, "input schema or commit")
    uuid = doc.get("run_uuid")
    require(isinstance(uuid, str) and len(uuid) == 32 and all(c in "0123456789abcdef" for c in uuid), "UUID")
    runner = pin_bytes(RUNNER_REF)
    for key in ("controller_source", "hooks_source", "observer_source"):
        pin_bytes(context[key])
    require(Path(context["observer_source"]["path"]) == Path(__file__).resolve(), "observer source location")
    validate_source_review(pin_json(context["independent_source_review"]), context)
    reg = pin_json(doc["root_registration"])
    cp = pin_json(doc["root_checkpoint"])
    lease = pin_json(doc["owner_lease"])
    basis = pin_json(doc["input_basis_ref"])
    job = pin_json(context["outer_job_contract"])
    require(basis == phase_projection(doc, runner, context["public_environment"]),
            "phase basis is not current closed input projection")
    for key in ("cli_binary", "intake_review", *mode_public_pins(doc)):
        pin_bytes(doc[key])
    require(reg.get("schema") == "researchos.mu-sdk-trial-root-registration.v1" and
            reg.get("actor_id") == ROOT_ACTOR and reg.get("run_uuid") == uuid and
            reg.get("phase") == doc["phase"] and reg.get("source_commit") == SOURCE_COMMIT and
            reg.get("source_ref") == RUNNER_REF and reg.get("owner") not in (None, "", ACTOR) and
            reg.get("input_basis_ref") == doc["input_basis_ref"] and
            reg.get("runtime_profile_ref") == doc["runtime_profile"] and
            reg.get("public_route_manifest_ref") == doc["public_route_manifest"], "registration binding")
    for key in ("data_root", "workspace", "repository_root", "once_path", "qualification_task_id",
                "qualification_run_id", "qualification_epoch", "runtime_id", "profile_entity_ref", "qualification_profile_hash"):
        require(reg.get(key) == doc.get(key), "registration field " + key)
    require(reg.get("started_at_utc") == doc.get("root_registration_started_at_utc"), "registration start")
    repo = checked_path(doc["repository_root"], True)
    require(repo == Path("D:/作品集/ResearchOS/research-os") and
            Path(doc["root_checkpoint"]["path"]) == repo / "execution/v2.4/checkpoint.json" and
            cp.get("head") == SOURCE_COMMIT, "current canonical checkpoint or HEAD")
    wip = cp.get("work_in_progress", {})
    require(wip.get("mu_sdk_active_run_uuid") == uuid and
            wip.get("mu_sdk_registration_ref") == doc["root_registration"] and
            wip.get("mu_sdk_owner_lease_ref") == doc["owner_lease"], "current checkpoint authority")
    require(lease.get("schema") == "researchos.mu-sdk-trial-owner-lease.v1" and
            lease.get("state") == "ACTIVE" and lease.get("run_uuid") == uuid and
            lease.get("owner") == reg.get("owner") and lease.get("data_root") == doc["data_root"] and
            datetime.fromisoformat(lease["expires_at_utc"].replace("Z", "+00:00")) > datetime.now(timezone.utc),
            "owner lease expired or changed")
    data = checked_path(doc["data_root"], True)
    workspace = checked_path(doc["workspace"], True)
    require(data.is_relative_to(repo / ".local") and workspace.is_relative_to(data) and workspace != data,
            "isolated data/workspace boundary")
    intake = pin_json(doc["intake_review"])
    private_root = checked_path(intake["resource"]["private_root_ref_only"], True)
    require(data != private_root and not data.is_relative_to(private_root) and
            not private_root.is_relative_to(data), "data root overlaps protected resource root")
    once = Path(doc["once_path"])
    checked_path(str(once.parent), True)
    require(once.parent == data / "trial-once" and once.name == uuid + ".json" and
            not os.path.lexists(once), "once marker already consumed or foreign")
    phase_dir = checked_path(context["phase_dir"], True)
    receipt_root = repo / "execution/v2.4/receipts/W05/W05-99/mu_sdk_real_trial_root_codex"
    require(phase_dir.parent.parent == receipt_root and phase_dir.name == doc["phase"] and
            len(phase_dir.parent.name) == 32 and all(c in "0123456789abcdef" for c in phase_dir.parent.name) and
            reg.get("phase_dir") == str(phase_dir) and lease.get("phase_dir") == str(phase_dir),
            "phase receipt directory outside registered owned receipt scope")
    require(job.get("schema") == "researchos.mu-sdk-trial-outer-job.v1" and
            job.get("run_uuid") == uuid and job.get("runner_pid") == pid and
            job.get("kill_on_close") is True and job.get("owns_child_tree") is True and
            job.get("controller_source_ref") == context["controller_source"], "outer Job contract")
    heartbeat_path = Path(job["heartbeat_path"])
    require(heartbeat_path.parent == data / "trial-control", "heartbeat outside isolated control")
    heartbeat = strict_json(checked_path(str(heartbeat_path)).read_bytes())
    now = time.monotonic()
    require(heartbeat.get("schema") == "researchos.mu-sdk-trial-job-heartbeat.v1" and
            heartbeat.get("run_uuid") == uuid and heartbeat.get("runner_pid") == pid and
            heartbeat.get("active") is True and
            type(heartbeat.get("monotonic_tick")) in (int, float) and
            math.isfinite(heartbeat["monotonic_tick"]) and 0 <= now - heartbeat["monotonic_tick"] <= 5,
            "heartbeat stale or changed")
    start, deadline = validate_limits(doc, reg, job, now)
    launch = validate_launch_inputs(context, basis)
    return {"doc": doc, "reg": reg, "job": job, "phase_dir": phase_dir,
            "started": start, "deadline": deadline, "heartbeat": heartbeat, "launch": launch}


def code_identity(code):
    """Compare executable structure, constants and line table, without executing it."""
    constants = tuple(code_identity(c) if isinstance(c, types.CodeType) else c for c in code.co_consts)
    return (code.co_name, code.co_filename, code.co_firstlineno, code.co_code, constants,
            code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
            code.co_argcount, code.co_kwonlyargcount, code.co_posonlyargcount,
            code.co_flags, code.co_linetable, code.co_exceptiontable)


def expected_hook_code(hooks_ref):
    hooks = ast.parse(pin_bytes(hooks_ref))
    hook_literals = [n.value.value for n in ast.walk(hooks) if isinstance(n, ast.Assign) and
                     any(isinstance(t, ast.Name) and t.id == "hook" for t in n.targets) and
                     isinstance(n.value, ast.Constant)]
    require(hook_literals == [HOOK], "hook template differs from reviewed observer ABI")
    text = pin_bytes(BASE_REF).decode("utf-8")
    require(text.count(SIGNATURE) == 1 and text.count(ASSIGNED) == 1, "base hook anchors")
    text = text.replace(SIGNATURE, SIGNATURE[:-2] + ", before_resume=None):")
    text = text.replace(ASSIGNED, ASSIGNED + HOOK)
    filename = str(Path(BASE_REF["path"])) + "::root-before-resume"
    compiled = compile(text, filename, "exec", dont_inherit=True)
    code = next(c for c in compiled.co_consts if isinstance(c, types.CodeType) and c.co_name == "run_owned")
    tree = ast.parse(text)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and
             isinstance(n.func, ast.Name) and n.func.id == "before_resume"]
    require(len(calls) == 1, "one actual before_resume call required")
    return code, calls[0].lineno


def observe_callback_frame(context, process_handle, thread_handle, job_handle, pid, creation_filetime, state):
    expected, call_line = expected_hook_code(context["hooks_source"])
    frame = inspect.currentframe()
    matches = []
    try:
        frame = frame.f_back
        while frame is not None:
            if frame.f_code.co_name == "run_owned" and frame.f_code.co_filename == expected.co_filename:
                matches.append(frame)
            frame = frame.f_back
        require(len(matches) == 1, "not in unique live reviewed run_owned callback")
        owner = matches[0]
        require(code_identity(owner.f_code) == code_identity(expected) and owner.f_lineno == call_line,
                "actual executing hook code or callback location changed")
        loc = owner.f_locals
        pi, result, cleanup = loc["pi"], loc["result"], loc["cleanup"]
        require(int(pi.hProcess) == process_handle and int(pi.hThread) == thread_handle and
                int(loc["job"]) == job_handle and int(pi.dwProcessId) == pid and
                result["creation_time_100ns"] == creation_filetime,
                "handles not from live CREATE_SUSPENDED frame")
        require(loc["stage"] == "ASSIGN_SUSPENDED_CHILD" and loc["assigned"] is True and
                cleanup["assigned_before_resume"] is True and result.get("resumed") is False and
                loc["flags"] & 0x4 and not loc["flags"] & 0x01000000 and
                cleanup["kill_on_job_close_configured"] is True,
                "live callback is not assigned-before-first-resume")
        actual_deadline = loc["started"] + loc["timeout"]
        require(loc["started"] >= state["started"] and
                actual_deadline == state["job"].get("actual_owned_runner_deadline_monotonic") and
                time.monotonic() < actual_deadline <= state["deadline"] and 0 < loc["timeout"] <= 300 and
                state["job"].get("actual_creation_time_100ns") == creation_filetime and
                loc["env"] == context["public_environment"],
                "live owned-process clock does not match grant")
        actual_launch = validate_callback_launch(context, loc, state)
        return {"method": "PINNED_EXECUTABLE_FRAME_AND_WINAPI", "frame_filename": expected.co_filename,
                "function": "run_owned", "callback_line": call_line,
                "creation_flags": loc["flags"], "assigned_before_resume": True,
                "resumed_at_observation": False, "base_source_ref": BASE_REF,
                "hooks_source_ref": context["hooks_source"],
                "actual_launch": actual_launch,
                "limit": "Reviewed synchronous callback position; not an independent OS suspend-count query."}
    finally:
        del frame
        matches.clear()


def validate_observed_facts(facts, pid, creation_filetime):
    require(type(pid) is int and pid > 0 and type(creation_filetime) is int and creation_filetime > 0,
            "PID or creation time type")
    require(facts["process_id"] == pid and facts["thread_process_id"] == pid and
            type(facts["thread_id"]) is int and facts["thread_id"] > 0 and
            facts["creation_filetime"] == creation_filetime, "OS process identity changed")
    require(facts["member_of_expected_job"] is True and facts["exit_code"] == 259 and
            facts["wait_result"] == 258, "process not active in exact Job")
    require(facts["assigned_count"] == facts["returned_count"] == 1 and facts["active_pids"] == [pid],
            "Job membership incomplete or not exclusive initial child")
    require(facts["job_limit_flags"] & 0x2000 and not facts["job_limit_flags"] & (0x800 | 0x1000),
            "kill-on-close absent or breakaway enabled")


def observe_windows(process_handle, thread_handle, job_handle, pid, creation_filetime):
    require(os.name == "nt" and ctypes.sizeof(ctypes.c_void_p) == 8, "Windows x64 required")
    for value in (process_handle, thread_handle, job_handle):
        require(type(value) is int and 0 < value < 2**63, "real non-pseudo handle required")
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    handle, dword, boolean = wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL
    def bind(name, args, result):
        fn = getattr(kernel, name)
        fn.argtypes, fn.restype = args, result
        return fn
    def checked(ok):
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
    get_pid = bind("GetProcessId", [handle], dword)
    get_tid = bind("GetThreadId", [handle], dword)
    thread_pid = bind("GetProcessIdOfThread", [handle], dword)
    times = bind("GetProcessTimes", [handle] + [ctypes.POINTER(wintypes.FILETIME)] * 4, boolean)
    member = bind("IsProcessInJob", [handle, handle, ctypes.POINTER(boolean)], boolean)
    exit_code = bind("GetExitCodeProcess", [handle, ctypes.POINTER(dword)], boolean)
    wait = bind("WaitForSingleObject", [handle, dword], dword)
    query = bind("QueryInformationJobObject", [handle, ctypes.c_int, ctypes.c_void_p, dword, ctypes.POINTER(dword)], boolean)
    class BasicLimit(ctypes.Structure):
        _fields_ = [("per_process", ctypes.c_int64), ("per_job", ctypes.c_int64), ("flags", dword),
                    ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t), ("active", dword),
                    ("affinity", ctypes.c_size_t), ("priority", dword), ("scheduling", dword)]
    class ExtendedLimit(ctypes.Structure):
        _fields_ = [("basic", BasicLimit), ("io", ctypes.c_uint64 * 6),
                    ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                    ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
    class PidList(ctypes.Structure):
        _fields_ = [("assigned", dword), ("returned", dword), ("pids", ctypes.c_size_t * 64)]
    observed_pid, tid, observed_thread_pid = int(get_pid(process_handle)), int(get_tid(thread_handle)), int(thread_pid(thread_handle))
    checked(observed_pid and tid and observed_thread_pid)
    creation, exited, kt, ut = (wintypes.FILETIME() for _ in range(4))
    checked(times(process_handle, ctypes.byref(creation), ctypes.byref(exited), ctypes.byref(kt), ctypes.byref(ut)))
    included, code, returned = boolean(), dword(), dword()
    checked(member(process_handle, job_handle, ctypes.byref(included)))
    checked(exit_code(process_handle, ctypes.byref(code)))
    ids, limits = PidList(), ExtendedLimit()
    checked(query(job_handle, 3, ctypes.byref(ids), ctypes.sizeof(ids), ctypes.byref(returned)))
    require(ids.returned <= 64, "Job PID buffer incomplete")
    checked(query(job_handle, 9, ctypes.byref(limits), ctypes.sizeof(limits), ctypes.byref(returned)))
    facts = {"process_id": observed_pid, "thread_id": tid, "thread_process_id": observed_thread_pid,
             "creation_filetime": (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime),
             "member_of_expected_job": bool(included.value), "exit_code": int(code.value),
             "wait_result": int(wait(process_handle, 0)), "assigned_count": int(ids.assigned),
             "returned_count": int(ids.returned), "active_pids": [int(ids.pids[i]) for i in range(ids.returned)],
             "job_limit_flags": int(limits.basic.flags), "query_monotonic": time.monotonic()}
    validate_observed_facts(facts, pid, creation_filetime)
    return facts


def observe_assigned_before_resume(context, *, process_handle, thread_handle, job_handle, pid, creation_filetime):
    """Return three byte pins after all checks; no partial review on check failure.

    Root must call synchronously inside the actual pinned run_owned callback.
    Root owns grant/heartbeat/lifetime/cleanup; this function never resumes/kills.
    """
    state = validate_context(context, pid)
    frame = observe_callback_frame(context, process_handle, thread_handle, job_handle, pid, creation_filetime, state)
    facts = observe_windows(process_handle, thread_handle, job_handle, pid, creation_filetime)
    # Re-read all authority/source bytes after OS observation, before publication.
    current = validate_context(context, pid)
    require(current["deadline"] == state["deadline"], "authority changed during observation")
    observe_callback_frame(context, process_handle, thread_handle, job_handle, pid, creation_filetime, current)
    doc = context["input_doc"]
    common = {"actor_id": ACTOR, "source_author_actor_id": AUTHOR, "actual_executor_actor_id": ROOT_ACTOR,
              "execution_kind": "AUTOMATED_IN_ROOT_CONTROLLER_PROCESS", "observer_source_ref": context["observer_source"],
              "independent_source_review_ref": context["independent_source_review"], "run_uuid": doc["run_uuid"],
              "phase_worker_source_ref": context["phase_worker_source"], "python_binary_ref": context["python_binary"],
              "observer_process_id": os.getpid(), "runner_pid": pid,
              "observed_at_utc": datetime.now(timezone.utc).isoformat(), "formal_acceptance": False,
              "full_lifecycle_cleanup_verified": False, "provider_requests_from_observer": 0,
              "automatic_retry": False, "source_qualification_issued": False}
    probe = dict(common, schema="researchos.mu-sdk-trial-os-job-probe.v1",
                 outer_job_ref=context["outer_job_contract"], member_of_expected_job=True,
                 os_observation=facts, callback_observation=frame,
                 root_checkpoint_ref=doc["root_checkpoint"], owner_lease_ref=doc["owner_lease"])
    directory = state["phase_dir"]
    paths = {"job_probe": directory / "observer.job-probe.json",
             "controller_review": directory / "observer.controller-review.json",
             "nonauthor_review": directory / "observer.nonauthor-review.json"}
    require(all(not os.path.lexists(path) for path in paths.values()), "observer receipt exists; no retry")
    raw_probe = json_bytes(probe)
    probe_ref = pin_of(paths["job_probe"], raw_probe)
    controller = dict(common, schema="researchos.mu-sdk-trial-controller-review.v1",
                      decision="ACTUAL_JOB_LIFECYCLE_REVIEWED", controller_source_ref=context["controller_source"],
                      outer_job_ref=context["outer_job_contract"], job_probe_ref=probe_ref,
                      heartbeat_path=state["job"]["heartbeat_path"],
                      review_scope="ASSIGNMENT_AND_PRE_RESUME_ADMISSION_ONLY", callback_observation=frame)
    nonauthor = dict(common, schema="researchos.mu-sdk-trial-nonauthor-review.v1",
                     decision="SOURCE_AND_SCOPE_REVIEWED", registration_ref=doc["root_registration"],
                     source_ref=RUNNER_REF, input_basis_ref=doc["input_basis_ref"],
                     runtime_profile_ref=doc["runtime_profile"], public_route_manifest_ref=doc["public_route_manifest"],
                     limits=LIMITS, review_scope="PINNED_SOURCE_REVIEW_AND_CURRENT_SCOPE_REVALIDATION")
    payloads = {"job_probe": raw_probe, "controller_review": json_bytes(controller), "nonauthor_review": json_bytes(nonauthor)}
    result = {}
    for name, raw in payloads.items():
        # Exclusive files; an I/O failure propagates, Root must stop and clean Job.
        with paths[name].open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        result[name] = pin_of(paths[name], raw)
    return result
