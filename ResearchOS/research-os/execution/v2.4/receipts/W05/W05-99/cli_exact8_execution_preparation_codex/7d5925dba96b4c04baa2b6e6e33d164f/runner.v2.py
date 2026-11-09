"""Prepared NONAUTHOR CLI47 runner. No action without Root's hash-bound scope.

Only main() executes. Preparation review may parse this file without importing it.
Every phase is single use; a failed marker requires a new Root-reviewed cohort.
"""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import sqlite3
import types
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/作品集/ResearchOS/research-os")
SOURCE = ROOT / ".local/worktrees/codex-w0599-cli-contract-repair-r303"
CHECKOUT = ROOT / ".local/independent-cli-exact8-0dcea526"
OUT = ROOT / "execution/v2.4/receipts/W05/W05-99/cli_exact8_independent_replay_codex/cli47-r308-7d5925db"
CANDIDATE = "b98738ac093ea55bb8700cfa724ddd9e6b2a1251"
GO = ROOT / ".local/tools/go1.27.1/go/bin/go.exe"
GIT = Path("C:/Program Files/Git/cmd/git.exe")
WORK = CHECKOUT / ".local/work"
CACHE = CHECKOUT / ".local/cache"
TEMP = CHECKOUT / ".local/temp"
BIN = OUT / "bin"
OWNED_HELPER = ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
OWNED_HELPER_SHA = "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
_PROCESS_HELPER = None
_RUNTIME_PATHS = set()
_KNOWN_INPUTS = set()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_bytes())


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def file_ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": sha(raw), "bytes": len(raw)}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def environment():
    # No inherited provider/credential/runtime environment, and no outer-Main VCS stamping.
    # Allowlist prevents unrelated secret-bearing environment variables entering receipts.
    env = {key: os.environ[key] for key in ("OS", "PATHEXT", "NUMBER_OF_PROCESSORS",
           "PROCESSOR_ARCHITECTURE", "PROCESSOR_IDENTIFIER", "PROCESSOR_LEVEL", "PROCESSOR_REVISION")
           if key in os.environ}
    env.update({"SystemRoot": os.environ["SystemRoot"], "WINDIR": os.environ["SystemRoot"],
                "ComSpec": str(Path(os.environ["SystemRoot"]) / "System32/cmd.exe"),
                "USERPROFILE": str(TEMP / "profile"), "LOCALAPPDATA": str(TEMP / "profile/AppData/Local"),
                "APPDATA": str(TEMP / "profile/AppData/Roaming")})
    env.update({"GOTOOLCHAIN": "local", "GOENV": "off", "GOWORK": "off",
                "GOOS": "windows", "GOARCH": "amd64", "GOAMD64": "v1", "CGO_ENABLED": "0",
                "GOEXPERIMENT": "", "GOFLAGS": "-buildvcs=false", "GODEBUG": "",
                "GOROOT": str(GO.parent.parent), "GOPATH": str(ROOT / ".local/gopath"),
                "GOCACHE": str(CACHE), "GOTMPDIR": str(WORK), "GOPROXY": "off", "GOSUMDB": "off",
                "TEMP": str(TEMP), "TMP": str(TEMP), "RESEARCHOS_GO": str(GO),
                "GIT_NO_REPLACE_OBJECTS": "1", "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "PATH": os.pathsep.join([str(GO.parent), str(GIT.parent),
                    str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0"),
                    str(Path(os.environ["SystemRoot"]) / "System32")])})
    return env


