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
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
READS = {}

def read(path):
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    path = path.resolve()
    if path not in READS: READS[path] = path.read_bytes()
    return READS[path]

def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    data = read(path); sha = hashlib.sha256(data).hexdigest()
    assert expected is None or sha == expected
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(data)}

def save(name, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream: stream.write(data)
    return ref(OUT / name)

lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [299, 127, 316]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert len(status.splitlines()) == 13 and sum(r[:2] == b' D' for r in status.splitlines()) == 11
prep = ROOT / 'execution/v2.4/receipts/W05/W05-99/provider_whole9_g1_esm_repair_preparation_codex/788ce69c409b472799ee1389b778f9da'
manifest_ref = ref(prep / 'manifest.json', 'ae768f423855d50d4fee8e187648ad57b18ac40e2a5c7c1c6dbc07a88ad328ad')
manifest = json.loads(read(prep / 'manifest.json'))
assert len(manifest['files']) == 45
for row in manifest['files']:
    p = Path(row['path']); assert not p.is_absolute() and '..' not in p.parts
    actual = ref(prep / p, row['sha256']); assert 'bytes' not in row or actual['bytes'] == row['bytes']
plan_ref = ref(prep / 'plan.json', 'cb0120d9702f719ecead10bd11b1403af45869b07dc79d47ec0d286e40dc0f16')
runner_ref = ref(prep / 'run_g1.py', '6562febe8fd5fab1be63405c4511b4cf31faafbcf007a36b05b0d1c30792e42d')
probe_ref = ref(prep / 'esm_probe.mjs.txt', 'f42c16036ad4b38c8fc8161d71862383614d4f287925f969b0c32bdb4de0637b')
inputs_ref = ref(prep / 'inputs.json', 'fefdb05f3710703ebb8238ecd034cdcffe53f7a099cd75106622984dbcc9a137')
plan = json.loads(read(prep / 'plan.json')); layout = json.loads(read(prep / 'layout.json')); inputs = json.loads(read(prep / 'inputs.json'))['inputs']
assert len(inputs) == 27 and plan['candidate_commit'] == '6fb5263681c17f0e50920c354dc07ed440a23714'
assert plan['proposed_executor'] == 'codex:/root' and not layout['shared_sdk_write_permission']
assert not Path(layout['future_work_dir']).exists() and not Path(layout['future_receipt_dir']).exists()
assert Path(layout['future_work_dir']).parent == Path(layout['candidate']) / '.local'
assert layout['future_overlay'] == {'Replace': {}}
for row in inputs:
    actual = ref(row['source'], row['sha256']); assert actual['bytes'] == row['bytes']
assert any(Path(row['source']) == prep / 'esm_probe.mjs.txt' and row['sha256'] == probe_ref['sha256'] for row in inputs)
assert any(Path(row['source']) == prep / 'four-export-pins.json' for row in inputs)
for row in json.loads(read(prep / 'four-export-pins.json')):
    ref(row['package'], row['package_sha256']); actual = ref(row['expected_entry'], row['entry_sha256'])
    assert actual['bytes'] == row['entry_bytes'] and Path(row['expected_entry']).resolve().is_relative_to(Path(layout['sdk_shared']).resolve())
    assert str(Path(row['expected_entry']).resolve()) == row['expected_realpath']
chain = cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation']
assert chain['actual_failed_invocations'] == chain['same_cause_failures'] == 1 and not chain['counter_reset']
old_failures = json.loads(before[CANON[0]])['failure_counters']
assert len(old_failures) == 316
root_review_ref = save('root_esm_preparation_review.json', {
    'actor': 'codex:/root', 'source_author': 'codex:/root/command_queue_impl',
    'decision': 'PRECISE_ESM_PREPARATION_REVIEWED_FOR_ROOT_ATTEMPT2_NO_PRODUCT_ACCEPTANCE',
    'manifest_ref': manifest_ref, 'runner_ref': runner_ref, 'plan_ref': plan_ref, 'probe_ref': probe_ref,
    'inputs_ref': inputs_ref, 'verified_public_manifest_files': 45, 'actual_inputs_verified': 27,
    'reviewed_diff': 'Original alias block now uses actual ESM resolver parentURL; new probe/pins/runner/layout/resources protected in complete before/after vectors; all Go3/JS3/builder/source9/stop/timeout constraints preserved.',
    'official_Node_version': '24.9.0', 'docs': ['https://nodejs.org/download/release/v24.9.0/docs/api/esm.html#importmetaresolvespecifier', 'https://nodejs.org/download/release/v24.9.0/docs/api/cli.html#--experimental-import-meta-resolve'],
    'four_entry_sha_realpaths_verified': True, 'first_native_failure_preserved': chain,
    'Source9_or_shared_SDK_changes': 0, 'actual_tests_so_far_in_repaired_lane': 0, 'formal_increment': 0})
scope_ref = save('provider_g1_esm_execution_scope.json', {
    'actor': 'codex:/root', 'executor': 'codex:/root', 'source_author': 'codex:/root/command_queue_impl',
    'current_card': 'W05-99', 'Main_head': head, 'candidate': plan['candidate_commit'],
    'plan_ref': plan_ref, 'runner_ref': runner_ref, 'manifest_ref': manifest_ref, 'root_review_ref': root_review_ref,
    'layout': layout, 'exact_execution': plan['minimal_scope'], 'limits': plan['timeouts_seconds'],
    'single_attempt': True, 'attempt_ordinal_same_chain': 2, 'prior_failed_invocations': 1,
    'prior_failure_ref': chain['failure_ref'], 'counter_reset': False, 'automatic_retries': 0,
    'first_unexpected_stops_dependency_lane': True, 'fresh_candidate_bundle_required': True,
    'full_actual_compile_SDK_toolchain_and_preparation_closure_required': True,
    'held_positive_cases_unlocked': 0, 'old64_or12_repeated': 0, 'G2_native_preflight_or_quarantine': 0,
    'SQL_DB_Host_or_vault_calls': 0, 'external_paid_private_model_calls': 0,
    'Source9_shared_SDK_Main_product_source_writes': 0, 'whole9_source_acceptance': False,
    'Main23_final_handler38_composition_acceptance': False, 'formal_increment': 0,
    'pre_existing_counter_state': {'checkpoint': 299, 'failure_origins': 316}})
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(provider_whole9_g1_esm_execution_scope_ref=scope_ref,
    provider_whole9_g1_esm_preparation_review_ref=root_review_ref,
    next_action='Root actual bounded ESM G1 attempt2: fresh bundle, independent Go3 and SDK JS3 with full input closure. Author handler38 final CLI/source closure in progress; F08 v5 readonly proposal pending. No whole9/SQL24/formal acceptance.')
chain.update(state='SECOND_ESM_ATTEMPT_AUTHORIZED_AFTER_PRECISE_ROOT_CAUSAL_REVIEW', latest_execution_scope_ref=scope_ref, attempt_ordinal_authorized=2)
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'PROVIDER_G1_ESM_ATTEMPT2_PRECISE_SCOPE_REGISTERED',
    'scope_ref': scope_ref, 'prior_alias_native_failures_preserved': 1, 'automatic_retries': 0,
    'failure_origins_before': 316, 'failure_origins_after': 316, 'formal_increment': 0})
