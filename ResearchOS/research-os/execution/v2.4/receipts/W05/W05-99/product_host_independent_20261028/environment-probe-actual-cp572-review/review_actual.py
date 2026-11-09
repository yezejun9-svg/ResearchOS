"""Read-only validation of completed CP572 A/B evidence; no helper or window actions."""
import datetime,hashlib,json
from pathlib import Path

OUT=Path(__file__).resolve().parent
BASE=OUT.parent.parent
SCOPE=BASE/'resume_cp528_codex'/'20261025-current-chat'/'continuation-cp572'/'Native-folder-finite-AB-scope.json'
EXEC=BASE/'product_host_native_20261028'/'native-init-diagnosis-02'/'environment-probe'/'execution-cp572-AB01'
PREP=EXEC.parent/'preparation02'
SNAP=OUT/'input-snapshots';SNAP.mkdir(exist_ok=False)
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
scope=load(SCOPE);scope_ref=ref(SCOPE)
assert scope_ref['sha256']=='e7d60fe901414bb2de327ce15aeae7bf9964f85714055cda80306e30a994e919'
assert scope['native_execution_authorized'] is True and scope['formal_increment']==0
assert scope['case_order']==['A','B'] and scope['max_helper_calls']==2
assert Path(scope['receipts_root']).resolve()==EXEC.resolve()
assert ref(PREP/'PREPARATION.json')['sha256']==scope['preparation_sha256']
assert ref(PREP/'controller.py')['sha256']==scope['controller_sha256']
assert ref(Path(scope['helper_path']))['sha256']==scope['helper_sha256']
for field in ('source_review_ref','preparation_scope_ref','python_ref'):
    actual=ref(Path(scope[field]['path']));assert actual['sha256']==scope[field]['sha256'] and actual['bytes']==scope[field]['bytes']
refs=[scope_ref,ref(PREP/'PREPARATION.json'),ref(PREP/'controller.py'),ref(Path(scope['helper_path']))]
(SNAP/'RUN-SCOPE.json').write_bytes(SCOPE.read_bytes())
for p in sorted(EXEC.rglob('*')):
    if not p.is_file():continue
    relative=p.relative_to(EXEC);target=SNAP/'execution'/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    raw=p.read_bytes();target.write_bytes(raw);assert p.read_bytes()==raw
    refs.append(ref(p))
save('INPUTS.json',refs)
environment=load(EXEC/'environment-contract.json')
terminal=load(EXEC/'CONTROLLER-TERMINAL.json')
overall=load(EXEC/'RESULT.json')
assert environment['scope_sha256']==terminal['scope_sha256']==scope_ref['sha256']
assert terminal['outer_exit_code']==0 and terminal['completed_before_yield'] is True and terminal['exec_session_id'] is None
assert overall['status']=='A_B_DIAGNOSTIC_COMPLETED' and overall['formal_increment']==0
expected_a={'SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA'}
assert set(environment['A_keys'])==expected_a
assert set(environment['B_keys'])==expected_a|{'SystemDrive'}
assert environment['B_only']=={'SystemDrive':'C:'}
cases=[]
for label in ('A','B'):
    folder=EXEC/label
    spawn,ready,result,cancel,ended,contract,windows=[load(folder/name) for name in
        ('spawn.json','ready.json','result.json','cancel.json','exit.json','hold-contract.json','windows.json')]
    assert contract['scope_sha256']==scope_ref['sha256']
    assert spawn['pid']==ready['pid']==result['pid']
    assert spawn['image']==scope['helper_path']
    assert spawn['hint']==environment['same_hint']
    assert spawn['startup_requested_flags']==1 and spawn['startup_requested_show']==0
    assert ready['startup_flags']==257 and ready['startup_show']==0
    assert set(spawn['env_keys'])==expected_a|({'SystemDrive'} if label=='B' else set())
    assert spawn['system_drive']==('C:' if label=='B' else None)
    assert result['error']=='INVALID_REQUEST: folder selection cancelled' and not result.get('chosen')
    assert ended['exit_code']==0 and ended['controller_cancelled'] is False
    assert cancel['post_idcancel'] is False
    assert ended['error']==result['error'] and ended['elapsed_ns']==result['elapsed_ns']
    assert next(c for c in overall['cases'] if c['case']==label)=={'case':label,'cancelled':False,'result':result}
    assert (folder/'stderr.raw').read_bytes()==b''
    assert not (folder/'UNRESOLVED.json').exists() and not (folder/'WAITING_FOR_ROOT.json').exists()
    expected_pid=61164 if label=='A' else 64276
    assert spawn['pid']==expected_pid
    dialogs=[dict(row,elapsed_ms=sample['elapsed_ms']) for sample in windows for row in sample['windows'] if row['class']=='#32770']
    for sample in windows:
        assert all(row['pid']==spawn['pid'] for row in sample['windows'])
    if label=='A':
        assert len(dialogs)==1 and dialogs[0]['visible'] is False and dialogs[0]['elapsed_ms']==104
    else:assert windows==[]
    cases.append({'case':label,'pid':spawn['pid'],'created_filetime':spawn['created_filetime'],
        'elapsed_ms':result['elapsed_ns']/1_000_000,'exit_code':ended['exit_code'],
        'requested_startup_flags':spawn['startup_requested_flags'],'observed_startup_flags':ready['startup_flags'],
        'startup_show':ready['startup_show'],'controller_idcancel':False,'error':result['error'],
        'window_sample_count':len(windows),'folder_dialog_samples':dialogs})