def authorize(args):
    require(sys.flags.isolated == 1 and sys.flags.optimize == 0, "Python must use -I without optimization")
    raw = Path(args.scope).read_bytes()
    require(sha(raw) == args.scope_sha256, "ROOT_SCOPE_HASH")
    scope = json.loads(raw)
    grant = scope["cli47_execution"]
    require(grant["candidate"] == CANDIDATE, "CANDIDATE_GRANT")
    require(Path(grant["checkout"]) == CHECKOUT and Path(grant["output"]) == OUT, "PATH_GRANT")
    manifest = HERE / "manifest.v2.json"
    require(grant["prepared_manifest_v2_sha256"] == sha(manifest.read_bytes()), "PREPARED_V2_MANIFEST_GRANT")
    helper = grant["owned_process_helper_ref"]
    require(Path(helper["path"]) == OWNED_HELPER and helper["sha256"] == OWNED_HELPER_SHA,
            "OWNED_PROCESS_HELPER_GRANT")
    require(file_ref(OWNED_HELPER)["sha256"] == OWNED_HELPER_SHA, "OWNED_HELPER_CHANGED")
    require(grant["invocation_limit"] == 47 and grant["leaf_limit"] == 221, "FINITE_GRANT")
    require(grant["SDK_MODEL_EXTERNAL_PAID_CALLS"] == 0, "NO_MODEL_GRANT")
    for row in read_json(manifest)["entries"]:
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "MANIFEST_MEMBER_PATH")
        path = HERE / relative
        _KNOWN_INPUTS.add(path)
        require(file_ref(path)["sha256"] == row["sha256"], "PREPARED_FILE_CHANGED:" + str(path))
    for row in read_json(HERE / "preparation_tools.v2.json"):
        require(file_ref(row["path"])["sha256"] == row["sha256"], "TOOL_PIN:" + row["path"])
    return {"scope": file_ref(args.scope), "grant": grant}


def initialize_owned_runtime():
    # Only called after actual Root scope authorization, never during preparation review.
    global _PROCESS_HELPER
    raw = OWNED_HELPER.read_bytes()
    require(sha(raw) == OWNED_HELPER_SHA, "OWNED_HELPER_CHANGED")
    sys.dont_write_bytecode = True
    module = types.ModuleType("researchos_owned_process")
    module.__file__ = str(OWNED_HELPER)
    exec(compile(raw, str(OWNED_HELPER), "exec"), module.__dict__)
    _PROCESS_HELPER = module


def runtime_vector():
    require(_PROCESS_HELPER is not None, "OWNED_RUNTIME_NOT_AUTHORIZED")
    require(file_ref(OWNED_HELPER)["sha256"] == OWNED_HELPER_SHA, "OWNED_HELPER_CHANGED")
    paths = {OWNED_HELPER, Path(sys.executable)}
    paths.update(Path(p) for p in _PROCESS_HELPER.runtime_resource_paths())
    for module in list(sys.modules.values()):
        for attribute in ("__file__", "__cached__"):
            name = getattr(module, attribute, None)
            if name:
                path = Path(name)
                if path.is_absolute() and path.is_file():
                    paths.add(path)
    _RUNTIME_PATHS.update(paths)
    _KNOWN_INPUTS.update(paths)
    return vector(_RUNTIME_PATHS)


def optional_ref(path):
    try:
        return {"exists": path.is_file(), "ref": file_ref(path) if path.is_file() else None}
    except BaseException as error:
        return {"exists": None, "ref": None, "observation_error": type(error).__name__ + ": " + str(error)}


def invoke(label, argv, env, cwd=CHECKOUT, timeout=510, stdin=None):
    directory = OUT / "invocations" / label
    directory.mkdir(parents=True, exist_ok=False)
    start = now()
    observation = {"actual_exit": None, "timed_out": False, "error": None,
                   "owned_child_pid": None, "creation_time_100ns": None,
                   "job_cleanup": None, "stage": "RUNNER_PRECALL"}
    wrapper_error = None
    result = None
    try:
        save(directory / "runtime.before.json", runtime_vector())
        if stdin is not None:
            require(isinstance(stdin, bytes), "STDIN_MUST_BE_EXACT_BYTES")
            with (directory / "stdin.raw").open("xb") as handle:
                handle.write(stdin)
        with (directory / "stdout.raw").open("xb") as stdout, (directory / "stderr.raw").open("xb") as stderr:
            input_file = None
            try:
                if stdin is not None:
                    input_file = (directory / "stdin.raw").open("rb")
                observation = _PROCESS_HELPER.run_owned(
                    [str(x) for x in argv], str(cwd), env, stdout, stderr, timeout, stdin=input_file)
            finally:
                if input_file is not None:
                    input_file.close()
    except BaseException as error:
        wrapper_error = {"error_type": type(error).__name__, "message": str(error)}
    finally:
        # Preserve launch/preparation/cleanup failures even when no process existed.
        runtime_error = None
        try:
            save(directory / "runtime.after.json", runtime_vector())
        except BaseException as error:
            runtime_error = {"error_type": type(error).__name__, "message": str(error)}
        result = {"argv": [str(x) for x in argv], "cwd": str(cwd), "environment": env,
                  "started_at": start, "ended_at": now(), "timeout_limit_seconds": timeout,
                  "owned_process_helper": {"path": str(OWNED_HELPER), "sha256": OWNED_HELPER_SHA},
                  "owned_process": observation, "wrapper_error": wrapper_error,
                  "runtime_observation_error": runtime_error,
                  "native_exit": observation.get("actual_exit"),
                  "pid": observation.get("owned_child_pid"),
                  "creation_time_100ns": observation.get("creation_time_100ns"),
                  "timeout": observation.get("timed_out"),
                  "stdout": optional_ref(directory / "stdout.raw"),
                  "stderr": optional_ref(directory / "stderr.raw"),
                  "stdin": optional_ref(directory / "stdin.raw") if stdin is not None else {"mode": "NUL"}}
        save(directory / "invocation.json", result)
    cleanup = observation.get("job_cleanup") or {}
    require(wrapper_error is None and result["runtime_observation_error"] is None
            and observation.get("error") is None and observation.get("actual_exit") == 0
            and observation.get("timed_out") is False and observation.get("resumed") is True
            and all(cleanup.get(key) is True for key in (
                "kill_on_job_close_configured", "assigned_before_resume", "primary_exit_confirmed",
                "job_idle_confirmed", "handles_closed")) and cleanup.get("errors") == [],
            "OWNED_NATIVE_FAILURE:" + label)
    return directory


