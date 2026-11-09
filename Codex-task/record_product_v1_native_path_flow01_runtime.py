import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104'
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/progress-cp637'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==636 and len(cp['failure_counters'])==2533 and not OUT.exists()
inner=read(HERE/'product-v1-native-path-entry-run-01-registration/real-flow.scope.json')
flow=Path(inner['run_root']);outer=CONTROL/'runs/product-v1-native-path-entry-flow-01/RESULT.json';r=read(outer)
v=read(flow/'receipts/result.json');n=read(flow/'receipts/native-folder-automation.json');helper=json.loads(n['stdout'])
assert r['status']=='CHILD_NONZERO_STOPPED' and r['root_exit_code']==2 and r['stop_proved'] and r['job_active_zero'] and not r['errors'] and not r['input_drift']
assert r['terminate_job_attempts']==0 and r['terminate_original_root_attempts']==0 and r['job_total_processes']==41
assert n['exit']==2 and helper['status']=='BLOCKED' and helper['reason']=='BUTTON_DIALOG_NOT_FOREGROUND_NO_CLICK'
assert helper['phase']=='INVALID_PATH' and not helper['invalid_ok_attempted'] and not helper['valid_ok_attempted'] and not helper['outcome_uncertain']
expected=str(flow/('invalid-nonexistent-'+inner['scope_nonce']));assert helper['invalid_input']['path']==expected
assert v['close']['app_close_resolved'] and v['actual_dom_submit_attempts']==0 and v['model_outcome']=='NOT_RUN_ZERO_BUDGET'
assert not [e for e in helper['history'] if e['event'].startswith('BUTTON_QUEUE')]
post=HERE/'product-v1-build07-post-native-flow01-root-readback.json'
assert sha(post)=='ff698e7a1d1b5261d778890ac9073043779cc70013e013b4cb4073b827c0a793'
pv=read(post);assert pv['listed_files']==134 and not pv['mismatches'] and not pv['unlisted_paths']
review=ROOT/'execution/product-v1/receipts/single-harness-20261104/native-path-entry-flow-01/independent-runtime-review/actual-review-report02.json'
assert sha(review)=='a5b85da70289560f2f097463a3e34355925313a76cb22a37e90155c47f6fd607';rv=read(review)
assert rv['decision']=='VERIFIED_BLOCKED_REAL_NATIVE_INPUT_ONLY' and rv['formal_increment']==0
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
now=datetime.now(timezone.utc).isoformat();original=list(cp['failure_counters']);known={e.get('origin_key') for e in original}
events=list(rv.get('diagnostic_events',[]))+[dict(origin_key='single-task-controller-author:post-freeze-source-change-before-review',classification='CANDIDATE_FREEZE_PROVENANCE_GAP',detail='C-only unreviewed one-task author modified revision01 runner/FROZEN after declaring freeze, before any review or execution. Original runner cf26312f9b3fb9f3e33b414a3afac2bbb5fa2f255fbcc0922ab137a2f32e6d49 and original FROZEN bytes were not found and were not reconstructed. Current01 preserved, current bytes explicitly refrozen as new02 with REVISION.md and current01-FROZEN copy. No model/App/task/D write occurred. New independent source review and Native prerequisite remain mandatory; old declaration is not approved evidence.')]
for e in events:
 assert e.get('origin_key') and e.get('classification')
 if e['origin_key'] not in known:cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**e});known.add(e['origin_key'])
assert cp['failure_counters'][:len(original)]==original
progress=dict(checkpoint_revision=637,at=now,status='REAL_NATIVE_UNICODE_INPUT_OBSERVED_PRE_OK_FOREGROUND_GUARD_BLOCKED',main_head=cp['current_Main_HEAD'],consumed_scope='product-v1-native-path-entry-flow-01',automatic_retry=0,
 actual=dict(helper_phase=helper['phase'],helper_reason=helper['reason'],unicode_input_readback_exact=True,invalid_ok_attempted=False,valid_ok_attempted=False,button_queue_events=0,outcome_uncertain=False,warning='NOT_REACHED',main_workspace_authorization='NOT_ESTABLISHED_BY_THIS_FLOW',native_cancel=helper['cleanup'],app_close_resolved=True,original_job_stop_proved=True,job_processes=41,forced_termination=False),
 diagnostic_limits='Runner generic UTF8/JSON error is an exit2 classification defect: original5451B helper stdout is complete valid UTF8 JSON. PendingUNKNOWN runner field was stale; helper proves known noOK. Actual01 lacks thread-active/foreground numeric snapshot and does not establish product foreground failure.',
 postbundle=dict(listed_files=134,mismatches=[],unlisted_paths=[]),independent_review_sha256=sha(review),old_protected_changes_preserved=True,
 real_model_requests=0,product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Keep consumed01 unchanged. Implement/review only C controller03 semantic fix: actual same-Core dialog thread GetGUIThreadInfo active/focus checks, no activation/AttachThreadInput/keyboard, plus strict nonzero helper JSON known-state diagnostics. Root then registers fresh zero-model flow02; no model scope until successful Native prerequisite independently verified. One-task candidate stays NOT_RUN/BLOCKED.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='REAL_NATIVE_UNICODE_INPUT_ONLY_PRE_OK_GUARD_BLOCKED',source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False));put(sf,s)
cp.update(revision=637,expected_previous_revision=636,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);tmp=hf.with_name(hf.name+'.cp637.new');assert not tmp.exists()
tmp.write_bytes(('# Current resume CP637 — REAL UNICODE NATIVE INPUT OBSERVED; PRE-OK GUARD BLOCKED\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Consumedflow01: Unicode input exact, no OK/warning/grant/task/model; normal appclose/original Jobzero/no force. 134bundlefiles intact. Independently verified blocked result; fix C active-thread semantics and parser in new revision, never replay01. No product completion/acceptance.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(OUT/'record_product_v1_native_path_flow01_runtime.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
