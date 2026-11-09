import copy
import datetime
import hashlib
import json
import os
import pathlib
import subprocess

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).resolve().parent
CANON = ROOT / 'execution/v2.4'
paths = [CANON / 'checkpoint.json', CANON / 'path_ownership.json', CANON / 'HANDOFF_RESUME_PACK.md']
original = {p: p.read_bytes() for p in paths}
cp = json.loads(original[paths[0]].decode('utf-8-sig'))
ownership = json.loads(original[paths[1]].decode('utf-8-sig'))
assert cp['revision'] == 425 and ownership['revision'] == 213
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == '243d3e4d59b002e7d049c19d4ea4a1761c974404'
state = (CANON / 'step_state.json').read_bytes()
old_failures = copy.deepcopy(cp['failure_counters'])
old_no_progress = cp['no_progress_rounds']
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

def write_new(path, value):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def receipt(name):
    return ROOT / 'execution/v2.4/receipts/W05/W05-99' / name / '20261012-current-chat'

diagnosis = ref(receipt('normal_desktop_first_use_diagnosis_codex') / 'manifest-02.json')
assert diagnosis['sha256'] == '38fac3909ae83fc10952ea637911b85f950b5f0c278943fa25feae9cfdef820b'
integration = ref(receipt('product_parent_image_observation_repair_integration_codex') / 'integration.json')
assert integration['sha256'] == 'a0009effad23648bd8338fb106a5d755d4881a3c9535f40c8d006ae089b03adf'
scope = {
    'schema': 'researchos.exact-causal-source-scope.v1', 'at': now,
    'step_id': 'W05-99', 'owner': 'codex:/root/w05_main24',
    'worktree': '.local/worktrees/w05-normal-first-use-contract-repair-20261012',
    'base_commit': head,
    'paths': ['apps/desktop/validator/main.go', 'apps/desktop/validator/main_test.go',
              'apps/desktop/main/lib/first-use.js', 'tests/ui/desktop/w13-react.test.js',
              'internal/host/native_first_use_windows_test.go'],
    'independent_scope_assessment_ref': diagnosis,
    'repairs': ['Accept schema-valid host.status revision=1 while preserving session/client/command identity and schema checks.',
                'Supply required requested_path:null to original Native chooser and correct invalid undefined expectation.'],
    'limits': ['Only these five source paths in new isolated worktree.', 'No frozen schema/Core response changes.',
               'No Root CLI issue patch, secret/token reads, model or tool completion calls.',
               'No GUI/probe/Owner synthesis. Preserve failed build and original native data.',
               'Build fresh source-bound validator/descriptor, freeze candidate and independently review before Main integration.'],
    'formal_increment': 0, 'parent_acceptance': False,
}
write_new(OUT / 'first-use-contract-scope.json', scope)
scope_ref = ref(OUT / 'first-use-contract-scope.json')
baseline = json.loads((receipt('current_chat_integration_preflight_codex') / 'preflight-v2.json').read_text(encoding='utf-8-sig'))
checked = []
for entry in baseline['protected_source']:
    actual = ref(ROOT / entry['path'])
    assert actual['sha256'] == entry['sha256'], entry['path']
    checked.append(actual)
write_new(OUT / 'protected-source.json', {'at': now, 'files': checked, 'drift': 0})
ownership['expected_previous_revision'] = 213
ownership['revision'] = 214
ownership['updated_at'] = now
ownership['updated_by'] = 'codex:/root'
ownership['path_lease_transfers'].append({
    'at': now, 'actor': 'codex:/root', 'new_owner': scope['owner'],
    'new_subtask': 'W05-99/normal_first_use_contract_repair', 'new_worktree': scope['worktree'],
    'paths': scope['paths'], 'scope_ref': scope_ref,
    'kind': 'EXACT_ACTUAL_SCHEMA_CALLER_REPAIR_PRESERVE_FROZEN_CONTRACTS',
})
cp.update(revision=426, expected_previous_revision=425, head=head, updated_at=now, updated_by='codex:/root')
cp['work_in_progress'].update(current_main_source_head=head,
    parent_image_repair_status='INDEPENDENT_ACCEPTED_COMPONENT_AND_MAIN_INTEGRATED',
    parent_image_repair_integration_ref=integration, first_use_contract_scope_ref=scope_ref,
    native_first_use_actual_state='REAL_READY_NATIVE_OWNER_INITIALIZED_ZERO_MODEL_TWO_CALLER_SCHEMA_FAILURES',
    coding_client_status='FROZEN_EB7F_INDEPENDENT_FOUR_BOUND_COUNTEREXAMPLES_PENDING_FINAL_REQUEST_CHANGES')
cp['current_effective_formal_status'].update(current_head=head, needs_rederive_after_source_change=True)
for item in cp['side_effects_pending']:
    if item.get('kind') == 'OWNED_NORMAL_DESKTOP_FIRST_USE_ZERO_MODEL_HOST' and item.get('desktop_pid') == 53188:
        item.update(state='NORMAL_WINDOW_CLOSE_EXITED_PID_RECHECKED', exited=True,
                    closure_ref=ref(receipt('normal_desktop_first_use_actual_codex') / 'normal-window-close.intent.json'))
