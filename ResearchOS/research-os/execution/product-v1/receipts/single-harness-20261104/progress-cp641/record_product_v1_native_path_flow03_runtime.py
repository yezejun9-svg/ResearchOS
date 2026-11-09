import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp641'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==640 and len(cp['failure_counters'])==2542 and not OUT.exists()
inner=read(HERE/'product-v1-native-path-entry-run-03-registration/real-flow.scope.json');flow=Path(inner['run_root'])
outer=CONTROL/'runs/product-v1-native-path-entry-flow-03/RESULT.json';r=read(outer);v=read(flow/'receipts/result.json');h=json.loads(read(flow/'receipts/native-folder-automation.json')['stdout'])
assert r['status']=='CHILD_NONZERO_STOPPED' and r['root_exit_code']==2 and r['stop_proved'] and r['job_active_zero'] and not r['errors'] and not r['input_drift']
assert r['terminate_job_attempts']==r['terminate_original_root_attempts']==0 and r['job_total_processes']==41
assert h['phase']=='INVALID_PATH' and h['reason']=='WARNING_IDOK_NOT_UNIQUE_NO_POST' and h['invalid_ok_attempted'] and not h['valid_ok_attempted'] and not h['outcome_uncertain']
w=h['invalid_warning'];assert w['observed'] and w['owner']==h['dialog_hwnd'] and w['caption']=='ResearchOS' and w['text']=='文件夹路径无效或不存在。请输入已有的文件夹路径后重试。'
assert [e['evidence']['purpose'] for e in h['history'] if e['event']=='BUTTON_POST_ACCEPTED_EFFECT_UNKNOWN']==['INVALID_OK']
assert not any(e['event']=='INVALID_DISMISSED_SAME_CHOOSER_RETAINED' for e in h['history'])
lookup=next(e['evidence'] for e in h['history'] if e['event']=='WARNING_IDOK_DIRECT_LOOKUP');assert lookup['is_zero'] and lookup['hwnd']==0
metadata=next(e['evidence'] for e in h['history'] if e['event']=='WARNING_IDOK_CHILD_METADATA');buttons=[row for row in metadata['rows'] if row['class_name']=='Button'];assert not metadata['truncated'] and metadata['enumeration_error'] is None and len(buttons)==1 and buttons[0]['control_id']==2
assert v['close']['app_close_resolved'] and v['actual_dom_submit_attempts']==0 and v['model_outcome']=='NOT_RUN_ZERO_BUDGET'
post=HERE/'product-v1-build07-post-native-flow03-root-readback.json';assert sha(post)=='ea62b94364daf7d57402df54619e2cac1aed201839bb1f859f820b445434b290';pv=read(post)
assert pv['listed_files']==134 and not pv['mismatches'] and not pv['unlisted_paths']
review=BASE/'native-path-entry-flow-03/independent-runtime-review/actual-review-report.json';assert sha(review)=='d56f312f4dab33511b97e16b037695fb73f4835201ba1153df52225c97b1a7e4';rv=read(review)
assert rv['decision']=='VERIFIED_BLOCKED_WARNING_CONTROL_ID_ASSUMPTION' and rv['formal_increment']==0
taskreview=BASE/'one-task-controller02-unreviewed/security-review/REVIEW.json';assert sha(taskreview)=='f9da90a1925045434db54e91f8555244213ebcbc7b5b34fdee5d9aebca94a2cd';tv=read(taskreview);assert tv['formal_increment']==0
tasksource=BASE/'one-task-controller03/reviews/REVIEW.json';assert sha(tasksource)=='81f17d92cb4efa28b4f55e5102ee267654dc6bfbf4d7ff5ed390cc7d398dc962';ts=read(tasksource);assert ts['decision']=='APPROVED_SOURCE_FIXTURE_ONLY' and ts['formal_increment']==0 and not ts['pending_blockers']
for ref,digest in read(HERE/'product-v1-native-path-entry-integration-plan.json')['protected_sha256'].items():
 p=ROOT/ref;assert (sha(p) if p.is_file() else 'ABSENT_BEFORE')==digest
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
for name,p in [('outer.RESULT.json',outer),('postbundle.json',post),('independent-review.json',review),('one-task-security-BLOCKED.json',taskreview),('one-task03-source-review.json',tasksource)]:(OUT/name).write_bytes(p.read_bytes())
for dirname in ['receipts','screenshots']:
 dest=OUT/dirname;dest.mkdir()
 for p in (flow/dirname).iterdir():
  if p.is_file() and p.name!='launch-input.json':
   assert p.suffix.lower() not in ['.db','.sqlite','.exe','.dll'] and p.stat().st_size<16*1024*1024
   (dest/p.name).write_bytes(p.read_bytes())
