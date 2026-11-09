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
F08 = ROOT / RP / 'cancel_finalization_whole_scope_independent_review_codex/634606ae35154ad7aa85223c84ddf0b7'
PUBLIC = ROOT / RP / 'provider_typed_route_independent_replay_codex/79e9ab97-1451-4537-94db-e8259c9c67fa'
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
    assert p.is_relative_to(ROOT), str(p)
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if expected:
        assert sha == expected, str(p)
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(raw)}

def check(row):
    got = ref(row['path'], row['sha256'])
    if 'bytes' in row:
        assert got['bytes'] == row['bytes']
    return got

before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (292, 120, 275)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
old_deletions = [x for x in status.splitlines() if x[:2] == b' D']
assert len(old_deletions) == 11
assert not any(x[:1] not in [b' ', b'?'] for x in status.splitlines())

copies = []
def copy_handler(row):
    rel = Path(row['path'])
    assert not rel.is_absolute() and rel.is_relative_to(HP)
    source = HANDLER / rel
    s = ref(source, row['sha256'])
    raw = source.read_bytes()
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw
    else:
        with target.open('xb') as f:
            f.write(raw)
    got = ref(target)
    copies.append({'source': s, 'copy': got})
    return got

def copy_nested(o):
    if isinstance(o, dict):
        if 'path' in o and 'sha256' in o and str(o['path']).startswith(HP.as_posix() + '/'):
            copy_handler(o)
        else:
            for v in o.values():
                copy_nested(v)
    elif isinstance(o, list):
        for v in o:
            copy_nested(v)

proposal_rel = HP / 'queue-fixture-supplement-6061bdc7ccb44b728f6cd8e7d4f5c418/proposal.json'
proposal_ref = copy_handler({'path': proposal_rel.as_posix(), 'sha256': '84cd04fbe38cffabe4904eb33d4d9165764e50b5e5074ec4a3dab869e936048d'})
proposal = json.loads((ROOT / proposal_ref['path']).read_bytes())
protected = ref(HANDLER / proposal['protected_goal_fixture_ref']['path'], proposal['protected_goal_fixture_ref']['sha256'])
queue_before = ref(HANDLER / proposal['original_source_ref']['path'], proposal['original_source_ref']['sha256'])
assert proposal['source_paths_added'] == [] and proposal['tests_executed'] == 0

f08_manifest_ref = ref(F08 / 'manifest.json', '8a673b93ad23567dc14d01bed6e9ee5fea360a8a885ab0fe96e0d763d6aea98f')
f08_manifest = json.loads((ROOT / f08_manifest_ref['path']).read_bytes())
assert len(f08_manifest['files']) == 661
for row in f08_manifest['files']:
    check(row)
f08_review_ref = ref(F08 / 'source_review.json', '45da506b8d7d39651681cbf7f57bb03df60036688d6e42d1580b8aa3fd5e5c4d')
f08_contract_ref = ref(F08 / 'required_closed_contract.json', 'bca7add9e43b77174f597a6022284ab059250313e9764e283f60e31726fcc776')
f08_failure_ref = ref(F08 / 'failure_origins.json', '8cf776bf65699759a9fa4848c6caefd3ff28722613e5f79b4fc05e942e0be056')
f08_review = json.loads((ROOT / f08_review_ref['path']).read_bytes())
assert f08_review['verdict'] == 'REQUEST_CHANGES' and f08_review['whole_effective_scope_reviewed']
assert f08_review['candidate_scope_paths'] == 19

public_manifest_ref = ref(PUBLIC / 'manifest.json', 'bfbfa270bb5ca01dff9169af370be22eec8f641f9e749331029234ce628562d7')
public_manifest = json.loads((ROOT / public_manifest_ref['path']).read_bytes())
assert len(public_manifest['files']) == 87
for row in public_manifest['files']:
    check(row)
public_review_ref = ref(PUBLIC / 'review.json', 'de73819506def3fb023f055dcd3d0dc6151f2d9941a278035731e7daf9e794ec')
public_failure_ref = ref(PUBLIC / 'failure_origins.json', '330d03d90b3218273760e70c7a56c4c2a675755a09c93515a5860100a77813fe')
public_review = json.loads((ROOT / public_review_ref['path']).read_bytes())
assert public_review['this_cohort_actual'] == public_review['this_cohort_fail'] == 1
assert public_review['remaining_NOT_RUN'] == 11 and public_review['cumulative_actual'] == 66
assert public_review['frozen_inputs'] == 48381 and not public_review['input_drift']

