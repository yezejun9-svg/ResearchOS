import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
READS = {}


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    raw = read(path)
    sha = hashlib.sha256(raw).hexdigest()
    assert expected is None or sha == expected, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(raw)}


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)


lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
before = {path: path.read_bytes() for path in CANON}
prepared = json.loads(read(OUT / 'prepared_refs.json'))
assert len(prepared['canonical_before']) == 4
for path, pin in zip(CANON, prepared['canonical_before']):
    assert path == ROOT / pin['path']
    assert hashlib.sha256(before[path]).hexdigest() == pin['sha256'] and len(before[path]) == pin['bytes']
cp, ow = [json.loads(before[path]) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [303, 131, 338]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == prepared['head'] == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == prepared['git_status_sha256'] == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
for item in prepared['all_verified_refs']:
    actual = ref(item['path'], item['sha256'])
    assert actual['bytes'] == item['bytes']
refs = prepared['pins']
audit_ref = prepared['audit_ref']
assert audit_ref['sha256'] == '25934a83e2141e466ee13f89e539f657230ef99e0485837c0516b568cf87e5dc'
assert ref(prepared['root_review_ref']['path'], prepared['root_review_ref']['sha256']) == prepared['root_review_ref']
audit = json.loads(read(audit_ref['path']))
assert audit['refs'] == refs and audit['canonical_before'] == prepared['canonical_before']
assert len(audit['manifests']) == 5 and all(row['bad'] == 0 for row in audit['manifests'])
origins = audit['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 5
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
for row in origins:
    assert row['origin_key'] not in old_keys
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:338] == old_failures and len(cp['failure_counters']) == 343
scope = json.loads(read(refs['C09_corrected_execution_scope']['path']))
assert scope['status'] == 'AUTHORIZED_BY_CAS304_ONLY_NOT_EXECUTED'
assert scope['candidate'] == '22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
assert len(scope['cases']) == 6 and scope['A_E_rerun'] is False
assert scope['product38_SQL_SDK_Main_canonical_writes'] == 0
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(configuration_handler_AE_nonauthor_audit_ref=refs['AE_audit'],
    configuration_handler_AE_manifest_ref=refs['AE_manifest'],
    configuration_handler_C09_original_failed_handoff_ref=refs['C09_handoff'],
    configuration_handler_C09_original_failure_ref=refs['C09_failure'],
    configuration_handler_C09_constructor_supplement_ref=refs['C09_supplement'],
    configuration_handler_C09_correction_nonauthor_review_ref=refs['C09_correction_review'],
    configuration_handler_C09_corrected_execution_scope_ref=refs['C09_corrected_execution_scope'],
    configuration_handler_scope_state='AE_FIVE_BATCHES_PASS_C09_ORIGINAL_PREREQUISITE_FAILURE_RETAINED_NEW_CORRECTED6_SCOPE_AUTHORIZED',
    configuration_handler_final_source_ready=False,
    cli_exact8_attach_producer_hold_ref=refs['cli_attach_hold'],
    cli_contract_diagnostic_state='EXACT8_AUTHOR_IMPLEMENTING_VALID_SELFWRITER_AND_STRICT_PROTOCOL_GATES_ACTUAL_WRITE_ATTACH_COMPLETION_POSITIVES_HELD',
    provider_g2_finite_nonauthor_root_scope_review_ref=refs['G2_root_review'],
    provider_g2_finite_nonauthor_root_conditions_ref=refs['G2_root_conditions'],
    provider_g2_causal_state='FINITE29_NONSELF_SCOPE_READY_WITH_CONDITIONS_SOURCE_AND_EXECUTION_LEASE_STILL_ABSENT')
chain_key = 'W05-99/handler38-C09-independent-prerequisite'
assert chain_key not in cp['failure_chains']
cp['failure_chains'][chain_key] = {'actual_failed_invocations': 1, 'same_cause_failures': 1,
    'distinct_actual_causes': 1, 'counter_reset': False, 'automatic_same_input_retry': False,
    'original_native_exit': 1, 'original_outer_exit': 1, 'failed_leaf_events': 1, 'failed_parent_events': 1,
    'unexecuted_static_after_sequence_defect_not_another_failure': True, 'remaining_NOT_RUN': 5,
    'original_failure_ref': refs['C09_failure'], 'corrected_scope_ref': refs['C09_corrected_execution_scope'],
    'state': 'ORIGINAL_FAILED_INVOCATION_RETAINED_NEW_TWO_FIX_CONSTRUCTOR_INPUT_REQUIRED_BEFORE_NEXT_CASE'}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
subtasks['host_configuration_public_handlers'].update(state=work['configuration_handler_scope_state'],
    source_ready=False, independent_AE_audit_ref=refs['AE_audit'], independent_C09_failure_ref=refs['C09_failure'],
    independent_C09_corrected_scope_ref=refs['C09_corrected_execution_scope'], current_source_writer='FROZEN_NO_PRODUCT_WRITES')
assert 'handler38_c09_fixture_corrected_independent' not in subtasks
subtasks['handler38_c09_fixture_corrected_independent'] = {'owner': 'codex:/root/w05_merge_review',
    'integrator': 'codex:/root', 'verifier': 'codex:/root/command_queue_impl',
    'checkout': scope['checkout'], 'receipt_namespace': scope['new_receipt_namespace'],
    'work_namespace': scope['new_work_namespace'], 'virtual_test': scope['virtual_test'],
    'allowed_new_artifact_surfaces': scope['change_surface'], 'scope_ref': refs['C09_corrected_execution_scope'],
    'nonauthor_test_correction_review_ref': refs['C09_correction_review'],
    'state': 'NEW_TWO_CONSTRUCTOR_FIX_INPUT_PLUS_FRESH_FULL_COMPILE_SIX_CASES_AUTHORIZED_NOT_ACCEPTED',
    'product_source_writer': False, 'product_source_acceptance': False, 'formal_increment': 0}
subtasks['cli_exact8_protocol_repair'].update(attach_producer_hold_ref=refs['cli_attach_hold'],
    actual_attach_completion_positives='HOLD_DOMAIN_PRODUCER_NO_FAKE_COMPLETION',
    state=work['cli_contract_diagnostic_state'], source_ready=False)
cp['next_command'] = 'W05-99: W05 implement only new C09 physical fixture constructor epoch:null plus actual after_sequence, raw-before-Decode and typed ACK/original journal/replay evidence; new full compiler closure/exe and original six copiedDB controls firstunexpected; no A-E repeat or product38 edits. Source exact8 CLI P01/P03/P04 continues valid selfwriter/readonly/refusal and strict typedfixture controls; actual new/noWriter/renewal attach completion positives HOLD/domainproducer, P02/fullformal held. Root records G2 finite29 nonauthor scope+conditions without source/executionlease; F08 exact21 SQL24 remains held. Original338prefix+5actualinvocations preserved, formal0/42.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'C09_TWO_CONSTRUCTOR_FIX_SCOPE_AFTER_ORIGINAL_FAILURE_AND_ATTACH_PRODUCER_HOLD_REGISTERED',
    'audit_ref': audit_ref, 'root_review_ref': prepared['root_review_ref'],
    'C09_corrected_scope_ref': refs['C09_corrected_execution_scope'],
    'CLI_attach_producer_hold_ref': refs['cli_attach_hold'], 'G2_nonauthor_scope_ref': refs['G2_root_review'],
    'failure_origins_before': 338, 'failure_origins_after': 343, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=304, expected_previous_revision=303, updated_at=now, updated_by='codex:/root')
