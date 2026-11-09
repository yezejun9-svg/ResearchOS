import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
RP = Path('execution/v2.4/receipts/W05/W05-99')
HANDLER = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
HP = RP / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
G1 = ROOT / RP / 'provider_whole9_g1_preparation_codex/093a934167674f6ca02e0a09dc5d5010'
F08 = ROOT / RP / 'cancel_finalization_whole20_scope_independent_review_codex/9781a48d5e844ebbaccab3670acfdd75'
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]

def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    assert expected is None or sha == expected, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(data)}

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return ref(OUT / name)

def verify_manifest(namespace, expected_sha, count):
    row = ref(namespace / 'manifest.json', expected_sha)
    manifest = json.loads((namespace / 'manifest.json').read_bytes())
    entries = manifest.get('files', manifest.get('entries'))
    assert len(entries) == count
    for entry in entries:
        path = Path(entry['path'])
        if not path.is_absolute(): path = ROOT / path if path.parts[0] == 'execution' else namespace / path
        actual = ref(path, entry['sha256'])
        assert 'bytes' not in entry or actual['bytes'] == entry['bytes']
    return row

before = {path: path.read_bytes() for path in CANON}
cp, ow = [json.loads(before[path]) for path in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (296, 124, 300)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert len(status.splitlines()) == 13 and len([row for row in status.splitlines() if row[:2] == b' D']) == 11
g1_manifest = verify_manifest(G1, '28167ff2d1b22d92378ed08376e5795a5bb42cc70992d6c15377f9091da2f1e2', 34)
g1_plan = ref(G1 / 'plan.json', '1a81fef42872ed4cd55e96feeb1fbc9ff7d4d9b656bac299ad58b8ffbf6749ac')
g1_runner = ref(G1 / 'run_g1.py', 'e0ab68f17a54db81e2a0173430f52a4d3e1c73578f6b87b48563ce652be8ce23')
plan = json.loads((G1 / 'plan.json').read_bytes())
layout = json.loads((G1 / 'layout.json').read_bytes())
assert plan['proposed_executor'] == 'codex:/root' and plan['candidate_commit'] == '6fb5263681c17f0e50920c354dc07ed440a23714'
assert not Path(layout['future_work_dir']).exists() and not Path(layout['future_receipt_dir']).exists()
assert not layout['shared_sdk_write_permission'] and layout['future_overlay'] == {'Replace': {}}
for item in json.loads((G1 / 'inputs.json').read_bytes())['inputs']:
    actual = ref(item['source'], item['sha256'])
    assert actual['bytes'] == item['bytes']
root_static = ref(ROOT / RP / 'provider_whole9_root_static_review_codex/r296/source_review.json', '46ff05149d89b9776f8f2cce878de6724c75c7bc0394716afe9f2ff7f3e7b85f')
g1_scope = save('provider_g1_execution_scope.json', {
    'schema': 'researchos.root.provider-whole9-g1-execution-scope.v1', 'actor': 'codex:/root', 'executor': 'codex:/root',
    'source_author': 'codex:/root/command_queue_impl', 'current_card': 'W05-99', 'Main_head': head,
    'candidate': plan['candidate_commit'], 'plan_ref': g1_plan, 'manifest_ref': g1_manifest, 'runner_ref': g1_runner,
    'root_static_review_ref': root_static, 'exact_execution': plan['minimal_scope'], 'layout': layout,
    'identity_split_erratum': {
        'sealed_plan_unchanged': True, 'cause': 'Plan swaps stream and verification between original7 and repaired2.',
        'repaired2': ['internal/domain/runtime_model_verification.go', 'internal/domain/runtime_provider_binding_windows_test.go'],
        'original7': ['adapters/runtime/mu/worker.mjs', 'adapters/runtime/mu/worker-provider-binding.test.mjs',
            'internal/domain/runtime_model.go', 'internal/domain/runtime_broker_windows.go', 'internal/domain/runtime_model_windows.go',
            'internal/domain/runtime_model_stream.go', 'internal/domain/runtime_provider_binding_test.go'],
        'basis': 'Existing 64+12 nonauthor exact2 review scope and frozen Git9; no source edits or acceptance widening.'},
    'single_attempt': True, 'first_unexpected_stops_dependency_lane': True, 'automatic_retries': 0,
    'limits': plan['timeouts_seconds'], 'full_actual_compile_and_SDK_input_closure_required': True,
    'fresh_bundle_from_candidate_required': True, 'shared_SDK_source_or_dist_writes': 0,
    'Main_product_source_writes': 0, 'external_paid_private_model_calls': 0, 'native_Go_Model_SQL_Host_cases': 0,
    'held_positive_cases_unlocked': 0, 'old64_or12_repeated': 0,
    'pre_existing_counter_state': {'checkpoint': 296, 'failure_origins': 300, 'counter_reset': False},
    'whole9_source_acceptance': False, 'Main23_composition_acceptance': False, 'formal_increment': 0})
f08_manifest = verify_manifest(F08, '5cfbb2847a1cd3a16de8d8e418529d18155f59cb63bdad39dbd197decf73a181', 172)
f08_review_ref = ref(F08 / 'source_review.json', 'eb3c51f299010f63dcb8ea162b0ecc6477df30adf34d46633146860701b4012d')
f08_review = json.loads((F08 / 'source_review.json').read_bytes())
assert f08_review['decision'] == 'REQUEST_CHANGES' and len(f08_review['findings']) == 2
assert f08_review['counts']['product_tests'] == f08_review['counts']['SQL'] == f08_review['counts']['formal_acceptance_increment'] == 0
f08_scope = save('f08_readonly_v5_revision_scope.json', {
    'schema': 'researchos.root.f08-readonly-revision-scope.v1', 'owner': 'codex:/root/command_queue_impl',
    'new_review_ref': f08_review_ref, 'review_manifest_ref': f08_manifest, 'source_paths_proposed': 20,
    'write_namespace_only': 'execution/v2.4/receipts/W05/W05-99/cancel_finalization_closed_contract_revision_v5_codex/**',
    'required_corrections': f08_review['findings'],
    'permitted': 'New immutable design/SQL text only/private evaluator contract/future controls. Whole20 closed relational contract revision in existing paths. Preserve all v4 and historical bytes.',
    'additional_source_categories': 'Report exact new categories if current32 cannot independently reconstruct current checkpoint/route authority; no assumption20suffices.',
    'source_or_SQL24_implementation_authorized': False, 'producer_file_writes_authorized': False,
    'SQL_or_tests_Node_HTTP_model_authorized': False, 'final_handler_freeze_required_before_implementation': True,
    'fresh_nonauthor_whole_scope_review_required': True, 'formal_increment': 0})

copies = []
def copy_handler_nested(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value and str(value['path']).startswith(HP.as_posix() + '/'):
            relative = Path(value['path']); assert relative.is_relative_to(HP)
            source = HANDLER / relative; src = ref(source, value['sha256']); data = source.read_bytes()
            target = ROOT / relative; target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): assert target.read_bytes() == data
            else:
                with target.open('xb') as stream: stream.write(data)
            copies.append({'source': src, 'copy': ref(target, src['sha256'])})
        else:
            for child in value.values(): copy_handler_nested(child)
    elif isinstance(value, list):
        for child in value: copy_handler_nested(child)

supplement_path = HP / 'cohort-supplement-876e36d2f7254b40949d660a3da760ef/supplement.json'
supplement_ref = ref(HANDLER / supplement_path, '8ed5ab5a63ac4fa21ccf18090bb2c15a099238a6b824167b768da7c004e2a765')
supplement = json.loads((HANDLER / supplement_path).read_bytes())
copy_handler_nested(dict(path=supplement_path.as_posix(), sha256=supplement_ref['sha256']))
copy_handler_nested(supplement)
supplement_ref = ref(ROOT / supplement_path)
assert len(supplement['new_failure_origins']) == 2 and supplement['no_combined_pass_total']
cohort_audit = []
for cohort in supplement['cohorts']:
    results = [row for row in cohort['refs'] if row['path'].endswith('/result.json')]
    invocations = [row for row in cohort['refs'] if row['path'].endswith('/command.invocation.json')]
    assert len(results) == len(invocations) == 1
    result = json.loads((ROOT / results[0]['path']).read_bytes())
    invocation = json.loads((ROOT / invocations[0]['path']).read_bytes())
    assert result['exit'] == invocation['exit'] and not result['source_drift']
    cohort_audit.append({'run': cohort['run'], 'result_ref': results[0], 'actual_exit': result['exit'],
        'input_count': result['input_count'], 'events': result['test_events'], 'source_acceptance': False})
audit_ref = save('handler_cohort_root_audit.json', {'supplement_ref': supplement_ref, 'cohorts': cohort_audit,
    'all_public_refs_verified': True, 'no_combined_pass_total': True, 'copies': copies, 'formal_increment': 0})
old_failures = copy.deepcopy(cp['failure_counters'])
for origin in supplement['new_failure_origins']:
    assert origin.get('actual_exit', origin.get('actual_outer_exit')) == 1
    key = 'W05-99/handler-cohort-supplement/' + origin['id']
    assert key not in {row.get('origin_key') for row in cp['failure_counters']}
    cp['failure_counters'].append({'origin_key': key, 'evidence_ref': supplement_ref, 'detail': origin,
        'attempts': 1, 'retries_used': 0, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE',
        'count_once': True, 'counter_reset': False, 'formal_increment': 0})
assert cp['failure_counters'][:300] == old_failures and len(cp['failure_counters']) == 302
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
for path, data in before.items():
    with (OUT / (path.stem + '.original.json')).open('xb') as stream: stream.write(data)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
subtasks['provider_whole9_g1_independent'] = {'owner': 'codex:/root', 'source_author': 'codex:/root/command_queue_impl',
    'state': 'BOUNDED_G1_SINGLE_ACTUAL_ATTEMPT_AUTHORIZED_NO_SOURCE_WRITES', 'scope_ref': g1_scope,
    'source_ready': False, 'production_source_writes': 0, 'formal_increment': 0}
subtasks['f08_whole_scope_readonly_review'].update(state='WHOLE20_V4_REQUEST_CHANGES_READONLY_V5_REVISION_ONLY',
    review_ref=f08_review_ref, readonly_v5_revision_scope_ref=f08_scope, SQL24_source_lease=False)
cp['work_in_progress'].update(provider_whole9_root_static_review_ref=root_static, provider_whole9_g1_execution_scope_ref=g1_scope,
    f08_whole20_review_ref=f08_review_ref, f08_readonly_v5_revision_scope_ref=f08_scope,
    configuration_handler_latest_cohorts_ref=audit_ref,
    pending_actual_failure_imports=['Root G1 newly executing single attempt, if failed; author exact38 new cohorts after 8ed supplement.'],
    next_action='Root NONAUTHOR executes exact G1 freshbundle/Go3/JS3 single attempt. Author implements CLI exact38. F08 v5 readonly design correction only after whole20 V4 REQUEST_CHANGES; no SQL24 lease. Final handler current freeze and whole9/current23 composition remain open.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'PROVIDER_G1_BOUND_AND_WHOLE20_REVIEW_REGISTERED',
    'scope_ref': g1_scope, 'F08_review_ref': f08_review_ref, 'failure_origins_before': 300, 'failure_origins_after': 302,
    'Main_source_writes': 0, 'formal_increment': 0})