old = copy.deepcopy(cp['failure_counters'])
keys = []
def append(key, evidence, detail):
    assert key not in {x.get('origin_key') for x in cp['failure_counters']}
    cp['failure_counters'].append({'origin_key': key, 'attempts': 1, 'retries_used': 0,
        'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_ORIGIN', 'evidence_ref': evidence,
        'detail': detail, 'count_once': True, 'counter_reset': False, 'formal_increment': 0})
    keys.append(key)

handler_failure_refs = []
for suffix, sha in [
    ('failure-supplement-a76b7d9c512a401c91f99783fe039850', '650935db4310972b6105b98ed435ba915f7b63a1f06e016e3f1df92c8363f67e'),
    ('failure-supplement-d5f06c32a7e0419a923c97ac53d40ea7', '0811d51cfae22eb0f566c03238b34ec44bafe943528f8d0cc07390a17e01ac53')]:
    fr = copy_handler({'path': (HP / suffix / 'failure_origins.json').as_posix(), 'sha256': sha})
    handler_failure_refs.append(fr)
    doc = json.loads((ROOT / fr['path']).read_bytes())
    copy_nested(doc)
    for row in doc.get('origins', doc.get('new_origins', [])):
        inv = row.get('invocation_ref', row.get('invocation'))
        actual = json.loads((ROOT / inv['path']).read_bytes())
        assert actual['exit'] == row['actual_exit'] == 1
        result_ref = row.get('result.json_ref', row.get('result'))
        if result_ref:
            assert json.loads((ROOT / result_ref['path']).read_bytes())['exit'] == 1
        identity = row.get('origin_id', inv['path'])
        append('W05-99/handler-validation/' + identity, fr, row)
    for row in doc.get('additional_tool_outer_nonzero', []):
        assert row['exit'] == 1
        append('W05-99/handler-read-tool/' + row['chunk'], fr, row)
for row in json.loads((ROOT / f08_failure_ref['path']).read_bytes())['origins']:
    assert row['actual_exit'] == 1
    append('W05-99/f08-read-tool/' + row['origin_id'], f08_failure_ref, row)
for row in json.loads((ROOT / public_failure_ref['path']).read_bytes())['origins']:
    assert row['native_exit'] == row['driver_outer_exit'] == 1
    for k in ['invocation', 'result', 'stdout', 'stderr']:
        check(row[k])
    assert json.loads(Path(row['result']['path']).read_bytes())['exit'] == 1
    append('W05-99/independent-provider-public/' + row['origin_id'], public_failure_ref, row)
assert len(keys) == 8 and len(cp['failure_counters']) == 283 and cp['failure_counters'][:275] == old

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
amendment = {'schema': 'researchos.root.same27-queue-fixture-amendment.v1', 'actor': 'codex:/root', 'at': now,
    'executor': 'codex:/root/sources_parent_impl', 'proposal_ref': proposal_ref,
    'original_scope_ref': cp['work_in_progress']['configuration_handler_scope_ref'],
    'path': 'internal/domain/client_command_queue_test.go', 'function': 'queueClientFixture',
    'exact_original_body_span': [11, 22], 'proposal_span23_includes_next_function_and_is_not_owned': True,
    'queue_before_ref': queue_before, 'protected_goal_fixture_ref': protected,
    'ordered_setup': proposal['ordered_minimal_setup'], 'prohibited': proposal['prohibited'],
    'authorized': True, 'source_paths_added': [], 'effective_source_path_count': 27,
    'common_owned_helper_hash_is_review_point_not_global_unchanged_requirement': True,
    'preserve_existing_test_bodies_assertions_queue_CAS_rollback_UNKNOWN_epoch': True,
    'new_workspace_write_MODEL_provenance_condition': 'Remove only new condition from owned Execute; preserve original Task/workspace/lease/baseline/permission guards. No model fixture expansion for workspace.write.',
    'new_cli6_scope_authorized': False, 'SQL_or_product_guard_relaxations': 0,
    'paid_external_or_private_calls': 0, 'formal_increment': 0}