def vector(paths):
    return [file_ref(p) for p in sorted(set(map(Path, paths)), key=lambda p: str(p).lower())]


def check_vector(expected, destination):
    actual = vector(x["path"] for x in expected)
    save(destination, actual)
    require(actual == expected, "INPUT_DRIFT:" + str(destination))


def json_stream(raw):
    decoder = json.JSONDecoder()
    text = raw.decode("utf-8")
    rows = []
    while text.strip():
        text = text.lstrip()
        value, end = decoder.raw_decode(text)
        rows.append(value)
        text = text[end:]
    return rows


def prepare(env):
    require(not CHECKOUT.exists(), "CHECKOUT_ALREADY_EXISTS_NO_RESET")
    CHECKOUT.mkdir(parents=True, exist_ok=False)
    for p in (WORK, CACHE, TEMP, BIN):
        p.mkdir(parents=True, exist_ok=False)
    resources = read_json(HERE / "public_compiler_export_plan.v2.json")
    external_pins = []
    for expected in resources["external_tools_modules_stdlib"]:
        actual = file_ref(expected["path"])
        require(actual["sha256"] == expected["sha256"] and actual["bytes"] == expected["bytes"],
                "APPROVED_EXTERNAL_INPUT_CHANGED:" + expected["path"])
        external_pins.append(actual)
        _KNOWN_INPUTS.add(Path(actual["path"]))
    save(OUT / "external.pins.before-go.json", external_pins)
    # Single immutable Git batch, not wildcard archive or a worktree mutation.
    rows = resources["git_resources"]
    data = ("\n".join(x["git_blob"] for x in rows) + "\n").encode("ascii")
    inv = invoke("git-public-export", [GIT, "-C", SOURCE, "cat-file", "--batch"], env,
                 cwd=ROOT, stdin=data)
    raw = (inv / "stdout.raw").read_bytes()
    offset = 0
    exported = []
    for row in rows:
        end = raw.index(b"\n", offset)
        blob, kind, size = raw[offset:end].decode("ascii").split()
        size = int(size)
        body = raw[end + 1:end + 1 + size]
        require(blob == row["git_blob"] and kind == "blob" and len(body) == size, "GIT_BLOB_FRAME")
        require(size == row["bytes"] and sha(body) == row["sha256"], "GIT_RESOURCE_HASH:" + row["path"])
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "EXPORT_PATH")
        path = CHECKOUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(body)
        exported.append(file_ref(path))
        _KNOWN_INPUTS.add(path)
        offset = end + size + 2
    require(offset == len(raw), "GIT_EXTRA_OUTPUT")
    save(OUT / "export.actual.json", exported)
    graphdir = invoke("go-list", [GO, "list", "-deps", "-test", "-json", "./apps/cli", "./tests/runtime/cli_contract"], env)
    packages = json_stream((graphdir / "stdout.raw").read_bytes())
    save(OUT / "go-packages.json", packages)
    inputs = {Path(x["path"]) for x in exported}
    inputs.update(Path(x["path"]) for x in resources["external_tools_modules_stdlib"])
    inputs.update(Path(x["path"]) for x in read_json(HERE / "preparation_tools.v2.json"))
    inputs.update(p for p in HERE.iterdir() if p.is_file())
    for pkg in packages:
        if not pkg.get("Dir"):
            continue
        directory = Path(pkg["Dir"])
        if not directory.is_dir():
            continue
        inputs.update(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in
                      (".go", ".s", ".h", ".c", ".cc", ".cpp", ".m", ".f", ".syso"))
        for key, names in pkg.items():
            if key.endswith("Files") and isinstance(names, list):
                for name in names:
                    path = directory / name
                    if path.is_file():
                        inputs.add(path.resolve())
    inputs.update(Path(x["path"]) for x in runtime_vector())
    _KNOWN_INPUTS.update(inputs)
    before = vector(inputs)
    save(OUT / "compile.inputs.before.json", before)
    invoke("go-version", [GO, "version"], env)
    invoke("go-env", [GO, "env", "-json"], env)
    builds = [("cli", [GO, "build", "-work", "-o", BIN / "researchos-cli.exe", "./apps/cli"]),
              ("test", [GO, "test", "-c", "-work", "-o", BIN / "cli.test.exe", "./apps/cli"]),
              ("harness-build-only", [GO, "build", "-work", "-o", BIN / "cli-contract.exe", "./tests/runtime/cli_contract"])]
    for label, argv in builds:
        invoke(label, argv, env)
    check_vector(before, OUT / "compile.inputs.after.json")
    generated = []
    archives = set()
    for p in WORK.rglob("*"):
        if p.is_file() and (p.name.startswith("importcfg") or p.name == "_testmain.go"):
            raw = p.read_bytes()
            dst = OUT / "compiler-generated" / p.relative_to(WORK)
            dst.parent.mkdir(parents=True, exist_ok=True)
            with dst.open("xb") as handle:
                handle.write(raw)
            generated.append(file_ref(dst))
            if p.name.startswith("importcfg"):
                for line in raw.decode("utf-8").splitlines():
                    if line.startswith("packagefile "):
                        archives.add(Path(line.split("=", 1)[1]))
    require(any(x["path"].endswith("_testmain.go") for x in generated), "GENERATED_TESTMAIN_ABSENT")
    save(OUT / "generated.manifest.json", generated)
    save(OUT / "compiled.archives.before.json", vector(archives))
    runtime = runtime_vector()
    save(OUT / "runtime.before-first-case.json", runtime)
    frozen = vector([x["path"] for x in before] + list(archives) + list(BIN.glob("*.exe"))
                    + [x["path"] for x in generated] + [OUT / "go-packages.json"]
                    + [x["path"] for x in runtime])
    _KNOWN_INPUTS.update(Path(x["path"]) for x in frozen)
    save(OUT / "execution.inputs.before-first-case.json", frozen)
    save(OUT / "prepare.completed.json", {"candidate": CANDIDATE, "input_count": len(frozen),
                                          "binaries": vector(BIN.glob("*.exe")), "cases_executed": 0})