cp['side_effects_pending'].append({
    'kind': 'OWNED_NORMAL_DESKTOP_FIRST_USE_CAUSAL_RETRY01_ZERO_MODEL_HOST',
    'desktop_pid': 57044, 'control_pid': 55208, 'cdp': 'http://127.0.0.1:13709',
    'core_source': '040d297627e2cfc5de2d6b9e770acc7bdf4f9ab7',
    'data_root': str(ROOT / '.local/live/current-chat-normal-desktop-first-use-20261012/data'),
    'launch_ref': ref(receipt('normal_desktop_first_use_causal_retry01_codex') / 'launch.json'),
    'model_calls_authorized': 0, 'qualification_confirm_authorized': False,
    'next_action': 'Normal private safe exit before fresh bound repaired distribution; reuse original data without reset.',
})
for key, status, proof in [
    ('normal-first-use-host-status-identity', 'ACTUAL_SCHEMA_VALID_REVISION1_REJECTED_BY_EXTRA_VALIDATOR_RULE', diagnosis),
    ('normal-first-use-native-chooser', 'ACTUAL_CLICK_MISSING_REQUIRED_REQUESTED_PATH_REJECTED_BEFORE_OS_CHOOSER', diagnosis),
    ('normal-first-use-db-guessed-table', 'READ_ONLY_DIAGNOSTIC_NO_SUCH_TABLE_CLIENT_COMMAND_RECEIPTS_SQL_CORRECTED_WITH_NEW_EVIDENCE', diagnosis),
    ('normal-first-use-browser-screenshot-timeout', 'READ_HELPER_SCREENSHOT_TIMEOUT_ORIGINAL_CAPTURE_NOT_CREATED_HELPER_ONLY_INTERRUPTED', ref(receipt('normal_desktop_first_use_causal_retry01_codex') / 'after-chooser-click.observed.json')),
]:
    origin = 'current-chat-20261012|' + key
    assert not any(x.get('origin_key') == origin for x in cp['failure_counters'])
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': status,
                                   'counter_reset': False, 'evidence_ref': proof, 'actual_models': 0})
cp['next_command'] = 'Repair exact first-use5 caller/validator paths, fresh bound build and independent review; preserve frozen coding client EB7F and finish four-counterexample causal repair in separate scope. Continue real Native first-use with original data before explicit one-model qualification/coding newref. Formal0/42 and all22 remain open.'
resume = {
    'schema': 'researchos.current-chat-resume.v22', 'at': now, 'checkpoint_revision': 426,
    'ownership_revision': 214, 'head': head, 'project_id': cp['project_id'], 'current_step_id': 'W05-99',
    'accepted_formal_cases': 0, 'required_formal_cases': 42, 'required_parent_tasks': 22,
    'failure_records_preserved': len(cp['failure_counters']), 'goal_status': 'ACTIVE',
    'first_use_scope_ref': scope_ref, 'diagnosis_ref': diagnosis, 'parent_integration_ref': integration,
    'failed_first_window_normally_closed': True, 'current_desktop_pid': 57044, 'current_control_pid': 55208,
    'real_models_this_preparation': 0, 'native_owner_initialized': True,
    'phone_user_answer': 'USE_REAL_PHONE_WHEN_PRODUCT_PAIRING_READY', 'phone_ready': False,
    'next_command': cp['next_command'],
}
write_new(OUT / 'RESUME.current.json', resume)
cp['artifacts'].extend([integration, diagnosis, scope_ref, ref(OUT / 'RESUME.current.json')])
cp['work_in_progress']['current_chat_resume_ref'] = ref(OUT / 'RESUME.current.json')
assert cp['failure_counters'][:len(old_failures)] == old_failures
assert cp['no_progress_rounds'] == old_no_progress
for p, name in zip(paths, ['checkpoint.before.raw.json', 'ownership.before.raw.json', 'HANDOFF.before.raw.md']):
    assert not (OUT / name).exists()
    (OUT / name).write_bytes(original[p])
assert (CANON / 'step_state.json').read_bytes() == state
for p in paths:
    assert p.read_bytes() == original[p], str(p)
handoff = ('# Current verified continuation CP426\n\nRead `' + ref(OUT / 'RESUME.current.json')['path'] + '` first. '
           'Main243 parent observation integrated; actual Desktop57044/control55208 READY with Native Owner and zero models. '
           'Two exact schema caller defects are scoped for Source repair; coding client remains rejected candidate pending final review. '
           'Formal acceptance 0/42, all22 parent obligations open, failures preserved. Phone uses user device when product pairing ready.\n\n').encode('utf-8') + original[paths[2]]
for p, raw in [(paths[0], (json.dumps(cp, ensure_ascii=False, indent=2)+'\n').encode()),
               (paths[1], (json.dumps(ownership, ensure_ascii=False, indent=2)+'\n').encode()), (paths[2], handoff)]:
    temp = p.with_name(p.name + '.cp426.tmp')
    assert not temp.exists()
    temp.write_bytes(raw)
    os.replace(temp, p)
assert (CANON / 'step_state.json').read_bytes() == state
print(json.dumps({'checkpoint': 426, 'ownership': 214, 'source_scope': scope_ref,
                  'resume': ref(OUT / 'RESUME.current.json'), 'old_failures_preserved': len(old_failures),
                  'new_failure_records': 4, 'formal_increment': 0}, ensure_ascii=False))
