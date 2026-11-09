"""Source-only Main23 build leaf. Import never starts Go, Win32 or a database.

A separately reviewed Root caller supplies a live registered owner/scope/lease.
The output is a candidate and factual provenance, never its own qualification.
"""
from __future__ import annotations
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
REF_KEYS = {"path", "sha256", "bytes"}
UINT64_MAX = (1 << 64) - 1
FILE_FIELDS = ("GoFiles", "CgoFiles", "CompiledGoFiles", "SFiles", "HFiles", "SysoFiles", "CFiles", "CXXFiles", "MFiles", "FFiles", "SwigFiles", "SwigCXXFiles", "EmbedFiles")


class BuildBoundaryError(RuntimeError):
    pass


def require(ok, code):
    if not ok:
        raise BuildBoundaryError(code)


def _ref(path):
    data = Path(path).read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _load(ref, name):
    # Bootstrap loader is independently reviewed with this leaf; exact pins only.
    require(isinstance(ref, dict) and set(ref) == REF_KEYS, "EXACT_REF_REQUIRED")
    require(type(ref["bytes"]) is int and 0 <= ref["bytes"] <= 1024 * 1024, "HELPER_SIZE_INVALID")
    require(_ref(ref["path"]) == ref, "HELPER_PIN_MISMATCH")
    module = types.ModuleType(name)
    exec(compile(Path(ref["path"]).read_bytes(), ref["path"], "exec"), module.__dict__)
    return module