def observe_child(stop, case_dir, expected_sha):
    """Best-effort copy, never alters/deletes a test temp file; logged hash remains required."""
    seen = set()
    while not stop.wait(0.05):
        for p in TEMP.rglob("researchos-cli.exe"):
            if str(p) in seen:
                continue
            try:
                raw = p.read_bytes()
            except OSError:
                continue
            if sha(raw) == expected_sha:
                dst = case_dir / "observed-child.exe"
                if not dst.exists():
                    with dst.open("xb") as handle:
                        handle.write(raw)
                    save(case_dir / "observed-child.json", {"actual_temporary_path": str(p), "copy": file_ref(dst)})
                seen.add(str(p))


def sql_atom(value):
    if isinstance(value, bytes):
        return {"type": "blob", "base64": base64.b64encode(value).decode("ascii")}
    return {"type": type(value).__name__, "value": value}


def dump_closed_databases(case_dir):
    for db in list(case_dir.rglob("*.sqlite")):
        require(not Path(str(db) + "-wal").exists(), "FIXTURE_WAL_STILL_PRESENT")
        original = file_ref(db)
        connection = sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            schema = connection.execute("SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name").fetchall()
            tables = []
            for (name,) in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name"):
                quoted = '"' + name.replace('"', '""') + '"'
                info = connection.execute("PRAGMA table_info(" + quoted + ")").fetchall()
                try:
                    cursor = connection.execute("SELECT rowid,* FROM " + quoted)
                    rowid = True
                except sqlite3.OperationalError as error:
                    require("no such column: rowid" in str(error), "ROWID_QUERY_UNEXPECTED:" + str(error))
                    cursor = connection.execute("SELECT * FROM " + quoted)
                    rowid = False
                rows = [[sql_atom(v) for v in row] for row in cursor.fetchall()]
                rows.sort(key=lambda row: json.dumps(row, sort_keys=True, ensure_ascii=False))
                tables.append({"name": name, "columns": info, "includes_rowid": rowid, "row_multiset": rows})
        finally:
            connection.close()
        save(db.with_suffix(".independent-alltables.json"), {"closed_database": original, "sqlite_schema": schema,
                                                         "tables": tables, "mode": "READONLY_PUBLIC_FIXTURE"})
        require(file_ref(db) == original, "CLOSED_DB_CHANGED")


