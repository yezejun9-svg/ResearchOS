"""Source-only public schema22 rehearsal leaf for a separately reviewed Root caller.

Importing this module never opens a database, loads a Windows API, or starts a child.
There is deliberately no standalone activation CLI and no JSON field that grants
execution authority. A registered Root caller must hold its live owner/scope/lease,
source review, Python/native resource closure and invoke run_registered_case().
"""
from __future__ import annotations
import base64
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import stat
import time
import types

AUTHOR = "codex:/root/native_temp_independent_review"
CASE = re.compile(r"^[0-9a-f]{32}$")
REF_KEYS = {"path", "sha256", "bytes"}
RESTORED = "RESTORED_RECONCILIATION_REQUIRED"
MAX_BYTES = 64 * 1024 * 1024

class BoundaryError(RuntimeError):
    pass

def require(ok, code):
    if not ok:
        raise BoundaryError(code)

def regular_absolute(path):
    require(isinstance(path, str) and path and not any(ord(c) < 32 for c in path), "PATH_INVALID")
    value = path.replace("/", "\\")
    drive, tail = ntpath.splitdrive(value)
    require(re.fullmatch(r"[A-Za-z]:", drive) is not None and tail.startswith("\\") and not tail.startswith("\\\\"), "LOCAL_ABSOLUTE_PATH_REQUIRED")
    require(":" not in tail, "ADS_PROHIBITED")
    parts = tail[1:].split("\\")
    require(all(x and x not in (".", "..") and not x.endswith((" ", ".")) for x in parts), "PATH_COMPONENT_INVALID")
    require(not any(re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", x) for x in parts), "DEVICE_PATH_PROHIBITED")
    return ntpath.normcase(ntpath.normpath(value))

def exact_ref(value):
    require(isinstance(value, dict) and set(value) == REF_KEYS, "EXACT_THREE_KEY_REF_REQUIRED")
    regular_absolute(value["path"])
    require(isinstance(value["sha256"], str) and re.fullmatch("[0-9a-f]{64}", value["sha256"]) is not None, "SHA256_REQUIRED")
    require(type(value["bytes"]) is int and 0 <= value["bytes"] <= 512 * 1024 * 1024, "BYTE_COUNT_INVALID")
    return value

def read_exact(ref):
    exact_ref(ref)
    raw = Path(ref["path"]).read_bytes()
    require(len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], "INPUT_PIN_MISMATCH")
    return raw

def observed_ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def save_new(path, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return observed_ref(path)

def same_json(emitted, persisted):
    require(isinstance(emitted, dict) and emitted == persisted, "PUBLIC_EMITTED_PERSISTED_RECEIPT_MISMATCH")
    return True

def closed_job(observation):
    require(isinstance(observation, dict), "OWNED_JOB_OBSERVATION_REQUIRED")
    cleanup = observation.get("job_cleanup", {})
    require(type(observation.get("actual_exit")) is int and observation["actual_exit"] == 0 and observation.get("timed_out") is False and observation.get("error") is None, "PUBLIC_CHILD_FAILED")
    require(type(observation.get("owned_child_pid")) is int and observation["owned_child_pid"] > 0, "CHILD_PID_NOT_OBSERVED")
    require(type(observation.get("creation_time_100ns")) is int and observation["creation_time_100ns"] > 0, "CHILD_CREATION_FILETIME_NOT_OBSERVED")
    require(observation.get("resumed") is True, "CHILD_NOT_RESUMED")
    require(all(cleanup.get(k) is True for k in ["unnamed_exclusive_job", "kill_on_job_close_configured", "assigned_before_resume", "job_idle_confirmed", "primary_exit_confirmed", "handles_closed"]), "OWNED_JOB_CLEANUP_UNCONFIRMED")
    require(type(cleanup.get("active_processes_last_observed")) is int and cleanup["active_processes_last_observed"] == 0 and cleanup.get("errors") == [], "OWNED_JOB_NOT_EMPTY")
    return True

def validate_ledger(observation, version):
    require(isinstance(observation.get("versions"), list) and all(type(v) is int for v in observation["versions"]) and observation["versions"] == list(range(1, version + 1)), "EXACT_SCHEMA_LEDGER_REQUIRED")
    require(observation.get("integrity") == ["ok"] and observation.get("foreign_key_violations") == 0, "DATABASE_VALIDATION_FAILED")
    tables = observation.get("tables", {})
    require("client_sessions" in tables and "client_command_queue" in tables, "ADDITIVE_SESSION_QUEUE_SCHEMA_REQUIRED")
    require(tables["client_sessions"]["count"] == 0 and tables["client_command_queue"]["count"] == 0, "BOOTSTRAP_ONLY_TYPED_EMPTY_SCOPE_REQUIRED")
    if version == 23:
        for name in ["client_command_identities", "host_model_configurations", "host_model_config_heads"]:
            require(name in tables and tables[name]["count"] == 0, "EMPTY_CONFIGURATION_PROFILE_REQUIRED")
    return True

def validate_restore22(observation, sealed22):
    """Require the complete logical schema22 state, including the fresh Owner."""
    validate_ledger(sealed22, 22)
    validate_ledger(observation, 22)
    for item in (sealed22, observation):
        require(item["tables"].get("auth_principals", {}).get("count") == 1, "PUBLIC_RESTORE_OWNER_ROW_REQUIRED")
        require(isinstance(item.get("schema_sha256"), str) and re.fullmatch("[0-9a-f]{64}", item["schema_sha256"]) is not None, "PUBLIC_RESTORE_SCHEMA_DIGEST_REQUIRED")
    require(observation["schema_sha256"] == sealed22["schema_sha256"], "PUBLIC_RESTORE_SCHEMA_MISMATCH")
    require(observation["tables"] == sealed22["tables"], "PUBLIC_RESTORE_TABLE_STATE_MISMATCH")
    return True


def compile_case(contract, request):
    """Pure command projection: no process, database, filesystem write or authority."""
    require(isinstance(request, dict) and set(request) == {"case_id", "output_root", "end_version"}, "REQUEST_FIELDS_INVALID")
    require(isinstance(request["case_id"], str) and CASE.fullmatch(request["case_id"]) is not None, "CASE_ID_INVALID")
    require(type(request["end_version"]) is int and request["end_version"] in (22, 23), "MAIN_PUBLIC_23_TO_24_NOT_ADOPTED")
    expected = ntpath.join(contract["output_parent"], "schema22-public-" + request["case_id"])
    require(regular_absolute(request["output_root"]) == regular_absolute(expected), "OUTPUT_SCOPE_ESCAPE")
    require(contract["source_author"] == AUTHOR, "SOURCE_AUTHOR_BINDING_MISMATCH")
    for role in ["old22_control", "old22_backup", "source_guard", "owned_job", "source_inputs_ref"]:
        exact_ref(contract[role])
    root = request["output_root"]
    path = lambda name: ntpath.join(root, name)
    paths = {
        "root": root, "data22": path("source22"), "db22": path("source22\\researchos.sqlite"),
        "private": path("private"), "owner_file": path("private\\owner.json"), "key": path("private\\recovery.key"),
        "backup22": path("backup22"), "verify22": path("verified22"), "work22": path("working22"),
        "workdb22": path("working22\\researchos.sqlite"), "snapshot23": path("upgrade22to23.snapshot"),
        "candidate23": path("candidate23"), "db23": path("candidate23\\researchos.sqlite"),
        "backup23": path("backup23"), "verify23": path("verified23"), "raw": path("raw"), "tmp": path("tmp"),
    }
    old_control, old_backup = contract["old22_control"]["path"], contract["old22_backup"]["path"]
    old_root = contract["old22_root"]
    phases = [
        {"id": "bootstrap22", "argv": [old_control, "--bootstrap-owner", "--credential-file", paths["owner_file"]], "cwd": old_root},
        {"id": "keygen22", "argv": [old_backup, "keygen", "--key-file", paths["key"]], "cwd": old_root},
        {"id": "backup22", "argv": [old_backup, "create", "--db", paths["db22"], "--out", paths["backup22"], "--key-file", paths["key"], "--root", old_root], "cwd": old_root},
        {"id": "verify22", "argv": [old_backup, "restore", "--backup", paths["backup22"], "--out", paths["verify22"], "--key-file", paths["key"], "--root", old_root], "cwd": old_root},
    ]
    return {"scope": contract["scope"], "end_version": request["end_version"], "paths": paths, "phases": phases, "unimplemented_next_stage": contract["blocked23to24"]}

def upgrade23_phases(contract, projection, qualified_main_program):
    """Only a Root-qualified current Main binding may replace the old candidate."""
    exact_ref(qualified_main_program)
    require(qualified_main_program != contract["main23_candidate_only"], "UNREBOUND_MAIN23_CANDIDATE_PROHIBITED")
    p = projection["paths"]
    program, root = qualified_main_program["path"], contract["main23_root"]
    return [
        {"id": "upgrade22to23", "argv": [program, "upgrade-local", "--db", p["workdb22"], "--backup", p["snapshot23"], "--out", p["candidate23"], "--key-file", p["key"], "--source-root", contract["old22_root"], "--root", root, "--source-program", contract["old22_control"]["path"], "--target-program", program, "--plan", contract["plan22to23"]], "cwd": root},
        {"id": "backup23", "argv": [program, "create", "--db", p["db23"], "--out", p["backup23"], "--key-file", p["key"], "--root", root], "cwd": root},
        {"id": "verify23", "argv": [program, "restore", "--backup", p["backup23"], "--out", p["verify23"], "--key-file", p["key"], "--root", root], "cwd": root},
    ]

def quiescent_database(path):
    path = Path(path)
    require(path.is_file(), "PUBLIC_DATABASE_MISSING")
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(str(path) + suffix)
        require(not sidecar.exists() or sidecar.stat().st_size == 0, "NONEMPTY_SQLITE_SIDECAR")
    return path

def readonly_database_observation(path):
    """Hash public fixture rows without emitting their values or writing SQL."""
    import sqlite3
    path = quiescent_database(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        versions = [r[0] for r in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
        schema = list(connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))
        names = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        tables = {}
        def encode(value):
            if isinstance(value, bytes):
                return {"blob_base64": base64.b64encode(value).decode("ascii")}
            return value
        for name in names:
            quoted = '"' + name.replace('"', '""') + '"'
            rows = [[encode(v) for v in r] for r in connection.execute("SELECT * FROM " + quoted)]
            serialized = sorted(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows)
            tables[name] = {"count": len(rows), "rows_sha256": hashlib.sha256(("\n".join(serialized)).encode()).hexdigest()}
        return {
            "database_ref": observed_ref(path), "versions": versions,
            "schema_sha256": hashlib.sha256(json.dumps(schema, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
            "integrity": [r[0] for r in connection.execute("PRAGMA integrity_check")],
            "foreign_key_violations": len(list(connection.execute("PRAGMA foreign_key_check"))),
            "tables": tables, "mode": "ro,immutable,query_only", "raw_rows_emitted": False,
        }
    finally:
        connection.close()

def _load_pinned_module(ref, name):
    module = types.ModuleType(name)
    exec(compile(read_exact(ref), ref["path"], "exec"), module.__dict__)
    return module

def _environment(paths):
    env = {key: os.environ[key] for key in ["SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "PROCESSOR_ARCHITECTURE"] if key in os.environ}
    env["PATH"] = ntpath.join(env.get("SystemRoot", r"C:\Windows"), "System32")
    env.update(TEMP=paths["tmp"], TMP=paths["tmp"], RESEARCHOS_DATA_DIR=paths["data22"])
    return env

def _contained_file_refs(root):
    root = Path(root)
    refs = []
    for p in sorted(root.rglob("*")):
        require(not p.is_symlink() and not p.is_junction(), "BASELINE_LINK_PROHIBITED")
        if p.is_file():
            require(p.stat().st_size <= MAX_BYTES, "BASELINE_FILE_SIZE_CAP")
            refs.append(observed_ref(p))
    require(len(refs) <= 256, "BASELINE_FILE_COUNT_CAP")
    return refs

def _assert_output_ancestors(path):
    p = Path(path)
    require(not p.exists(), "OUTPUT_ALREADY_EXISTS")
    for ancestor in p.parents:
        if ancestor.exists():
            require(not ancestor.is_symlink() and not ancestor.is_junction(), "OUTPUT_REPARSE_POINT_PROHIBITED")
    require(p.parent.is_dir(), "REGISTERED_OUTPUT_PARENT_REQUIRED")

def run_registered_case(contract_ref, request_ref, root_scope):
    """Execute only inside the separately reviewed caller's live Root scope.

    root_scope is a live capability supplied by the Root caller, not deserialized
    from request JSON. Its require_registered/require_phase methods must enforce
    Root ownership, exact Source review/refs, current lease and registered scope.
    This leaf neither creates registration nor decides those authority checks.
    """
    exact_ref(contract_ref); exact_ref(request_ref)
    require(root_scope is not None and not isinstance(root_scope, dict), "LIVE_ROOT_SCOPE_REQUIRED")
    require(all(callable(getattr(root_scope, name, None)) for name in ["require_registered", "require_phase", "receipt_context", "qualified_current_main23"]), "ROOT_SCOPE_INTERFACE_REQUIRED")
    # No file or process side effect occurs before the Root caller's live gate.
    root_scope.require_registered(contract_ref, request_ref, source_author=AUTHOR)
    contract = json.loads(read_exact(contract_ref))
    request = json.loads(read_exact(request_ref))
    projection = compile_case(contract, request)
    paths = projection["paths"]
    binding = None
    if projection["end_version"] == 23:
        binding = root_scope.qualified_current_main23(contract_ref, contract["current_main_source_refs"])
        require(isinstance(binding, dict) and set(binding) == {"program_ref", "qualification_ref", "source_refs"}, "FRESH_MAIN_PROGRAMME_BINDING_REQUIRED")
        exact_ref(binding["program_ref"]); exact_ref(binding["qualification_ref"])
        require(binding["source_refs"] == contract["current_main_source_refs"], "CURRENT_MAIN_SOURCE_BINDING_MISMATCH")
        projection["phases"] += upgrade23_phases(contract, projection, binding["program_ref"])
    root = Path(paths["root"])
    state = {
        "schema": "researchos.schema22-public-case-observation.v1", "case_id": request["case_id"],
        "contract_ref": contract_ref, "request_ref": request_ref, "root_context": None,
        "scope": contract["scope"], "end_version_requested": request["end_version"],
        "status": "STARTED", "phase": "prepare", "calls": [], "observations": {},
        "qualified_current_main23": binding, "formal_acceptance": False, "full20to24": "OPEN",
        "schema21": "OPEN_NO_PROGRAMME_BOUND", "next23to24": contract["blocked23to24"],
        "old_source_program_version": 22, "credential_or_key_bytes_emitted": False,
        "first_failure": None, "baseline_retained": False,
        "preparation": {"root_created": False, "created_directories": [], "attempted_path": None},
        "closed_receipt": {"status": "NOT_ATTEMPTED", "ref": None, "error": None},
    }
    source_guard = baseline_guard = None
    guard_module = job_module = None
    baseline_refs = []
    try:
        root_scope.require_phase("prepare", request_ref, paths["root"])
        state["root_context"] = root_scope.receipt_context()
        _assert_output_ancestors(paths["root"])
        state["preparation"]["attempted_path"] = str(root)
        root.mkdir()
        state["preparation"]["root_created"] = True
        state["preparation"]["created_directories"].append(str(root))
        for name in ["private", "raw", "tmp", "work22"]:
            state["preparation"]["attempted_path"] = paths[name]
            Path(paths[name]).mkdir()
            state["preparation"]["created_directories"].append(paths[name])
        guard_module = _load_pinned_module(contract["source_guard"], "schema22_source_guard")
        source_guard = guard_module.SourceReadGuard()
        source_inputs = json.loads(read_exact(contract["source_inputs_ref"]))
        refs = source_inputs["references"] + [contract_ref, request_ref, contract["source_inputs_ref"]]
        if binding:
            refs += [binding["program_ref"], binding["qualification_ref"]]
        source_guard.acquire(refs)
        job_module = _load_pinned_module(contract["owned_job"], "schema22_owned_job")
        env = _environment(paths)
        for phase in projection["phases"]:
            state["phase"] = phase["id"]
            root_scope.require_phase(phase["id"], request_ref, paths["root"])
            if phase["id"] == "upgrade22to23":
                require(baseline_guard is not None, "READONLY_BASELINE_REQUIRED")
                data = baseline_guard.get_buffer(paths["db22"])
                with Path(paths["workdb22"]).open("xb") as f:
                    f.write(data); f.flush(); os.fsync(f.fileno())
                require(observed_ref(paths["workdb22"])["sha256"] == observed_ref(paths["db22"])["sha256"], "WORKING_COPY_NOT_EXACT_BASELINE")
            stdout_path = Path(paths["raw"]) / (phase["id"] + ".stdout")
            stderr_path = Path(paths["raw"]) / (phase["id"] + ".stderr")
            invocation = {
                "phase": phase["id"], "argv": phase["argv"], "cwd": phase["cwd"], "env": env,
                "timeout_seconds": 90, "started_at_unix_ns": time.time_ns(), "observation": None,
                "actual_exit": None, "native_child_kind": "public_go_program",
            }
            invocation["before_ref"] = save_new(Path(paths["raw"]) / (phase["id"] + ".before.json"), {k:v for k,v in invocation.items() if k != "before_ref"})
            with stdout_path.open("xb") as out, stderr_path.open("xb") as err:
                observed = job_module.run_owned(phase["argv"], phase["cwd"], env, out, err, 90, creation_flags=0x08000000)
            invocation.update(observation=observed, actual_exit=observed.get("actual_exit"), ended_at_unix_ns=time.time_ns(), stdout_ref=observed_ref(stdout_path), stderr_ref=observed_ref(stderr_path))
            invocation["result_ref"] = save_new(Path(paths["raw"]) / (phase["id"] + ".result.json"), {k:v for k,v in invocation.items() if k != "result_ref"})
            state["calls"].append(invocation)
            closed_job(observed)
            require(stdout_path.stat().st_size <= 4 * 1024 * 1024 and stderr_path.stat().st_size <= 4 * 1024 * 1024, "PUBLIC_OUTPUT_SIZE_CAP")
            emitted = json.loads(stdout_path.read_bytes()) if phase["id"] != "bootstrap22" else None
            if phase["id"] == "bootstrap22":
                before = readonly_database_observation(paths["db22"]); validate_ledger(before, 22)
                require(before["tables"].get("auth_principals", {}).get("count") == 1, "PUBLIC_BOOTSTRAP_OWNER_ROW_REQUIRED")
                state["observations"]["created22"] = before
            elif phase["id"] == "backup22":
                same_json(emitted, json.loads((Path(paths["backup22"]) / "manifest.json").read_bytes()))
                current = readonly_database_observation(paths["db22"]); validate_ledger(current, 22)
                require(current["tables"] == state["observations"]["created22"]["tables"], "BACKUP_CHANGED_ORIGINAL_LOGICAL_STATE")
                baseline_refs = _contained_file_refs(paths["data22"]) + _contained_file_refs(paths["backup22"])
                for baseline in baseline_refs:
                    os.chmod(baseline["path"], stat.S_IREAD)
                baseline_attributes = [{"path": r["path"], "readonly_attribute": bool(Path(r["path"]).stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)} for r in baseline_refs]
                require(all(r["readonly_attribute"] for r in baseline_attributes), "BASELINE_READONLY_ATTRIBUTE_NOT_SET")
                baseline_guard = guard_module.SourceReadGuard()
                baseline_guard.acquire(baseline_refs)
                state["baseline_manifest_ref"] = save_new(root / "baseline22.manifest.json", {"references": baseline_refs, "file_attributes": baseline_attributes, "created_by": "pinned_old22_public_programs", "source_guard_share": "FILE_SHARE_READ_ONLY", "private_key_outside_baseline": True})
                state["baseline_retained"] = True
                state["observations"]["sealed22"] = current
            elif phase["id"] in ("verify22", "verify23", "upgrade22to23"):
                destination = paths[{"verify22":"verify22", "verify23":"verify23", "upgrade22to23":"candidate23"}[phase["id"]]]
                persisted = json.loads((Path(destination) / "restore-report.json").read_bytes())
                same_json(emitted, persisted)
                require(emitted.get("status") == RESTORED, "PUBLIC_RESTORE_STATUS_NOT_COMPLETE")
                dbname = "researchos.sqlite" if phase["id"] == "upgrade22to23" else "state.sqlite"
                version = 22 if phase["id"] == "verify22" else 23
                observation = readonly_database_observation(Path(destination) / dbname)
                state["observations"][phase["id"]] = observation
                validate_ledger(observation, version)
                if phase["id"] == "verify22":
                    validate_restore22(observation, state["observations"]["sealed22"])
                if version == 23:
                    require(observation["tables"]["domain_objects"] == state["observations"]["sealed22"]["tables"]["domain_objects"], "BOOTSTRAP_DOMAIN_ROWS_CHANGED")
            elif phase["id"] == "backup23":
                same_json(emitted, json.loads((Path(paths["backup23"]) / "manifest.json").read_bytes()))
        if baseline_guard:
            require(all(observed_ref(r["path"]) == r for r in baseline_refs), "READONLY_BASELINE_DRIFT")
        state["status"] = "PUBLIC22_BASELINE_VERIFIED_PENDING_ROOT_REVIEW" if request["end_version"] == 22 else "PUBLIC22_TO23_REHEARSAL_OBSERVED_PENDING_ROOT_REVIEW"
    except BaseException as exc:
        state["status"] = "STOPPED_AT_FIRST_FAILURE"
        state["first_failure"] = {"phase": state["phase"], "type": type(exc).__name__, "message": str(exc), "original_ordinal": None, "Root_assignment_required": True, "last_child_exit": state["calls"][-1]["actual_exit"] if state["calls"] else None}
    finally:
        state["guard_cleanup"] = {}
        for name, guard in [("baseline", baseline_guard), ("source", source_guard)]:
            if guard is not None:
                audit = guard.close()
                state["guard_cleanup"][name] = audit
                if audit.get("verification") != "PASSED" or not audit.get("closed") or audit.get("retained_handles_count") != 0 or audit.get("errors"):
                    state["status"] = "STOPPED_GUARD_CLEANUP_UNCONFIRMED"
        state["publication"] = {k: Path(paths[k]).exists() for k in ["root", "private", "raw", "tmp", "work22", "backup22", "verify22", "snapshot23", "candidate23", "backup23", "verify23"]}
        state["recoverability"] = {
            "original_public22_baseline_retained": bool(baseline_refs), "encrypted_backup22_exists": Path(paths["backup22"]).is_dir(),
            "recovery_key_exists": Path(paths["key"]).is_file(), "private_key_path": paths["key"],
            "recovery_requires_new_root_registration": True,
            "public_recovery_command": [contract["old22_backup"]["path"], "restore", "--backup", paths["backup22"], "--out", "<NEW_ROOT_REGISTERED_DESTINATION>", "--key-file", paths["key"], "--root", contract["old22_root"]],
            "automatic_retry_or_recovery_performed": False,
        }
        if state["preparation"]["root_created"]:
            try:
                state["closed_receipt"]["status"] = "PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF"
                receipt_ref = save_new(root / "case.closed.json", state)
                state["closed_receipt"].update(status="PUBLISHED", ref=receipt_ref)
            except BaseException as exc:
                state["closed_receipt"].update(status="FAILED_ROOT_MUST_PERSIST_RETURNED_STATE", error={"type": type(exc).__name__, "message": str(exc)})
                if state["first_failure"] is None:
                    state["first_failure"] = {"phase": "close_receipt", "type": type(exc).__name__, "message": str(exc), "original_ordinal": None, "Root_assignment_required": True, "last_child_exit": state["calls"][-1]["actual_exit"] if state["calls"] else None}
                state["status"] = "STOPPED_CLOSED_RECEIPT_PUBLICATION_FAILED"
        else:
            state["closed_receipt"]["status"] = "ROOT_NOT_CREATED_ROOT_MUST_PERSIST_RETURNED_STATE"
    return state

