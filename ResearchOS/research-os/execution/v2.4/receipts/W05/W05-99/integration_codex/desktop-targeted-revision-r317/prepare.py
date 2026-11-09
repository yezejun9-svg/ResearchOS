import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'session-list-closedcopy-harness-v4-r316'
PROPOSAL = OUT.parent / 'desktop-exact15-nonauthor-scope-r317'
CANON = [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
WT = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311'
AUTHOR = WT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd'
FINAL = AUTHOR / 'final-audit-c0fea60e04e34fbd803b5d2feae78df8'
REVIEW = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_source_independent_review_codex/094badb378bf4323a24a5d8bb2c09ab1'
CMD_WT = ROOT / '.local/worktrees/codex-w0599-session-list-proof-r312'
CMD_FINAL = CMD_WT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex/postcommit-v4/final_handoff.json'
READS = {}


def read(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def pin(path, expected=None):
    path = Path(path).resolve()
    raw = read(path)
    result = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected, str(path)
    return result


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(OUT / name)


def script(name, source):
    ast.parse(source)
    with (OUT / name).open('xb') as stream:
        stream.write(source.encode('utf-8'))
    return pin(OUT / name)


def once(source, old, new):
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new, 1)


assert sys.flags.isolated and not sys.flags.optimize and len(sys.argv) == 1
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [316, 144, 406]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
git = lock['git']['path']
for key in ['python', 'git']:
    assert hashlib.sha256(Path(lock[key]['path']).read_bytes()).hexdigest() == lock[key]['sha256']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=WT).decode().strip() == '0f708eaf0c624fb721f7c9a00d5465ef5f13a68c'