def execute(env):
    require((OUT / "prepare.completed.json").is_file(), "PREPARE_REQUIRED")
    roster = read_json(HERE / "finite_selectors.json")["selectors"]
    require(len(roster) == 47, "ROSTER_LIMIT")
    frozen = read_json(OUT / "execution.inputs.before-first-case.json")
    _KNOWN_INPUTS.update(Path(x["path"]) for x in frozen)
    runtime_at_freeze = read_json(OUT / "runtime.before-first-case.json")
    current_runtime = runtime_vector()
    frozen_by_path = {x["path"]: x for x in frozen}
    require(all(frozen_by_path.get(x["path"]) == x for x in current_runtime), "NEW_RUNTIME_INPUT_BEFORE_CASE")
    check_vector(runtime_at_freeze, OUT / "runtime.execution-start.json")
    completed = []
    cli = file_ref(BIN / "researchos-cli.exe")
    for index, entry in enumerate(roster):
        case_dir = OUT / "cases" / f"{index:02d}"
        case_dir.mkdir(parents=True, exist_ok=False)
        check_vector(frozen, case_dir / "inputs.before.json")
        case_env = dict(env, RESEARCHOS_CLI_PROTOCOL_BINARY=str(BIN / "researchos-cli.exe"),
                        RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR=str(case_dir / "fixtures"))
        argv = [GO, "tool", "test2json", "-t", "-p", "researchos.local/research-os/apps/cli",
                BIN / "cli.test.exe", "-test.v", "-test.timeout=480s", "-test.failfast", "-test.run=" + entry["selector"]]
        native_windows = entry["selector"] == "^TestCLIReadStatusActualWindowsConsoleSignal$"
        stop = threading.Event()
        watcher = None
        if native_windows:
            watcher = threading.Thread(target=observe_child, args=(stop, case_dir, cli["sha256"]), daemon=True)
            watcher.start()
        try:
            invocation = invoke(f"case-{index:02d}", argv, case_env, cwd=CHECKOUT / "apps/cli")
        finally:
            stop.set()
            if watcher:
                watcher.join()
            current_runtime = runtime_vector()
            require(all(frozen_by_path.get(x["path"]) == x for x in current_runtime), "NEW_RUNTIME_INPUT_AFTER_CASE")
            check_vector(frozen, case_dir / "inputs.after.json")
            invocation_path = OUT / "invocations" / f"case-{index:02d}" / "invocation.json"
            observed = read_json(invocation_path) if invocation_path.is_file() else {}
            cleanup = observed.get("owned_process", {}).get("job_cleanup") or {}
            if cleanup.get("job_idle_confirmed") is True and cleanup.get("primary_exit_confirmed") is True:
                dump_closed_databases(case_dir)
            else:
                save(case_dir / "closed-database-dump.NOT_RUN.json", {
                    "reason": "OWNED_PROCESS_JOB_IDLE_NOT_CONFIRMED", "SQL_reads": 0,
                    "invocation": optional_ref(invocation_path)})
        events = [json.loads(line) for line in (invocation / "stdout.raw").read_text(encoding="utf-8").splitlines() if line.strip()]
        terminal = [e for e in events if e.get("Test") and e.get("Action") in ("pass", "fail", "skip")]
        leaves = [e for e in terminal if not any(x["Test"].startswith(e["Test"] + "/") for x in terminal)]
        actual_names = [e["Test"] for e in leaves]
        require(all(e["Action"] == "pass" for e in terminal), "FAIL_OR_SKIP:" + entry["selector"])
        require(sorted(actual_names) == sorted(entry["expected_leaf_names"]), "LEAF_INVENTORY_DRIFT")
        if native_windows:
            text = "".join(e.get("Output", "") for e in events)
            match = re.search(r"actual compiled CLI sha256=([0-9a-f]{64}) bytes=(\d+)", text)
            require(match is not None and match[1] == cli["sha256"] and int(match[2]) == cli["bytes"], "WINDOWS_CHILD_BINARY_BINDING")
            save(case_dir / "windows-child-binding.json", {"logged_hash": match[1], "logged_bytes": int(match[2]),
                "retained_prebuilt": cli, "actual_temp_copy_retained": (case_dir / "observed-child.exe").is_file(),
                "limitation": "Original test removes temporary file; matching logged hash binds content, not persistence of original path."})
        result = {"selector": entry["selector"], "native_exit": 0, "actual_leaves": actual_names,
                  "actual_leaf_count": len(leaves), "all_pass": True, "formal_acceptance": False}
        save(case_dir / "result.json", result)
        completed.append(result)
    check_vector(frozen, OUT / "execution.inputs.after-all.json")
    save(OUT / "execute.completed.json", {"actual_processes": len(completed),
         "actual_pass_leaves": sum(x["actual_leaf_count"] for x in completed), "results": completed,
         "not_run_hold": ["existing-open-readonly", "existing-self-send", "P02", "actual attach completion", "fullharness"],
         "SDK_MODEL_EXTERNAL_PAID_CALLS": 0, "source_acceptance": False})