save('queue_fixture_scope_amendment.json', amendment)
amendment_ref = ref(OUT / 'queue_fixture_scope_amendment.json')
save('handler-public-copy-audit.json', {'copies': copies, 'count': len(copies), 'Main_product_source_writes': 0})
save('f08-and-provider-input-audit.json', {'f08_manifest_ref': f08_manifest_ref, 'f08_files_checked': 661,
    'provider_manifest_ref': public_manifest_ref, 'provider_files_checked': 87, 'all_hashes_match': True})
for p, raw in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(raw)
sub = ow['card_path_bindings']['W05-99']['subtasks']['host_configuration_public_handlers']
assert len(sub['paths']) == 27
sub['queue_fixture_amendment_ref'] = amendment_ref
sub['state'] = 'EXACT27_HANDLER_QUEUE_FIXTURE_AUTHORIZED_CLI6_ADDITIONAL_SCOPE_UNDER_INDEPENDENT_READONLY_REVIEW'
ow['card_path_bindings']['W05-99']['subtasks']['f08_whole_scope_readonly_review'].update(
    state='WHOLE19_REQUEST_CHANGES_READONLY_CLOSED_CONTRACT_AUTHOR_REVISION_ONLY',
    review_ref=f08_review_ref, required_closed_contract_ref=f08_contract_ref,
    author_revision_namespace='execution/v2.4/receipts/W05/W05-99/cancel_finalization_closed_contract_revision_codex/**',
    response_cap_decision='REMOVE_NEW_RESPONSE_1MIB_CAP_PRESERVE_EXISTING_ENVELOPE_HEADER_LIMITS')
cp['work_in_progress'].update(configuration_handler_queue_fixture_amendment_ref=amendment_ref,
    configuration_handler_failure_supplements_r293=handler_failure_refs,
    f08_whole19_source_review_ref=f08_review_ref, f08_whole19_closed_contract_ref=f08_contract_ref,
    provider_independent_second_public_stop_ref=public_review_ref,
    pending_actual_failure_imports=['CLI6 proposal read tool3f47e5; F08 author revision locator toolde02b4, awaiting sealed copy/import'],
    next_action='Complete same27 handler queue fixtures and final bounded matrix; independent review exact6 CLI fixture additions before source scope33. Provider current64 internalPASS plus2 retained public harness failures; terminal-array proposal pending Root producer audit and separate third public12 authorization. F08 author closed-contract revision read-only; noSQL24 source lease before handler final freeze and whole revised contract review.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'SAME27_QUEUE_FIXTURE_AND_EIGHT_ACTUAL_FAILURE_ORIGINS_REGISTERED',
    'amendment_ref': amendment_ref, 'failure_keys': keys, 'failure_origins_before': 275, 'failure_origins_after': 283,
    'f08_review_ref': f08_review_ref, 'provider_public_stop_ref': public_review_ref, 'formal_increment': 0})
cp.update(revision=293, expected_previous_revision=292, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=121, amended_at=now, amended_by='codex:/root')
for row in [amendment_ref, f08_manifest_ref, f08_review_ref, f08_contract_ref, f08_failure_ref, public_manifest_ref, public_review_ref, public_failure_ref] + handler_failure_refs:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
save('record.json', {'checkpoint': [292, 293], 'ownership': [120, 121], 'failure_origins': [275, 283],
    'source_paths': 27, 'Main_product_source_writes': 0, 'formal_increment': 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
assert ref(HANDLER / proposal['protected_goal_fixture_ref']['path']) == protected
assert ref(HANDLER / proposal['original_source_ref']['path']) == queue_before
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
for p, value in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + '.root293.tmp')
    with temp.open('xb') as f:
        f.write(encode(value))
    assert p.read_bytes() == before[p]
    os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 293, 'ownership': 121, 'failure_origins': 283,
    'queue_fixture_amendment_ref': amendment_ref, 'source_paths': 27,
    'Main_product_source_writes': 0, 'formal_increment': 0}, ensure_ascii=True))