def relative_file(value):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value and not value.startswith("/"), "RELATIVE_FILE_INVALID")
    require(all(x and x not in (".", "..") and not x.endswith((" ", ".")) and not re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", x) for x in value.split("/")), "RELATIVE_FILE_INVALID")
    require(not any(ord(c) < 32 for c in value), "RELATIVE_FILE_INVALID")
    return value


def below(path, root):
    p, r = ntpath.normcase(ntpath.normpath(str(path))), ntpath.normcase(ntpath.normpath(str(root)))
    return p.startswith(r + "\\")


def compile_request(contract, request, base):
    require(isinstance(request, dict) and set(request) == {"case_id", "output_root"}, "REQUEST_FIELDS_INVALID")
    require(isinstance(request["case_id"], str) and re.fullmatch("[0-9a-f]{32}", request["case_id"]) is not None, "CASE_ID_INVALID")
    expected = ntpath.join(contract["output_parent"], "fresh-main23-" + request["case_id"])
    require(base.regular_absolute(request["output_root"]) == base.regular_absolute(expected), "OUTPUT_SCOPE_ESCAPE")
    require(contract["source_author"] == AUTHOR and contract["schema_version"] == 23, "SOURCE_CONTRACT_INVALID")
    root = request["output_root"]
    paths = {"root": root, **{name: ntpath.join(root, name) for name in ["frozen_main", "module_cache", "gocache", "gopath", "tmp", "raw"]}}
    paths["program"] = ntpath.join(root, "main-backup23.exe")
    go = contract["go_ref"]["path"]
    phases = [
        ("go-version", [go, "version"], 30),
        ("list-declared", [go, "list", "-deps", "-compiled", "-json", "./ops/backup"], 120),
        ("list-export", [go, "list", "-deps", "-compiled", "-export", "-json", "./ops/backup"], 600),
        ("build-main23", [go, "build", "-x", "-work", "-o", paths["program"], "./ops/backup"], 600),
        ("inspect-binary", [go, "version", "-m", paths["program"]], 30),
    ]
    return {"paths": paths, "phases": [{"id": name, "argv": argv, "timeout": timeout} for name, argv, timeout in phases]}


def environment(contract, paths):
    env = {key: os.environ[key] for key in ["SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "PROCESSOR_ARCHITECTURE"] if key in os.environ}
    env.update(GOROOT=contract["goroot"], GOTOOLCHAIN="local", GOENV="off", GOWORK="off", GO111MODULE="on",
               GOPATH=paths["gopath"], GOMODCACHE=paths["module_cache"], GOCACHE=paths["gocache"],
               GOPROXY="off", GOSUMDB="off", GONOPROXY="none", GONOSUMDB="none", GOPRIVATE="",
               GOOS="windows", GOARCH="amd64", GOAMD64="v1", CGO_ENABLED="0", GOEXPERIMENT="",
               GOFLAGS="-mod=readonly -trimpath -buildvcs=false", GOTELEMETRY="off",
               GOTMPDIR=paths["tmp"], TMP=paths["tmp"], TEMP=paths["tmp"])
    env["PATH"] = ntpath.join(contract["goroot"], "bin") + ";" + ntpath.join(env.get("SystemRoot", r"C:\Windows"), "System32")
    return env


def validate_owned(observation, base):
    base.closed_job(observation)
    require(type(observation["creation_time_100ns"]) is int and 0 < observation["creation_time_100ns"] <= UINT64_MAX, "FILETIME_EXACT_UINT64_REQUIRED")
    require(type(observation["owned_child_pid"]) is int and 0 < observation["owned_child_pid"] <= 0xffffffff, "PID_EXACT_UINT32_REQUIRED")
    return True


def parse_json_stream(raw):
    require(isinstance(raw, bytes) and len(raw) <= 16 * 1024 * 1024, "GO_LIST_OUTPUT_CAP")
    text = raw.decode("utf-8")
    decoder, rows = json.JSONDecoder(), []
    while text.strip():
        text = text.lstrip()
        value, end = decoder.raw_decode(text)
        require(isinstance(value, dict), "GO_LIST_PACKAGE_OBJECT_REQUIRED")
        rows.append(value)
        require(len(rows) <= 1024, "GO_LIST_PACKAGE_CAP")
        text = text[end:]
    require(rows, "GO_LIST_EMPTY")
    return rows


def declared_closure(packages, allowed_refs, paths, contract, base, need_exports):
    allowed = {base.regular_absolute(r["path"]): r for r in allowed_refs}
    rows, used, exports, names = [], {}, [], set()
    for package in packages:
        require(not package.get("Error") and not package.get("DepsErrors") and not package.get("Incomplete"), "GO_LIST_INCOMPLETE")
        name = package.get("ImportPath")
        require(isinstance(name, str) and name and name not in names and not package.get("ForTest"), "PACKAGE_IDENTITY_INVALID")
        names.add(name)
        folder = package.get("Dir")
        require(isinstance(folder, str) and any(below(folder, root) or base.regular_absolute(folder) == base.regular_absolute(root) for root in [paths["frozen_main"], paths["module_cache"], contract["goroot"]]), "PACKAGE_DIR_OUTSIDE_FROZEN_INPUTS")
        selected = {}
        for field in FILE_FIELDS:
            values = package.get(field, [])
            require(isinstance(values, list), "PACKAGE_FILES_INVALID")
            selected[field] = []
            for value in values:
                require(isinstance(value, str), "PACKAGE_FILES_INVALID")
                path = value if ntpath.isabs(value) else ntpath.join(folder, relative_file(value.replace("\\", "/")))
                key = base.regular_absolute(path)
                require(key in allowed, "DECLARED_BUILD_INPUT_NOT_FROZEN")
                used[key] = allowed[key]
                selected[field].append(key)
            selected[field].sort()
        module = package.get("Module") or {}
        require(not module.get("Replace"), "MODULE_REPLACEMENT_PROHIBITED")
        if module:
            modpath = module.get("GoMod")
            require(isinstance(modpath, str) and base.regular_absolute(modpath) in allowed, "MODULE_GOMOD_NOT_FROZEN")
            used[base.regular_absolute(modpath)] = allowed[base.regular_absolute(modpath)]
            if module.get("Main"):
                require(module.get("Path") == contract["module_path"], "MAIN_MODULE_IDENTITY_MISMATCH")
            else:
                require(contract["module_versions"].get(module.get("Path")) == module.get("Version"), "MODULE_VERSION_NOT_PINNED")
        record = {"ImportPath": name, "Dir": base.regular_absolute(folder), "Name": package.get("Name"), "Standard": package.get("Standard", False), "inputs": selected,
                  "Imports": sorted(package.get("Imports", [])), "ImportMap": package.get("ImportMap", {}),
                  "module": {k: module.get(k) for k in ["Path", "Version", "Main", "GoMod", "Sum", "GoModSum"]}}
        rows.append(record)
        if need_exports and name != "unsafe":
            export = package.get("Export")
            require(isinstance(export, str) and below(export, paths["gocache"]) and ntpath.basename(export).endswith("-d"), "EXPORT_NOT_IN_FRESH_GOCACHE")
            base.regular_absolute(export)
            require(isinstance(package.get("BuildID"), str) and package["BuildID"], "EXPORT_BUILD_ID_REQUIRED")
            exports.append({"ImportPath": name, "path": export, "BuildID": package["BuildID"]})
    target = [x for x in rows if x["ImportPath"] == contract["module_path"] + "/ops/backup"]
    require(len(target) == 1 and target[0]["Name"] == "main", "BACKUP_MAIN_PACKAGE_MISSING")
    return {"packages": sorted(rows, key=lambda x: x["ImportPath"]), "input_refs": [used[k] for k in sorted(used)], "exports": sorted(exports, key=lambda x: x["ImportPath"])}


def verify_binary_metadata(raw, contract):
    require(len(raw) <= 1024 * 1024, "BINARY_METADATA_CAP")
    lines = raw.decode("utf-8").splitlines()
    require(lines and lines[0].endswith(": go1.27.1"), "BINARY_GO_VERSION_MISMATCH")
    fields = [line.strip().split("\t") for line in lines[1:]]
    require(["path", contract["module_path"] + "/ops/backup"] in fields, "BINARY_PACKAGE_IDENTITY_MISMATCH")
    required = {"CGO_ENABLED=0", "GOOS=windows", "GOARCH=amd64", "GOAMD64=v1", "-trimpath=true"}
    observed = {x[1] for x in fields if len(x) == 2 and x[0] == "build"}
    require(required <= observed, "BINARY_BUILD_SETTINGS_MISMATCH")
    for field in fields:
        if field and field[0] == "dep":
            require(len(field) >= 3 and contract["module_versions"].get(field[1]) == field[2], "BINARY_DEPENDENCY_VERSION_MISMATCH")
    return True


def tree_refs(root, base, cap=50000):
    result = []
    for path in sorted(Path(root).rglob("*")):
        require(not path.is_symlink() and not path.is_junction(), "OUTPUT_REPARSE_POINT_PROHIBITED")
        if path.is_file():
            require(path.stat().st_size <= 128 * 1024 * 1024, "FILE_SIZE_CAP")
            result.append(base.observed_ref(path))
            require(len(result) <= cap, "FILE_COUNT_CAP")
    return result


def assert_pins(refs, base):
    for ref in refs:
        base.read_exact(ref)
    return True


def main_inventory(contract, base):
    files = []
    for relative in contract["main_scopes"]:
        root = Path(contract["main_root"]).joinpath(*relative_file(relative).split("/"))
        require(root.is_dir(), "MAIN_SCOPE_MISSING")
        for path in root.rglob("*"):
            require(not path.is_symlink() and not path.is_junction(), "MAIN_REPARSE_POINT_PROHIBITED")
            if path.is_file() and not any(part in ("__pycache__", ".git", "node_modules") for part in path.relative_to(root).parts):
                files.append(base.regular_absolute(str(path)))
    files += [base.regular_absolute(str(Path(contract["main_root"]) / name)) for name in ["go.mod", "go.sum"]]
    return sorted(set(files))


def verify_frozen_inventory(paths, copied, base):
    expected_main = sorted((r for r in copied if below(r["path"], paths["frozen_main"])), key=lambda r: base.regular_absolute(r["path"]))
    observed_main = sorted(tree_refs(paths["frozen_main"], base), key=lambda r: base.regular_absolute(r["path"]))
    require(observed_main == expected_main, "FROZEN_MAIN_INVENTORY_DRIFT")
    expected_modules = {base.regular_absolute(r["path"]): r for r in copied if below(r["path"], paths["module_cache"])}
    for item in tree_refs(paths["module_cache"], base):
        key = base.regular_absolute(item["path"])
        if key in expected_modules:
            require(item == expected_modules.pop(key), "FROZEN_MODULE_INPUT_DRIFT")
        else:
            require(item["bytes"] == 0 and item["path"].endswith(".lock"), "UNDECLARED_MODULE_CACHE_FILE")
    require(not expected_modules, "FROZEN_MODULE_INPUT_MISSING")
    return True


def copy_inputs(items, paths, source_guard, base):
    copied = []
    for item in items:
        if item["kind"] not in ("main", "module"):
            continue
        relative = relative_file(item["relative_path"])
        parent = paths["frozen_main"] if item["kind"] == "main" else paths["module_cache"]
        target = Path(parent).joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source_guard.get_buffer(item["ref"]["path"])
        with target.open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        ref = base.observed_ref(target)
        require(ref["sha256"] == item["ref"]["sha256"] and ref["bytes"] == item["ref"]["bytes"], "FROZEN_COPY_MISMATCH")
        os.chmod(target, stat.S_IREAD)
        copied.append(ref)
    return copied


def run_registered_build(contract_ref, request_ref, root_scope):
    """Live Root API; request JSON cannot grant registration or authority."""
    require(root_scope is not None and not isinstance(root_scope, dict), "LIVE_ROOT_SCOPE_REQUIRED")
    require(all(callable(getattr(root_scope, n, None)) for n in ["require_registered", "require_phase", "receipt_context"]), "ROOT_SCOPE_INTERFACE_REQUIRED")
    root_scope.require_registered(contract_ref, request_ref, source_author=AUTHOR)
    # Root has pinned this leaf, contract and bootstrap helper before this call.
    require(_ref(contract_ref["path"]) == contract_ref, "CONTRACT_PIN_MISMATCH")
    contract = json.loads(Path(contract_ref["path"]).read_bytes())
    base = _load(contract["base_helper_ref"], "main23_existing_source_helpers")
    base.exact_ref(contract_ref); base.exact_ref(request_ref)
    request = json.loads(base.read_exact(request_ref))
    projection = compile_request(contract, request, base)
    paths, root = projection["paths"], Path(projection["paths"]["root"])
    state = {"schema": "researchos.fresh-main23-build-observation.v1", "status": "STARTED", "phase": "prepare", "case_id": request["case_id"],
             "contract_ref": contract_ref, "request_ref": request_ref, "root_context": None, "calls": [], "first_failure": None,
             "root_created": False, "prepared_directories": [], "attempted_path": None, "formal_acceptance": False,
             "programme_qualification": "PENDING_INDEPENDENT_NONAUTHOR", "product_program_executions": 0,
             "model_calls": 0, "database_calls": 0, "schema21": "OPEN", "full20to24": "OPEN", "next23to24": "BLOCKED_MAIN_NOT_ADOPTED"}
    guards, copied, original_refs, export_refs = [], [], [], []
    package_closure = export_closure = None
    try:
        root_scope.require_phase("prepare", request_ref, paths["root"])
        state["root_context"] = root_scope.receipt_context()
        base._assert_output_ancestors(paths["root"])
        state["attempted_path"] = str(root); root.mkdir(); state["root_created"] = True
        state["prepared_directories"].append(str(root))
        for name in ["frozen_main", "module_cache", "gocache", "gopath", "tmp", "raw"]:
            state["attempted_path"] = paths[name]; Path(paths[name]).mkdir(); state["prepared_directories"].append(paths[name])
        manifest = json.loads(base.read_exact(contract["input_manifest_ref"]))
        original_refs = [item["ref"] for item in manifest["items"]]
        original_refs += [contract_ref, request_ref, contract["builder_ref"], contract["input_manifest_ref"], contract["base_helper_ref"], contract["source_guard_ref"], contract["owned_job_ref"], contract["toolchain_lock_ref"]]
        expected_main_inventory = sorted(base.regular_absolute(x["ref"]["path"]) for x in manifest["items"] if x["kind"] == "main")
        require(main_inventory(contract, base) == expected_main_inventory, "CURRENT_MAIN_INVENTORY_DRIFT")
        guard_module = base._load_pinned_module(contract["source_guard_ref"], "main23_source_guard")
        guard = guard_module.SourceReadGuard(total_cap=512 * 1024 * 1024); guards.append(("original_inputs", guard)); guard.acquire(original_refs)
        require(all(ref in original_refs for ref in contract["current_main_source_refs"]), "CURRENT_MAIN_REFS_NOT_IN_INPUT_CLOSURE")
        require(contract["go_ref"] in original_refs, "GO_NOT_IN_INPUT_CLOSURE")
        state["source_before_ref"] = base.save_new(root / "source.before.json", {"refs": original_refs, "guard_share": "FILE_SHARE_READ_ONLY"})
        copied = copy_inputs(manifest["items"], paths, guard, base)
        require(main_inventory(contract, base) == expected_main_inventory, "CURRENT_MAIN_INVENTORY_DRIFT")
        frozen_guard = guard_module.SourceReadGuard(total_cap=256 * 1024 * 1024); guards.append(("frozen_inputs", frozen_guard)); frozen_guard.acquire(copied)
        state["frozen_before_ref"] = base.save_new(root / "frozen.before.json", {"refs": copied})
        require(tree_refs(paths["gocache"], base) == [], "FRESH_EMPTY_GOCACHE_REQUIRED")
        state["gocache_initial"] = {"path": paths["gocache"], "files": [], "shared_cache_copied": False}
        state["environment_ref"] = base.save_new(root / "environment.json", environment(contract, paths))
        job = base._load_pinned_module(contract["owned_job_ref"], "main23_owned_job")
        env = environment(contract, paths)
        allowed_refs = copied + [x["ref"] for x in manifest["items"] if x["kind"] == "toolchain"]
        for phase in projection["phases"]:
            state["phase"] = phase["id"]
            root_scope.require_phase(phase["id"], request_ref, paths["root"])
            assert_pins(original_refs + copied, base)
            verify_frozen_inventory(paths, copied, base)
            require(main_inventory(contract, base) == expected_main_inventory, "CURRENT_MAIN_INVENTORY_DRIFT")
            invocation = {"phase": phase["id"], "argv": phase["argv"], "cwd": paths["frozen_main"], "env": env, "timeout_seconds": phase["timeout"],
                          "started_at_unix_ns": time.time_ns(), "actual_exit": None, "observation": None,
                          "individual_descendant_exit_codes": None, "descendant_evidence": "TYPED_JOB_AGGREGATE_IDLE_AND_HANDLES_CLOSED"}
            state["calls"].append(invocation)
            invocation["before_ref"] = base.save_new(Path(paths["raw"]) / (phase["id"] + ".before.json"), dict(invocation))
            stdout = Path(paths["raw"]) / (phase["id"] + ".stdout")
            stderr = Path(paths["raw"]) / (phase["id"] + ".stderr")
            invocation.update(stdout_path=str(stdout), stderr_path=str(stderr))
            with stdout.open("xb") as out, stderr.open("xb") as err:
                observation = job.run_owned(phase["argv"], paths["frozen_main"], env, out, err, phase["timeout"], creation_flags=0x08000000)
            invocation.update(observation=observation, actual_exit=observation.get("actual_exit"), ended_at_unix_ns=time.time_ns(), stdout_ref=base.observed_ref(stdout), stderr_ref=base.observed_ref(stderr))
            invocation["result_ref"] = base.save_new(Path(paths["raw"]) / (phase["id"] + ".result.json"), dict(invocation))
            validate_owned(observation, base)
            require(stdout.stat().st_size <= 16 * 1024 * 1024 and stderr.stat().st_size <= 16 * 1024 * 1024, "GO_OUTPUT_SIZE_CAP")
            if phase["id"] == "go-version":
                require(stdout.read_bytes().decode().strip() == "go version go1.27.1 windows/amd64", "QUALIFIED_GO_VERSION_MISMATCH")
            elif phase["id"] in ("list-declared", "list-export"):
                closure = declared_closure(parse_json_stream(stdout.read_bytes()), allowed_refs, paths, contract, base, phase["id"] == "list-export")
                if phase["id"] == "list-declared":
                    package_closure = closure
                    state["declared_closure_ref"] = base.save_new(root / "declared-closure.json", closure)
                else:
                    require(closure["packages"] == package_closure["packages"] and closure["input_refs"] == package_closure["input_refs"], "DECLARED_EXPORT_CLOSURE_DRIFT")
                    export_closure = closure
                    for item in closure["exports"]:
                        item["ref"] = base.observed_ref(item["path"]); export_refs.append(item["ref"])
                    export_guard = guard_module.SourceReadGuard(total_cap=512 * 1024 * 1024); guards.append(("export_inputs", export_guard)); export_guard.acquire(export_refs)
                    state["export_closure_ref"] = base.save_new(root / "export-closure.json", closure)
                    cache_before = tree_refs(paths["gocache"], base)
                    state["cache_before_build_ref"] = base.save_new(root / "cache.before-build.json", {"refs": cache_before})
            elif phase["id"] == "build-main23":
                require(package_closure is not None and export_closure is not None, "DECLARED_EXPORT_CLOSURE_REQUIRED")
                assert_pins(cache_before + export_refs, base)
                require(Path(paths["program"]).is_file(), "BUILT_PROGRAM_MISSING")
                state["program_ref"] = base.observed_ref(paths["program"])
                state["cache_after_build_ref"] = base.save_new(root / "cache.after-build.json", {"refs": tree_refs(paths["gocache"], base)})
                state["retained_build_work_ref"] = base.save_new(root / "build-work.json", {"refs": tree_refs(paths["tmp"], base), "retained": True})
                program_guard = guard_module.SourceReadGuard(); guards.append(("program", program_guard)); program_guard.acquire([state["program_ref"]])
            else:
                verify_binary_metadata(stdout.read_bytes(), contract)
        assert_pins(original_refs + copied + export_refs, base)
        verify_frozen_inventory(paths, copied, base)
        require(main_inventory(contract, base) == expected_main_inventory, "CURRENT_MAIN_INVENTORY_DRIFT")
        state["source_after_ref"] = base.save_new(root / "source.after.json", {"refs": [base.observed_ref(x["path"]) for x in original_refs]})
        state["frozen_after_ref"] = base.save_new(root / "frozen.after.json", {"refs": [base.observed_ref(x["path"]) for x in copied]})
        state["current_main_source_refs"] = contract["current_main_source_refs"]
        state["status"] = "BUILT_CANDIDATE_PENDING_NONAUTHOR_PROGRAMME_REVIEW"
    except BaseException as exc:
        state["status"] = "STOPPED_AT_FIRST_FAILURE"
        state["first_failure"] = {"phase": state["phase"], "type": type(exc).__name__, "message": str(exc), "original_ordinal": None,
                                  "Root_assignment_required": True, "last_child_exit": state["calls"][-1]["actual_exit"] if state["calls"] else None}
    finally:
        state["guard_cleanup"] = {}
        for name, guard in reversed(guards):
            try:
                audit = guard.close(); state["guard_cleanup"][name] = audit
                require(audit.get("verification") == "PASSED" and audit.get("closed") is True and audit.get("retained_handles_count") == 0 and not audit.get("errors"), "SOURCE_GUARD_CLOSE_UNCONFIRMED")
            except BaseException as exc:
                state["status"] = "STOPPED_GUARD_CLEANUP_UNCONFIRMED"
                state.setdefault("cleanup_errors", []).append({"guard": name, "type": type(exc).__name__, "message": str(exc)})
                if state["first_failure"] is None:
                    state["first_failure"] = {"phase": "guard_cleanup", "type": type(exc).__name__, "message": str(exc), "original_ordinal": None, "Root_assignment_required": True, "last_child_exit": state["calls"][-1]["actual_exit"] if state["calls"] else None}
        state["automatic_retry"] = False
        state["partial_output_retained"] = state["root_created"]
        state["Root_full_outer_hostpair_required"] = True
        state["closed_receipt"] = {"status": "ROOT_MUST_PERSIST_RETURNED_STATE", "ref": None}
        if state["root_created"]:
            try:
                state["closed_receipt"]["status"] = "PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF"
                closed = base.save_new(root / "build.closed.json", state)
                state["closed_receipt"].update(status="PUBLISHED", ref=closed)
            except BaseException as exc:
                state["closed_receipt"].update(status="FAILED_ROOT_MUST_PERSIST_RETURNED_STATE", error={"type": type(exc).__name__, "message": str(exc)})
                if state["first_failure"] is None:
                    state["first_failure"] = {"phase": "close_receipt", "type": type(exc).__name__, "message": str(exc), "original_ordinal": None, "Root_assignment_required": True, "last_child_exit": state["calls"][-1]["actual_exit"] if state["calls"] else None}
                state["status"] = "STOPPED_RECEIPT_PUBLICATION_FAILED"
        if state["status"] == "BUILT_CANDIDATE_PENDING_NONAUTHOR_PROGRAMME_REVIEW":
            state["candidate_for_independent_review"] = {"program_ref": state["program_ref"], "provenance_ref": state["closed_receipt"]["ref"], "source_refs": contract["current_main_source_refs"], "qualification_ref": None}
    return state
