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
    assert expected is None or sha == expected
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
cp, ow = [json.loads(before[path]) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [300, 128, 316]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
refs = json.loads(read(OUT / 'prepared_refs.json'))
for row in refs.values():
    for item in row if isinstance(row, list) else [row]:
        actual = ref(item['path'], item['sha256'])
        assert actual['bytes'] == item['bytes']
audit_ref = refs['audit_ref']
assert audit_ref['sha256'] == '7fd430e788fbd8f98446dbfbd5346d9e6cb0affaa04e5770c0128dd02220e6c1'
assert refs['handler_scope_ref']['sha256'] == '456a3a93e9e0d458206af572038cf530a7eefcab332ab484444b68620e8e5fff'
assert refs['tap_scope_ref']['sha256'] == 'e21a09b9409b1991f2710278f3e8eef9eca7f088fa54a0943de66d49e9926e73'
audit = json.loads(read(audit_ref['path']))
for row in audit['handler_public_copies']:
    actual = ref(row['path'], row['sha256'])
    assert actual['bytes'] == row['bytes']
g1_audit_ref = audit['g1_originals_audit_ref']
g1_audit = json.loads(read(g1_audit_ref['path']))
for row in g1_audit['g1_original_refs'] + g1_audit['outer_original_refs']:
    actual = ref(row['path'], row['sha256'])
    assert actual['bytes'] == row['bytes']
assert g1_audit['outer_actual_exit'] == 1 and g1_audit['Go3_actual_exit'] == g1_audit['JS3_actual_exit'] == 0
assert g1_audit['compiled_inputs_count'] == 48392 and g1_audit['before_precase_failurecurrent_identical']
origins = audit['origins']
assert len(origins) == 6
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len({row['origin_key'] for row in origins}) == 6
for row in origins:
    assert row['origin_key'] not in old_keys
    evidence_ref = row['evidence_ref']
    ref(evidence_ref['path'], evidence_ref['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:316] == old_failures and len(cp['failure_counters']) == 322
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(configuration_handler_final_source_commit='22752a6a41732c8c158d7d7e1b8932ec958f8cb8',
    configuration_handler_final_evidence_commit='49aa8c6b3214997bcbbe28d10bed0df487d06601',
    configuration_handler_final_completion_commit='b01cd99531e88f344566f664f6e0dd4801521931',
    configuration_handler_current_nonauthor_review_ref=refs['review_ref'],
    configuration_handler_current_nonauthor_execution_scope_ref=refs['handler_scope_ref'],
    configuration_handler_scope_state='CURRENT38_FROZEN_NONSELF_EXECUTION_AUTHORIZED_NOT_ACCEPTED',
    configuration_handler_final_source_ready=False,
    configuration_handler_original_failure_audit_ref=audit_ref,
    provider_whole9_g1_attempt2_originals_ref=g1_audit_ref,
    provider_whole9_g1_readonly_adjudication_scope_ref=refs['tap_scope_ref'],
    provider_whole9_g1_state='ATTEMPT2_FAILED_TAP_SUMMARY_CLASSIFIER_NATIVE_CHILDREN0_READONLY_ADJUDICATION_AUTHORIZED',
    provider_independent_whole9_source_ready=False)
chain = cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation']
assert chain['actual_failed_invocations'] == chain['same_cause_failures'] == 1
chain.update(actual_failed_invocations=2, same_cause_failures=1,
    distinct_causes={'CJS_IMPORT_ONLY_ALIAS_PREPARATION': 1, 'TAP_TODO_ZERO_SUMMARY_CLASSIFIER': 1},
    latest_failure_ref=g1_audit_ref, state='SECOND_ATTEMPT_FAILED_NEW_HARNESS_CAUSE_NO_TEST_RETRY_AUTHORIZED',
    readonly_adjudication_scope_ref=refs['tap_scope_ref'], counter_reset=False, automatic_retry=False)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
handler = subtasks['host_configuration_public_handlers']
handler.update(state='CURRENT38_FROZEN_NONSELF_EXECUTION_AUTHORIZED_NOT_ACCEPTED',
    current_source_writer='FROZEN_NO_PRODUCT_WRITES', final_source_ready=False,
    final_source_commit=work['configuration_handler_final_source_commit'],
    final_evidence_commit=work['configuration_handler_final_evidence_commit'],
    final_completion_commit=work['configuration_handler_final_completion_commit'],
    final_nonauthor_review_ref=refs['review_ref'], nonauthor_execution_scope_ref=refs['handler_scope_ref'],
    nonauthor_executor='codex:/root/w05_merge_review', original_failure_audit_ref=audit_ref)
provider = subtasks['provider_whole9_g1_independent']
provider.update(state=work['provider_whole9_g1_state'], source_ready=False,
    attempt2_failure_originals_ref=g1_audit_ref, readonly_adjudication_scope_ref=refs['tap_scope_ref'])
cp['next_command'] = 'W05-99: NONAUTHOR execute frozen handler38 A-E and six explicit C09 overlay controls under CAS301 exact scope; Root readonly adjudicate original G1 native0 evidence under preserved harness failure. Source agent whole20/34 F08 v5 readonly review; command agent G2 causal proposal. No held cases, source merge or formal acceptance without actual current proof.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'HANDLER38_NONSELF_SCOPE_AND_G1_READONLY_ADJUDICATION_REGISTERED',
    'audit_ref': audit_ref, 'root_review_ref': refs['root_review_ref'],
    'handler_scope_ref': refs['handler_scope_ref'], 'tap_scope_ref': refs['tap_scope_ref'],
    'failure_origins_before': 316, 'failure_origins_after': 322,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=301, expected_previous_revision=300, updated_at=now, updated_by='codex:/root')
ow.update(revision=129, amended_at=now, amended_by='codex:/root')
for row in [audit_ref, refs['root_review_ref'], refs['handler_scope_ref'], refs['tap_scope_ref'], refs['review_ref'], refs['completion_ref']]:
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
    'transition': {'checkpoint': [300, 301], 'ownership': [128, 129], 'failures': [316, 322]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root301.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root301.tmp'), path)
        expected_live[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual = json.loads(CANON[0].read_bytes())
    actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [301, 129, 322]
    assert actual['failure_counters'][:316] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 301, 'ownership': 129, 'failure_origins': 322,
        'intent_ref': intent_ref, 'old316_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r301-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 301, 'failure_origins': 322,
    'counter_reset': False, 'original_failure_audit_ref': audit_ref,
    'previous_handoff_ref': ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-g1-esm-attempt2-scope-r300/handoff-r300-running.json', '64ac45e3fc01a8e57b013e82670cff729f9c59e2d308f48123337580e2b42077'),
    'current_card': 'W05-99', 'handler_scope_ref': refs['handler_scope_ref'], 'tap_readonly_scope_ref': refs['tap_scope_ref'],
    'handler': 'Frozen38/source+evidence+completion commits delivered. NONAUTHOR A-E plus six synthetic C09 controls authorized once; not yet executed by this registration.',
    'provider': 'Original alias1 and new harness TODO0 classifier failure retained; native Go3/JS26 child0 and48392 sealed equal inputs. Readonly retained-artifact/input/raw adjudication authorized; no test rerun.',
    'F08': 'NONAUTHOR whole20/34 v5 readonly review running, SQL24 implementation lease not granted.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 301, 'ownership': 129, 'failure_origins': 322, 'handoff_ref': handoff_ref}, ensure_ascii=True))
