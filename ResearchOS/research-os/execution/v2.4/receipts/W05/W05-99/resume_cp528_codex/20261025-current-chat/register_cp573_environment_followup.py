"""Adopt actual bounded A/B evidence and prepare one finite discriminating follow-up."""
import datetime
import json
import os
from pathlib import Path
from preserve_main_baseline import R, N, read, ref
from preserve_desktop_main_ecc28 import verify


def new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    paths = [R/'execution/v2.4/checkpoint.json', R/'execution/v2.4/path_ownership.json',
             R/'execution/v2.4/HANDOFF_RESUME_PACK.md', R/'execution/v2.4/step_state.json']
    old = {path: path.read_bytes() for path in paths}
    cp, ow = read(paths[0]), read(paths[1])
    assert cp['revision'] == 572 and ow['revision'] == 357
    assert len(cp['failure_counters']) == 2299
    preserved = verify()
    base = R/'execution/v2.4/receipts/W05/W05-99'
    env = base/'product_host_native_20261028/native-init-diagnosis-02/environment-probe'
    actual = env/'execution-cp572-AB01'
    review = base/'product_host_independent_20261028/environment-probe-actual-cp572-review/REVIEW.json'
    analysis = env.parent/'static-cause-analysis02/REPORT.md'
    assert ref(review)['sha256'] == '83fdadc071e901a16ef6b6c394d17a83fa579fd714ccdad4cd52ecbd6153761e'
    assert read(review)['status'] == 'FINITE_AB_DIAGNOSTIC_ACCEPTED_SYSTEMDRIVE_ALONE_DID_NOT_RESCUE'
    assert ref(analysis)['sha256'] == '1660530a15acf03467d126a4d44354e320ad12bb3526521489d9755573daf757'
    assert read(actual/'CONTROLLER-TERMINAL.json')['outer_exit_code'] == 0
    for case in ('A', 'B'):
        assert read(actual/case/'exit.json')['exit_code'] == 0
        assert read(actual/case/'cancel.json')['post_idcancel'] is False
    prior_scope = read(N/'continuation-cp572/Native-folder-finite-AB-scope.json')
    out = N/'continuation-cp573'
    out.mkdir()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    adoption = {
        'at': now, 'state': 'ACTUAL_FINITE_AB_DIAGNOSTIC_ACCEPTED_SELECTION_NOT_PROVEN',
        'review_ref': ref(review), 'analysis_ref': ref(analysis),
        'actual_refs': [ref(p) for p in sorted(actual.rglob('*')) if p.is_file()],
        'controller_tool_chunk': '908d30', 'controller_exit': 0,
        'formal_increment': 0,
        'conclusions': [
            'SystemDrive alone did not rescue: A113.3683ms and B96.2467ms Shell-null without IDCANCEL.',
            'A owned invisible dialog observed; B no samples does not prove no dialog.',
            'Retained helper handles ended. Numeric PID61164 later reused by svchost; never target it.',
            'No product selection, native lifecycle or installer acceptance follows from this diagnostic.'
        ]
    }
    new(out/'Native-AB-actual-adoption.json', adoption)
    new(out/'preservation.json', preserved)
    scope = {
        'schema': 'researchos.native-folder-followup-preparation.v1', 'at': now,
        'owner': 'codex:/root/product_host_resume_20261028',
        'reviewer': 'codex:/root/product_host_independent_20261028',
        'worktree': str(R/'.local/worktrees/desktop-installed-delivery-20261025'),
        'candidate_commit': '5c4c94022bd92da68ef544f2779527bfe065c428',
        'write_root': str(env/'preparation03'),
        'prior_controller_ref': ref(env/'preparation02/controller.py'),
        'prior_preparation_ref': ref(env/'preparation02/PREPARATION.json'),
        'helper_ref': ref(Path(prior_scope['helper_path'])),
        'actual_adoption_ref': ref(out/'Native-AB-actual-adoption.json'),
        'analysis_ref': ref(analysis),
        'old_probe_state_root': prior_scope['state_root'],
        'old_probe_environment_ref': ref(actual/'environment-contract.json'),
        'old_probe_spawn_ref': ref(actual/'A/spawn.json'),
        'native_execution_authorized': False, 'formal_increment': 0,
        'helper_rebuild_authorized': False, 'product_source_writes_authorized': False,
        'max_helper_calls_for_future_run': 2,
        'plan': [
            {'case': 'C', 'environment': 'Seven original A keys and exact values plus approved OS Shell keys and synthetic HOME values', 'startup': 'STARTF_USESHOWWINDOW/SW_HIDE'},
            {'case': 'A2', 'condition': 'C produced stable visible owned dialog and exact normal IDCANCEL', 'environment': 'Exact original A seven keys and values', 'startup': 'STARTF_USESHOWWINDOW/SW_HIDE'},
            {'case': 'D', 'condition': 'C completed with Shell-null and no controller cancellation', 'environment': 'Exact C environment', 'startup': 'Only clear STARTF_USESHOWWINDOW; confirm observed flags differ only in that bit'}
        ],
        'approved_os_environment_keys': ['ComSpec', 'Path', 'PATHEXT', 'OS', 'ProgramData',
            'ProgramFiles', 'ProgramFiles(x86)', 'USERNAME', 'USERDOMAIN', 'SystemDrive'],
        'requirements': [
            'Prepare only. Root must independently verify accepted controller and seal exact run scope before any helper launch.',
            'Reuse frozen helper binary byte-for-byte. Do not rebuild or alter chooser/main/package/COM/callback.',
            'Preserve original A USERPROFILE/APPDATA/LOCALAPPDATA/TEMP/TMP and hint values exactly. Explicitly permit reuse only of CP572 owned synthetic probe state, never original product/user project data. Validate exact root and no reparse escapes. Manifest all owned probe files before and after each case; retain prior receipts unchanged.',
            'Build C from exact A seven-key values. Add only listed current OS keys if present; derive HOMEDRIVE/HOMEPATH from synthetic USERPROFILE. No other environment keys, no inherited secrets/providers/proxies.',
            'C then precisely one conditional second case A2 or D. Unexpected state aborts remaining cases. This explicit finite plan is not an automatic same-input retry.',
            'Copy accepted prep02 retained-handle, BaseException hold, nonce/Root release and exact-owned IDCANCEL logic without weakening it. Never kill helpers or operate other windows.',
            'Capture raw stdout bytes and parsed events, raw stderr, exact spawn flags/environment binding, window observations, result, handle terminal status. Any postspawn I/O failure remains held.',
            'Scope validator requires max2, correct branch plan, immutable hashes, current clean candidate and fresh receipt root. Use Git -c gc.auto=0 -c maintenance.auto=false.',
            'Focused pure mocks for branch selection/environment identity/startup mode/raw capture and hold preservation only. No native run, original evidence writes or unrelated regression reruns.',
            'C visible then A2 null supports the environment group in this owned profile; both visible suggests state/order effects. C null then D visible supports startup influence; both null leaves profile/hint/session hypotheses open. No single key or product causality claim.'
        ],
        'not_authorized': ['Any actual helper launch before later Root run scope',
            'Real Windows user profile values or original user data', 'Product/Core/Electron/CLI or provider startup',
            'Product source, installer, registry, old receipt edits', 'Extra cases, force kill, same-input retries']
    }
    assert not Path(scope['write_root']).exists()
    new(out/'Native-folder-followup-preparation03-scope.json', scope)
    diagnostics = [
        {'origin_key': '20261028|root|history-backend-recovery-failures', 'status': 'READONLY_BACKEND_UNAVAILABLE',
         'attempts': 3, 'detail': 'One notes list and two history list calls returned backend request failed; no product effect.'},
        {'origin_key': '20261028|root|session-display-cp936-encode', 'status': 'READONLY_DISPLAY_ENCODING_FAILURE',
         'attempts': 1, 'exit': 1, 'tool_chunk': '26c4ba', 'detail': 'Read-only display failed GBK encoding; no source or evidence writes.'},
        {'origin_key': '20261028|root|management-source-locator', 'status': 'READONLY_LOCATOR_DIAGNOSTIC',
         'attempts': 1, 'exit': 1, 'tool_chunk': '452236', 'detail': 'Guessed desktop/src path absent. Actual desktop/main/lib path later read.'},
        {'origin_key': '20261028|root|controller-receipt-wrong-cwd', 'status': 'READONLY_LOCATOR_DIAGNOSTIC',
         'attempts': 1, 'exit': 1, 'tool_chunk': '028323', 'detail': 'Receipt path queried under product worktree; absolute Main path then read.'},
        {'origin_key': '20261028|native-folder-probe|AB-no-usable-dialog', 'status': 'ZERO_EXIT_DIAGNOSTIC_NO_SELECTION',
         'attempts': 2, 'ref': ref(out/'Native-AB-actual-adoption.json'), 'detail': 'Both helper invocations exit0 but no usable dialog or observed cancellation; not native product success.'}
    ]
    for row in diagnostics:
        row['counter_reset'] = False
    new(out/'diagnostics.json', {'at': now, 'records': diagnostics, 'original_records_preserved': 2299})
    resume = read(N/'continuation-cp572/RESUME.current.json')
    resume.update(schema='researchos.current-chat-resume.v151', at=now, checkpoint_revision=573,
                  ownership_revision=358, native_AB_actual_adoption_ref=ref(out/'Native-AB-actual-adoption.json'),
                  native_followup_preparation_scope_ref=ref(out/'Native-folder-followup-preparation03-scope.json'),
                  next_command='Prepare/review finite C then conditional A2/D controller using unchanged helper and exact owned probe profile. No native authority yet. Installer P1a frozen accepted; P1b assessment parallel. Full goal remains unfinished.')
    new(out/'RESUME.current.json', resume)
    cp['failure_counters'].extend(diagnostics)
    cp.update(revision=573, expected_previous_revision=572, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
    cp['work_in_progress']['current_chat_continuation_cp573'] = ref(out/'RESUME.current.json')
    cp['evidence_index'].extend([
        {'kind': 'FINITE_AB_ACTUAL_DIAGNOSTIC_ADOPTED', 'ref': ref(out/'Native-AB-actual-adoption.json'), 'formal_increment': 0},
        {'kind': 'NATIVE_ENVIRONMENT_FOLLOWUP_PREPARATION_SCOPE', 'ref': ref(out/'Native-folder-followup-preparation03-scope.json'), 'formal_increment': 0}])
    ow.update(revision=358, expected_previous_revision=357, updated_at=now, updated_by='codex:/root')
    ow['special_paths']['Native_folder_environment_probe'].update(owner=scope['owner'], state='AB_DIAGNOSTIC_ACCEPTED_FOLLOWUP_PREPARATION_ONLY', native_authorized=False,
        scope_ref=ref(out/'Native-folder-followup-preparation03-scope.json'))
    prefix = '# Current verified continuation CP573\n\nRead '+str(out/'RESUME.current.json')+' first. A/B diagnostic completed: SystemDrive alone did not rescue. Both helpers exited; numeric PID reuse is not residue. Follow-up C/conditional A2-or-D preparation only. Installer static accepted; full goal unfinished.\n\n'
    changes = {paths[0]: (json.dumps(cp, ensure_ascii=False, indent=2)+'\n').encode(),
               paths[1]: (json.dumps(ow, ensure_ascii=False, indent=2)+'\n').encode(), paths[2]: prefix.encode()+old[paths[2]]}
    for path in paths:
        assert path.read_bytes() == old[path]
    for path, data in changes.items():
        (out/(path.name+'.before.raw')).write_bytes(old[path])
        temp = path.with_name(path.name+'.cp573.pending')
        with temp.open('xb') as stream:
            stream.write(data)
        assert path.read_bytes() == old[path]
        os.replace(temp, path)
    assert paths[3].read_bytes() == old[paths[3]]
    print(json.dumps({'checkpoint': 573, 'ownership': 358, 'records': len(cp['failure_counters']), 'scope': ref(out/'Native-folder-followup-preparation03-scope.json')}))


if __name__ == '__main__':
    main()
