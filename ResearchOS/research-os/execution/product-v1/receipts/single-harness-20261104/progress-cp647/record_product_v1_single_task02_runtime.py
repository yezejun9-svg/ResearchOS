import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp647'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==646 and len(cp['failure_counters'])==2547 and not OUT.exists()
flow=HERE/'product-v1-single-task-中文-run-02';outer=CONTROL/'runs/product-v1-single-task-flow-02/RESULT.json';r=read(outer);v=read(flow/'receipts/result.json');task=v['task'];caps=read(flow/'receipts/capabilities-immediately-before-submit.json');events=read(flow/'receipts/events.json')
assert r['status']=='CHILD_NONZERO_STOPPED' and r['root_exit_code']==2 and r['job_total_processes']==59 and r['stop_proved'] and r['job_active_zero'] and r['terminate_job_attempts']==0 and not r['errors'] and not r['input_drift']
assert v['actual_dom_submit_attempts']==1 and v['request_id']=='15a8196b-9109-4633-a851-76e2d51aaf87' and v['close']['app_close_resolved']
assert task['status']=='FAILED' and task['terminal'] and task['failure']['code']=='HARNESS_UNAVAILABLE' and task['failure']['retryable'] is False and task['result']['assistant_text']=='' and task['result']['cli_thread_id'] is None
assert task['task_ref']==v['task_ref'] and task['run']==v['run_ref'] and task['request_id']==v['request_id']
assert caps['authentication']['state']=='LOGGED_IN' and caps['authentication']['kind']=='chatgpt'
phrase='windows unelevated restricted-token sandbox cannot enforce split filesystem read restrictions directly; refusing to run unsandboxed'
assert sum(phrase in (e['payload'].get('text') or '') for e in events)==2
post=HERE/'product-v1-build07-post-single-task02-root-readback.json';assert sha(post)=='23b1b6cfa67dc4781d69bde59fccf00a7f96f170b2d81c812e8cdde01f6adbbf';pv=read(post);assert pv['listed_files']==134 and not pv['mismatches'] and not pv['unlisted_paths']
review=BASE/'single-task-flow-02/independent-runtime-review/REVIEW.json';assert sha(review)=='b7d036f40b82822093649359238b3e98f50e1b46e7e0709f97793528acfd228a';rv=read(review);assert rv['decision']=='VERIFIED_ACTUAL_SINGLE_TASK_RESOURCE_BLOCKED_NO_REPLAY' and rv['formal_increment']==0
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
now=datetime.now(timezone.utc).isoformat();old=list(cp['failure_counters']);known={e.get('origin_key') for e in old}
for e in rv.get('diagnostic_events',[]):
 assert e.get('origin_key') and e.get('classification')
 if e['origin_key'] not in known:cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**e});known.add(e['origin_key'])
assert cp['failure_counters'][:len(old)]==old
progress=dict(checkpoint_revision=647,at=now,status='ACTUAL_SINGLE_TASK_FAILED_CLOSED_WINDOWS_UNELEVATED_SPLIT_READ_UNSUPPORTED',main_head=cp['current_Main_HEAD'],consumed_scope='product-v1-single-task-flow-02',automatic_retry=0,
 actual=dict(dom_submit_attempts=1,request_id=v['request_id'],task_ref=v['task_ref'],run_ref=v['run_ref'],task_status='FAILED',failure_code='HARNESS_UNAVAILABLE',retryable=False,assistant_text_empty=True,cli_thread_id=None,authentication_gate=dict(state='LOGGED_IN',kind='chatgpt'),native_harness_invocations=1,model_inference='NOT_CONFIRMED_SESSION_START_FAILED',internal_model_api_calls='NOT_MEASURED',fixture_hashes_unchanged='INDEPENDENT_READONLY_SUPPLEMENTAL_CHECK_RUNNER_SUCCESS_STAGE_NOT_REACHED',original_job_processes=59,original_job_stop_proved=True,forced_termination=False,app_close_resolved=True),
 resource_blocker=dict(harness='codex',version='0.166.0',mode='unelevated',profile='codex-workspace-read-v1',error=phrase,policy='Keep root deny/minimal read/source read and fail-closed behavior; no --dangerous, sandbox removal, API fallback or old Task replay.',construction_record_only_not_product_admission_implementation=True),
 postbundle=dict(listed_files=134,mismatches=[],unlisted_paths=[]),old_protected_changes_preserved=True,source_pins_in_actual_scope=47,
 authorization_scope='Parent confirmed necessary existing-account test uses only new non-sensitive fixtures/fixed content; no real user project, credentials or extra personal data as task inputs. This failed call retained; no extra model run authorized by this checkpoint.',
 real_model_requests=1,real_model_requests_unit='ONE_HOST_TASK_AND_NATIVE_HARNESS_INVOCATION_NOT_CONFIRMED_LLM_INFERENCE',product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Do not replay original request/Task/Run or reset consumed one-Harness budget. Continue one-file Native conversation wrapper fix under new isolated source lease. Windows resource branch only prepares/reviews no-model MXC availability echo probe using existing resources; official explicit mxc fails closed, no admin setup/accounts/firewall/savedconfig changes. Current public OS build26200.9711 meets documented minimum but does not prove MXC. Further split-read enforcement/context minimization and any new actual task need separately reviewed concrete scopes. No product completion/READY claim.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old);s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next']);s.setdefault('runtime_evidence',[]).append(dict(kind='ACTUAL_SINGLE_TASK_RESOURCE_FAILED_CLOSED_ONE_INVOCATION_NO_CONFIRMED_INFERENCE',source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False));s.setdefault('resource_blockers',[]).append(progress['resource_blocker']);put(sf,s)
cp.update(revision=647,expected_previous_revision=646,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0);assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp647.new');assert not t.exists();t.write_bytes(('# Current resume CP647 — ACTUAL TASK FAILED CLOSED ON WINDOWS UNELEVATED SPLIT-READ PROFILE\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. One realHostTask/Run/Harness invocation;ChatGPTgate passed;Native session start refused unsupported sandbox, no confirmed inference.59procJobzero/no force,fixture unchanged/134bundle intact. Preserve original identities/budget/history; no replay/unsafe fallback. Continue UIwrapper source and prepare only local no-model MXC availability check; all formal/V1 acceptance remains0.\n\n').encode('utf8')+old);os.replace(t,hf);(OUT/'record_product_v1_single_task02_runtime.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
