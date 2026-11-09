"""Finite pure Source controls: no Go, native API, SQLite or product execution."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import types

O = Path(__file__).resolve().parent
source = (O / "main23_builder.py").read_bytes()
builder = types.ModuleType("builder_source_controls")
exec(compile(source, str(O / "main23_builder.py"), "exec"), builder.__dict__)
contract = json.loads((O / "contract.json").read_bytes())
base_ref = contract["base_helper_ref"]
base_raw = Path(base_ref["path"]).read_bytes()
assert hashlib.sha256(base_raw).hexdigest() == base_ref["sha256"] and len(base_raw) == base_ref["bytes"]
base = types.ModuleType("existing_source_primitives")
exec(compile(base_raw, base_ref["path"], "exec"), base.__dict__)
checks = []


def check(name, result):
    checks.append({"id": name, "passed": bool(result), "scope": "PURE_SOURCE_NOT_RUNTIME"})
    if not result:
        raise AssertionError(name)


def reject(name, call, expected):
    try:
        call()
    except (builder.BuildBoundaryError, base.BoundaryError) as exc:
        check(name, str(exc) == expected)
    else:
        check(name, False)


request = {"case_id": "a" * 32, "output_root": contract["output_parent"] + "/fresh-main23-" + "a" * 32}
projection = builder.compile_request(contract, request, base)
paths = projection["paths"]
check("exact-five-Go-commands", len(projection["phases"]) == 5 and all(p["argv"][0] == contract["go_ref"]["path"] for p in projection["phases"]))
check("single-build-no-product-execution", [p["argv"][1] for p in projection["phases"]] == ["version", "list", "list", "build", "version"])
check("export-is-explicit", "-export" in projection["phases"][2]["argv"])
check("build-retains-work-and-raw-commands", "-work" in projection["phases"][3]["argv"] and "-x" in projection["phases"][3]["argv"])
check("unique-output-program", projection["phases"][3]["argv"][-2] == paths["program"] and builder.below(paths["program"], paths["root"]))
for label, bad, code in [
    ("extra-authority-field", {**request, "approved": True}, "REQUEST_FIELDS_INVALID"),
    ("wrong-directory", {**request, "output_root": contract["output_parent"] + "/elsewhere"}, "OUTPUT_SCOPE_ESCAPE"),
    ("bool-case-id", {**request, "case_id": True}, "CASE_ID_INVALID"),
    ("upper-case-id", {**request, "case_id": "A" * 32}, "CASE_ID_INVALID"),
]:
    reject("request-reject-" + label, lambda bad=bad: builder.compile_request(contract, bad, base), code)
for value in ["../escape", "/absolute", "drive:stream", "foo\\bar", "foo//bar", "CON", "foo/..", "foo/COM1.txt", "foo. ", "foo\x00"]:
    reject("relative-reject-" + repr(value), lambda value=value: builder.relative_file(value), "RELATIVE_FILE_INVALID")
check("relative-normal-path", builder.relative_file("cache/download/module/@v/v1.0.0.mod") == "cache/download/module/@v/v1.0.0.mod")
check("scope-prefix-not-sibling", not builder.below("D:/out-sibling/file", "D:/out"))
env = builder.environment(contract, paths)
check("offline-fixed-platform", all(env[k] == v for k, v in {"GOPROXY": "off", "GOSUMDB": "off", "GOOS": "windows", "GOARCH": "amd64", "CGO_ENABLED": "0", "GOWORK": "off", "GOENV": "off", "GOTOOLCHAIN": "local"}.items()))
check("cache-and-module-cache-are-unique", env["GOCACHE"] == paths["gocache"] and env["GOMODCACHE"] == paths["module_cache"])
check("no-ambient-extension-execution", "GOCACHEPROG" not in env and "GO_EXTLINK_ENABLED" not in env and not any(x.startswith("RESEARCHOS_") for x in env))
check("no-vcs-or-auto-go-mod-mutation", "-mod=readonly" in env["GOFLAGS"] and "-buildvcs=false" in env["GOFLAGS"])
observation = {"actual_exit": 0, "timed_out": False, "error": None, "owned_child_pid": 123,
    "creation_time_100ns": (1 << 63) + 123, "resumed": True,
    "job_cleanup": {"unnamed_exclusive_job": True, "kill_on_job_close_configured": True, "assigned_before_resume": True,
        "job_idle_confirmed": True, "primary_exit_confirmed": True, "handles_closed": True, "active_processes_last_observed": 0, "errors": []}}
check("FILETIME-above-2pow53-preserved-exact-int", builder.validate_owned(observation, base))
check("FILETIME-json-roundtrip-is-Python-int", json.loads(json.dumps(observation))["creation_time_100ns"] == (1 << 63) + 123)
for value, code in [(float(1 << 63), "CHILD_CREATION_FILETIME_NOT_OBSERVED"), (True, "CHILD_CREATION_FILETIME_NOT_OBSERVED"), (0, "CHILD_CREATION_FILETIME_NOT_OBSERVED"), (1 << 64, "FILETIME_EXACT_UINT64_REQUIRED")]:
    reject("FILETIME-reject-" + repr(value), lambda value=value: builder.validate_owned({**observation, "creation_time_100ns": value}, base), code)
reject("PID-reject-overflow", lambda: builder.validate_owned({**observation, "owned_child_pid": 1 << 32}, base), "PID_EXACT_UINT32_REQUIRED")
for value in [None, False, 1]:
    reject("child-exit-reject-" + repr(value), lambda value=value: builder.validate_owned({**observation, "actual_exit": value}, base), "PUBLIC_CHILD_FAILED")
for field in ["assigned_before_resume", "job_idle_confirmed", "handles_closed"]:
    altered = copy.deepcopy(observation); altered["job_cleanup"][field] = False
    reject("Job-reject-" + field, lambda altered=altered: builder.validate_owned(altered, base), "OWNED_JOB_CLEANUP_UNCONFIRMED")

def ref(path):
    return {"path": path, "sha256": "1" * 64, "bytes": 10}

main_go = builder.ntpath.join(paths["frozen_main"], "ops", "backup", "main.go")
go_mod = builder.ntpath.join(paths["frozen_main"], "go.mod")
refs = [ref(main_go), ref(go_mod)]
package = {"ImportPath": contract["module_path"] + "/ops/backup", "Name": "main", "Dir": builder.ntpath.dirname(main_go),
    "GoFiles": ["main.go"], "CompiledGoFiles": ["main.go"], "Module": {"Path": contract["module_path"], "Main": True, "GoMod": go_mod},
    "Export": builder.ntpath.join(paths["gocache"], "ab", "1" * 64 + "-d"), "BuildID": "synthetic-source-only-build-id"}
closure = builder.declared_closure([package], refs, paths, contract, base, True)
check("declared-closure-exact-inputs", len(closure["input_refs"]) == 2 and len(closure["exports"]) == 1)
check("JSON-stream-multiple-objects", len(builder.parse_json_stream(json.dumps(package).encode() + b"\n" + json.dumps({"a": 1}).encode())) == 2)
reject("JSON-stream-empty", lambda: builder.parse_json_stream(b" "), "GO_LIST_EMPTY")
reject("JSON-stream-not-object", lambda: builder.parse_json_stream(b"[]"), "GO_LIST_PACKAGE_OBJECT_REQUIRED")
try:
    builder.parse_json_stream(b'{} trailing')
except json.JSONDecodeError:
    check("JSON-stream-trailing-garbage-rejected", True)
else:
    check("JSON-stream-trailing-garbage-rejected", False)
for label, update, code in [
    ("error", {"Error": {"Err": "missing dependency"}}, "GO_LIST_INCOMPLETE"),
    ("incomplete", {"Incomplete": True}, "GO_LIST_INCOMPLETE"),
    ("test-package", {"ForTest": "some/test"}, "PACKAGE_IDENTITY_INVALID"),
    ("outside-directory", {"Dir": "D:/Outside"}, "PACKAGE_DIR_OUTSIDE_FROZEN_INPUTS"),
    ("unfrozen-file", {"GoFiles": ["other.go"]}, "DECLARED_BUILD_INPUT_NOT_FROZEN"),
    ("escaping-file", {"GoFiles": ["../other.go"]}, "RELATIVE_FILE_INVALID"),
    ("outside-export", {"Export": "D:/SharedGOCACHE/output-d"}, "EXPORT_NOT_IN_FRESH_GOCACHE"),
    ("no-buildid", {"BuildID": ""}, "EXPORT_BUILD_ID_REQUIRED"),
    ("wrong-main", {"Name": "library"}, "BACKUP_MAIN_PACKAGE_MISSING"),
]:
    altered = {**package, **update}
    reject("closure-reject-" + label, lambda altered=altered: builder.declared_closure([altered], refs, paths, contract, base, True), code)
for label, update, code in [
    ("replace", {"Replace": {"Dir": "D:/Replacement"}}, "MODULE_REPLACEMENT_PROHIBITED"),
    ("unfrozen-gomod", {"GoMod": "D:/other/go.mod"}, "MODULE_GOMOD_NOT_FROZEN"),
    ("main-name", {"Path": "other.module"}, "MAIN_MODULE_IDENTITY_MISMATCH"),
    ("external-version", {"Main": False, "Path": "malicious.module", "Version": "v9.9.9"}, "MODULE_VERSION_NOT_PINNED"),
]:
    altered = {**package, "Module": {**package["Module"], **update}}
    reject("closure-reject-module-" + label, lambda altered=altered: builder.declared_closure([altered], refs, paths, contract, base, True), code)
reject("duplicate-package-rejected", lambda: builder.declared_closure([package, package], refs, paths, contract, base, False), "PACKAGE_IDENTITY_INVALID")
metadata = ("D:/output/main-backup23.exe: go1.27.1\n\tpath\t" + contract["module_path"] + "/ops/backup\n" + "".join("\tbuild\t" + field + "\n" for field in ["CGO_ENABLED=0", "GOOS=windows", "GOARCH=amd64", "GOAMD64=v1", "-trimpath=true"])).encode()
check("binary-metadata-correct-identity", builder.verify_binary_metadata(metadata, contract))
reject("binary-version-mismatch", lambda: builder.verify_binary_metadata(metadata.replace(b"go1.27.1", b"go1.20.0"), contract), "BINARY_GO_VERSION_MISMATCH")
reject("binary-package-mismatch", lambda: builder.verify_binary_metadata(metadata.replace(b"/ops/backup", b"/apps/cli"), contract), "BINARY_PACKAGE_IDENTITY_MISMATCH")
reject("binary-settings-mismatch", lambda: builder.verify_binary_metadata(metadata.replace(b"CGO_ENABLED=0", b"CGO_ENABLED=1"), contract), "BINARY_BUILD_SETTINGS_MISMATCH")
reject("binary-module-mismatch", lambda: builder.verify_binary_metadata(metadata + b"\tdep\tbad/module\tv9.9.9\n", contract), "BINARY_DEPENDENCY_VERSION_MISMATCH")

dummy = {"path": "D:/NeverOpened/contract.json", "sha256": "0" * 64, "bytes": 1}
reject("no-live-scope-no-read", lambda: builder.run_registered_build(dummy, dummy, None), "LIVE_ROOT_SCOPE_REQUIRED")
reject("JSON-authority-not-live-scope", lambda: builder.run_registered_build(dummy, dummy, {"actor": "Root"}), "LIVE_ROOT_SCOPE_REQUIRED")
class Revoked:
    def require_registered(self, *a, **kw): raise builder.BuildBoundaryError("ROOT_LEASE_REVOKED")
    def require_phase(self, *a): raise AssertionError("must not reach phase")
    def receipt_context(self): raise AssertionError("must not reach context")
reject("revoked-registration-before-file-read", lambda: builder.run_registered_build(dummy, dummy, Revoked()), "ROOT_LEASE_REVOKED")

def prepare_failure(name, fail_receipt=False):
    saved_builder = {k: getattr(builder, k) for k in ["Path", "_ref", "_load"]}
    saved_base = {k: getattr(base, k) for k in ["read_exact", "_assert_output_ancestors", "save_new"]}
    made, attempts, receipts = [], [], []
    normalize = base.regular_absolute
    failed = normalize(paths[name])
    class MemoryPath:
        def __init__(self, p): self.path = str(p)
        def __str__(self): return self.path
        def __truediv__(self, p): return MemoryPath(builder.ntpath.join(self.path, p))
        def read_bytes(self): return json.dumps(contract).encode()
        def mkdir(self):
            key = normalize(self.path); attempts.append(key)
            if key == failed: raise OSError("INJECTED_PREPARE_FAILURE:" + name)
            made.append(key)
    class Scope:
        def require_registered(self, *a, **kw): pass
        def require_phase(self, phase, *a): assert phase == "prepare"
        def receipt_context(self): return {"SOURCE_CONTROL": "SYNTHETIC_NOT_AUTHORITY"}
    def save(path, value):
        if fail_receipt: raise OSError("INJECTED_RECEIPT_FAILURE")
        receipts.append(copy.deepcopy(value)); return ref(str(path))
    try:
        builder.Path = MemoryPath; builder._ref = lambda _: dummy; builder._load = lambda *a: base
        base.read_exact = lambda _: json.dumps(request).encode()
        base._assert_output_ancestors = lambda _: None; base.save_new = save
        state = builder.run_registered_build(dummy, dummy, Scope())
    finally:
        for k, value in saved_builder.items(): setattr(builder, k, value)
        for k, value in saved_base.items(): setattr(base, k, value)
    suffix = name + ("-receipt-failed" if fail_receipt else "")
    check("prepare-" + suffix + "-first-failure", state["first_failure"]["phase"] == "prepare" and state["first_failure"]["message"] == "INJECTED_PREPARE_FAILURE:" + name and state["first_failure"]["last_child_exit"] is None and state["first_failure"]["original_ordinal"] is None)
    check("prepare-" + suffix + "-no-child-no-retry", state["calls"] == [] and state["automatic_retry"] is False and len(attempts) == len(set(attempts)))
    check("prepare-" + suffix + "-partial-output", [normalize(x) for x in state["prepared_directories"]] == made and normalize(state["attempted_path"]) == failed)
    if name == "root" or fail_receipt:
        check("prepare-" + suffix + "-Root-fallback", not receipts and "ROOT_MUST_PERSIST_RETURNED_STATE" in state["closed_receipt"]["status"])
    else:
        check("prepare-" + suffix + "-closed-receipt", len(receipts) == 1 and receipts[0]["first_failure"] == state["first_failure"] and state["closed_receipt"]["status"] == "PUBLISHED")
for name in ["root", "frozen_main", "module_cache", "gocache", "gopath", "tmp", "raw"]:
    prepare_failure(name)
prepare_failure("tmp", fail_receipt=True)

tree = ast.parse(source)
check("no-standalone-entrypoint", not any(isinstance(n, ast.If) and "__name__" in ast.unparse(n.test) for n in tree.body))
check("no-top-level-native-db-process-import", not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any(x in ast.unparse(n) for x in ["ctypes", "sqlite3", "subprocess"]) for n in tree.body))
check("only-existing-owned-job-invocation", sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "run_owned" for n in ast.walk(tree)) == 1)
check("builder-never-self-issues-qualification", b'"qualification_ref": None' in source and b'"programme_qualification": "PENDING_INDEPENDENT_NONAUTHOR"' in source)
manifest = json.loads((O / "input-manifest.json").read_bytes())
check("no-shared-GOCACHE-in-Source-inputs", manifest["shared_GOCACHE_files_included"] == 0 and not any("/.local/gocache/" in x["ref"]["path"] for x in manifest["items"]))
check("Go-input-pinned-to-current-lock", contract["go_ref"] in [x["ref"] for x in manifest["items"]])
check("exact-three-key-refs-only", all(set(x["ref"]) == {"path", "sha256", "bytes"} for x in manifest["items"]))
check("current-Main-five-refs-all-in-closure", all(x in [i["ref"] for i in manifest["items"]] for x in contract["current_main_source_refs"]))
result = {"schema": "researchos.main23-builder-pure-source-controls.v1", "count": len(checks), "pass": sum(x["passed"] for x in checks), "fail": sum(not x["passed"] for x in checks),
          "Go_processes": 0, "product_processes": 0, "SQLite_calls": 0, "native_API_calls": 0, "runtime_verified": False, "controls": checks}
with (O / "source-controls.json").open("x", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2); f.write("\n")
print(json.dumps({k: v for k, v in result.items() if k != "controls"}))
