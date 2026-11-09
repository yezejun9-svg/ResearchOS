import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
OLD = OUT.parent / 'independent-cli-list-scopes-r308'
BASE = ROOT / 'execution/v2.4'


def ref(path, expected=None):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected
    return item


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def write(name, value):
    ast.parse(value)
    with (OUT / name).open('xb') as stream:
        stream.write(value.encode('utf-8'))
    return ref(OUT / name)


def replace_once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new, 1)


jev = {
    'evaluation/holdout/jev/generate_other.go': {'git_blob': 'a0edc3fd43095520d2b5a77a4d1027e41c5ef147', 'sha256': '2afa6e97311ece753df8af74bd68de7ded3445d8a40bfa988f8ba17baadd5bf4', 'bytes': 186},
    'evaluation/holdout/jev/generate_windows.go': {'git_blob': '46bb72987cddbeeafb296dce03b2f160f5ec8c85', 'sha256': 'c02188ddd6c831ef0dc6b7af97b7667a05fa50e62f074d4b7ff709a0607baab1', 'bytes': 988},
    'evaluation/holdout/jev/generator.go': {'git_blob': '5be93941e7d0b8c3d22c60649f6dfe7689bcedd0', 'sha256': '1dc3d5154fe713155944b9ce761cd0bfc6a1fc4d92f34d0bac7ccd37df8aa523', 'bytes': 12685},
    'evaluation/holdout/jev/rubric.go': {'git_blob': '11bbedbcb5b621d6d0f0f8a2d2dbc38cb577eb8f', 'sha256': '10f3cc145780b4934e005db9bfb5ca7501a152f1caee89aee8732cc5eaf6e2ae', 'bytes': 2916},
    'evaluation/holdout/jev/truth.go': {'git_blob': '43e9c19fbbf98fc0ed790ec77d001b8182e8c9d7', 'sha256': 'b41064e0890811113e249a8fedc3a3ae153a5f71fa868e4763ffa2ad76cc4ca2', 'bytes': 4804},
}
resource_plan_path = BASE / 'receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json'
resource_plan_ref = ref(resource_plan_path)
resource_plan = json.loads(resource_plan_path.read_bytes())
assert resource_plan['git_resource_count'] == 518 and resource_plan['external_count'] == 5921
resources = {item['path']: item for item in resource_plan['git_resources']}
for name, pin in jev.items():
    assert all(resources[name][key] == value for key, value in pin.items())

