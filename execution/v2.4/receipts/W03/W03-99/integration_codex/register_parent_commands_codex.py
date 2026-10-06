"""Root-only registration after integrating the verified W03 implementation."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
V24 = ROOT / 'execution/v2.4'
EXECUTOR = HERE.parent / 'executor_codex'

def load(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

baseline_path = HERE / 'binding_baseline_codex.json'
baseline = load(baseline_path)
scope = load(HERE / 'source_repair_scope_codex.json')
integration = load(HERE / 'source_integration_codex.json')
assert integration['status'] == 'PASS_SCOPED_SOURCE_INTEGRATION'
assert integration['production_repair_scope_sha256'] == sha(HERE / 'source_repair_scope_codex.json')
for name, digest in integration['integrated_input_hashes'].items():
    assert sha(ROOT / name) == digest, name
for gate in ['W03-G01', 'W03-G02', 'W03-G03']:
    report = load(EXECUTOR / ('candidate_' + gate + '.json'))
    assert report['status'] == 'PASS' and report['assertion_ids'] == [gate]
    assert report['assertions'] == 1 and report['formal_product_acceptance'] == 'NOT_RUN'
    assert report['owned_acceptance_ids'] == []
    assert report['mode'] == ('DEVELOPMENT' if gate == 'W03-G01' else 'FIXTURE')
    assert report['evidence_index_sha256'] == sha(ROOT / report['evidence_index'])
registry_path = V24 / 'commands.json'
registry = load(registry_path)
before = copy.deepcopy(registry)
assert registry['revision'] == baseline['commands_revision'] == 36
assert registry['commands'] == baseline['v24_decoded_commands']
assert sha(ROOT / 'execution/commands.json') == baseline['legacy_registry_sha256']
for name, digest in baseline['protected_source_hashes'].items():
    assert sha(ROOT / name) == digest, name
for name, digest in scope['protected_sha256'].items():
    assert sha(ROOT / name) == digest, name
legacy_registry = load(ROOT / 'execution/commands.json')
changed = {}
keys = ['contracts.validate', 'test.domain']
extra_checks = {'contracts.validate': ['W03-G01', 'W03-G03'], 'test.domain': ['W03-G02']}
driver_files = ['bridge.py', 'gate_driver.py', 'expected.json']
driver_hashes = {name: sha(EXECUTOR / name) for name in driver_files}
for key in keys:
    original = copy.deepcopy(before['commands'][key])
    legacy = legacy_registry['commands'][key]
    entry = copy.deepcopy(original)
    entry['executable_tool'] = 'python'
    entry['argv'] = ['-B', (EXECUTOR / 'bridge.py').relative_to(ROOT).as_posix(), key]
    entry['tool_env'] = {**legacy['tool_env'], **original['tool_env'], 'RESEARCHOS_GO': 'go'}
    selectors = {}
    for field in ['task_id', 'check_id', 'case_id']:
        extension = ['W03'] if field == 'task_id' else extra_checks[key] if field == 'check_id' else []
        selectors[field] = list(dict.fromkeys(original['selectors'].get(field, []) + legacy['selectors'].get(field, []) + extension))
    entry['selectors'] = selectors
    # Historical legacy handlers read this registered identity. It is fixed by
    # the integrator and cannot come from an arbitrary caller environment.
    entry['fixed_env'] = {**legacy['fixed_env'], **original['fixed_env']}
    entry['owner_card'] = 'W03-99'
    entry['note'] = ('Exact W03 parent gates use the explicit command key and strict current immutable atom validation. '
        'Original W03 child handlers and other admitted legacy tuples retain their production Go/Python handlers and exit/streams. '
        'Singleton parent assertions remain separate from internal tests/fixtures. No formal case acceptance is produced.')
    artifacts = [(EXECUTOR / name).relative_to(ROOT).as_posix() for name in driver_files]
    artifacts += [(EXECUTOR / ('current_' + gate + '.json')).relative_to(ROOT).as_posix() for gate in extra_checks[key]]
    artifacts += [scope['root_owned_projection_path']]
    entry['expected_artifacts'] = list(dict.fromkeys(original['expected_artifacts'] + artifacts))
    for name in ['cwd', 'platforms', 'required_env', 'allowed_env', 'timeout_seconds', 'assertion_field', 'state']:
        assert entry[name] == original[name], name
    assert all(entry['fixed_env'][name] == value for name, value in original['fixed_env'].items())
    assert all(entry['tool_env'][name] == value for name, value in original['tool_env'].items())
    changed[key] = {'original_v24_entry': original, 'original_legacy_entry': legacy, 'new_entry': entry}
    registry['commands'][key] = entry
registry['revision'] = 37
assert {k: v for k, v in before['commands'].items() if k not in keys} == {k: v for k, v in registry['commands'].items() if k not in keys}
assert {k: v for k, v in before.items() if k not in ['commands', 'revision']} == {k: v for k, v in registry.items() if k not in ['commands', 'revision']}
assert not (HERE / 'parent_command_binding_codex.json').exists()
registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert load(registry_path) == registry
save_new(HERE / 'parent_command_binding_codex.json', {
    'schema': 'researchos.exact-parent-command-binding.v1', 'actor': 'codex:/root',
    'registered_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'registry_revision': 37, 'registry_sha256': sha(registry_path),
    'baseline_sha256': sha(baseline_path), 'production_repair_scope_sha256': sha(HERE / 'source_repair_scope_codex.json'),
    'source_integration_sha256': sha(HERE / 'source_integration_codex.json'),
    'bridge_input_hashes': driver_hashes, 'changed_entries': changed,
    'other_decoded_entries_preserved': len(registry['commands']) - 2,
    'protected_source_hashes_unchanged': baseline['protected_source_hashes'],
    'legacy_registry_sha256_before_after': baseline['legacy_registry_sha256'],
    'new_product_executions': 0, 'owned_acceptance_ids': [], 'formal_case_count_delta': 0,
    'parent_accepted': False,
})
print(json.dumps({'status': 'PASS_W03_PARENT_COMMAND_REGISTRATION', 'revision': 37,
    'other_entries_preserved': len(registry['commands']) - 2, 'new_product_executions': 0}))