assert subprocess.check_output([git, 'status', '--porcelain=v1'], cwd=WT) == b''
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=CMD_WT).decode().strip() == 'fa73a24f4dd5a9d3246650551aa54b98043fb8fd'
assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=CMD_WT) == b''
pins = {}
for key, path, sha in [
    ('previous_handoff', PREVIOUS / 'handoff-r316-running.json', 'eaa29ad62e14ecb7c0a6875d3ba823ffbf1393be80cb3d6c89b2b7316f0602d5'),
    ('previous_manifest', PREVIOUS / 'manifest.json', '87fdf47e01bd935c90571f17ef007ec95138d6403d7b13dc3b1ad36356b18385'),
    ('original_scope', OUT.parent / 'desktop-http-exact15-lease-r311/scope_registration.json', '3595c57c257c097718d5d1debecf219f2707fea9294812c81d7cbfc6a6864a84'),
    ('author_handoff', FINAL / 'handoff.json', 'c4bea94e1eec3c9f4a9393e9433d8501a9c51e81b899c51245a8027166a51f60'),
    ('author_manifest', FINAL / 'manifest.json', '835f1ecdb3cf792ca2f058fdc3d0fec052d772f8ecfa75cd5ca2a99b5ca79ab7'),
    ('source_review', REVIEW / 'source_review.json', '70acbd8f1d98815824e5f3ee0cdac418fb8a89a13c356d632414f193c5fcf927'),
    ('source_review_manifest', REVIEW / 'manifest.json', '1060a56dff1d472fd0ee3f03d2fa4abbde2d93368eb27f3fc503deceff32a6a5'),
    ('source_review_handoff', REVIEW / 'handoff.json', '2dadf97121b267918949f0f4315b351e23d68f215d66a1b19c30d94529cdf235'),
    ('supplemental_counterexamples', REVIEW / 'proposed-counterexamples.NOT_RUN.json', 'd2edb4e53737038dd83e95da84ca36b727a5e66739eb23e87b8491ab3c8230a5'),
    ('old_root_replay_proposal_HOLD', PROPOSAL / 'desktop_finite_replay.scope.draft.json', '49f66101c003f4127c1b763b8ce1328022eeccc333b40738832126fdaf405f96'),
    ('cmd_final_handoff', CMD_FINAL, '3d9d409ba5888dca94c22c380b22da1bb6b1a9d1ba0a145a33ecab5ea723ec7b'),
    ('composition_handoff', ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_composition_readonly_codex/b3387a4cb00d42cb92394d175eddfc1a/handoff.json', '8b02c0e6dae6d6cce633693a377a114483ce0820f4ff2029fc216bfb2b5fef68')]:
    pins[key] = pin(path, sha)
original = json.loads(read(ROOT / pins['original_scope']['path']))
for key in ['path_bounds_ref', 'source_roster_ref', 'implementation_conditions_ref', 'protected_spans_ref', 'preflight_supplement_ref']:
    item = original[key]
    pins[key] = pin(ROOT / item['path'], item['sha256'])
    assert pins[key]['bytes'] == item['bytes']
handoff = json.loads(read(FINAL / 'handoff.json'))
source_audit_item = handoff['source_scope_audit_ref']
pins['author_source_audit'] = pin(WT / source_audit_item['path'], source_audit_item['sha256'])
source_audit = json.loads(read(ROOT / pins['author_source_audit']['path']))
assert source_audit['outside_bounds'] == [] and len(source_audit['rows']) == 15
source_pins = {row['path']: pin(WT / row['path'], row['sha256']) for row in source_audit['rows']}
assert set(source_pins) == set(original['exact_paths'])
review = json.loads(read(REVIEW / 'source_review.json'))
assert review['decision'] == 'REQUEST_CHANGES'
controls = json.loads(read(REVIEW / 'proposed-counterexamples.NOT_RUN.json'))
composition = json.loads(read(ROOT / pins['composition_handoff']['path']))
assert [composition['handler_list_unique'], composition['handler_list_cli_unique'], composition['all_candidate_unique']] == [38, 43, 58]
for index, item in enumerate(composition['key_refs']):
    pins['composition_' + str(index)] = pin(ROOT / item['path'], item['sha256'])
cmd = json.loads(read(CMD_FINAL))
assert cmd['source_commit'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert cmd['receipt_commit'] == 'fa73a24f4dd5a9d3246650551aa54b98043fb8fd'
assert cmd['actual_leaf_pass'] == 14 and cmd['actual_skip'] == 0
assert cmd['actual_driver_exit'] == cmd['actual_outer_exit'] == 0 and cmd['HTTP_total'] == 78
assert cmd['source_acceptance'] is False and cmd['new_v4_failure_origins'] == 0
for key in ['execution_summary', 'public_manifest', 'original_execution_handoff', 'git_blob_audit', 'postcommit_manifest']:
    item = cmd[key]
    pins['cmd_' + key] = pin(CMD_WT / item['path'], item['sha256'])
    assert pins['cmd_' + key]['bytes'] == item['bytes']
origins = []
source_origin_ref = pin(AUTHOR / 'failure-origin-tool-f02bcf.json', 'c157908f48ed70b2296ed71328a5b0fa2e5cf32c09be1d160bc0b848fc04b6ac')
source_origin = json.loads(read(ROOT / source_origin_ref['path']))
assert source_origin['actual_outer_exit'] == 1 and source_origin['native_product_test_failure'] is False
origins.append({'origin_key': 'r317-source-desktop-receipt-sealer-f02bcf', 'actor': 'codex:/root/sources_parent_impl',
    'event_kind': 'ACTUAL_NONZERO_EXECUTION', 'actual_outer_exit': 1, 'actual_native_exit': None,
    'native_kind': 'RECEIPT_ONLY_PYTHON_SEALER', 'product_cases_run': 0, 'native_product_test_failure': False,
    'cause': source_origin['cause'], 'evidence_ref': source_origin_ref, 'original_payload': source_origin,
    'original_tool_ref': 'f02bcf', 'raw_file': None, 'null_native_exit_not_inferred_as_product_failure': True})
for name in ['failure_origin.lookup-2ab98e.json', 'failure_origin.lookup-7158ee.json', 'failure_origin.lookup-dfd177.json']:
    evidence = pin(PROPOSAL / name)
    raw = json.loads(read(ROOT / evidence['path']))
    assert raw['actual_outer_exit'] == 1 and raw['actual_native_exit'] is None and raw['product_cases_run'] == 0
    origins.append({**raw, 'evidence_ref': evidence, 'original_payload': raw})
assert len(origins) == len({row['origin_key'] for row in origins}) == 4
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 406, 'after': 410, 'origins': origins,
    'new_actual_nonzero_tool_origins': 4, 'new_product_test_failure_assertions': 0,
    'new_static_review_findings_counted_as_native_failures': 0, 'count_once': True, 'counter_reset': False})
targeted_paths = ['apps/desktop/main/lib/ipc.js', 'apps/desktop/validator/main.go',
    'apps/desktop/validator/main_test.go', 'apps/desktop/main/lib/http-wire.js',
    'tests/ui/desktop/http-wire-boundary.test.mjs', 'apps/desktop/build-validator.py']
pins['scope'] = save('scope_registration.json', {
    'schema': 'researchos.desktop-exact15-targeted-source-revision-scope.v1',
    'state': 'AUTHORIZED_AFTER_ACTUAL_CAS317_AND_REGISTRATION_SEAL_ONLY_NOT_STARTED',
    'registration_checkpoint': 317, 'owner': 'codex:/root/sources_parent_impl', 'root_integrator': 'codex:/root',
    'worktree': str(WT), 'branch': original['branch'], 'source_only_base': '840bc6cc3237ba4dddd3812d2bec157666dc50ee',
    'evidence_head_before_revision': '0f708eaf0c624fb721f7c9a00d5465ef5f13a68c',
    'original_exact15_lease_ref': pins['original_scope'], 'original_path_bounds_ref': pins['path_bounds_ref'],
    'original_implementation_conditions_ref': pins['implementation_conditions_ref'],
    'protected_17_spans_ref': pins['protected_spans_ref'], 'protected_spans_byte_unchanged_required': True,
    'all_original15_source_before': source_pins, 'revision_allowed_paths': targeted_paths,
    'optional_builder_change': 'Only one synthetic child fault mode for otherwise valid private verdict prefixed with raw UTF-8 NBSP; normal production builder guards unchanged.',
    'ipc_bounds': 'Original callV2 function59-110 (current59-119) and its owned internal state only; protected imports1-8/11-58 and legacy11/exports remain byte exact. A function-local WeakMap or same owned function state may hold the lifecycle independently of presentation tickets.',
    'mandatory_revision_findings_ref': pins['source_review'], 'mandatory_supplemental_control_ref': pins['supplemental_counterexamples'],
    'mandatory_fixes': [
        'Reserve each original command lifecycle before async exposure. Concurrent GET/read ticket cannot erase a validated original ACK/Pending barrier. Adoption must consult current outstanding command state. Only validated terminal response for exact original request/command identity releases barrier. Preserve context generation/tuple and original replay identity.',
        'Before Go struct projection, reject duplicate/missing/extra/case-aliased keys and nonstring/null schema,phase,nonce,request_raw_base64,response_raw_base64. REQUEST http_status must be null and response_raw_base64 exactly empty string; RESPONSE http_status integral100..599. Preserve all existing raw UTF8/base64/depth/phase/hash limits.',
        'Private JSON whitespace scanner accepts only SP,HT,LF,CR. Reject NBSP/BOM/VT/FF without trimming/normalization and before any POST; retain exact child stdout and full lifecycle proof.'
    ],
    'tests': {'original_roster_ref': pins['source_roster_ref'], 'original_finite_leaves': 159, 'original_regression_units': 7,
        'three_new_supplemental_controls': controls, 'supplemental_HTTP_maximum': 4, 'supplemental_pure_child_maximum': 11,
        'Go_unit_execution': 'Two original main_test.go functions previously compiled only may now execute once, plus explicit exact-key/type table and JSON boundary units in that same pure helper test file; no Host/DB/model. Freeze named unit selectors before launch and report actual exits distinctly.',
        'revised_author_finite_phase_HTTP_maximum': 390, 'original_phase_actual_HTTP_preserved': 302,
        'old_phase_plus_new_phase_HTTP_upper_bound': 692, 'old_failure_counters_not_reset': True,
        'new_phase': 'Fresh revised-source build, unique output/cache/WORK/exe/descriptor/React assets and one frozen revised cohort. Original159+7 and3 new controls all must have actual current receipts; do not union old840 PASS. No unchanged-input retry.',
        'stage_specific_noPOST_required': True, 'per_leaf_caps_are_maxima': True},
    'build_rule': original['authorized_build_outputs'], 'input_closure': 'Preserve original full compiled variants, generated WORK/archive/descriptor/module/offscreen/assets vectors. New code and binaries must enter actual current frozen cohort; check full vector before/after finite batches and critical per-child inputs.',
    'process_rule': original['process_rule'], 'SDK_MODEL_external_paid_private_calls': 0,
    'first_unexpected_stop': True, 'automatic_same_input_retry': False, 'counter_reset': False,
    'maximum_active_construction_tasks': 2, 'Main_product_source_writes': 0,
    'execution_grant': 'Root exact follow-up only after non-author registration draft review, actual CAS317 and sealed registration. Stop after separate source-only delta commit and receipt-only commit for non-author review.',
    'root_full159_replay_on_old840': 'HOLD_NOT_GRANTED', 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0, 'remaining_gates': original['remaining_gates']})
old = read(PREVIOUS / 'register.py').decode('utf-8', errors='strict')
header = once(old[:old.index("pins = prepared['pins']")], '[315, 143, 393]', '[316, 144, 406]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 317 and scope['root_full159_replay_on_old840'] == 'HOLD_NOT_GRANTED'
desktop_worktree = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311'
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=desktop_worktree).decode().strip() == scope['evidence_head_before_revision']
assert subprocess.check_output([git, 'status', '--porcelain=v1'], cwd=desktop_worktree) == b''
for item in scope['all_original15_source_before'].values():
    assert ref(item['path'], item['sha256']) == item
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 4
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys and row['event_kind'] == 'ACTUAL_NONZERO_EXECUTION'
    assert row['actual_outer_exit'] == 1 and row['actual_native_exit'] is None
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:406] == old_failures and len(cp['failure_counters']) == 410
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(desktop_http_exact15_source_review_ref=pins['source_review'],
    desktop_http_exact15_source_review_state='REQUEST_CHANGES_TWO_FINDINGS_THREE_SUPPLEMENTAL_CONTROLS_NOT_RUN',
    desktop_http_exact15_targeted_revision_scope_ref=pins['scope'],
    desktop_http_exact15_root_replay_on_old840_state='HOLD_NOT_GRANTED',
    desktop_http_exact15_receipt_sealer_failure_registered=True,
    session_list_closedcopy_exact1_final_handoff_ref=pins['cmd_final_handoff'],
    session_list_closedcopy_exact1_state='AUTHOR_EXECUTION_REPORTED_SOURCE_AND_EVIDENCE_COMMITTED_14PASS_78HTTP_NONAUTHOR_REVIEW_PENDING',
    integration_composition_handoff_ref=pins['composition_handoff'],
    integration_composition_unique_paths={'handler_list_helper': 38, 'plus_cli': 43, 'plus_desktop_after_acceptance': 58})