now=datetime.now(timezone.utc).isoformat();original=list(cp['failure_counters']);known={e.get('origin_key') for e in original};events=list(rv.get('diagnostic_events',[]))
for f in tv['diagnostic_events']:
 if f['id'] in ['TASK02-F1','TASK02-F2','TASK02-F3','TASK02-TEMPLATE']:
  events.append(dict(origin_key='single-task-controller02-security:'+f['id'],classification='UNEXECUTED_TASK_CONTROLLER_SECURITY_FINDING',detail=f['finding'],evidence_ref=str(taskreview.relative_to(ROOT))))
for e in events:
 assert e.get('origin_key') and e.get('classification')
 if e['origin_key'] not in known:cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**e});known.add(e['origin_key'])
assert cp['failure_counters'][:len(original)]==original
progress=dict(checkpoint_revision=641,at=now,status='REAL_NATIVE_MB_OK_SINGLE_BUTTON_ID2_OBSERVED_SELECTOR_FIX_PENDING',main_head=cp['current_Main_HEAD'],consumed_scope='product-v1-native-path-entry-flow-03',automatic_retry=0,
 actual=dict(unicode_input_readback_exact=True,dialog_thread_active_focus_verified=True,invalid_ok_posted_once=True,owned_warning_caption_text_owner_verified=True,warning_dismiss_posted=False,valid_ok_attempted=False,warning_retention_after_dismiss='NOT_REACHED',main_workspace_binding='NOT_ESTABLISHED_BY_THIS_FLOW',helper_reason=h['reason'],app_close_resolved=True,original_job_stop_proved=True,job_processes=41,forced_termination=False),
 diagnostic_limit='Actual03 records direct ID1 lookup NULL and all three warning descendants: exactly one same-Core visible/enabled Button with actual control ID2, plus two Static controls. Selector assumed ID1 by confusing MessageBox return IDOK with internal control ID. Observation applies to this pinned owned MB_OK warning; no arbitrary-button fallback is allowed.',warning_button_metadata=metadata,
 postbundle=dict(listed_files=134,mismatches=[],unlisted_paths=[]),independent_review_sha256=sha(review),old_protected_changes_preserved=True,
 one_task='Unexecuted03 F1/F2/F3 task identity fixes independently SourceFixture-approved, review81f17d92. Its Native04 helper still assumed warning control ID1. New04 must merge only final Native05 actual-ID2 selector changes, retain03 frozen and repeat only changed-source review. No successful Native prerequisite, no model execution. Declared-freeze01 provenance gap remains CP637.',
 real_model_requests=0,product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Keep consumed01/02/03 and candidates unchanged. Finish C Native05 exact pinned owned MB_OK single actual ButtonID2 selector/evidence review, then fresh zero-model flow04. All chooserID1/owner/active/deadline/PIDL/canonical/consent gates stay. After real Main ACTIVE fixture binding independently verified, review new one-task04 minimal Native05 merge with unchanged03 task identity logic and register one-use ChatGPT-gated task. Internal LLM API calls are NOT_MEASURED; budget means one Harness task invocation.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='REAL_NATIVE_MB_OK_ACTUAL_SINGLE_BUTTON_ID2_SELECTOR_ASSUMPTION_CONFIRMED',source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False));put(sf,s)
cp.update(revision=641,expected_previous_revision=640,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);tmp=hf.with_name(hf.name+'.cp641.new');assert not tmp.exists()
tmp.write_bytes(('# Current resume CP641 — REAL MB_OK WARNING HAS SINGLE BUTTON ID2; SELECTOR FIX PENDING\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Consumedflow03 proves ID1 lookup NULL and actual sole ButtonID2 in pinned warning; no dismiss/validOK/Main binding/task/model. NormalAppclose/41procJobzero/no force,134bundle intact. Next exact evidence-bound selector05 review/newflow04; task03 identity SourceFixture-approved but Native helper requires new04. Preserve all history/UNKNOWN.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(OUT/'record_product_v1_native_path_flow03_runtime.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
