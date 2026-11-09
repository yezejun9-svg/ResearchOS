import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp684'
CONTROL=HERE/'product-v1-owned-verification-20261104'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.cp684.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==683 and len(cp['failure_counters'])==2630 and not OUT.exists()
scope=CONTROL/'scopes/product-v1-native-synthetic-flow-01.json';assert sha(scope)=='181da91b8024cc2d222092950d16705945ed77b667259ba8f04297cd9da3045c'
run=HERE/'product-v1-native-synthetic-acceptance-中文-run-01';receipts=run/'receipts'
r=read(receipts/'result.json');task=read(receipts/'final-task.json');events=read(receipts/'events.json')
assert r['actual_dom_submit_attempts']==1 and r['task_ref']['task_id']==task['task_ref']['task_id']=='c9fc3e4dc1ea5d34a0ca003a983b43c6'
assert task['terminal'] and task['status']=='FAILED' and task['result'] is None and task['run']=={'run_id':'a46af22fb058915f9f7119b2d7d73f8f','epoch':'1'}
assert task['request_id']=='b8e0abb5-503d-4795-9a43-1d3772382315' and task['failure']['code']=='HARNESS_UNAVAILABLE'
assert {e['kind'] for e in events}=={'TASK_QUEUED','RUN_STARTED','TASK_TERMINAL'}
assert r['close']['attempted'] and not r['close']['app_close_resolved']
root_result=CONTROL/'runs/product-v1-native-synthetic-flow-01/RESULT.json'
observed=read(root_result) if root_result.exists() else dict(status='PENDING_ORIGINAL_JOB_RESULT',exec_session_id=31014)
now=datetime.now(timezone.utc).isoformat();OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
for name in ['result.json','final-task.json','events.json','sole-submit-intent.json','owned-core.json']:(OUT/name).write_bytes((receipts/name).read_bytes())
original=list(cp['failure_counters']);origin='native-synthetic-flow01:task-c9fc3e4dc1ea5d34a0ca003a983b43c6-preparation-failed'
assert not any(x.get('origin_key')==origin for x in original)
cp['failure_counters'].append(dict(at=now,attempts=1,counter_reset=False,origin_key=origin,classification='ACTUAL_SYNTHETIC_HOST_TASK_FAILED_PRE_MODEL_PRODUCT_REPORTED',detail='One actual fresh DOM submit committed authoritative Task/Run and QUEUED/STARTED/TERMINAL events. FAILED HARNESS_UNAVAILABLE says Native preparation failed before model launch; resultnull. No resubmit. Actual qualification private receipt and stop proof await original Job, so no specific Native policy finding or inference/cost claim yet.'))
assert cp['failure_counters'][:len(original)]==original
progress=dict(checkpoint_revision=684,at=now,status='ACTUAL_SINGLE_TASK_FAILED_PREPARATION_APP_CLOSE_UNCONFIRMED_JOB_PENDING',main_head=cp['current_Main_HEAD'],actual_scope=dict(scope_id='product-v1-native-synthetic-flow-01',scope_path=str(scope),scope_sha256=sha(scope),scope_consumed=True,replay_allowed=False,exec_session_id=31014,root_result_path=str(root_result),observed_root_result=observed,original_timeout_seconds=690),actual=dict(project_id=task['task_ref']['project_id'],request_id=task['request_id'],task_ref=task['task_ref'],run=task['run'],task_status=task['status'],task_revision=task['task_revision'],terminal=True,result=None,dom_submit_attempts=1,close=r['close'],event_kinds=[e['kind'] for e in events],native_qualification_processes='NOT_YET_INDEPENDENTLY_ESTABLISHED',model_delegation='PRODUCT_REPORTED_NONE_PREPARATION_FAILURE',specific_preparation_reason='PRIVATE_FIXED_RECEIPT_READ_AFTER_ORIGINAL_JOB_STOP_ONLY'),real_model_requests=2,real_model_requests_unit='LEGACY_FIELD_NOW_COUNTS_TWO_CONFIRMED_HOST_TASK_SUBMISSIONS; NOT_MODEL_INFERENCE_COUNT',prior_cp647_host_task_invocations=1,prior_cp647_inference='NOT_CONFIRMED',new_host_task_submissions=1,new_inference='NOT_CONFIRMED; PRODUCT_REPORTED_NO_MODEL_DELEGATION',product_journeys_accepted=0,product_journeys_required=13,legacy_formal_accepted=0,legacy_formal_required=42,historical_records=len(cp['failure_counters']),old_records_reset=False,implementation='Build13 verified135files/67pins/18oldprotected; C registrar02 reviewed+actualreadonlypreflight passed and registration archived; event UI/native selection/real task dispatch exercised. No successful model answer.',next='Wait/reconcile original f13 scope session31014 RESULT before any action; no replay or arbitrary PID/name kill. Preserve consumed Task and failed terminal evidence. After exact Job stop, read only separately authorized current Task/Run fixed synthetic qualification paths, independently diagnose preparation failure and app.close. Continue safe source fixes/fake tests without extra live/model attempts; adapt future integration tools to preserve confirmed HostTask total2 rather than old hardcoded1. No full completion claim.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';sr=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(sr)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='ACTUAL_SYNTHETIC_FLOW01_ONE_HOST_TASK_FAILED_PRE_MODEL_JOB_PENDING',source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False))
cp.update(revision=684,expected_previous_revision=683,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[],formal_increment=0)
assert cpf.read_bytes()==raw and sf.read_bytes()==sr;put(sf,s);put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp684.new');assert not t.exists();t.write_bytes(('# Current resume CP684 - ONE REAL TASK FAILED PREPARATION; ORIGINAL JOB PENDING\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. New scope consumed exactly1DOMsubmit; taskc9fc/run a46a/epoch1 terminalFAILED before model per product, no replay. App close unconfirmed; original f13 session31014/690s containment still authoritative until RESULT. Do not inspect private qualification capture before original Job stop. Legacy real_model_requests field now2confirmedHostTasks, not inference count; preserve old counters and all old scopes. Build13 verified; journeys0/13 and formal0/42.\n\n').encode('utf8')+old);os.replace(t,hf)
(OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=684,confirmed_host_tasks_total=2,new_dom_submit_attempts=1,task_status='FAILED',root_job_status=observed['status'],historical_records=len(cp['failure_counters']),replay_allowed=False)))
