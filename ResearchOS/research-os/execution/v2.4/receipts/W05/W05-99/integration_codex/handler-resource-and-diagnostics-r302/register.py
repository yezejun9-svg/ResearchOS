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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [301, 129, 322]
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
assert audit_ref['sha256'] == '08bfa673a21a32c8ec4f0b79b888c22210999bea35be6b5dea9f7c7cb8aa69d5'
assert prepared['root_review_ref']['sha256'] == '008b5dc2cce224f566430ea03d502b2cd475c398ee8638ab544d3d4a559bbe93'
audit = json.loads(read(audit_ref['path']))
assert audit['refs'] == refs and audit['canonical_before'] == prepared['canonical_before']
assert len(audit['manifests']) == 5 and all(row['bad'] == 0 for row in audit['manifests'])
origins = audit['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 8
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
for row in origins:
    assert row['origin_key'] not in old_keys
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:322] == old_failures and len(cp['failure_counters']) == 330
g1 = json.loads(read(refs['g1_result']['path']))
assert g1['original_outer_actual_exit'] == 1 and g1['original_termination_actual_exit'] == 128
assert g1['original_Go3_actual_exit'] == g1['original_JS3_actual_exit'] == 0
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(configuration_handler_public_compile_resource_amendment_ref=refs['resource'],
    configuration_handler_public_compile_resource_review_ref=refs['resource_review'],
    configuration_handler_scope_state='CURRENT38_FROZEN_CORRECTED_PREPARATION_AUTHORIZED_NOT_ACCEPTED',
    configuration_handler_final_source_ready=False,
    provider_whole9_g1_readonly_result_ref=refs['g1_result'],
    provider_whole9_g1_readonly_actual_invocation_ref=refs['g1_invocation'],
    provider_whole9_g1_state='LIMITED_ORIGINAL_NATIVE_G1_VERIFIED_HARNESS_FAILURE_PRESERVED_NONSELF_ADJUDICATION_REVIEW_PENDING',
    provider_independent_whole9_source_ready=False,
    f08_v5_whole20_34_nonauthor_review_ref=refs['f08_review'],
    f08_type_boundary_revision_ref=refs['f08_type_revision'],
    f08_type_boundary_state='REVISION_REVIEW_PENDING_STARTUP_CALLER_SCOPE_GAP_NO_SQL24_LEASE',
    cli_contract_diagnostic_nonauthor_review_ref=refs['cli_review'],
    cli_contract_diagnostic_scope_proposal_ref=refs['cli_proposal'],
    cli_contract_diagnostic_state='STATIC_P01_P03_CONFIRMED_P04_CATEGORY_INTERPRETATION_PENDING_NO_SOURCE_LEASE',
    provider_g2_causal_scope_review_ref=refs['g2_review'],
    provider_g2_causal_conditions_ref=refs['g2_conditions'],
    provider_g2_causal_selectors_ref=refs['g2_selectors'],
    provider_g2_causal_state='EXACT2_SCOPE_CONDITIONS_VERIFIED_FUTURE_NAMES_RUNNER_PENDING_NO_EDIT_OR_EXECUTION_LEASE')
chain = cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation']
assert chain['actual_failed_invocations'] == 2 and chain['same_cause_failures'] == 1
chain.update(state='LIMITED_NATIVE_EVIDENCE_READONLY_VERIFIED_ORIGINAL_BOTH_HARNESS_FAILURES_PRESERVED',
    readonly_result_ref=refs['g1_result'], counter_reset=False, automatic_retry=False)
handler_chain_key = 'W05-99/handler38-independent-preparation'
assert handler_chain_key not in cp['failure_chains']
cp['failure_chains'][handler_chain_key] = {'actual_failed_invocations': 1, 'same_cause_failures': 1,
    'distinct_causes': {'NONEXISTENT_SPEC_V24_CONTRACTS_ARCHIVE_PATHSPEC': 1},
    'original_origin_key': 'W05-99/handler38-independent-preparation/public-source-archive-39b9d782',
    'native_exit': 128, 'outer_exit': 1, 'count_same_batch_once': True,
    'state': 'EXPLICIT_REVIEWED_RESOURCE_CORRECTION_SINGLE_NEW_PREPARATION_AUTHORIZED',
    'amendment_ref': refs['resource'], 'counter_reset': False, 'automatic_retry': False}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
