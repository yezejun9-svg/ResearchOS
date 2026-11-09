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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [304, 132, 343]
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
assert audit_ref['sha256'] == '42495b8497d2de1a03d2e17a46ddf1a0c0ba6e588582b75b31d2874f933df9ef'
assert ref(prepared['root_review_ref']['path'], prepared['root_review_ref']['sha256']) == prepared['root_review_ref']
audit = json.loads(read(audit_ref['path']))
assert audit['refs'] == refs and audit['canonical_before'] == prepared['canonical_before']
assert len(audit['manifests']) == 2 and all(row['bad'] == 0 for row in audit['manifests'])
origins = audit['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 5
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
for row in origins:
    assert row['origin_key'] not in old_keys
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:343] == old_failures and len(cp['failure_counters']) == 348
scope = json.loads(read(refs['cli_create_owned_lease_amendment_scope']['path']))
assert scope['status'] == 'AUTHORIZED_BY_CAS305_ONLY_NOT_EXECUTED'
assert scope['same8'] is True and len(scope['amendment_source_paths']) == 3
assert [row['id'] for row in scope['row_delta']] == ['P01-04', 'P01-05', 'P01-07']
assert len(scope['mandatory_conditions']) == 10 and scope['domain_SQL_provider_Main_frozen_contract_writes'] == 0
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(cli_created_owner_amendment_scope_ref=refs['cli_create_owned_lease_amendment_scope'],
    cli_created_owner_nonauthor_review_ref=refs['amendment_nonauthor_review'],
    cli_exact8_pre_amendment_development_handoff_ref=refs['source_pre_amendment_handoff_root_original'],
    cli_exact8_pre_amendment_failure_ref=refs['source_pre_amendment_failures_root_original'],
    cli_contract_diagnostic_state='EXACT8_AUTHOR_NARROW_CREATE_COMPLETED_VALID_OWN_LEASE_DIRECT_SEND_AMENDMENT_AUTHORIZED_FRESH_SOURCE_CASES_REQUIRED',
    cli_contract_source_ready=False)
chain_key = 'W05-99/cli-exact8-pre-amendment-build-and-tools'
assert chain_key not in cp['failure_chains']
cp['failure_chains'][chain_key] = {'actual_failed_invocations': 5, 'distinct_actual_causes': 5,
    'native_formatter_failure': 1, 'native_go_list_failure': 1, 'readonly_tool_failures': 3,
    'counter_reset': False, 'automatic_same_input_retry': False,
    'original_failure_ref': refs['source_pre_amendment_failures_root_original'],
    'pre_amendment_handoff_ref': refs['source_pre_amendment_handoff_root_original'],
    'state': 'FIVE_ORIGINAL_ORIGINS_RETAINED_NO_SOURCE_ACCEPTANCE_NO_NEW_TEST_INHERITANCE'}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
subtasks['cli_exact8_protocol_repair'].update(create_owned_lease_amendment_scope_ref=refs['cli_create_owned_lease_amendment_scope'],
    create_owned_lease_nonauthor_review_ref=refs['amendment_nonauthor_review'],
    pre_amendment_handoff_ref=refs['source_pre_amendment_handoff_root_original'],
    state=work['cli_contract_diagnostic_state'], source_ready=False,
    actual_attach_completion_positives='HOLD_DOMAIN_PRODUCER_NO_FAKE_COMPLETION',
    fresh_amended_source_compile_and_case_freeze_required=True)
cp['next_command'] = 'W05-99: Source exact8 applies only original session.create COMPLETED strict-full snapshot validated own nonexpired lease direct-send amendment, preserves 10 independent conditions and original row IDs, freezes exact future leaves and NEW full compiled artifacts before finite firstunexpected cases. Pre-amendment two native0 batches57/10leaf are historical development evidence only, no source acceptance inheritance. W05 C09 corrected six public copiedDB controls continue with raw-beforeDecode and original ACK/replay assertions; no A-E repeat. Actual attach acquire/renewal, P02/fullformal, provider G2 lease and F08 SQL24 remain HOLD. Original343prefix+5actualorigins retained; all22+42 acceptance required, formal0/42.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'CLI_SAME8_CREATE_COMPLETED_VALID_OWN_LEASE_AMENDMENT_BOUND_BY_NONAUTHOR_REVIEW',
    'audit_ref': audit_ref, 'root_review_ref': prepared['root_review_ref'],
    'amendment_scope_ref': refs['cli_create_owned_lease_amendment_scope'],
    'nonauthor_review_ref': refs['amendment_nonauthor_review'],
    'pre_amendment_handoff_ref': refs['source_pre_amendment_handoff_root_original'],
    'failure_origins_before': 343, 'failure_origins_after': 348, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=305, expected_previous_revision=304, updated_at=now, updated_by='codex:/root')
ow.update(revision=133, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [304, 305], 'ownership': [132, 133], 'failures': [343, 348]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root305.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root305.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual = json.loads(CANON[0].read_bytes())
    actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [305, 133, 348]
    assert actual['failure_counters'][:343] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 305, 'ownership': 133, 'failure_origins': 348,
        'intent_ref': intent_ref, 'old343_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r305-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 305, 'failure_origins': 348,
    'counter_reset': False, 'audit_ref': audit_ref, 'previous_handoff_ref': refs['previous_handoff'],
    'current_card': 'W05-99', 'cli_created_owner_scope_ref': refs['cli_create_owned_lease_amendment_scope'],
    'CLI': 'Exact8 narrowed create original COMPLETED/full own valid lease direct send authorized under10 nonauthor conditions. P01-04 actual public API/SQLite durable send TaskBLOCKED3 only; P01-05/07 protocol fixtures. New leaf freeze/full compiler provenance/new executables required. Previous native0 strict57leaf/attach10leaf development preserved without acceptance inheritance. Actual attach acquire/renewal and P02/fullformal HOLD.',
    'handler': 'r304 C09 corrected six copiedDB cases continue in assigned immutable cohort; original A-E and failed first C09 retained, no source38 acceptance yet.',
    'provider_F08': 'G2 finite29 and F08 exact21 future scopes ready with conditions, no product/edit/executionlease.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 305, 'ownership': 133, 'failure_origins': 348, 'handoff_ref': handoff_ref}, ensure_ascii=True))
