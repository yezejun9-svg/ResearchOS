import hashlib
import json
from pathlib import Path
import sys
import uuid

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
BASE = Path(__file__).resolve().parent
REG = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/parallel-source-and-go3-r320'
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
READS = {}


def read(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path).resolve()
    raw = read(path)
    result = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected, str(path)
    return result


def verify(item, as_json=False):
    p = Path(item['path'])
    if not p.is_absolute():
        p = ROOT / p
    actual = ref(p, item['sha256'])
    assert actual['bytes'] == item['bytes']
    return json.loads(read(p)) if as_json else None


cp = json.loads(read(ROOT / 'execution/v2.4/checkpoint.json'))
ow = json.loads(read(ROOT / 'execution/v2.4/path_ownership.json'))
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [320, 148, 417]
audit_ref = ref(REG / 'registration-audit.json', 'aaa3a333c20c4dd60827dd234ce75c17fd2cca106a248bcbd3a4d49f69bfe123')
audit = json.loads(read(REG / 'registration-audit.json'))
assert audit['status'] == 'ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE'
assert audit['actual_registration_exit'] == 0 and audit['after'] == [320, 148, 417]
manifest_ref = ref(REG / 'manifest.json', '5af93dcc4467da9736f39693e9f3cb48bbe8ac5d26068cf884ded2b5ad2b8e80')
manifest = json.loads(read(REG / 'manifest.json'))
assert manifest['count'] == len(manifest['entries'])
for item in manifest['entries']:
    verify(item)
invocation = json.loads(read(REG / 'invocation.json'))
assert invocation['actual_exit'] == 0 and invocation['automatic_retry'] is False
registration_review = verify(invocation['review_ref'], as_json=True)
assert registration_review['decision'] == 'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION'
assert registration_review['sealer_ref']['sha256'] == '39090dedbbeb8d2f33c9fc3b45097fe67837c205e790cb4ffa90a2066087b782'
intent = json.loads(read(REG / 'canonical-write.intent.json'))
for item in intent['metadata']:
    expected = item['desired_ref']
    assert read(ROOT / item['path']) == read(ROOT / expected['path'])
for name in ['step_state', 'commands']:
    assert read(ROOT / 'execution/v2.4' / (name + '.json')) == read(REG / (name + '.original.json'))
scope_ref = ref(REG / 'go3_execution_scope.json')
scope = json.loads(read(REG / 'go3_execution_scope.json'))
assert scope['registration_checkpoint'] == 320 and scope['owner'] == 'codex:/root'
assert ow['card_path_bindings']['W13-03']['subtasks']['go3_debug_component_root_once']['scope_ref']['sha256'] == scope_ref['sha256']
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] is None
spec = verify(scope['spec_ref'], as_json=True)
spec_ref = ref(ROOT / scope['spec_ref']['path'], '858463e5dd1f5570c372de42476c65042d5e3d675085317711fe377323a4db76')
review = verify(scope['review_ref'], as_json=True)
assert review['decision'] == 'READY_FOR_ROOT_REGISTERED_GO3_DEBUG_PROOF_ONCE'
assert spec['source_commit'] == '06b1fbcb5934cbc70e5d65a46481e60c05c6594b'
assert spec['python_flags'] == ['-I', '-S', '-X', 'utf8'] and spec['caps']['test_executions'] == 1
assert spec['caps']['http'] == spec['caps']['sdk_model'] == spec['caps']['external'] == spec['caps']['paid'] == 0
assert not Path(spec['new_output_root']).exists()
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == spec['python_ref']['sha256']
for key in ['runner_ref', 'debug_helper_ref', 'outer_helper_ref', 'runtime_catalog_ref', 'test_exe']:
    verify(spec[key])
vector = verify(spec['input_vector_ref'], as_json=True)
assert isinstance(vector, list) and len(vector) == 8577
for item in vector:
    verify(item)
for item in spec['compiled_evidence_refs']:
    verify(item)
assert all(path.read_bytes() == raw for path, raw in READS.items())
out = BASE / uuid.uuid4().hex
out.mkdir()
authority = [audit_ref, manifest_ref, scope_ref, ref(REG / 'scope_registration.json'),
    ref(REG / 'invocation.json'), ref(REG / 'canonical-write.verified.json'),
    ref(ROOT / invocation['review_ref']['path']),
    ref(ROOT / scope['review_ref']['path']), ref(ROOT / scope['review_manifest_ref']['path']),
    ref(REG / 'seal.v2.py'), ref(REG / 'sealer-fix.binding.json')]
for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']:
    raw = read(ROOT / 'execution/v2.4' / (name + '.json'))
    with (out / (name + '.json')).open('xb') as stream:
        stream.write(raw)
    authority.append(ref(out / (name + '.json')))
grant = {'schema': 'researchos.root-go3-debug-component-grant.v2', 'authorized': True,
    'issuer': 'codex:/root', 'operation': 'GO3_SINGLE_DEBUG_EVENT_COMPONENT_EVIDENCE_V2',
    'max_executions': 1, 'actual_registration_completed': True, 'registration': [320, 148, 417],
    'spec_ref': spec_ref, 'authority_refs': authority, 'source_commit': spec['source_commit'],
    'test_exe': spec['test_exe'], 'selectors': spec['selectors'], 'caps': spec['caps'],
    'python_flags': spec['python_flags'], 'new_output_root': spec['new_output_root'],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'new_input_not_historical_normal_mode_attestation': True, 'Python_lifecycle_capture': False,
    'counter_reset': False, 'automatic_retry': False}
for key in ['runner_ref', 'debug_helper_ref', 'outer_helper_ref', 'python_ref', 'runtime_catalog_ref']:
    grant[key] = spec[key]
with (out / 'grant.json').open('xb') as stream:
    stream.write((json.dumps(grant, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
grant_ref = ref(out / 'grant.json')
with (out / 'grant-preflight.json').open('xb') as stream:
    stream.write((json.dumps({'grant_ref': grant_ref, 'compiled_inputs_rehashed': len(vector),
        'input_drift': 0, 'registered_scope_ref': scope_ref, 'product_processes_started': 0,
        'authority_ref_count': len(authority), 'counter_reset': False}, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'grant_ref': grant_ref, 'preflight_ref': ref(out / 'grant-preflight.json'), 'product_processes_started': 0}, ensure_ascii=True))