desktop = ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']
assert desktop['current_source_writer'] == 'codex:/root/sources_parent_impl'
desktop.update(targeted_revision_scope_ref=pins['scope'], source_review_ref=pins['source_review'],
    state='SOURCE_TARGETED_REVISION_AUTHORIZED_AFTER_SEAL', source_ready=False, source_acceptance=False)
cmd_subtask = ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']
assert cmd_subtask['current_source_writer'] == 'codex:/root/command_queue_impl'
cmd_subtask.update(current_source_writer=None, last_source_writer='codex:/root/command_queue_impl',
    state='WRITER_STOPPED_AUTHOR14_REPORTED_NONAUTHOR_REVIEW_PENDING', final_handoff_ref=pins['cmd_final_handoff'],
    source_only_commit='a5d6d16ffaf129de0361470c3a1570228bd259a2',
    receipt_only_commit='fa73a24f4dd5a9d3246650551aa54b98043fb8fd', source_ready=False, source_acceptance=False)
cp['failure_chains']['W13-03/r317-targeted-source-review-and-receipt-tool-origins'] = {
    'new_actual_nonzero_tool_origins': 4, 'new_static_review_findings_counted_as_native_failures': 0,
    'original406_prefix_unchanged': True, 'counter_reset': False, 'audit_ref': pins['audit'],
    'failure_cut_ref': pins['failure_cut'], 'automatic_same_input_retry': False}