ow.update(revision=132, amended_at=now, amended_by='codex:/root')
for row in [audit_ref, prepared['root_review_ref'], *refs.values()]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
for path, raw in before.items():
    with (OUT / (path.stem + '.original.json')).open('xb') as stream:
        stream.write(raw)
with (OUT / 'git-status.original.raw').open('xb') as stream:
    stream.write(status)
desired = {path: (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8') for path, value in zip(CANON[:2], [cp, ow])}
for path, raw in desired.items():
    with (OUT / (path.stem + '.desired.json')).open('xb') as stream:
        stream.write(raw)
intent_ref = save('canonical-write.intent.json', {'actor': 'codex:/root', 'Main_head': head,
    'status_ref': ref(OUT / 'git-status.original.raw'), 'register_ref': ref(Path(__file__)),
    'toolchain_lock_ref': ref(ROOT / 'execution/toolchains/locked.json'),
    'transition': {'checkpoint': [303, 304], 'ownership': [131, 132], 'failures': [338, 343]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root304.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root304.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual = json.loads(CANON[0].read_bytes())
    actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [304, 132, 343]
    assert actual['failure_counters'][:338] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 304, 'ownership': 132, 'failure_origins': 343,
        'intent_ref': intent_ref, 'old338_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r304-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 304, 'failure_origins': 343,
    'counter_reset': False, 'audit_ref': audit_ref, 'previous_handoff_ref': refs['previous_handoff'],
    'current_card': 'W05-99', 'handler_C09_corrected_scope_ref': refs['C09_corrected_execution_scope'],
    'handler': 'Original A-E separate189/10/1/1/294 named PASS and39/4/1/1/69 topPASS,0fail/skip,42940inputsno drift. Original C09 native1/outer1 at firstattach DecodeEnvelope retained, fiveNOTRUN. New epoch:null+actualafter_sequence constructors, raw-beforeDecode and typedACK/journal/replay full evidence with six fresh copiedDB and NEW fullcompiled executable authorized. No source38 acceptance or A-E repeat.',
    'CLI': 'Exact8 source author implementing P01/P03/P04 in isolated22752 branch. Current actual writeattach onlyACK/no finalizer, so real create/noWriter/renewal completion positives HOLD; valid selfwriter via readonlyvalidatedsnapshot, foreign/expired refusal and labelledtypedprotocolfixture controls may proceed. Original37 scenario roster and old69IDs/26failures retained; no false fullscope acceptance, P02/fullformal held.',
    'provider': 'G1 original child0 readonlyadjudicated originalouter1/taskkill128/chain2 retained. Finite29 test-only G2 scope now Root-nonauthor reviewed with precise stage/fault/reservation conditions but still no edits/executionlease, no whole9 acceptance.',
    'F08': 'Exact21 startupcaller/type scope remains ready with12conditions but SQL24 source/editlease absent,40+12controls NOT_RUN.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 304, 'ownership': 132, 'failure_origins': 343, 'handoff_ref': handoff_ref}, ensure_ascii=True))