handler = subtasks['host_configuration_public_handlers']
handler.update(state=work['configuration_handler_scope_state'], current_source_writer='FROZEN_NO_PRODUCT_WRITES',
    final_source_ready=False, public_compile_resource_amendment_ref=refs['resource'],
    public_compile_resource_review_ref=refs['resource_review'],
    nonauthor_executor='codex:/root/w05_merge_review',
    corrected_preparation='Existing isolated checkout, fifteen pathspecs and exact twelve compile-only public Go blobs; new immutable driver/raw namespace. Same A-E and six C09; first unexpected stops.')
subtasks['provider_whole9_g1_independent'].update(state=work['provider_whole9_g1_state'], source_ready=False,
    readonly_result_ref=refs['g1_result'], readonly_actual_invocation_ref=refs['g1_invocation'])
subtasks['f08_whole_scope_readonly_review'].update(state=work['f08_type_boundary_state'],
    whole20_34_nonauthor_review_ref=refs['f08_review'], type_revision_ref=refs['f08_type_revision'],
    SQL24_implementation_lease=False)
cp['next_command'] = 'W05-99: NONAUTHOR handler38 corrected preparation once (15 confirmed pathspecs+12 compile-only public Go files), then frozen A-E+6C09, first unexpected stops. Cmd independently review actual Root G1 readonly result. Source finish F08 TYPE/BOUND startup-caller scope review; no SQL24 lease. G2 finite helper/control/runner proposal and CLI precise fix scopes remain pending. Preserve all original failures and0/42 current formal; no product merge until actual independent evidence.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'HANDLER38_RESOURCE_CORRECTION_G1_LIMITED_ORIGINALS_AND_STATIC_DIAGNOSTICS_REGISTERED',
    'audit_ref': audit_ref, 'root_review_ref': prepared['root_review_ref'],
    'resource_amendment_ref': refs['resource'], 'nonauthor_resource_review_ref': refs['resource_review'],
    'G1_limited_result_ref': refs['g1_result'], 'G1_nonauthor_adjudication_review_pending': True,
    'failure_origins_before': 322, 'failure_origins_after': 330, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=302, expected_previous_revision=301, updated_at=now, updated_by='codex:/root')
ow.update(revision=130, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [301, 302], 'ownership': [129, 130], 'failures': [322, 330]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root302.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root302.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual = json.loads(CANON[0].read_bytes())
    actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [302, 130, 330]
    assert actual['failure_counters'][:322] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 302, 'ownership': 130, 'failure_origins': 330,
        'intent_ref': intent_ref, 'old322_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r302-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 302, 'failure_origins': 330,
    'counter_reset': False, 'audit_ref': audit_ref, 'previous_handoff_ref': refs['previous_handoff'],
    'current_card': 'W05-99', 'resource_scope_ref': refs['resource'], 'resource_review_ref': refs['resource_review'],
    'handler': 'Original archive128 preserved once. Reviewed correction15pathspecs+12publiccompilefiles authorizes single new preparation on existing checkout; A-E+6C09 remain NOT_RUN at registration.',
    'provider': 'G1 original3Go top/13named pass and26JS actual0 verified through readonly full48392 inputs/artifacts; originalouter1/taskkill128/chain2 retained. Nonauthor readonly review pending; no whole9 source acceptance. G2 conditions/11future selectors still proposal/no edit or execution lease.',
    'F08': 'Old20/34 review and TYPE/BOUND revision recorded. Current independent review found postadditive startup caller scope gap; awaiting final. SQL24 implementation lease false.',
    'CLI': 'Independent static original69IDs/26failures retained; P01-P03 product gaps and P04 category interpretation recorded. No source/harness execution lease.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
assert handoff_ref['sha256'] == hashlib.sha256((OUT / 'handoff-r302-running.json').read_bytes()).hexdigest()
print(json.dumps({'checkpoint': 302, 'ownership': 130, 'failure_origins': 330, 'handoff_ref': handoff_ref}, ensure_ascii=True))