cp['next_command'] = 'Source completes independent Cmd14 closure review, then revised Desktop ACK/strict packet fixes plus original159+7 and3 supplemental controls under new bounded revised-source cohort after actual317+seal. Root14 new runner awaits static review and separate actual grant; old840 full Desktop replay HOLD. Root G2 finite29 continues under immutable313 snapshot with reviewed v3 post-execution sealer. Shared Main source/composed38-43-58/all22/all42 remain HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'DESKTOP_TWO_FINDINGS_TARGETED_REVISION_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'source_review_ref': pins['source_review'], 'audit_ref': pins['audit'],
    'failure_origins_before': 406, 'failure_origins_after': 410, 'new_actual_nonzero_tool_origins': 4,
    'static_findings_are_NOT_RUN_not_native_failure': True, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=317, expected_previous_revision=316, updated_at=now, updated_by='codex:/root')
ow.update(revision=145, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r316-running.json'")]
for a, b in [('[315, 316]', '[316, 317]'), ('[143, 144]', '[144, 145]'), ('[393, 406]', '[406, 410]'),
    ('[316, 144, 406]', '[317, 145, 410]'), ('[:393]', '[:406]'),
    ("'checkpoint': 316", "'checkpoint': 317"), ("'ownership': 144", "'ownership': 145"),
    ("'failure_origins': 406", "'failure_origins': 410"), ('old393_prefix_unchanged', 'old406_prefix_unchanged'),
    ('new_targeted_harness_v4_execution_only', 'new_targeted_Desktop_revision_only')]:
    tail = once(tail, a, b)
assert tail.count('root316.tmp') == 2
tail = tail.replace('root316.tmp', 'root317.tmp')
handoff_source = '''handoff_ref = save('handoff-r317-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 317, 'failure_origins': 410, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'desktop_targeted_revision_scope_ref': pins['scope'], 'desktop_source_review_ref': pins['source_review'],
    'cmd_author14_final_handoff_ref': pins['cmd_final_handoff'],
    'next': 'Source targeted Desktop revision after exact grant; Cmd14 non-author review and Root independent14 scope preparation; immutable313 G2 continues. No Main composition or current formal acceptance.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 317, 'ownership': 145, 'failure_origins': 410, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff_source)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8', errors='strict')
wrapper = once(wrapper, 'root_registration_r316_readonly_review_codex', 'root_registration_r317_readonly_review_codex')
wrapper = once(wrapper, 'review[\'expected_before\'] == [315, 143, 393] and review[\'expected_after\'] == [316, 144, 406]',
    'review[\'expected_before\'] == [316, 144, 406] and review[\'expected_after\'] == [317, 145, 410]')
wrapper = once(wrapper, "cp['revision'] == 315 and len(cp['failure_counters']) == 393", "cp['revision'] == 316 and len(cp['failure_counters']) == 406")
wrapped = script('run.py', wrapper)
sealer = read(PREVIOUS / 'seal.py').decode('utf-8', errors='strict')
sealer = once(sealer, "PREVIOUS = OUT.parent / 'session-list-closedcopy-harness-v3-r315'", "PREVIOUS = OUT.parent / 'session-list-closedcopy-harness-v4-r316'")
sealer = once(sealer, "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [315, 143, 393]", "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [316, 144, 406]")
sealer = once(sealer, "assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [316, 144, 406]", "assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [317, 145, 410]")
sealer = once(sealer, '[:393]', '[:406]')
sealer = once(sealer, "'before': [315, 143, 393], 'after': [316, 144, 406]", "'before': [316, 144, 406], 'after': [317, 145, 410]")
sealer = once(sealer, 'old393_failure_prefix_unchanged', 'old406_failure_prefix_unchanged')
sealer = once(sealer, "'harness_review_ref': prepared['pins']['harness_review']", "'source_review_ref': prepared['pins']['source_review']")
sealer = once(sealer, "'new_v4_execution': 'NOT_STARTED_AT_REGISTRATION_SEAL'", "'new_targeted_Desktop_revision': 'NOT_STARTED_AT_REGISTRATION_SEAL'")
sealer = once(sealer, "'current': [316, 144, 406]", "'current': [317, 145, 410]")
seal = script('seal.py', sealer)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [316, 144, 406], 'expected_after': [317, 145, 410],
    'scope_ref': pins['scope'], 'source_review_ref': pins['source_review'], 'new_origins': origins,
    'old406_prefix_unchanged': True, 'new_actual_nonzero_tool_origins': 4, 'new_product_failure_assertions': 0,
    'static_findings_with_null_actual_counts_not_native_failures': True, 'new_supplemental_control_ref': pins['supplemental_counterexamples'],
    'root_old840_full_replay_HOLD': True, 'root_session_list14_draft_not_granted': True,
    'cmd_source_and_receipts_reported_not_accepted': True, 'handler_list_helper_unique38_plusCLI43_plusDesktop58': True,
    'original302_HTTP_preserved_new_revised_source_phase_cap390': True, 'counter_reset': False,
    'maximum_active_construction_tasks': 2, 'Cmd_writer_stopped_Source_only_targeted_writer': True,
    'Main_source_integration': False, 'formal_increment': 0, 'execution_after_CAS_and_seal_only': True})
prepared = save('prepared_refs.json', {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'TARGETED_DESKTOP_REVISION_DRAFT_NOT_EXECUTED', 'register': register,
    'wrapper': wrapped, 'prepared': prepared, 'audit': pins['audit'], 'scope': pins['scope'], 'seal': seal}, ensure_ascii=True))