cp.update(revision=300, expected_previous_revision=299, updated_at=now, updated_by='codex:/root')
ow.update(revision=128, amended_at=now, amended_by='codex:/root')
ow['card_path_bindings']['W05-99']['subtasks']['provider_whole9_g1_independent'].update(
    state='BOUNDED_ESM_G1_ATTEMPT2_AUTHORIZED_NO_SOURCE_WRITES', scope_ref=scope_ref,
    first_attempt_scope_ref=ow['card_path_bindings']['W05-99']['subtasks']['provider_whole9_g1_independent']['scope_ref'],
    source_ready=False, current_attempt_ordinal=2)
for row in [manifest_ref, plan_ref, runner_ref, probe_ref, inputs_ref, root_review_ref, scope_ref]:
    if row['path'] not in cp['evidence_index']: cp['evidence_index'].append(row['path'])
assert cp['failure_counters'] == old_failures
for p, data in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as stream: stream.write(data)
with (OUT / 'git-status.original.raw').open('xb') as stream: stream.write(status)
desired = {p: (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8') for p, v in zip(CANON[:2], [cp, ow])}
for p, data in desired.items():
    with (OUT / (p.stem + '.desired.json')).open('xb') as stream: stream.write(data)
intent_ref = save('canonical-write.intent.json', {'actor': 'codex:/root', 'Main_head': head,
    'status_ref': ref(OUT / 'git-status.original.raw'), 'register_ref': ref(Path(__file__)),
    'toolchain_lock_ref': ref(ROOT / 'execution/toolchains/locked.json'),
    'transition': {'checkpoint': [299, 300], 'ownership': [127, 128], 'failures': [316, 316]},
    'metadata': [{'path': p.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (p.stem + '.original.json')),
        'desired_ref': ref(OUT / (p.stem + '.desired.json'))} for p in CANON[:2]],
    'unchanged': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[p]).hexdigest()} for p in CANON[2:]],
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(p.read_bytes() == data for p, data in before.items())
assert all(p.read_bytes() == data for p, data in READS.items())
for p, data in desired.items():
    with p.with_name(p.name + '.root300.tmp').open('xb') as stream: stream.write(data)
expected_live = dict(before); phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for p, data in desired.items():
        assert all(c.read_bytes() == expected_live[c] for c in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(p.with_name(p.name + '.root300.tmp'), p); expected_live[p] = data
        assert p.read_bytes() == data
        phase = p.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + p.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(data).hexdigest()})
    assert all(p.read_bytes() == data for p, data in expected_live.items())
    actual = json.loads(CANON[0].read_bytes()); actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [300, 128, 316]
    assert actual['failure_counters'] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 300, 'ownership': 128, 'failure_origins': 316,
        'intent_ref': intent_ref, 'old316_all_origins_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r300-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 300, 'failure_origins': 316,
    'counter_reset': False, 'G1_execution_scope_ref': scope_ref, 'G1_root_preparation_review_ref': root_review_ref,
    'previous_handoff_ref': ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/handler-numeric-original-failures-r299/handoff-r299-running.json', '354d9aa56fdc4e9da28538948064058a019fd5e6c01a1ac8b0f225cf8ae0fea5'),
    'current_card': 'W05-99', 'handler': 'Final38 CLI/current freeze and NONAUTHOR whole review still required; newest author CLI failure imports pending sealed supplement.',
    'provider': 'Root NONAUTHOR single ESM attempt2 now authorized after preserving first alias failure. G1 not started by registration; no source or whole9 qualification.',
    'F08': 'Readonly v5 correcting legal refs multiset and subsequent Run epoch; proposed two extra source categories still require precise proposal/review. No SQL24 source lease.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 300, 'ownership': 128, 'failure_origins': 316, 'scope_ref': scope_ref, 'handoff_ref': handoff_ref}, ensure_ascii=True))
