import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
from pathlib import Path
import uuid

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PLAN = ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/7b236231f51d42319f8c21c0db715b01'

def ref(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    raw = p.read_bytes()
    item = {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected, str(p)
    return item

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)

proposed_ref = ref(PLAN / 'scope.final.proposed.json', 'dba36d6a333e405863a006ef6686e7d033982de340d914329792a0e15504c6c7')
controller_ref = ref(PLAN / 'integrate_exact38.py', '7ca8b3dcdfdfc4135da349bacefba7eb41ba18c425db43abb3e51df0fc2e155c')
ast.parse(Path(controller_ref['path']).read_bytes(), filename=controller_ref['path'])
mf_ref = ref(PLAN / 'manifest.json', 'c4f68af65250d5f3a0500b8568ee4a4b9a0a972ed17212b0c95d361db93cb5c1')
mf = json.loads(Path(mf_ref['path']).read_bytes())
assert len(mf['entries']) == 63
for item in mf['entries']:
    actual = ref(item['path'], item['sha256'])
    assert actual['bytes'] == item['bytes']
scope = json.loads(Path(proposed_ref['path']).read_bytes())
assert scope['status'] == 'PREPARATION_ONLY_NOT_EXECUTABLE'
assert scope['controller_ref'] == controller_ref
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
ow = json.loads((ROOT / 'execution/v2.4/path_ownership.json').read_bytes())
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [320, 148, 417]
assert ref(ROOT / 'execution/v2.4/checkpoint.json') == scope['preparation_canonical_checkpoint_ref'] | {'path': str(ROOT / 'execution/v2.4/checkpoint.json')}
operation = uuid.uuid4().hex
scope.update(
    status='ROOT_REGISTERED_EXACT38_INTEGRATION_ONCE',
    registration_checkpoint=321,
    registration_namespace=OUT.relative_to(ROOT).as_posix(),
    operation_uuid=operation,
    new_output_root=str(ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_executor_codex' / operation),
    base_commit=scope['source_chain'][0], target_source_commit=scope['source_chain'][-1],
    max_source_FF_operations=1,
    source_paths_ref=scope['exact38_ref'],
    Go_compile=0, Go_test=0, SQL=0, HTTP=0, SDK_MODEL_external_paid=0,
    effective_only_after_actual_registration_seal_and_once_grant=True,
    maximum_owned_Git_invocations=56,
    query_timeout_seconds=60, fast_forward_timeout_seconds=180,
    owned_child_cleanup_wait_seconds=5,
    native_process_bounds='Fixed 56-call maximum: three state snapshots *3, 6 chain queries, 1 local config, 1 aggregate diff, 38 target blobs, 1 FF. Each query60s, FF180s, owned cleanup5s. Root Python preflight/evidence IO is outside native child intervals.',
    Main_integration_currently_authorized=False,
    preparation_manifest_ref=mf_ref,
    read_only_task_packet_handoff_ref=ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/package-packet-and-zeroexit-lookups-r320/handoff.json', '1572419110be7501759a57a79c2496104d8d21b3c7293459b0368871d852e6ee'),
)
assert not Path(scope['new_output_root']).exists()
scope_ref = save('scope_registration.json', scope)
audit_ref = save('scope-freeze-audit.json', {
    'schema': 'researchos.root-source-only-scope-freeze.v1',
    'state': 'FROZEN_FOR_NONAUTHOR_CONTROLLER_SCOPE_REVIEW_NOT_REGISTERED_OR_EXECUTED',
    'controller_ref': controller_ref, 'scope_ref': scope_ref, 'preparation_manifest_ref': mf_ref,
    'only_scope_changes': 'Fresh UUID/output, actual registration namespace, explicit Root321 source-only constraints and numeric child bounds; original prepared controller/exact38/protected/evidence refs preserved.',
    'canonical_tuple': [320, 148, 417], 'expected_registration': [321, 149, 421],
    'actual_source_FF': 0, 'canonical_writes': 0, 'formal_increment': 0,
})
print(json.dumps({'scope_ref': scope_ref, 'controller_ref': controller_ref, 'audit_ref': audit_ref}, ensure_ascii=True))