original = (OLD / 'list_replay.py').read_text(encoding='utf-8')
assert ref(OLD / 'list_replay.py')['sha256'] == '764a62d357527f8503840ece15409a7a83d1c85d293680db35d6322cf2c61b5c'
code = original.replace('root-r308-534857db', 'root-r309-534857db-public-jev').replace('independent-session-list-r308-534857db', 'independent-session-list-r309-534857db-public-jev')
code = replace_once(code, "STATE = {'phase': 'NOT_STARTED'", 'PUBLIC_JEV = ' + repr(jev) + '\nRESOURCE_PLAN_REF = ' + repr(resource_plan_ref) + "\nSTATE = {'phase': 'NOT_STARTED'")
code = replace_once(code, "assert scope_path == DRAFT / 'list_independent_scope.json'", "assert scope_path == DRAFT / 'list_independent_scope.json'")
code = replace_once(code, 'global ENV, OVERRIDES, CLEARED, RUN_OWNED, OWN_OUT_CREATED', 'global ENV, OVERRIDES, CLEARED, RUN_OWNED, OWN_OUT_CREATED, PROCESS_HELPER')
code = replace_once(code, "helper_path = DRAFT / 'windows_owned_process.py'", "helper_path = (ROOT / scope['owned_process_helper_ref']['path']).resolve()")
code = replace_once(code, 'RUN_OWNED = helper_module.run_owned', 'RUN_OWNED = helper_module.run_owned\n    PROCESS_HELPER = helper_module\n    # Pure local URI conversion loads lazy standard-library modules before any input freeze.\n    (ROOT / \'__pure_uri_preload_no_file_access__\').as_uri()')
code = replace_once(code, "assert cp['revision'] >= 308", "assert cp['revision'] >= 309")
code = replace_once(code, "if name not in ['go.mod', 'go.sum', 'VERSION'] and not name.startswith", "if name not in PUBLIC_JEV and name not in ['go.mod', 'go.sum', 'VERSION'] and not name.startswith")
code = replace_once(code, "assert kind == 'blob' and mode in ['100644', '100755']", "assert kind == 'blob' and mode in ['100644', '100755']\n        if name in PUBLIC_JEV:\n            assert blob == PUBLIC_JEV[name]['git_blob']")
code = replace_once(code, "save('public-source-export.json', exports)", "save('public-source-export.json', exports)\n    for name, pin in PUBLIC_JEV.items():\n        actual = row(EXPORT / name)\n        assert actual['sha256'] == pin['sha256'] and actual['bytes'] == pin['bytes']\n    save('public-JEV-classification.json', {'resources': PUBLIC_JEV, 'classification': 'Previously approved generic public Go compiler sources; no private truth/qualification data or test generator execution', 'plan_ref': RESOURCE_PLAN_REF})")
initial = '''    initial_paths = {Path(item['path']) for item in exports}
    plan_path = ROOT / RESOURCE_PLAN_REF['path']
    assert sha(plan_path) == RESOURCE_PLAN_REF['sha256']
    public_plan = load(plan_path)
    for pin in public_plan['external_tools_modules_stdlib']:
        actual = row(pin['path'])
        assert actual['sha256'] == pin['sha256'] and actual['bytes'] == pin['bytes']
        initial_paths.add(Path(pin['path']))
    for directory in [goroot / 'src', goroot / 'pkg/tool', goroot / 'lib']:
        initial_paths.update(path for path in directory.rglob('*') if path.is_file())
    initial_paths.update([Path(lock[key]['path']) for key in ['python', 'git', 'go']])
    initial_paths.update([Path(go).parent / 'gofmt.exe', Path(__file__), helper_path, scope_path, lock_path, plan_path])
    initial_paths.update(runtime_paths())
    initial_freeze = vector(initial_paths)
    STATE['frozen_inputs'] = initial_freeze
    save('inputs.before_Go_tools.json', initial_freeze)
'''
code = replace_once(code, "    run('readonly-gofmt',", initial + "    run('readonly-gofmt',")
code = replace_once(code, "    inputs = {Path(item['path']) for item in exports}", "    save('inputs.after_Go_list.json', check_vector(initial_freeze))\n    inputs = set(initial_paths)")
code = replace_once(code, '    freeze = vector(inputs)', '    inputs.update(runtime_paths())\n    freeze = vector(inputs)')
code = replace_once(code, "        run(stem, [str(executable)", "        check_stage(stem, 'before_native', freeze)\n        run(stem, [str(executable)")
code = replace_once(code, "        stdout = (OUT / (stem + '.stdout.raw')).read_text", "        check_stage(stem, 'after_native', freeze)\n        stdout = (OUT / (stem + '.stdout.raw')).read_text")
code = replace_once(code, '        total_calls += wire_check', "        check_stage(stem, 'after_fixture_proofs', freeze)\n        total_calls += wire_check")
runtime = '''def runtime_paths():
    paths = {Path(path).resolve() for path in PROCESS_HELPER.runtime_resource_paths()}
    paths.update(Path(module.__file__).resolve() for module in list(sys.modules.values()) if getattr(module, '__file__', None) and Path(module.__file__).is_file())
    paths.update(path.resolve() for path in Path(sys.executable).parent.glob('python*.dll') if path.is_file())
    return paths


def check_stage(stem, stage, freeze):
    frozen = {item['path']: item for item in freeze}
    runtime = vector(runtime_paths())
    save(stem + '.' + stage + '.runtime.json', runtime)
    if any(frozen.get(item['path']) != item for item in runtime):
        raise RuntimeError('Unfrozen runtime input at ' + stem + ':' + stage)
    save(stem + '.' + stage + '.inputs.json', check_vector(freeze))


'''
code = replace_once(code, 'def typed_cells(values):', runtime + 'def typed_cells(values):')
runner_ref = write('list_replay.py', code)
scope = json.loads((OLD / 'list_independent_scope.json').read_bytes())
scope.update(status='AUTHORIZED_BY_CAS309_ONLY_NOT_EXECUTED', runner_ref=runner_ref,
    checkout=str(ROOT / '.local/independent-session-list-r309-534857db-public-jev'),
    output=str(ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r309-534857db-public-jev'),
    public_JEV_sources=jev, approved_public_compiler_plan_ref=resource_plan_ref,
    previous_failed_scope_ref=ref(OLD / 'list_independent_scope.json'),
    previous_failed_driver_ref=ref(OLD / 'list_replay.py'),
    input_change='Five hash-bound public compiler sources added; new export/cache/WORK/exe. Pure URI preload and full Python/OS closure before Go; containment and all inputs verified before native, after native, after fixture analysis.',
    preGo_freeze='All exported Git sources, prior public5921 modules/std inputs, full GOROOT src/tools/lib, Python/Go/Git/gofmt/controller/helper/scope/plan and actual runtime. Actual full Go deps/compiled/test/platform/embed graph augments freeze before fresh compile.',
    source_edit=0, same_input_automatic_retry=False)
scope['public_export'] += ' Only five individually pinned public evaluation/holdout/jev Go implementation files added; no JEV test/README/private data.'
list_scope_ref = save('list_independent_scope.json', scope)
cli_dir = BASE / 'receipts/W05/W05-99/cli_exact8_continuation_preparation_codex/cli44-r309-c927f880'
cli_handoff = json.loads((cli_dir / 'handoff.v3.json').read_bytes())
cli_spec = json.loads((cli_dir / 'prepared_execution_spec.v3.json').read_bytes())
for key in ['manifest', 'runner', 'spec', 'roster', 'static_audit', 'original_controller_failure']:
    pin = cli_handoff[key]
    actual = ref(pin['path'], pin['sha256'])
    assert actual['bytes'] == pin['bytes']
cli_scope = {'schema': 'researchos.finite-nonauthor-execution-scope.v1', 'status': 'AUTHORIZED_BY_CAS309_ONLY_NOT_EXECUTED',
    'owner': 'codex:/root/w05_merge_review', 'source_author': 'codex:/root/sources_parent_impl',
    'cli44_continuation': cli_spec['root_grant']['cli44_continuation'],
    'prepared_handoff_ref': ref(cli_dir / 'handoff.v3.json'),
    'prepared_spec_ref': ref(cli_dir / 'prepared_execution_spec.v3.json'),
    'runner_ref': ref(cli_dir / 'runner.v3.py'),
    'reused76': 'Original indexes0..2 native0 with completed runtime and7718 input closures. Preserved original cohort, not newly executed.',
    'new44': 'Supplement original3/4 closure-incomplete plus original5..46 NOT_RUN;145 expected unique leaves. No oldDB reuse or original-source rewrite.',
    'original_controller_failure_ref': ref(cli_handoff['original_controller_failure']['path']),
    'source_acceptance': False, 'Main_integration_authorized': False, 'Main_product_source_writes': 0, 'formal_increment': 0,
    'SDK_worker_MODEL_external_paid_private': 0, 'first_unexpected_stop': True, 'same_input_automatic_retry': False}
cli_scope['cli44_continuation']['prepared_manifest_v3_sha256'] = cli_handoff['manifest']['sha256']
cli_scope_ref = save('cli_continuation_scope.json', cli_scope)
cli_tree = ast.parse((cli_dir / 'runner.v3.py').read_text(encoding='utf-8'))
assert len([n for n in ast.walk(cli_tree) if isinstance(n, ast.FunctionDef) and n.name == 'authorize']) == 1
save('runner-preparation.audit.json', {'status': 'STATIC_DRAFTS_PREPARED_NO_NATIVE_PROCESS_CASE_OR_COMPILE',
    'original_list_driver_unchanged': ref(OLD / 'list_replay.py'), 'new_list_runner_ref': runner_ref,
    'new_list_scope_ref': list_scope_ref, 'new_CLI44_scope_ref': cli_scope_ref,
    'public_JEV5_already_in_approved_plan': True, 'CLI44_manifest8_checked': True,
    'new_export_build_SQL_HTTP_SDK_MODEL_paid': 0, 'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'list_runner': runner_ref, 'list_scope': list_scope_ref, 'cli_scope': cli_scope_ref}, ensure_ascii=True))
