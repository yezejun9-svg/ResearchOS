from pathlib import Path
import json,hashlib,datetime
R=Path.cwd();run='d8edec82-2949-481d-bfad-4b6bd06604f7';O=R/'execution/verifier/W12'/('global-review-'+run);A=json.loads((O/'envelope-audit.json').read_text(encoding='utf8'));load=lambda p:json.loads(p.read_text(encoding='utf8'));checks=[]
def ck(k,ok,details=None):
 checks.append({'id':k,'pass':bool(ok),'details':details})
 if not ok:print('FAIL',k,details)
d=R/'execution/receipts/W12/d6a7202b-82fc-4900-8c48-6b6e9453c46b';report=load(d/'report.json');rows={x['assertion_id']:x for x in report['assertions']};ev=lambda k:rows[k]['evidence']
e=ev('C11-01');ck('C11_identity_and_new_context',e['before']['id']==e['after']['id'] and e['before']['task_id']==e['after']['task_id'] and e['cycle_before']==e['cycle_after'] and e['current_context']['id']!=e['before']['context_bundle_id'])
crash=load(d/'TestW12CrashAndResume/crash-process.json');resume=load(d/'TestW12CrashAndResume/resume-process.json');ck('C11_native_forced_exit_restart',crash['pid']>0 and crash['exit_code']!=0 and 'EXTERNAL_COMMITTED_BEFORE_LOCAL_ACK' in crash['stdout'] and resume['pid']>0 and resume['pid']!=crash['pid'] and resume['exit_code']==0)
e=ev('C11-02');ck('C11_reconcile_before_resume',rows['C11-02']['actual']==1 and e['blind_retry']=='BLOCKED' and e['unknown_resume']=='BLOCKED' and e['reconciliation']=='QUERIED_PROVIDER_BEFORE_RESUME')
ck('C11_dedupe_monotonic',rows['C11-03']['actual']==[1,2,409,True,1,0,[200,409,409],[201,201,201]])
e=ev('C13-01');ck('C13_unlimited_unknown_preserved',e['policy']['mode']=='UNLIMITED_AMOUNT' and e['policy']['cap'] is None and e['ledger']['money'] is None and e['ledger']['cost_basis']=='UNKNOWN')
e=ev('C13-02');ck('C13_new_session_active_goal',e['old_session_pid']!=e['new_session_pid'] and rows['C13-02']['actual']==['ACTIVE','RUNNING',True])
e=ev('C13-03');ck('C13_concurrency_queue',rows['C13-03']['actual']==[409,409,100,'DRAFT'] and len(set(e['active_runs']))==2 and e['run_policy']['max_concurrency']==2 and e['run_policy']['max_queue']==100)
e=ev('C14-01');ck('C14_exact_caps_atomic',e['parent_policy']['cap']['amount']=='10.00' and e['child_policy']['cap']['amount']=='20.00' and e['prior_reserved']['money']['amount']=='2.00' and rows['C14-01']['actual']==[1,1])
events=[]
for p in (d/'TestW12Budget').glob('http-*.json'):events+=load(p)['exchanges']
ledger=[x for x in events if x['method']=='POST' and x['path'].endswith('/budget-ledger')]
amount2=[x['status'] for x in ledger if (x['request'].get('money') or {}).get('amount')=='2.00' and x['request']['operation']=='RESERVE'];ck('C14_wire_reservations',sorted(amount2)==[201,201,422],amount2)
ck('C14_wire_initial_spend',any(x['request']['operation']=='RECONCILE' and x['status']==201 and x['request']['money']['amount']=='6.00' for x in ledger))
ck('C14_strict_unbounded_and_currency',rows['C14-02']['actual']==[422,422,422])
e=ev('C14-03');ck('C14_late_cost_after_cancel',e['late']['operation']=='COMMIT' and e['late']['money']['amount']=='2.50' and e['late']['run_id']==e['run']['id'] and e['run']['status']=='CANCEL_REQUESTED')
ck('C14_two_connection_race',rows['W12-BUDGET-SQLITE-CONNECTIONS']['actual']==[201,422] and ev('W12-BUDGET-SQLITE-CONNECTIONS')['sqlite_connections']==2)
for x in ev('W12-BUDGET-EXPERIMENT-SCOPES'):
 ck('C14_bound_scope_'+x['limiting_scope'],x['over_cap']['code']=='GATE_FAILED' and x['at_cap']['money']['amount']=='2')
for x in ev('C15-01'):ck('C15_qualification_'+x['scenario'],x['automatic_switch']==(x['scenario']=='qualified_authorized'))
for x in ev('C15-02'):
 q=x['request'];ck('C15_request_'+x['scenario'],x['open_count']==1 and x['trigger_count']==5 and q['cost_known'] is False and q['estimated_cost'] is None and len(q['completed_artifact_refs'])>0 and len(q['continuable_task_ids'])>0 and q['resume_checkpoint_ref'] is not None)
for x in ev('C15-03'):ck('C15_continuation_'+x['scenario'],x['independent_task_status']=='ACCEPTED' and bool(x['checkpoint_id']) and bool(x['same_run_id']) and bool(x['unchanged_contract_hash']))
ck('C16_retry_bound',rows['C16-01']['actual']==[['FAILED','FAILED','DEFERRED_NO_PROGRESS'],409])
e=ev('C16-02');ck('C16_not_accepted_and_resume_conditions',e['progress']['status']=='DEFERRED_NO_PROGRESS' and e['progress']['same_failure_count']==3 and e['progress']['no_progress_iterations']==3 and e['task']['acceptance_id'] is None and len(e['progress']['resume_conditions'])>0)
e=ev('C16-03');ck('C16_child_and_new_input',e['child_same']['no_progress_record_id']==e['old']['id'] and e['new_inputs']['no_progress_record_id']!=e['old']['id'] and e['old']['no_progress_iterations']==3 and bool(e['explicit_resume']['resume_reason']) and len(e['explicit_resume']['new_evidence_refs'])>0 and rows['C16-03']['actual']==[True,409,3,True,1,'READY'])
http_count=0;attempts=0
for reportpath in A['report_paths'].values():
 rd=(R/reportpath).parent
 for p in rd.rglob('http-*.json'):
  raw=load(p);http_count+=1;attempts+=len(raw['readiness']);ck('readiness:'+str(p.relative_to(R)),1<=len(raw['readiness'])<=3 and raw['readiness'][-1]['status']==404 and raw['readiness'][-1]['error'] is None)
for iid in ['242d5be5-4058-4e7c-a5ac-5ee1a944936f','4bb22431-ece1-45e6-ace5-d50a72d032be']:
 inv=load(R/'execution/invocations'/iid/'receipt.json');ck('historical_failure:'+iid,inv['exit_code']!=0 and inv['status']!='PASS',{'exit_code':inv['exit_code'],'status':inv['status'],'assertions':len(inv['assertion_ids'])})
result={'scope':'OFFLINE_INDEPENDENT_EVIDENCE_RECONSTRUCTION','checks':checks,'count':len(checks),'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'http_fixture_count':http_count,'readiness_attempts':attempts,'no_new_test_or_provider_calls':True};(O/'semantic-audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');print({k:v for k,v in result.items() if k!='checks'})
