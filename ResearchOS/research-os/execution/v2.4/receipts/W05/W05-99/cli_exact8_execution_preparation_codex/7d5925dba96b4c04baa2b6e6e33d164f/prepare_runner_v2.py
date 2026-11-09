"""Preparation only: transform immutable runner v1; AST parse, never import runners/helper."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
HELPER = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'
HELPER_SHA = '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'

def ref(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    with (HERE / name).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def replace_once(body, old, new):
    if body.count(old) != 1:
        raise RuntimeError('Replacement occurrence mismatch: ' + old[:100])
    return body.replace(old, new, 1)

if ref(HELPER)['sha256'] != HELPER_SHA:
    raise RuntimeError('HELPER_SHA')
ast.parse(HELPER.read_text(encoding='utf-8'))
old_manifest = json.loads((HERE / 'manifest.json').read_bytes())
old_refs = [ref(HERE / row['path']) for row in old_manifest['entries']]
for row, actual in zip(old_manifest['entries'], old_refs):
    if row['sha256'] != actual['sha256']:
        raise RuntimeError('OLD_MANIFEST_DRIFT:' + row['path'])
old_refs += [ref(HERE / n) for n in ('manifest.json', 'handoff.json')]
body = (HERE / 'runner.py').read_text(encoding='utf-8')
body = replace_once(body, 'import subprocess\n', 'import types\n')
body = replace_once(body, 'BIN = OUT / "bin"\n', '''BIN = OUT / "bin"
OWNED_HELPER = ROOT / "execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
OWNED_HELPER_SHA = "6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"
_PROCESS_HELPER = None
_RUNTIME_PATHS = set()
_KNOWN_INPUTS = set()
''')
body = replace_once(body, 'manifest = HERE / "manifest.json"\n    require(grant["prepared_manifest_sha256"] == sha(manifest.read_bytes()), "PREPARED_MANIFEST_GRANT")', '''manifest = HERE / "manifest.v2.json"
    require(grant["prepared_manifest_v2_sha256"] == sha(manifest.read_bytes()), "PREPARED_V2_MANIFEST_GRANT")
    helper = grant["owned_process_helper_ref"]
    require(Path(helper["path"]) == OWNED_HELPER and helper["sha256"] == OWNED_HELPER_SHA,
            "OWNED_PROCESS_HELPER_GRANT")
    require(file_ref(OWNED_HELPER)["sha256"] == OWNED_HELPER_SHA, "OWNED_HELPER_CHANGED")''')
body = replace_once(body, 'path = HERE / row["path"]\n        require(file_ref(path)', '''relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts, "MANIFEST_MEMBER_PATH")
        path = HERE / relative
        _KNOWN_INPUTS.add(path)
        require(file_ref(path)''')
start = body.index('def invoke(')
end = body.index('\n\ndef vector(', start)
body = body[:start] + '''def initialize_owned_runtime():
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
''' + body[end:]
body = replace_once(body, 'external_pins.append(actual)', 'external_pins.append(actual)\n        _KNOWN_INPUTS.add(Path(actual["path"]))')
body = replace_once(body, 'exported.append(file_ref(path))', 'exported.append(file_ref(path))\n        _KNOWN_INPUTS.add(path)')
body = replace_once(body, 'before = vector(inputs)', '''inputs.update(Path(x["path"]) for x in runtime_vector())
    _KNOWN_INPUTS.update(inputs)
    before = vector(inputs)''')
body = replace_once(body, 'frozen = vector([x["path"] for x in before] + list(archives) + list(BIN.glob("*.exe"))\n                    + [x["path"] for x in generated] + [OUT / "go-packages.json"])', '''runtime = runtime_vector()
    save(OUT / "runtime.before-first-case.json", runtime)
    frozen = vector([x["path"] for x in before] + list(archives) + list(BIN.glob("*.exe"))
                    + [x["path"] for x in generated] + [OUT / "go-packages.json"]
                    + [x["path"] for x in runtime])
    _KNOWN_INPUTS.update(Path(x["path"]) for x in frozen)''')
body = replace_once(body, 'completed = []\n    cli =', '''_KNOWN_INPUTS.update(Path(x["path"]) for x in frozen)
    runtime_at_freeze = read_json(OUT / "runtime.before-first-case.json")
    current_runtime = runtime_vector()
    frozen_by_path = {x["path"]: x for x in frozen}
    require(all(frozen_by_path.get(x["path"]) == x for x in current_runtime), "NEW_RUNTIME_INPUT_BEFORE_CASE")
    check_vector(runtime_at_freeze, OUT / "runtime.execution-start.json")
    completed = []
    cli =''')
body = replace_once(body, 'check_vector(frozen, case_dir / "inputs.after.json")', '''current_runtime = runtime_vector()
            require(all(frozen_by_path.get(x["path"]) == x for x in current_runtime), "NEW_RUNTIME_INPUT_AFTER_CASE")
            check_vector(frozen, case_dir / "inputs.after.json")''')
body = replace_once(body, '            dump_closed_databases(case_dir)', '''            invocation_path = OUT / "invocations" / f"case-{index:02d}" / "invocation.json"
            observed = read_json(invocation_path) if invocation_path.is_file() else {}
            cleanup = observed.get("owned_process", {}).get("job_cleanup") or {}
            if cleanup.get("job_idle_confirmed") is True and cleanup.get("primary_exit_confirmed") is True:
                dump_closed_databases(case_dir)
            else:
                save(case_dir / "closed-database-dump.NOT_RUN.json", {
                    "reason": "OWNED_PROCESS_JOB_IDLE_NOT_CONFIRMED", "SQL_reads": 0,
                    "invocation": optional_ref(invocation_path)})''')
start = body.index('\ndef main():')
body = body[:start] + '''
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
'''
tree = ast.parse(body)
if 'taskkill' in body or 'subprocess.Popen' in body or 'subprocess.run' in body:
    raise RuntimeError('OLD_PROCESS_PATH_REMAINS')
with (HERE / 'runner.v2.py').open('xb') as f:
    f.write(body.encode('utf-8'))
spec = json.loads((HERE / 'prepared_execution_spec.json').read_bytes())
spec['runner'] = ref(HERE / 'runner.v2.py')
spec['previous_prepared_v1'] = ref(HERE / 'handoff.json')
spec['owned_process_helper_ref'] = ref(HELPER)
grant = spec['Root_grant_required_top_level_key']['cli47_execution']
del grant['prepared_manifest_sha256']
grant['prepared_manifest_v2_sha256'] = '<actual manifest.v2.json hash from handoff.v2; manifest does not contain itself/handoff>'
grant['owned_process_helper_ref'] = ref(HELPER)
spec['launch_after_registration'] = [x.replace('<runner.py>', '<runner.v2.py>') for x in spec['launch_after_registration']]
spec['owned_process_contract'] = {
    'helper_import_before_root_grant': False,
    'success': 'actual_exit0/errorNULL/timed_outfalse/resumedtrue; assigned-before-resume, primary-exit, job-idle, handles-closed confirmed; cleanup errors empty',
    'stdin': 'immutable invocation/stdin.raw xb then rb file object; absent input NUL',
    'timeout_cleanup': 'only exclusive Job handle; helper tracks process handle+creation time; no PID taskkill',
    'residual_descendants': 'wait for primary AND Job idle; bounded timeout then owned Job termination; never native0 alone',
    'launch_and_cleanup_errors': 'finally seals argv/environment/current observations/stdout/stderr even actual_exit NULL; stops branch',
    'runtime_closure': 'after authorization only: actual loaded OS DLL inventory from helper, Python source/cache/modules/exe/helper; before compiler/firstcase and after/current hash closure, no assumed DLL path',
    'failure_facts': 'best effort current known input hashes and own fixture existence/WAL/SHM/alltable receipt; no new SQL/retry/claim closed on exceptions',
    'static_review_only': True,
    'windows_helper_runtime_tested': False,
}
save('prepared_execution_spec.v2.json', spec)
save('runner_static_audit.v2.json', {
    'decision': 'PREPARED_V2_AST_VALID_NO_IMPORT_OR_PRODUCT_EXECUTION',
    'runner': ref(HERE / 'runner.v2.py'), 'helper': ref(HELPER),
    'functions': [n.name for n in tree.body if isinstance(n, ast.FunctionDef)],
    'old_manifest_all_members_unchanged': all(ref(Path(x['path'])) == x for x in old_refs),
    'old_refs': old_refs,
    'roster': ref(HERE / 'finite_selectors.json'),
    'no_process_execution_during_review': True,
    'read_tool_refs': ['a8bb8c:helper-read actual0', 'e8977f:runner-read actual0', 'bf0648:spec-manifest-read actual0', 'f52e18:AGENTS/helperhash actual0'],
    'source_changes': 0, 'export_compile_cases': 0,
})
names = [x['path'] for x in old_manifest['entries']] + ['manifest.json', 'handoff.json', 'runner.v2.py',
    'prepared_execution_spec.v2.json', 'runner_static_audit.v2.json', 'prepare_runner_v2.py']
entries = []
for name in sorted(set(names)):
    entry = ref(HERE / name)
    entry['path'] = name
    entries.append(entry)
save('manifest.v2.json', {'schema': 'researchos.prepared-runner-manifest.v2', 'entries': entries,
    'count': len(entries), 'self_excluded': True, 'handoff_excluded': True,
    'external_helper': ref(HELPER)})
save('handoff.v2.json', {
    'decision': 'CLI47_V2_OWNED_JOB_RUNNER_PREPARED_FOR_ROOT_REGISTRATION_NO_EXECUTION',
    'manifest': ref(HERE / 'manifest.v2.json'), 'runner': ref(HERE / 'runner.v2.py'),
    'spec': ref(HERE / 'prepared_execution_spec.v2.json'), 'helper': ref(HELPER),
    'static_audit': ref(HERE / 'runner_static_audit.v2.json'),
    'origin09ff5c': ref(HERE / 'failure_origin_09ff5c.json'),
    'previous_handoff_unchanged': ref(HERE / 'handoff.json'),
    'source_export_compile_case_count': 0, 'new_tool_failures': [],
    'future_root_key': 'cli47_execution.prepared_manifest_v2_sha256',
    'candidate': spec['candidate'], 'exact_invocations': 47, 'expected_leaves': 221,
    'source_acceptance': False,
})
print(json.dumps({n: ref(HERE / n) for n in ('runner.v2.py', 'manifest.v2.json', 'prepared_execution_spec.v2.json', 'handoff.v2.json')}, ensure_ascii=False))
