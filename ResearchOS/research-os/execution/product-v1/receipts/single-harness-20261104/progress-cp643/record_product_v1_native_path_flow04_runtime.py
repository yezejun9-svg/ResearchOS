import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp643'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==642 and len(cp['failure_counters'])==2544 and not OUT.exists()
inner=read(HERE/'product-v1-native-path-entry-run-04-registration/real-flow.scope.json');flow=Path(inner['run_root'])
outer=CONTROL/'runs/product-v1-native-path-entry-flow-04/RESULT.json';r=read(outer);result=flow/'receipts/result.json';v=read(result);h=json.loads(read(flow/'receipts/native-folder-automation.json')['stdout'])
assert sha(result)=='0a81b047fa46464ee3f97f0613ba44b4f885a77b8f9a865fcb0ed6ee77535548' and sha(outer)=='16dfca2a599409e15fa0099ddb61f660292a061d7010430320b2696cacf43d72'
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['root_exit_code']==0 and r['stop_proved'] and r['job_active_zero'] and not r['errors'] and not r['input_drift']
assert r['terminate_job_attempts']==r['terminate_original_root_attempts']==0 and r['job_total_processes']==57
assert v['status']=='REAL_NATIVE_PATH_ENTRY_AND_PROJECT_BINDING_OBSERVED_NOT_PRODUCT_ACCEPTED' and v['native_workspace_authorization']=='REAL_MAIN_ACTIVE_PROJECT_WORKSPACE_BINDING_OBSERVED'
assert v['close']['app_close_resolved'] and v['actual_dom_submit_attempts']==0 and v['model_outcome']=='NOT_RUN_ZERO_BUDGET'
assert [e['evidence']['purpose'] for e in h['history'] if e['event']=='BUTTON_POST_ACCEPTED_EFFECT_UNKNOWN']==['INVALID_OK','WARNING_DISMISS','VALID_OK']
assert h['invalid_kept_chooser_open'] and h['valid_ok_attempted'] and h['clicked_ok'] and not h['outcome_uncertain']
observation=read(flow/'receipts/main-current-project-observation.json');assert observation['context']['project_id']==v['project_id']
binding=observation['listed']['result']['items'][0];assert binding['status']=='ACTIVE' and binding['project_id']==v['project_id'] and binding['display_path']==str(flow/'workspace')
assert read(flow/'receipts/main-context-after-open.json')['context']['project_id']==v['project_id']
post=HERE/'product-v1-build07-post-native-flow04-root-readback.json';assert sha(post)=='9585660b85246cc9dbf92dc024acd40d00e4a90d18cb3876b59ad17891324523';pv=read(post);assert pv['listed_files']==134 and not pv['mismatches'] and not pv['unlisted_paths']
review=BASE/'native-path-entry-flow-04/independent-runtime-review/actual-review-report.json';assert sha(review)=='1cec87e65f97025a88122b33e5f6d7f7c4e84652e0d39703727645ee5408304f';rv=read(review)
assert rv['decision']=='VERIFIED_REAL_NATIVE_PATH_ENTRY_AND_MAIN_BINDING_FUNCTIONAL_OBSERVATION_ONLY' and rv['formal_increment']==0 and not rv.get('diagnostic_events')
for ref,digest in read(HERE/'product-v1-native-path-entry-integration-plan.json')['protected_sha256'].items():
 p=ROOT/ref;assert (sha(p) if p.is_file() else 'ABSENT_BEFORE')==digest
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
for name,p in [('outer.RESULT.json',outer),('postbundle.json',post),('independent-review.json',review)]:(OUT/name).write_bytes(p.read_bytes())
for dirname in ['receipts','screenshots']:
 dest=OUT/dirname;dest.mkdir()
 for p in (flow/dirname).iterdir():
  if p.is_file() and p.name!='launch-input.json':
   assert p.suffix.lower() not in ['.db','.sqlite','.exe','.dll'] and p.stat().st_size<16*1024*1024
   (dest/p.name).write_bytes(p.read_bytes())
now=datetime.now(timezone.utc).isoformat()
progress=dict(checkpoint_revision=643,at=now,status='REAL_NATIVE_UNICODE_INVALID_VALID_PATH_AND_MAIN_ACTIVE_BINDING_VERIFIED',main_head=cp['current_Main_HEAD'],consumed_scope='product-v1-native-path-entry-flow-04',automatic_retry=0,
 actual=dict(unicode_input_readback_exact=True,owned_warning_verified=True,warning_dismiss_id=2,invalid_dialog_retained=True,valid_shell_confirmed=True,actual_main_project_id=v['project_id'],actual_active_workspace_ref=binding['authorized_workspace_ref'],public_display_path=binding['display_path'],private_real_path='NOT_EXPOSED_BY_PUBLIC_BRIDGE',same_project_workbench_opened=True,app_close_resolved=True,original_job_stop_proved=True,job_processes=57,forced_termination=False,task_and_capability_ready='NOT_CLAIMED_LOADING_IN_SCREENSHOT'),
 prerequisite=dict(runner_result_path=str(result),runner_result_sha256=sha(result),root_result_path=str(outer),root_result_sha256=sha(outer),independent_actual_review_path=str(review),independent_actual_review_sha256=sha(review),postbundle_sha256=sha(post)),
 postbundle=dict(listed_files=134,mismatches=[],unlisted_paths=[]),old_protected_changes_preserved=True,
 one_task='single-task04 incrementally SourceFixture-approved509372d819c522feb214ce35352d64d59fcf3c1def95bb68060736e86167095d; exact Native05 warning selector plus unchanged03 Task identities. Not registered/run. Root must archive/pin final04 source/review and bind above Native prerequisite to fresh one-use scope.',
 visual_followup='Real empty workbench screenshot suggests Native conversation wrapper/sticky composer overlap while data loading; C-only bounded layout proposal in progress. No source change registered for that yet.',
 real_model_requests=0,product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Archive/pin final single-task04 source/review. Register fresh one-use readonly task scope with exact successful Native runner+original f13+independent actual review and postbundle pins. Actual Host caps must be LOGGED_IN/chatgpt immediately before single normal DOM submit; UNKNOWN preserves original refs/no new ID/retry, exact Task/Run/events/canary+unchanged fixture and original Job stop required. One Harness invocation, internal LLM API calls NOT_MEASURED. Keep old failed scopes and pending layout proposal; no J01/J03 acceptance or completion claim.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old);s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='REAL_NATIVE_UNICODE_PATH_ENTRY_MAIN_ACTIVE_BINDING_FUNCTIONAL_OBSERVATION',source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False));put(sf,s)
cp.update(revision=643,expected_previous_revision=642,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);tmp=hf.with_name(hf.name+'.cp643.new');assert not tmp.exists();tmp.write_bytes(('# Current resume CP643 — REAL NATIVE UNICODE INVALID/VALID FLOW AND MAIN BINDING VERIFIED\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Actualflow04 succeeded, independent functional observation only;57processes originalJobzero/no force,134bundle intact. Model tasks still0, journeys0/13. Next source-approved04 new one-task scope/ChatGPT gate; preserve all consumed scopes/history/UNKNOWN.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(OUT/'record_product_v1_native_path_flow04_runtime.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
