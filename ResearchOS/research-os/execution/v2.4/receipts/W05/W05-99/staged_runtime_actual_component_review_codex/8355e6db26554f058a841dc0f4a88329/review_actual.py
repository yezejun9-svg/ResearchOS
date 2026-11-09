"""Independent actual-component review. Reads public pinned receipts; no candidate import or native call."""
import hashlib,json,math
from pathlib import Path
OUT=Path(__file__).resolve().parent
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/staged-runtime-prepare-root-59ef355458e14c0082ae8f82d98")
ROOT=Path('D:/作品集/ResearchOS/research-os')
inputs=[];checks=[]
def pin(path):
 raw=Path(path).read_bytes();return {'path':str(Path(path)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(ref):
 raw=Path(ref['path']).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==ref['sha256'] and len(raw)==ref['bytes'],'input pin drift '+ref['path']
 inputs.append(ref);return raw
def obj(ref):return json.loads(read(ref))
def local(name):return obj(pin(BASE/name))
def check(name,passed):
 checks.append({'check':name,'passed':bool(passed)})
 assert passed,name
def put(name,value):
 with (OUT/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(OUT/name)
def gh(value):return 'sha256:'+hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
expected={'bootstrap.result.json':('9c44d044d1c1d5ef988c043bb36209561330bbc1694d71d64ec2eb4a69a5b410',3370),'runtime.prepare.actual.json':('1a40ef5d138dad5c43ff39c250ecf941e115b9212afbdd14f6f785a5bc7f12e2',1205),'prepare.finalized.actual.json':('089983062632d85e47f49012d1842dbc72d1b86ba843354dec4aa07c61e6f202',849),'bootstrap.lifecycle.actual.json':('fd1d6de03e4445721a522042f9ff055a0f368119a14558af941af0dd0d72733d',6471),'continue_existing_cli.actual_owned.py':('c9f6e743c8f861cd6c2bf730e887481e1ec3e0dcc2ac8a4b2b9b7222eec07a68',15973)}
loaded={name:read({'path':str(BASE/name),'sha256':sha,'bytes':size}) for name,(sha,size) in expected.items()}
b=json.loads(loaded['bootstrap.result.json']);r=json.loads(loaded['runtime.prepare.actual.json']);p=json.loads(loaded['prepare.finalized.actual.json']);l=json.loads(loaded['bootstrap.lifecycle.actual.json'])
seed=local('seed.public.actual.json');intent=local('continuation.intent.json');guard=local('bootstrap.source-guard.cleanup.actual.json')
check('five_declared_original_pins',len(loaded)==5)
check('source_guard_complete',guard['closed'] is True and guard['retained_handles_count']==0 and guard['errors']==[] and guard['verification']=='PASSED' and guard['share_mode']=='FILE_SHARE_READ_ONLY' and len(guard['entries'])==17 and all(all(e[k] is True for k in ('verified','final_path_match','closed')) for e in guard['entries']))
for ref in intent['source_refs']:read(ref)
for e in guard['entries']:
 ref={k:e[k] for k in ('path','sha256','bytes')};read(ref)
check('guard_bound_to_intent_exact_inputs',{(str(Path(e['path'])),e['sha256'],e['bytes']) for e in guard['entries']}=={(str(Path(e['path'])),e['sha256'],e['bytes']) for e in intent['source_refs']})
for ref in intent['canonical_refs']:read(ref)
check('canonical_original_pins_still_match',len(intent['canonical_refs'])==4)
initial=obj(b['initial_cli_init_component_review_ref'])
check('prior_init_component_review',initial['decision']=='PASS_COMPONENT_EVIDENCE_WITH_GOAL_BLOCKED' and initial['failed_checks']==[] and initial['project_id']==b['project_id'] and initial['source_author']=='codex:/root')
initialh=obj(initial['source_handoff_ref']);initialpart=obj(initialh['partial_bootstrap_snapshot_ref']);oldbinding=obj(initialpart['workspace_binding_ref'])
check('same_initialized_workspace',initialpart['project_id']==b['project_id'] and initialpart['config']['workspace_ref']==b['workspace_ref'] and all(Path(initialpart[k])==Path(b[k]) for k in ('data_root','workspace','discovery_file','cli_config_file')))
initinvoke=obj(b['cli_init_ref'])
check('prior_actual_CLI_init_native_zero',initinvoke['result']['actual_exit']==0)
check('bootstrap_continuation_scope',b['stage']=='BOOTSTRAP_ONLY' and b['actor_id']=='codex:/root' and b['provider_requests']==0 and b['qualification'] is None and b['formal_acceptance'] is None and l['schema']=='researchos.actual-cli-staged-continuation-lifecycle.v1' and l['all_owned_jobs_cleanup_confirmed'] is True and l['error'] is None and l['provider_requests']==0)
check('two_continuation_plus_two_prepare_closures',len(l['jobs'])==2 and {j['label'] for j in l['jobs']}=={'normal-host','cli-goal'} and len(l['prepare_closed_refs'])==2)
closures={j['label']:j for j in l['jobs']}
for ref in l['prepare_closed_refs']:
 c=obj(ref);closures[c['label']]=c
check('exact_four_owned_jobs',set(closures)=={'runtime-prepare','normal-host','cli-goal','finalize-prepare'})
invocations={};native_results={}
for label,c in closures.items():
 individual=local(label+'.closure.actual.json');check(label+'_lifecycle_same_original',individual==c)
 inv=obj(c['invocation_ref']);before=obj(c['before_resume_ref']);res=inv['result'];identity=c['identity'];proof=c['actual_fresh_cleanup'];j=res['job_cleanup'];w=c['watchdog_cleanup'];dup=c['duplicate_producer_cleanup']
 expected_exit=3758097672 if label=='normal-host' else 0
 check(label+'_native_result',res['actual_exit']==inv['actual_native_exit']==expected_exit and res['error'] is None and res['timed_out'] is False and res['resumed'] is True and res['owned_child_pid']==identity['runner_pid'] and res['creation_time_100ns']==identity['creation_time_100ns'])
 check(label+'_native_job_closed',j['errors']==[] and type(j['active_processes_last_observed']) is int and j['active_processes_last_observed']==0 and all(j[k] is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')))
 check(label+'_original_before_resume',before['identity']==identity and before['assigned_before_resume'] is True and before['resumed'] is False and all(identity[k] is True for k in ('captured_before_resume','held_job_handle','held_primary_handle')) and identity['owner_pid']==l['actual_parent_pid'])
 start,end=c['observed_monotonic_start'],c['observed_monotonic_end']
 check(label+'_fresh_original_identity_proof',proof['schema']=='researchos.held-job-cleanup-observation.v1' and 0<=end-start<=2 and start<=proof['observed_monotonic']<=end and proof['errors']==[] and type(proof['active_processes']) is int and proof['active_processes']==0 and proof['primary_exit_code']==expected_exit and all(proof[k] is True for k in ('captured_before_resume','held_job_handle','held_primary_handle','primary_exit_confirmed','pid_match','creation_match')) and all(type(proof[k]) is type(identity[k]) and proof[k]==identity[k] for k in ('run_uuid','owner_pid','runner_pid','creation_time_100ns','job_binding_id')))
 check(label+'_duplicate_watchdog_producer_closed',c['closed'] is True and w['duplicate_handle_closed'] is True and w['errors']==[] and w['deadline_monotonic']==before['actual_deadline_monotonic'] and all(dup[k] is True for k in ('job_handle_closed','primary_handle_closed','closed')) and dup['errors']==[] and dup['run_uuid']==identity['run_uuid'] and dup['owner_pid']==identity['owner_pid'])
 read(inv['stdout_ref']);read(inv['stderr_ref']);invocations[label]=inv;native_results[label]={'native_exit':expected_exit,'runner_pid':identity['runner_pid'],'creation_time_100ns':identity['creation_time_100ns'],'original_fresh_cleanup_verified':True,'all_handles_closed':True}
check('normal_host_planned_teardown',l['host_stop']=={'planned_pre_trial_host_teardown':True,'requested_exit_code':3758097672,'actual_TerminateJobObject_return':True})
check('prepare_calls_successful_exact_phases',invocations['runtime-prepare']['argv'][1:3]==['-phase','prepare-runtime'] and invocations['finalize-prepare']['argv'][1:3]==['-phase','finalize-prepare'])
for label,receipt_name in (('runtime-prepare','runtime.prepare.actual.json'),('finalize-prepare','prepare.finalized.actual.json')):
 argv=invocations[label]['argv'];options=dict(zip(argv[1::2],argv[2::2]))
 check(label+'_exact_semantic_arguments',len(options)*2+1==len(argv) and Path(options['-seed'])==BASE/'seed.public.actual.json' and Path(options['-receipt'])==BASE/receipt_name and Path(invocations[label]['cwd'])==ROOT and (label!='finalize-prepare' or options['-draft-goal-id']==b['goal_id']))
check('same_preparation_binary',Path(invocations['runtime-prepare']['argv'][0])==Path(invocations['finalize-prepare']['argv'][0]) and pin(invocations['runtime-prepare']['argv'][0])['sha256']=='117638d8215a20516693dc1b6380723e3d968c17220c918f3051f16b43560099')
check('pre_draft_seed_and_final_goal',seed['draft_goal_id']=='' and p['draft_goal_id']==b['goal_id'] and r['source_seed_sha256']==p['source_seed_sha256']==pin(BASE/'seed.public.actual.json')['sha256'])
shared=('project_id','qualification_goal_id','qualification_task_id','runtime_id','profile_artifact_id','profile_hash','model_ref','host_instance_id')
check('prepared_shared_identity_tuple',all(type(r[k]) is str and r[k] and r[k]==p[k] for k in shared) and p['project_id']==b['project_id'] and p['qualification_task_id']==b['qualification_task_id'])
check('actual_preparation_receipt_status',r['schema']==p['schema']=='researchos.trusted-qualification-host.v1' and r['phase']=='prepare-runtime' and r['status']=='RUNTIME_READY' and p['phase']=='finalize-prepare' and p['status']=='PREPARED' and r['provider_requests']==p['provider_requests']==0)
stdout=read(invocations['cli-goal']['stdout_ref']).decode('utf-8');rows=[json.loads(line) for line in stdout.splitlines()]
check('one_typed_goal_reply',len(rows)==1)
reply=rows[0];op=reply['operations'][0];snap=op['result']['snapshot']
check('real_CLI_draft_goal_creation',reply['status']=='GOAL_DRAFT_CREATED' and reply['exit_code']==0 and reply['requests_sent']==['goal.start'] and reply['execution']=={'independent_acceptance':'NOT_EVALUATED','status':'NOT_STARTED'} and len(reply['operations'])==1 and op['status']=='COMPLETED' and op['method']=='goal.start' and op['exit_code']==0 and op['result']['goal_id']==b['goal_id'] and op['result']['goal_status']=='DRAFT' and snap['active_run_id'] is None)
beforeconfig=local('cli-config.before-goal.raw');afterconfig=local('cli-config.after-goal.raw')
check('config_actual_transition',beforeconfig['session_id']=='' and afterconfig['project_id']==b['project_id'] and afterconfig['session_id']==b['typed_draft_context']['session_id']==reply['session_id'] and afterconfig['session_revision']==reply['saved_context']['session_revision']==snap['revision'] and afterconfig['workspace_ref']==b['workspace_ref'])
witness=read(b['workspace_witness_ref'])
check('workspace_witness_and_seed',witness.decode().strip()==b['workspace_witness'] and seed['witness_sha256']==b['workspace_witness_ref']['sha256'] and seed['witness_bytes']==len(witness) and Path(seed['workspace_dir'])==Path(b['workspace']))
observed=json.loads((OUT/'actual-business-observations.json').read_bytes());one,two=observed['first'],observed['second'];objects=one['objects'];counts=two['counts']
check('reviewer_database_ro_query_only',one['query_only']==two['query_only']==1 and observed['open_mode']=='mode=ro')
check('current_actual_business_counts',counts.get('Task',0)==1 and counts.get('Goal',0)==2 and all(counts.get(k,0)==0 for k in ('Run','BudgetLedgerEntry','resource_effects','runtime_qualification_runs','Acceptance','RuntimeQualification')) and counts['runtime_qualification_plans']==1)
task=objects['Task'][0];ordinary=next(g for g in objects['Goal'] if g['id']==b['goal_id']);qualification=next(g for g in objects['Goal'] if g['id']==p['qualification_goal_id'])
check('current_ordinary_DRAFT_without_tasks',ordinary['status']=='DRAFT' and ordinary['task_ids']==[] and ordinary['acceptance_id'] is None and all(t['goal_id']!=ordinary['id'] for t in objects['Task']))
check('current_unique_qualification_DRAFT',len(objects['Task'])==1 and task['id']==p['qualification_task_id'] and task['status']=='DRAFT' and task['task_type']=='runtime_qualification' and task['active_run_id'] is None and task['acceptance_id'] is None and task['goal_id']==qualification['id']!=ordinary['id'] and qualification['task_ids']==[task['id']])
artifact=next(a for a in objects['Artifact'] if a['id']==p['profile_artifact_id']);profile=two['profile'];runtime=objects['RuntimeRegistration'][0];binding=two['bindings'][0];workspace=two['workspaces'][0];session=two['sessions'][0]
entity={'entity_type':'Artifact','id':artifact['id'],'revision':artifact['revision'],'content_hash':artifact['content_hash']}
check('current_profile_sealed_bytes',artifact['sealed_at'] is not None and artifact['validity']=='CURRENT' and artifact['byte_size']==two['profile_bytes'] and artifact['content_hash']==p['profile_hash']=='sha256:'+two['profile_content_sha256'] and profile['runtime_id']==runtime['id']==p['runtime_id'])
technical=gh([runtime[k] for k in ('adapter','adapter_revision','capabilities','platform','measurement_mode','credential_ref')])
check('current_formal_runtime_binding',len(objects['RuntimeRegistration'])==len(two['bindings'])==1 and binding['project']==runtime['project_id']==b['project_id'] and binding['runtime']==runtime['id'] and json.loads(binding['profile_ref'])==entity and binding['profile_hash']==gh(entity) and binding['technical_hash']==profile['technical_hash']==technical and task['input_refs']==[entity])
check('current_unqualified_registered_runtime',runtime['status']=='REGISTERED' and runtime['qualification_ids']==[])
check('current_unique_session_goal_workspace_model',len(two['sessions'])==1 and session['id']==reply['session_id'] and session['project_id']==b['project_id'] and session['goal_id']==ordinary['id'] and session['task_id'] is None and session['run_id'] is None and session['workspace_ref']==b['workspace_ref'] and session['model_config_ref']==p['model_ref']==profile['model_config']['ref'] and session['revision']==reply['saved_context']['session_revision'] and session['writer_epoch']==reply['saved_context']['writer_epoch'])
check('current_durable_workspace_binding_owner',len(two['workspaces'])==1 and workspace==oldbinding['actual_binding'] and workspace['status']=='ACTIVE' and workspace['project_id']==b['project_id'] and workspace['authorized_workspace_ref']==b['workspace_ref'] and Path(workspace['real_path'])==Path(b['workspace']) and workspace['principal_id']==binding['owner'])
check('current_model_config_hash',gh(profile['model_config'])==profile['model_qualification']['model_config_hash'])
unique={}
for ref in inputs:unique[(str(Path(ref['path'])),ref['sha256'],ref['bytes'])]=ref
for ref in unique.values():
 actual=pin(ref['path']);assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
checks_ref=put('evidence-checks.json',{'checks':checks,'passed':len(checks),'failed':0,'input_pin_reads':len(inputs),'unique_inputs':len(unique),'input_drift':0})
input_ref=put('input-intake.json',{'refs':list(unique.values()),'input_drift':0})
review=put('review.json',{'schema':'researchos.staged-runtime-actual-component-independent-review.v1','actor_id':'codex:/root/command_queue_impl','source_author':'codex:/root','decision':'PASS_ACTUAL_COMPONENT_NO_PROVIDER','source_ref':pin(BASE/'continue_existing_cli.actual_owned.py'),'bootstrap_ref':pin(BASE/'bootstrap.result.json'),'runtime_prepare_ref':pin(BASE/'runtime.prepare.actual.json'),'prepare_ref':pin(BASE/'prepare.finalized.actual.json'),'lifecycle_ref':pin(BASE/'bootstrap.lifecycle.actual.json'),'source_guard_cleanup_ref':pin(BASE/'bootstrap.source-guard.cleanup.actual.json'),'evidence_checks_ref':checks_ref,'input_intake_ref':input_ref,'business_observations_ref':pin(OUT/'actual-business-observations.json'),'verified_checks':len(checks),'unique_input_count':len(unique),'input_drift':0,'project_id':b['project_id'],'ordinary_goal_id':b['goal_id'],'qualification_task_id':p['qualification_task_id'],'runtime_id':p['runtime_id'],'actual_parent_pid':l['actual_parent_pid'],'actual_owned_jobs':native_results,'native_jobs_all_confirmed_closed':True,'source_guard_entries':17,'current_counts':{'Goal':2,'Task':1,'ordinary_goal_tasks':0,'Run':0,'BudgetLedgerEntry':0,'resource_effects':0,'runtime_qualification_runs':0,'runtime_qualification_plans':1,'Acceptance':0},'profile_content_hash':p['profile_hash'],'profile_artifact_ref_hash':binding['profile_hash'],'technical_hash':technical,'provider_requests':0,'runtime_qualification':False,'formal_acceptance':False,'formal_acceptance_count':0,'execution_grant_issued':False,'reviewer_native_provider_calls':0,'reviewer_SQL_mode':'mode=ro; PRAGMA query_only=ON','private_host_state_credential_token_vault_read':False,'Main_canonical_writes':0,'new_tool_failures':0,'limitations':['Cleanup freshness is verified at original producer timestamps, not by reopening dead processes.','Provider-free component evidence uses no-admission Source flow, typed CLI result and current zero Run/effect/ledger state; this is not a provider network trace.','Coordinator v4 Source is not independently reviewed here. Its strict finalize argv order differs from these semantically valid original arguments and was reported separately to Root.','Root outer/Python exits are parent-provided original outcome; per-job native exits and cleanup are independently read.'],'stopped':True})
print(json.dumps({'review_ref':review,'checks':len(checks),'unique_inputs':len(unique),'drift':0,'decision':'PASS_ACTUAL_COMPONENT_NO_PROVIDER'},ensure_ascii=True))

