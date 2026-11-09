import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os').resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
RECEIPTS = Path('execution/v2.4/receipts/W05/W05-99')
STOP = ROOT / RECEIPTS / 'provider_typed_route_independent_replay_codex/cc88ef8c-d066-4b10-b6c5-1d9bba89baad'
HANDLER = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
HP = RECEIPTS / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
CORRECTION = HP / 'snapshot-correction-ddae7b88430349d6b747f0a6a5b64f4e/failure_and_correction.json'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]


def encode(o):
    return (json.dumps(o, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def save(n, o):
    with (OUT / n).open('xb') as f:
        f.write(encode(o))


def ref(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    assert p.is_relative_to(ROOT)
    raw = p.read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    if expected:
        assert h == expected, str(p)
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': h, 'bytes': len(raw)}


def check(row):
    actual = ref(row['path'])
    assert actual['sha256'] == row['sha256'], row['path']
    if 'bytes' in row:
        assert actual['bytes'] == row['bytes'], row['path']


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (291, 119, 270)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
manifest_ref = ref(STOP / 'manifest.json', '9686f70444d3ac8f03a72da637f504d17e605801b8638c13b9e4676c072c9d59')
manifest = json.loads((ROOT / manifest_ref['path']).read_bytes())
assert len(manifest['files']) == 692
for row in manifest['files']:
    check(row)
review_ref = ref(STOP / 'review.json', '9a93dbc6d65f76f1c50a98b282a7c927fff7869a9e014b3225fc1fbd817473f7')
failure_ref = ref(STOP / 'failure_origins.json', '0cad4f7f7f27c7b131ca078adee7318169f782303db9312081003f985d2daea1')
proposal_ref = ref(STOP / 'public-overlay-causal-repair-proposal.json', 'f9c64207f3fa0754bd49914bffe26a499847e0ada2eacce2a3ef80b6a0898496')
review = json.loads((ROOT / review_ref['path']).read_bytes())
proposal = json.loads((ROOT / proposal_ref['path']).read_bytes())
assert review['actual_cases'] == 65 and review['internal_PASS'] == 64 and review['internal_FAIL'] == review['internal_SKIP'] == 0
assert review['public_attempt1_fail_harness'] == 1 and review['public_remaining_not_run'] == 11
assert review['frozen_inputs'] == 48435 and not review['input_drift']
assert review['schema_composition'] == 22 and not review['exact2_source_accepted'] and not review['whole_original9_accepted']
assert review['model_HTTP_Node_worker_paid_private'] == 0
check(review['independent_binary'])
for row in review['review_refs']:
    check(row)
check(proposal['source'])
check(proposal['production_interface'])
check(proposal['actual_failure'])
origin = json.loads((ROOT / failure_ref['path']).read_bytes())['origins'][0]
for key in ['invocation', 'result', 'raw']:
    check(origin[key])
result = json.loads((ROOT / ref(origin['result']['path'])['path']).read_bytes())
assert result['exit'] == origin['actual_exit'] == origin['driver_outer_exit'] == 1
assert origin['public_case_failed'] == 1 and not origin['product_P1']

copies = []


def copy_handler(row):
    rel = Path(row['path'])
    assert not rel.is_absolute() and rel.is_relative_to(HP)
    source = HANDLER / rel
    source_ref = ref(source, row['sha256'])
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    if target.exists():
        assert target.read_bytes() == raw
    else:
        with target.open('xb') as f:
            f.write(raw)
    got = ref(target)
    copies.append({'source': source_ref, 'copy': got})
    return got


correction_ref = copy_handler({'path': CORRECTION.as_posix(), 'sha256': '11f14b9adaa8a85ef88fed137287743a8e97e5b62ae70baea15ad726dab1c567'})
correction = json.loads((ROOT / correction_ref['path']).read_bytes())
check(correction['actual_source_ref'])
failed_handler = correction['actual_failed_origin']
for key, value in failed_handler.items():
    if key.endswith('_ref') and isinstance(value, dict):
        copy_handler(value)
handler_invocation = json.loads((ROOT / failed_handler['invocation_ref']['path']).read_bytes())
handler_result = json.loads((ROOT / failed_handler['result_ref']['path']).read_bytes())
assert failed_handler['actual_exit'] == handler_result['exit'] == handler_invocation['exit'] == 1
assert failed_handler['test_events'] == {'pass': 1, 'fail': 3, 'skip': 0} and failed_handler['distinct_leafs'] == 2
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
amendment = {
    'schema': 'researchos.root.independent-provider-public12-causal-overlay-amendment.v1',
    'actor': 'codex:/root', 'executor': 'codex:/root/w05_merge_review', 'at': now,
    'original_scope_ref': cp['work_in_progress']['provider_typed_route_independent_execution_scope_ref'],
    'previous_resource_amendment_ref': cp['work_in_progress']['provider_independent_complete_compiler_resource_amendment_ref'],
    'stopped_review_ref': review_ref, 'stopped_manifest_ref': manifest_ref,
    'failure_origin_ref': failure_ref, 'proposal_ref': proposal_ref,
    'original_overlay_ref': proposal['source'], 'production_interface_ref': proposal['production_interface'],
    'implementation_authorized': True, 'product_source_writes': 0, 'SQL_product_changes': 0,
    'exact_two_changes': [
        {'function': 'independentDecodedArchive', 'rule': 'wantWorkspace=false is accepted only with independently verified original ALL WorkspaceBinding row count0, absent workspace-index.json and absent every workspace-* decoded resource and manifest entry. No empty-index alternative. wantWorkspace=true still requires exact V1 index, one original authorized workspace and one31-byte supplied witness blob, full hash/metadata/callback/pin and restored/rebackup chain. Other inventory/ledger/schema/fullrow checks unchanged.'},
        {'function': 'independentWorkspace.SnapshotWorkspace and two constructors', 'rule': 'Rename third parameter destination and bind exactly the actual own case first backup or rebackup absolute directory. PrincipalID is compared to the exact frozen original binding field, not third argument or an invented constant. Preserve full original/ref/project/access/body checks, request/returned pins, limits and31-byte supplied witness. Never access original workspace path.'}
    ],
    'root_primary_source_check': 'Root actual99b9e9 exit0 read immutable backup_workspace.go:166-175 returns nil resources when no active bindings;190 passes destination to SnapshotWorkspace. Original proposal188 locator preserved but actual190 takes precedence. Root selects stricter original all-binding-count0/no workspace resources condition for these fixed public inputs.',
    'new_control_budget': {'public_positive': 6, 'public_negative': 6, 'total_new_public_invocations': 12,
        'positive_order': [1, 0, 2, 3, 4, 5], 'completed_internal_controls_not_repeated': 64,
        'retained_failed_public_invocations': 1, 'cumulative_planned_actual_invocations': 77},
    'cohort_rule': 'Keep internal64 actualPASS on original32f9 executable with its original48435 closure and exact candidate9. New public12 has its own new overlay/compiler/exe/complete before+after/current closure. Do not assert76PASS in one new exe, erase failed public1, or infer equivalence between old/new test executables. Pure product9 bytes remain identical, different test cohorts are declared explicitly.',
    'write_scope': 'Only new independent owned immutable overlay/driver/spec/receipt namespace and isolated cache. Preserve c300 old overlay, failed raw and all65 closed-case copies. No other helper/expectation/source change beyond exact two corrections and normal gofmt.',
    'next_sequence': 'New overlay -> actual gofmt/go-list/compiler closure/compile/exe freeze -> public-positive1 then0,2,3,4,5 actualCreateBackup/decode/Restore/rebackup, then six missing-dispatch negative publicCreateBackup refusal controls. First unexpected stops dependent controls; no automatic third edit/rerun.',
    'source_acceptance': False, 'whole9_acceptance': False, 'Main23_acceptance': False,
    'models_HTTP_Node_worker_paid_private_calls': 0, 'failure_reset': False,
    'old_history5_held': True, 'old_P1_three_preserved': True, 'preparation_failures': 3,
    'formal_increment': 0
}
save('public12_scope_amendment.json', amendment)
amendment_ref = ref(OUT / 'public12_scope_amendment.json')
save('handler-correction-copy-audit.json', {'copies': copies, 'count': len(copies), 'source_writes': 0})
old = copy.deepcopy(cp['failure_counters'])
keys = []


def append(key, status, evidence, detail):
    assert key not in {r.get('origin_key') for r in cp['failure_counters']}
    cp['failure_counters'].append({'origin_key': key, 'attempts': 1, 'retries_used': 0, 'status': status,
        'evidence_ref': evidence, 'detail': detail, 'count_once': True, 'counter_reset': False, 'formal_increment': 0})
    keys.append(key)


append('W05-99/independent-provider-public/' + origin['origin_id'], 'ACTUAL_PUBLIC_BACKUP_HARNESS_EXIT1_OUTER1_SINGLE_NIL_INDEX_CAUSE', failure_ref, origin)
append('W05-99/handler-validation/' + failed_handler['origin_id'], 'ACTUAL_BATCH_EXIT1_TWO_LEAF_FAILURES_ONE_SNAPSHOT_FIELD_CAUSAL_ORIGIN', correction_ref, failed_handler)
for row in correction['additional_tool_outer_nonzero']:
    assert row['outer_exit'] == 1
    append('W05-99/handler-read-tool/' + row['chunk'], 'REPORTED_ACTUAL_TOOL_OUTER1_TRANSCRIPT_LOCATOR_NO_PRODUCT_CASE', correction_ref, row)
assert cp['failure_counters'][:270] == old and len(keys) == 5 and len(cp['failure_counters']) == 275
for p, raw in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(raw)
sub = ow['card_path_bindings']['W05-99']['subtasks']['provider_typed_route_independent_replay']
sub.update(state='INTERNAL64_VALIDATED_ORIGINAL_COHORT_NEW_PUBLIC12_CAUSAL_OVERLAY_REPAIR_AUTHORIZED',
    public12_amendment_ref=amendment_ref, current_review_ref=review_ref,
    maximum_controls=77, completed_internal_controls=64, retained_failed_public_controls=1, public_controls_remaining=12,
    maximum_controls_meaning='Cumulative explicit Root amendment: original internal64 + failed public1 + new public12, not77 unique controls or76 single-exe PASS.')
cp['work_in_progress'].update(provider_independent_public12_amendment_ref=amendment_ref,
    provider_independent_internal64_review_ref=review_ref,
    configuration_handler_snapshot_correction_ref=correction_ref,
    configuration_handler_16pass_and_actual_tls_sdk='Author reported current16PASS and isolatedTLS1PASS on separate explicit frozen cohorts; final full27/matrix/nonself acceptance still pending. Original no-task_id snapshot mistake corrected through command-correlated immutable TASK_CHANGED events/Task/NoProgressRecord chain.',
    pending_actual_failure_imports=['handler firstTLS Node alias executable reparse refusal, awaiting new sealed failure refs'],
    next_action='Execute only newpublic12 with two causal overlay corrections and new cohort; retain originalinternal64. Handler same27 completes actualTLS/provenance/settledRun controls then fullsourcefreeze. F08 whole19 remains readonly, closed witness/legacy origin boundary/response limit still mandatory design corrections. No current formal acceptance.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'PROVIDER_INTERNAL64_RETAINED_PUBLIC12_TWO_CAUSAL_OVERLAY_REPAIRS_AND_HANDLER_SNAPSHOT_PROOF_CORRECTION',
    'amendment_ref': amendment_ref, 'handler_correction_ref': correction_ref, 'unique_failures': keys,
    'failure_origins_before': 270, 'failure_origins_after': 275, 'formal_increment': 0})
cp.update(revision=292, expected_previous_revision=291, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=120, amended_at=now, amended_by='codex:/root')
for row in [amendment_ref, review_ref, manifest_ref, failure_ref, proposal_ref, correction_ref]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
save('record.json', {'checkpoint': [291, 292], 'ownership': [119, 120], 'failure_origins': [270, 275],
    'internal_pass_retained': 64, 'retained_public_failure': 1, 'new_public_budget': 12,
    'cumulative_planned_actual': 77, 'source_changes': 0, 'formal_increment': 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, value in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + '.root292.tmp')
    with temp.open('xb') as f:
        f.write(encode(value))
    assert p.read_bytes() == before[p]
    os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 292, 'ownership': 120, 'failure_origins': 275,
    'public12_amendment_ref': amendment_ref, 'retained_internal': 64,
    'source_writes': 0, 'formal_increment': 0}, ensure_ascii=True))