cp.update(revision=297, expected_previous_revision=296, updated_at=now, updated_by='codex:/root')
ow.update(revision=125, amended_at=now, amended_by='codex:/root')
for row in [g1_scope, g1_plan, g1_runner, g1_manifest, root_static, f08_manifest, f08_review_ref, f08_scope, supplement_ref, audit_ref]:
    if row['path'] not in cp['evidence_index']: cp['evidence_index'].append(row['path'])
save('record.json', {'checkpoint': [296, 297], 'ownership': [124, 125], 'failures': [300, 302],
    'G1_scope_ref': g1_scope, 'F08_v5_readonly_scope_ref': f08_scope, 'Main_source_writes': 0, 'formal_increment': 0})
assert all(path.read_bytes() == data for path, data in before.items())
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
for path, value in zip(CANON[:2], [cp, ow]):
    temp = path.with_name(path.name + '.root297.tmp')
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
    assert path.read_bytes() == before[path]
    os.replace(temp, path)
assert all(path.read_bytes() == before[path] for path in CANON[2:])
print(json.dumps({'checkpoint': 297, 'ownership': 125, 'failure_origins': 302,
    'G1_scope_ref': g1_scope, 'F08_v5_scope_ref': f08_scope, 'Main_source_writes': 0, 'formal_increment': 0}, ensure_ascii=True))