save('EVIDENCE-RECOMPUTATION.json',{'scope_binding':'PASS','source_binding':'PASS','A_B_environment_difference':environment['B_only'],
    'same_hint':environment['same_hint'],'cases':cases,'controller_terminal':terminal,
    'classification':'DIAGNOSTIC_COMPLETED_WITH_SHELL_NULL_IN_BOTH_CASES_NOT_SELECTION_SUCCESS'})

process_observation={'at':'2026-10-28T08:13:01.6986109Z','tool_chunk':'b0daf5',
    'method':'Reviewer Get-CimInstance Win32_Process filtered by known IDs OR exact helper image; no process actions',
    'expected_helper_pids':[61164,64276],'matching_processes':[
        {'ProcessId':61164,'Name':'svchost.exe','ExecutablePath':None,'CreationDate':'2026-10-28T16:12:38.488897+08:00'}],
    'interpretation':'PID61164 was reused after helper exit by a different-name process with later creation time. Do not operate on it. No exact helper image matched; PID64276 absent.',
    'process_actions':0}
expected_unix_ns=(cases[0]['created_filetime']-116444736000000000)*100
reused_at=datetime.datetime.fromisoformat(process_observation['matching_processes'][0]['CreationDate'])
assert int(reused_at.timestamp()*1_000_000_000)>expected_unix_ns
save('PROCESS-OBSERVATION.json',process_observation)
save('WORKTREE-OBSERVATION.json',{'head':'5c4c94022bd92da68ef544f2779527bfe065c428','head_tool_chunk':'e5c487',
    'status_porcelain':'','status_tool_chunk':'bc6aaa','git_options':['-c','gc.auto=0','-c','maintenance.auto=false'],
    'source_or_shared_state_changes_by_reviewer':0})
next_experiment={'status':'PROPOSAL_ONLY_REQUIRES_SEPARATE_ROOT_SCOPE','question':'Does STARTF_USESHOWWINDOW/SW_HIDE change the early Shell-null behavior?',
    'minimum_design':'Two finite fresh helper cases with the same already accepted helper binary, B environment, Unicode hint, stdio redirection and finite observation. Control retains STARTF_USESHOWWINDOW/SW_HIDE; treatment clears only STARTF_USESHOWWINDOW. Verify actual GetStartupInfo flags differ only at that bit.',
    'unchanged':['Frozen chooser bytes and COM/callback/Shell flags','Same helper binary','B seven keys plus verified SystemDrive','No product Electron/Core/CLI startup'],
    'measure':['Helper ready flags','Window PID/HWND/class/visibility/rectangle and timing','Exact error and elapsed_ns','Whether exact-owned normal IDCANCEL was sent','Retained helper terminal code'],
    'outcome_rules':['Treatment visible/stable and needs owned IDCANCEL while control early-null: startup visibility affects this helper scenario; not yet a product fix.',
        'Both early-null: changing startup visibility alone did not rescue; next distinguish callback/window-create/show/destroy timing in a separately scoped observation-only probe.',
        'Any unexpected live helper or I/O failure: preserve same child handle and abort later cases; no forced kill or automatic retry.'],
    'limits':['Fixed order/shared paths can carry state effects; no automatic A2 or extra repetitions. A reversal confirmation requires a later explicit scope if a difference appears.',
        'Do not add COM initialization, change chooser flags, or widen environment simultaneously; those would confound this comparison.',
        'Window polling remains a sampled observation; unobserved is not nonexistent.']}
save('NEXT-MINIMAL-EXPERIMENT.json',next_experiment)
review={'schema':'researchos.independent-native-folder-environment-actual-review.v1',
    'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/product_host_independent_20261028',
    'status':'FINITE_AB_DIAGNOSTIC_ACCEPTED_SYSTEMDRIVE_ALONE_DID_NOT_RESCUE',
    'scope_and_source_binding_accepted':True,'actual_diagnostic_evidence_accepted':True,
    'native_selection_success':False,'product_qualification_accepted':False,'formal_increment':0,
    'reviewer_helper_runs':0,'reviewer_native_window_actions':0,'source_or_main_writes':0,
    'scope_ref':scope_ref,'cases':cases,
    'conclusions':['A113.3683ms and B96.2467ms both returned INVALID_REQUEST: folder selection cancelled, then helper exit0; controller completed exit0 without a yielded session.',
        'A captured an invisible owned #32770 dialog at104ms. B captured no window sample. Neither controller sent IDCANCEL; B empty sampling does not prove no window existed.',
        'Adding only SystemDrive did not produce a usable folder choice in this bounded A/B run. It does not prove SystemDrive is irrelevant to every Shell path or identify the underlying cause.',
        'Cancellation text is generated by selected==0 in the frozen chooser; it is not evidence of a human cancel. Helper exit0 reports completed diagnostic output, not successful selection.',
        'Both retained helper handles ended exit0. Later numeric PID61164 is a newly created svchost.exe and must not be treated as owned helper residue; no exact helper image matched the reviewer query.'],
    'limitations':['Helper stdout is retained as parsed JSON events, not a separate byte-for-byte stdout.raw file; raw stderr exists and is empty.',
        'Fresh isolated profile was shared across A then B; fixed order/state effects and50ms polling limit causal claims.',
        'This was a direct unchanged-chooser helper, not the installed Core/Electron/CLI path; no product acceptance increment.'],
    'next_step_ref':ref(OUT/'NEXT-MINIMAL-EXPERIMENT.json'),
    'evidence_refs':[ref(OUT/'INPUTS.json'),ref(OUT/'EVIDENCE-RECOMPUTATION.json'),ref(OUT/'PROCESS-OBSERVATION.json'),ref(OUT/'WORKTREE-OBSERVATION.json')]}
save('REVIEW.json',review)
print(json.dumps(ref(OUT/'REVIEW.json'),ensure_ascii=False))