def preserve_failure_observations(phase):
    # No child launch, SQL read, repair, or rerun. Unknown closure/DB cleanliness stays unknown.
    observations = []
    for path in sorted(_KNOWN_INPUTS, key=lambda p: str(p).casefold()):
        observations.append({"path": str(path), **optional_ref(path)})
    save(OUT / (phase + ".failure-known-inputs.json"), observations)
    fixtures = []
    cases = OUT / "cases"
    if cases.exists():
        for path in sorted(cases.rglob("*.sqlite")):
            fixtures.append({"path": str(path), **optional_ref(path),
                             "wal_exists": Path(str(path) + "-wal").exists(),
                             "shm_exists": Path(str(path) + "-shm").exists(),
                             "database_closed": None,
                             "alltables_receipt": optional_ref(path.with_suffix(".independent-alltables.json"))})
    save(OUT / (phase + ".failure-fixture-existence.json"), {
        "facts": fixtures, "limitation": "Existence/hash only. No new DB open or closure assertion on exceptional path."})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "execute"))
    parser.add_argument("--scope", required=True)
    parser.add_argument("--scope-sha256", required=True)
    args = parser.parse_args()
    auth = authorize(args)
    OUT.mkdir(parents=True, exist_ok=True)
    save(OUT / (args.phase + ".started.json"), {"at": now(), "authorization": auth, "argv": sys.argv})
    try:
        initialize_owned_runtime()
        save(OUT / (args.phase + ".runtime.initial.json"), runtime_vector())
        env = environment()
        (prepare if args.phase == "prepare" else execute)(env)
    except BaseException as error:
        observation_error = None
        try:
            preserve_failure_observations(args.phase)
        except BaseException as observation:
            observation_error = {"error_type": type(observation).__name__, "message": str(observation)}
        save(OUT / (args.phase + ".stopped.json"), {"at": now(), "error_type": type(error).__name__, "message": str(error),
             "failure_observation_error": observation_error,
             "next_action": "STOP; preserve originals; Root review before any correction/retry", "source_changes": 0})
        raise


if __name__ == "__main__":
    main()
