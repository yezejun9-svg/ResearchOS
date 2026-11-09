"""Read-only public failure review and evidence sealing preparation; no candidate execution."""
import hashlib,json,math
from pathlib import Path
OUT=Path(__file__).resolve().parent
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/root-model-trial-v5-870ecc93e109c85ee985e1566ff");TRIAL=BASE/'trial-output'
HELPER=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_v4_codex/staged-root-69e7c3008fd968419f4d4072c3c8")
ROOT=Path('D:/作品集/ResearchOS/research-os')
inputs=[];checks=[]
def pin(p):
 raw=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(ref):
 raw=Path(ref['path']).read_bytes();assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'];inputs.append(ref);return raw
def obj(ref):return json.loads(read(ref))
def put(n,x):
 with (OUT/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(OUT/n)
def check(n,x):
 checks.append({'check':n,'passed':bool(x)});assert x,n
original=json.loads((OUT/'original-observations.json').read_bytes())
public=json.loads(original['public_receipts_read']['original_result']['output'])
docs={}
for ref in public['public_pins']:
 raw=read(ref);docs[Path(ref['path']).name]=raw.decode() if ref['path'].endswith('.raw') else json.loads(raw)
life=docs['root-coordinator.lifecycle.json'];ad=docs['host.admitted.json'];ready=docs['host.ready.json'];authority=docs['host-go.authority.json'];contract=docs['host-job.contract.json'];probe=docs['host-job.probe.json'];clock=docs['whole-trial-clock.json']
check('failed_execution_closed_with_GO_consumed',life['state']=='FAILED_EXECUTION_CLOSED' and life['actual_parent_pid']==20540 and life['go_sent'] is True and life['provider_requests'] is None and life['same_parent_must_remain_alive'] is False and life['automatic_retry'] is False)
check('exact_canonical_number_stderr',docs['host-execute-admitted.stderr.raw'].strip()=='TRUSTED_QUALIFICATION_ERROR: JSON number is not losslessly representable by canonical JSON')
check('admitted_and_ready_before_failure',ad['status']=='ADMITTED_NOT_DISPATCHED' and ready['status']=='READY_ADMISSION_PENDING' and all(ad[k]==ready[k]==authority[k] for k in ('project_id','runtime_id','qualification_task_id','qualification_run_id','qualification_epoch','profile_hash','host_instance_id')) and ready['host_pid']==contract['host_pid']==probe['host_pid']==23436)
for key,name in (('ready_receipt','host.ready.json'),('root_grant','root-host-go.json'),('once_marker','host-go.once.json'),('outer_job_contract','host-job.contract.json'),('host_job_probe','host-job.probe.json')):
 ref=authority[key];read(ref);check('GO_exact_'+key,Path(ref['path'])==TRIAL/name)
# Public private_coordinator pins are metadata only: do not open their referenced files.
check('private_coordinator_metadata_bound_without_read',authority['private_coordinator']==ready['private_coordinator'])
check('once_clock_preserved',docs['host-go.once.json']['state']=='CONSUMED_FOR_HOST_GO' and docs['host-go.once.json']['qualification_run_id']==ad['qualification_run_id'] and docs['host-go.once.json']['owner_pid']==life['actual_parent_pid'] and clock['clock_reset_permitted'] is False and clock['absolute_deadline_monotonic']-clock['started_monotonic']==300 and clock['started_utc']==ad['root_started_utc'])
check('two_exact_native_jobs',len(life['jobs'])==2 and {j['label'] for j in life['jobs']}=={'host-admit-only','host-execute-admitted'})
for job in life['jobs']:
 label=job['label'];inv=docs[label+'.invocation.json'];res=inv['result'];c=job['cleanup'];proof=c['proof'];wd=c['watchdog'];prod=c['producer'];code=0 if label=='host-admit-only' else 1
 check(label+'_actual_exit_identity',res['actual_exit']==inv['native_exit']==proof['primary_exit_code']==code and res['error'] is None and res['timed_out'] is False and res['owned_child_pid']==proof['runner_pid'] and res['creation_time_100ns']==proof['creation_time_100ns'] and proof['owner_pid']==life['actual_parent_pid'])
 jc=res['job_cleanup']
 check(label+'_native_job_closed',jc['errors']==[] and type(jc['active_processes_last_observed']) is int and jc['active_processes_last_observed']==0 and all(jc[k] is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')))
 check(label+'_held_original_proof_and_duplicates_closed',c['closed'] is True and proof['errors']==[] and type(proof['active_processes']) is int and proof['active_processes']==0 and all(proof[k] is True for k in ('captured_before_resume','held_job_handle','held_primary_handle','primary_exit_confirmed','pid_match','creation_match')) and wd['duplicate_handle_closed'] is True and wd['errors']==[] and prod['errors']==[] and all(prod[k] is True for k in ('job_handle_closed','primary_handle_closed','closed')) and prod['run_uuid']==proof['run_uuid'] and prod['owner_pid']==proof['owner_pid'])
 read(inv['stdout_ref']);read(inv['stderr_ref'])
execproof=next(j for j in life['jobs'] if j['label']=='host-execute-admitted')['cleanup']['proof']
check('host_contract_probe_original_identity',contract['held_identity']==probe['held_identity'] and all(contract['held_identity'][k]==execproof[k] for k in ('run_uuid','owner_pid','runner_pid','creation_time_100ns','job_binding_id')) and contract['root_pid']==probe['root_pid']==life['actual_parent_pid'])
guards=life['source_guard_cleanup']
check('seven_Source_guards_eighty_entries_closed',len(guards)==7 and sum(len(g['entries']) for g in guards)==80 and all(g['closed'] is True and g['retained_handles_count']==0 and g['errors']==[] and all(e['closed'] is True and e['verified'] is True for e in g['entries']) for g in guards))
wrapper=obj(pin(BASE/'wrapper.source-guard.cleanup.actual.json'))
check('wrapper_Source_guard_six_entries_closed',wrapper['closed'] is True and wrapper['retained_handles_count']==0 and wrapper['errors']==[] and len(wrapper['entries'])==6 and all(e['closed'] is True and e['verified'] is True for e in wrapper['entries']))
execref={'path':str(HELPER/'execute.go'),'sha256':'54d7c3d068722c3fab967fc91d35cbd708e9de158f94e7712878fed0dd4e7242','bytes':25064}
execute=read(execref).decode()
domainref=pin(ROOT/'internal/domain/contracts.go');domain=read(domainref).decode()
canonicalref=pin(ROOT/'internal/canonical/jcs.go');canonical=read(canonicalref).decode()
dispatchref=pin(ROOT/'internal/domain/runtime_coordinator_windows.go');dispatchsource=read(dispatchref).decode()
check('readPinnedObject_uses_Domain_Decode','return domain.Decode(raw)' in execute[execute.index('func readPinnedObject'):execute.index('func verifyGOEvidence')])
verify=execute[execute.index('func verifyGOEvidence'):execute.index('func sealedProfile')]
check('GO_evidence_order_grant_once_contract_probe',verify.index('a.RootGrant')<verify.index('a.OnceMarker')<verify.index('a.OuterJobContract')<verify.index('a.HostJobProbe'))
executephase=execute[execute.index('func executeAdmitted'):execute.index('func completeQualification')]
check('readGO_error_precedes_execution_claim_and_RunAdmitted',executephase.index('authority, err := readGO(')<executephase.index('v.ExecuteClaimedAt =')<executephase.index('coordinator.RunAdmitted(') and 'return nil, err' in executephase[executephase.index('authority, err := readGO('):executephase.index('v.ExecuteClaimedAt =')])
check('DomainDecode_exact_rational_guard','canonical.JSON(raw)' in domain and 'JSON number is not losslessly representable by canonical JSON' in domain and 'new(big.Rat).SetString(x.String())' in domain and 'r.Cmp(s) == 0' in domain)
check('canonical_IEEE754_contract','JCS uses finite IEEE-754 numbers' in canonical and 'v.Canonicalize()' in canonical)
number=contract['held_identity']['creation_time_100ns'];number2=probe['held_identity']['creation_time_100ns']
check('actual_integer_is_not_binary64_lossless',number==number2==134359521876434319 and number>2**53 and int(float(number))==134359521876434320 and int(float(number))-number==1)
numeric=original['numeric_diagnostic']
check('independent_JavaScript_numeric_render',numeric['original_decimal']==str(number) and numeric['binary64_shortest_decimal']=='134359521876434320' and numeric['integer_delta']=='1')
def ints(obj,path=''):
 if isinstance(obj,dict):
  return [(p,n) for k,v in obj.items() for p,n in ints(v,path+'.'+k)]
 if isinstance(obj,list):return [(p,n) for k,v in enumerate(obj) for p,n in ints(v,path+'['+str(k)+']')]
 return [(path,obj)] if type(obj) is int else []
check('grant_once_have_no_unsafe_integers',all(abs(n)<=2**53 for name in ('root-host-go.json','host-go.once.json') for path,n in ints(docs[name])))
check('contract_only_unsafe_integer_is_creation_time',[path for path,n in ints(contract) if abs(n)>2**53]==['.held_identity.creation_time_100ns'])
one=json.loads(original['read_only_sql_1']['original_result']['output']);two=json.loads(original['read_only_sql_2']['original_result']['output'])
run=one['run'][0];task=one['task'][0];dispatch=two['dispatch'][0];marker=two['qualification_marker'][0]
check('readonly_SQL_business_observations',one['query_only']==two['query_only']==1 and len(one['run'])==len(one['task'])==len(two['dispatch'])==len(two['qualification_marker'])==1)
check('current_Run_admitted_queued_and_Task_running',run['id']==task['active_run_id']==ad['qualification_run_id'] and run['status']=='QUEUED' and task['status']=='RUNNING' and run['task_id']==task['id']==ad['qualification_task_id'] and run['runtime_id']==ad['runtime_id'] and run['lease_epoch']==ad['qualification_epoch']==1)
check('current_dispatch_never_claimed',dispatch['project']==ad['project_id'] and dispatch['run']==run['id'] and dispatch['epoch']==1 and dispatch['state']=='PREPARED' and dispatch['worker']==dispatch['journal_locator']=='' and json.loads(dispatch['identity'])=={} and dispatch['observation_sequence']==0 and dispatch['observation_hash']=='')
check('current_qualification_RunMarker_bound',marker['project']==ad['project_id'] and marker['task']==task['id'] and marker['run']==run['id'] and marker['runtime']==ad['runtime_id'] and marker['epoch']==1 and marker['profile_hash']=='sha256:86278f59fb3170c34191a484086fced79bd8d0ff82a960b0fd81265270f96b68')
check('zero_recorded_effects_observations_uploads_ledger_acceptance',all(two['counts'][k]==0 for k in ('resource_effects','runtime_observations','runtime_uploads','project_resource_effects','project_BudgetLedgerEntry','project_Acceptance')) and two['counts']['project_Run']==1)
check('provider_total_remains_unknown',life['provider_requests'] is None and two['provider_requests_total'] is None and all(v is None for v in two['dedicated_run_counter_json_types'].values()) and two['model_requests_recorded_as_resource_effects']==0)
check('RunAdmitted_would_start_dispatch_before_bridge',dispatchsource.index("UPDATE runtime_dispatches SET state='STARTED'")<dispatchsource.index('bridge, e := rt.StartBridge'))
check('ordinary_ready_and_C7_outputs_absent',not (TRIAL/'host.ready.ordinary.json').exists() and not (TRIAL/'c7-outcomes').exists() and not (TRIAL/'c7-phase').exists())
unique={}
for ref in inputs:unique[(str(Path(ref['path'])),ref['sha256'],ref['bytes'])]=ref
for ref in unique.values():
 a=pin(ref['path']);assert a['sha256']==ref['sha256'] and a['bytes']==ref['bytes']
checkref=put('evidence-checks.json',{'checks':checks,'passed':len(checks),'failed':0,'unique_input_count':len(unique),'input_drift':0})
inputref=put('input-intake.json',{'input_refs':list(unique.values()),'private_refs_not_opened':True,'input_drift':0})
observationref=put('business-state.observed.json',{'read_only_query_only':True,'run':run,'task':task,**two,'private_lease_material_not_selected':True})
report={'schema':'researchos.model-trial-failure-component-independent-review.v1','actor_id':'codex:/root/command_queue_impl','decision':'FAILURE745_CONFIRMED_CLOSED_DISPATCH_NOT_STARTED','failed_trial_provider_requests':None,'model_requests_recorded_as_resource_effects':0,'root_failure_ordinal':745,'root_origin_owned_by':'codex:/root','reviewer_new_failure_ordinal':746,'reviewer_failure_origin_ref':pin(OUT/'failure-origin.746.json'),'evidence_checks_ref':checkref,'input_intake_ref':inputref,'business_state_ref':observationref,'verified_checks':len(checks),'unique_input_count':len(unique),'input_drift':0,'cause':{'error':'JSON number is not losslessly representable by canonical JSON','first_failing_public_evidence':pin(TRIAL/'host-job.contract.json'),'field':'held_identity.creation_time_100ns','original_decimal':str(number),'canonical_binary64_decimal':'134359521876434320','precision_delta':'1','probe_contains_same_unsafe_integer':True,'source_chain':['execute.go:451 readGO','execute.go:206 verifyGOEvidence','execute.go:234 readPinnedObject(OuterJobContract)','execute.go:217 domain.Decode','internal/domain/contracts.go:35-52 canonical plus rational equality rejection'],'verification_method':'Pinned actual input, exact observed stderr, Source control-flow and pure numeric proof; no Go/native reproduction was executed.'},'failure_position':{'before_ExecuteClaimedAt':True,'before_RunAdmitted':True,'basis':'Source early-return ordering plus actual PREPARED dispatch with empty worker/identity; private state was not inspected.'},'state':{'actual_parent_pid':life['actual_parent_pid'],'GO_sent':True,'once_consumed':True,'clock_reset_permitted':False,'admit_native_exit':0,'execute_native_exit':1,'native_timeout':False,'owned_jobs_closed':2,'duplicate_handles_closed':True,'coordinator_guard_groups_closed':7,'coordinator_guard_entries_closed':80,'wrapper_guard_entries_closed':6,'current_Run_status':'QUEUED','current_qualification_Task_status':'RUNNING','dispatch_state':'PREPARED','dispatch_worker':'','C7_started':False},'runtime_qualification':False,'formal_acceptance':False,'formal_acceptance_count':0,'new_execution_grant_issued':False,'reviewer_candidate_native_provider_calls':0,'reviewer_SQL_mode':'mode=ro; PRAGMA query_only=ON; whitelisted business fields only','private_state_lease_token_vault_read':False,'Source_Main_canonical_trial_artifact_writes':0,'limitations':['The lifecycle null provider total remains null. Zero recorded model effects is a scoped database observation, not an independent network request count.','Business Run/Task are still admitted/active despite process cleanup; no reconciliation, retry, once reset or clock reset was performed.','Original cleanup records were reviewed; no new OS handle probe was run.','The new reviewer path-guess failure 746 is distinct from Root trial failure745 and has its own original observation record.'],'stopped':True}
ref=put('review.json',report)
print(json.dumps({'review_ref':ref,'checks':len(checks),'inputs':len(unique),'provider_requests':None,'model_effects_recorded':0,'new_reviewer_failure':746},ensure_ascii=True))

