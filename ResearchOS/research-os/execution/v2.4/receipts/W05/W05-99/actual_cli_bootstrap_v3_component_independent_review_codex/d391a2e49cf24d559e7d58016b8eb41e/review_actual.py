"""Read-only review of sealed records; no candidate import, native, GUI or SQL."""
import hashlib,json,math
from pathlib import Path
BASE=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d/actual-cli-bootstrap-v3-80c7b29a01c341a884597b7da9e17c4a')
DELTA=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/actual_cli_bootstrap_v3_delta_review_codex/1d473bc60a0b48e29df3ea1ce297cbf7')
OUT=Path(__file__).resolve().parent
records={};checks=[]
def pin(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
def read(ref):
    path=Path(ref['path']);raw=path.read_bytes()
    actual={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    match=actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
    key=str(path).lower()
    if key not in records:records[key]={'ref':actual,'expected_ref':ref,'matches':match}
    if not match:raise RuntimeError('sealed input drift: '+str(path))
    return raw
def doc(ref):return json.loads(read(ref))
def put(name,value):
    with (OUT/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(OUT/name)
H={'path':str(BASE/'handoff.json'),'sha256':'febb4773875ea52c22a356bee9edb8b22ebdc8e54d3fe2ecee25fc80129c4152','bytes':2564}
M={'path':str(BASE/'manifest.json'),'sha256':'27c367c8a9f13bcbeebc3f72c614cde3c398aedb3003ed583606974846581fe0','bytes':8470}
h=doc(H);m=doc(M)
check('handoff_manifest_pin',h['manifest_ref']['sha256']==M['sha256'] and h['manifest_ref']['bytes']==M['bytes'])
members={Path(ref['path']).name:ref for ref in m['members']}
snap=OUT/'snapshots';snap.mkdir()
for ref in m['members']:
    raw=read(ref)
    with (snap/Path(ref['path']).name).open('xb') as f:f.write(raw)
for name,ref in [('root-handoff.json',H),('root-manifest.json',M)]:
    with (snap/name).open('xb') as f:f.write(read(ref))
get=lambda name:doc(members[name])
intent=get('bootstrap.intent.json');life=get('bootstrap.lifecycle.actual.json');guard=get('bootstrap.source-guard.cleanup.actual.json')
init=get('cli-init.invocation.json');goal=get('cli-goal.invocation.json');host=get('normal-host.invocation.json')
picker=get('workspace-picker.actual.json');binding=get('workspace-binding.actual.json');partial=get('partial-bootstrap.actual-db-readonly.json')
failure=get('failure-origin.719.original-tool-io.json');clarify=get('failure719.native-and-closure.clarification.json')
config=json.loads(read(members['cli-init.config.after.raw']))
initrows=[json.loads(line) for line in read(init['stdout_ref']).splitlines()]
goalrows=[json.loads(line) for line in read(goal['stdout_ref']).splitlines()]
for invocation in (init,goal,host):
    read(invocation['stdout_ref']);read(invocation['stderr_ref'])
source=read(h['source_ref']).decode()
check('actual_init_native_exit_0',init['actual_native_exit']==init['result']['actual_exit']==0 and init['result']['timed_out'] is False and init['result']['error'] is None)
check('single_init_completed_summary',len(initrows)==1 and initrows[0]['command']=='init' and initrows[0]['status']=='COMPLETED' and initrows[0]['exit_code']==0 and initrows[0]['requests_sent']==['workspace.register','project.bootstrap'])
isummary=initrows[0];gsummary=goalrows[0]
project=isummary['project_id'];ws=config['workspace_ref'];rootdir=Path(intent['data_root']);workspace=Path(intent['workspace'])
check('fresh_unique_isolated_workspace_source',rootdir.name=='mu-sdk-isolated-project-ed84838046934329a76733a005c9b162' and workspace==rootdir/'workspace' and 'assert not data.exists();workspace.mkdir(parents=True)' in source)
check('cli_init_config_and_argv_bind_actual_directory',Path(init['argv'][2])==workspace and Path(init['environment']['RESEARCHOS_CLI_CONFIG'])==Path(intent['cli_config_file']) and Path(init['environment']['RESEARCHOS_CLI_DISCOVERY'])==Path(intent['discovery_file']) and config['project_id']==project and config['session_id']=='' and config['config_revision']==0 and isummary['workspace_ref']==ws)
check('durable_unique_binding_source_not_sql_replay',"binding_rows=binding_db.execute(\"SELECT body FROM domain_objects WHERE kind='WorkspaceBinding' AND json_extract(body,'$.authorized_workspace_ref')=?\",(before_config[\"workspace_ref\"],)).fetchall()" in source and 'assert len(binding_rows)==1' in source and 'mode=ro' in source)
ab=binding['actual_binding']
check('actual_binding_project_ref_status_physical_path',binding['source']=='ACTUAL_HOST_DURABLE_DOMAIN_OBJECT' and binding['project_id']==ab['project_id']==project and binding['workspace_ref']==ab['authorized_workspace_ref']==ws and ab['status']=='ACTIVE' and Path(ab['real_path'])==workspace==Path(binding['expected_directory']) and binding['matches_unique_isolated_workspace'] is True)
check('init_public_binding_agrees_durable_record',isummary['result']['workspace']['authorized_workspace_ref']==ws and isummary['result']['workspace']['project_id']==project and isummary['result']['workspace']['revision']==ab['revision'] and isummary['result']['workspace']['status']==ab['status'])
read(picker['actual_workspace_binding_ref']);read(partial['workspace_binding_ref']);read(partial['picker_ref'])
check('one_actual_picker_observation',picker['mode']=='ACTUAL_HOST_SHELL_DIALOG_AUTOMATION' and len(picker['observations'])==1 and picker['clicked_once'] is True and picker['confirmed_by_native_cli_result'] is True and picker['actual_dialog_closed'] is True and picker['actual_workspace_binding_matches_unique_directory'] is True and picker.get('error') is None and not picker.get('callback_errors'))
obs=picker['observations'][0];host_before=get('normal-host.before-resume.actual.json')['identity'];live=obs['actual_held_host_identity']
idkeys=('run_uuid','owner_pid','runner_pid','creation_time_100ns','job_binding_id')
check('picker_binds_live_Host_PID_creation_held_handles',all(type(live[k]) is type(host_before[k]) and live[k]==host_before[k] for k in idkeys) and obs['host_pid']==host['result']['owned_child_pid']==host_before['runner_pid'] and obs['host_creation_time_100ns']==host['result']['creation_time_100ns']==host_before['creation_time_100ns'] and live['pid_match'] is True and live['creation_match'] is True and live['primary_exit_confirmed'] is False and type(live['active_processes']) is int and live['active_processes']>0 and live['errors']==[])
check('actual_Static_title_and_IDOK_same_Host',obs['dialog_class']=='#32770' and any(c['class']=='Static' and c['text']=='Select a ResearchOS workspace folder' and c['pid']==obs['host_pid'] for c in obs['children']) and any(c['hwnd']==obs['idok_hwnd'] and c['class']=='Button' and c['pid']==obs['host_pid'] and c['text']==obs['idok_text'] for c in obs['children']))
check('source_WM_GETTEXT_then_real_IDOK_BM_CLICK','u.SendMessageTimeoutW(hwnd,0x000D,len(b),ctypes.addressof(b),0x0002,500' in source and 'button=u.GetDlgItem(hwnd,1)' in source and 'u.SendMessageTimeoutW(button,0x00F5,0,0,0x0002,1000' in source and picker['actual_BM_CLICK_send_completed'] is True and picker['send_winerror']==0 and picker['message_result_not_success_evidence']==0)
check('no_cross_process_custom_pointer_preselection',obs['cross_process_custom_pointer_message_sent'] is False and obs['workspace_preselection']=='UNCHANGED_HOST_SAME_PROCESS_CALLBACK')
check('Goal_exact_failure_native_and_body',goal['actual_native_exit']==goal['result']['actual_exit']==3 and goal['result']['timed_out'] is False and goal['result']['error'] is None and len(goalrows)==1 and gsummary['exit_code']==3 and gsummary['status']=='REJECTED' and gsummary['reason']=='HOST_REJECTED:RESOURCE_BLOCKED' and gsummary['requests_sent']==['goal.start'] and gsummary['operations']==[{'exit_code':3,'method':'goal.start','reason':'HOST_REJECTED:RESOURCE_BLOCKED','result':None,'status':'REJECTED'}])
check('Goal_argv_is_draft_same_actual_project',goal['argv'][1]=='goal' and goal['argv'][-3:]==['--project',project,'--draft'] and gsummary['session_id']=='')
check('719_outer_Python1_separate_from_native3',failure['observed_ordinal']==719 and failure['actual_outer_exit']==failure['actual_python_exit']==failure['tool_result']['exit_code']==1 and 'RESEARCHOS_BOOTSTRAP_V3_PYTHON_EXIT=1' in failure['tool_result']['output'] and clarify['actual_cli_native_exit']==3 and clarify['reason']==gsummary['reason'] and life['error']=="AssertionError('CLI command did not succeed')")
check('3_actual_owned_jobs_exact_set',len(life['jobs'])==3 and {j['label'] for j in life['jobs']}=={'normal-host','cli-init','cli-goal'} and life['all_owned_jobs_cleanup_confirmed'] is True)
invocations={'normal-host':host,'cli-init':init,'cli-goal':goal}
timeouts={'normal-host':60,'cli-init':20,'cli-goal':10}
for j in life['jobs']:
    label=j['label'];before=get(label+'.before-resume.actual.json');i=invocations[label];p=j['actual_fresh_cleanup'];c=i['result']['job_cleanup'];dup=j['duplicate_producer_cleanup'];wd=j['watchdog_cleanup']
    check(label+'_PID_create_Job_identity_continuity',all(type(p[k]) is type(before['identity'][k]) and p[k]==before['identity'][k] for k in idkeys) and p['owner_pid']==life['actual_parent_pid'] and p['runner_pid']==i['result']['owned_child_pid'] and p['creation_time_100ns']==i['result']['creation_time_100ns'])
    check(label+'_native_idle_handles_closed',j['original_native_cleanup_confirmed'] is True and type(c['active_processes_last_observed']) is int and c['active_processes_last_observed']==0 and c['errors']==[] and all(c[k] is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')))
    check(label+'_held_actual_fresh_idle_signaled',p['schema']=='researchos.held-job-cleanup-observation.v1' and type(p['active_processes']) is int and p['active_processes']==0 and p['primary_exit_code']==i['actual_native_exit'] and p['errors']==[] and all(p[k] is True for k in ('captured_before_resume','held_job_handle','held_primary_handle','pid_match','creation_match','primary_exit_confirmed')) and type(p['observed_monotonic']) in (int,float) and math.isfinite(p['observed_monotonic']) and p['observed_monotonic']>=before['actual_deadline_monotonic']-timeouts[label]+i['result']['elapsed_seconds'] and p['observed_monotonic']>=life['host_stop']['at_monotonic'])
    check(label+'_duplicates_closed_after_proof',dup['closed'] is True and dup['job_handle_closed'] is True and dup['primary_handle_closed'] is True and dup['errors']==[] and dup['owner_pid']==life['actual_parent_pid'] and dup['run_uuid']==p['run_uuid'] and wd['duplicate_handle_closed'] is True and wd['errors']==[] and wd['deadline_monotonic']==before['actual_deadline_monotonic'] and j['closed'] is True)
check('explicit_Host_teardown_exit_matches_native',life['host_stop']['actual_TerminateJobObject_return'] is True and life['host_stop']['planned_pre_trial_host_teardown'] is True and life['host_stop']['requested_exit_code']==host['actual_native_exit']==3758097672 and host['result']['timed_out'] is False)
expected_guard=intent['source_refs']+[h['source_ref']]
check('source_guard_all10_exact_pins_closed',len(guard['entries'])==len(expected_guard)==10 and guard['closed'] is True and type(guard['retained_handles_count']) is int and guard['retained_handles_count']==0 and guard['errors']==[] and guard['failure'] is None and guard['verification']=='PASSED' and all(e['verified'] is True and e['final_path_match'] is True and e['closed'] is True for e in guard['entries']) and {(str(Path(e['path'])).lower(),e['sha256'],e['bytes']) for e in guard['entries']}=={(str(Path(e['path'])).lower(),e['sha256'],e['bytes']) for e in expected_guard})
canon=[]
for ref in intent['canonical_refs']:
    raw=read(ref);canon.append({'ref':ref,'matches_current':True})
check('canonical_four_unchanged_current_hashes',len(canon)==4 and {Path(r['ref']['path']).name for r in canon}=={'checkpoint.json','path_ownership.json','step_state.json','commands.json'})
check('Root_readonly_counts_not_independent_SQL',partial['project_id']==project and partial['config']==config and partial['counts']['ProjectProfile']==1 and all(type(partial['counts'][k]) is int and partial['counts'][k]==0 for k in ('Goal','Task','Run','BudgetLedgerEntry','resource_effects')))
check('WorkspaceBinding_project_column_zero_does_not_override_body_ref_query',partial['counts']['WorkspaceBinding']==0 and ab['project_id']==project and ab['authorized_workspace_ref']==ws and 'assert len(binding_rows)==1' in source)
check('bootstrap_success_absent_and_not_accepted','bootstrap.result.json' not in members and not (BASE/'bootstrap.result.json').exists() and partial['bootstrap_accepted'] is False and h['bootstrap_accepted'] is False and h['runtime_qualification'] is False and h['formal_acceptance'] is False)
check('provider_zero_supported_by_no_runtime_and_effect_snapshot',intent['no_runtime_coordinator'] is True and partial['counts']['resource_effects']==0 and partial['counts']['Run']==0 and life['provider_requests']==0 and h['provider_requests']==0)
delta_h=doc(pin(DELTA/'handoff.json'));delta_review=doc(delta_h['review_ref']);delta_manifest=doc(delta_h['manifest_ref'])
check('independent_v3_Source_delta_matches_actual_source',delta_h['decision']=='READY_SOURCE_DELTA' and delta_h['source_ref']['sha256']==h['source_ref']['sha256'] and delta_review['remaining_findings']==[] and delta_review['source_author']=='codex:/root')
for ref in intent['source_refs']:read(ref)
check('original_error_not_reclassified_success',clarify['actual_outer_exit']==clarify['actual_python_exit']==1 and clarify['actual_cli_native_exit']==3 and failure['automatic_retry'] is False and failure['counter_reset'] is False)
failed=[c for c in checks if not c['passed']]
put('evidence-checks.json',{'checks':checks,'total':len(checks),'matched':len(checks)-len(failed),'failed':failed,'canonical_current_recheck':canon,'reviewer_SQL_or_GUI_native_calls':0})
put('input-intake.json',{'inputs':list(records.values()),'unique_inputs':len(records),'drift':sum(not r['matches'] for r in records.values()),'root_manifest_members':len(members),'reviewer_candidate_imports':0,'reviewer_SQL_or_GUI_native_calls':0})
decision='PASS_COMPONENT_EVIDENCE_WITH_GOAL_BLOCKED' if not failed else 'REQUEST_CHANGES'
review={'schema':'researchos.actual-cli-bootstrap-component-independent-review.v1','actor_id':'codex:/root/command_queue_impl','source_author':'codex:/root','decision':decision,'source_handoff_ref':H,'source_manifest_ref':M,'evidence_checks_ref':pin(OUT/'evidence-checks.json'),'input_intake_ref':pin(OUT/'input-intake.json'),'verified_scope':['ACTUAL_CLI_INIT_EXIT_ZERO','ACTUAL_HOST_OWNED_GUI_PICKER_AND_UNIQUE_DURABLE_BINDING','GOAL_RESOURCE_BLOCKED_EXIT_THREE_RECORDED','THREE_OWNED_JOBS_AND_DUPLICATES_CONFIRMED_CLOSED_IN_ORIGINAL_RUN','SOURCE_GUARD_TEN_ENTRIES_ZERO_RETAINED','FOUR_CANONICAL_HASHES_UNCHANGED'],'project_id':project,'host_pid':host['result']['owned_child_pid'],'host_creation_time_100ns':host['result']['creation_time_100ns'],'root_original_failure':719,'root_outer_exit':1,'root_python_exit':1,'actual_cli_goal_exit':3,'goal_reason':gsummary['reason'],'bootstrap_accepted':False,'runtime_qualification':False,'formal_acceptance':False,'execution_grant_issued':False,'provider_requests_in_original_scoped_run':0,'limitations':['Read-only review of pinned actual records; no OS event or database query rerun.','Database counts are Root produced sealed readonly snapshot, not reviewer SQL execution.','Cleanup freshness is bound to original invocation timing, not a new current-process observation.','WorkspaceBinding scoped project-column count zero does not imply missing binding; actual body-authorized-ref query is unique and binds the physical path.','Inventory stage ID in init stdout is not proof of a Task row.','No successful bootstrap.result.json or draft Goal exists in this evidence.'],'new_tool_failures':0,'reviewer_native_GUI_SQL_provider_calls':0,'Main_canonical_writes':0,'failed_checks':failed}
put('review.json',review)
print(json.dumps({'decision':decision,'checks':len(checks),'matched':len(checks)-len(failed),'failed':[c['name'] for c in failed],'unique_inputs':len(records),'input_drift':0,'candidate_native_GUI_SQL_provider_calls':0}))
