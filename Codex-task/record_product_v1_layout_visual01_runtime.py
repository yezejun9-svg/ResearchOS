import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104';BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp652'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==651 and len(cp['failure_counters'])==2554 and not OUT.exists()
flow=HERE/'product-v1-layout-visual-中文-run-01';outer=CONTROL/'runs/product-v1-layout-visual-01/RESULT.json';r=read(outer);v=read(flow/'receipts/result.json');g=read(flow/'receipts/workbench-responsive-visual.json')
assert r['status']=='CHILD_NONZERO_STOPPED' and r['root_exit_code']==2 and r['job_total_processes']==57 and r['stop_proved'] and r['job_active_zero'] and r['terminate_job_attempts']==0 and not r['errors'] and not r['input_drift']
assert v['error']['code']=='VISUAL_GEOMETRY_FAILED' and v['actual_dom_submit_attempts']==0 and v['close']['app_close_resolved']
initial=[s for s in g['scenarios'] if s['phase']=='INITIAL_VIEWPORT'];assert len(initial)==4
for s in initial:
 assert s['document']['scroll_y']==0 and s['transcript_scroll']['scroll_top']==0 and not s['horizontal_overflow']
 assert s['viewport']['inner_width']==s['viewport']['requested_width'] and s['viewport']['inner_height']==s['viewport']['requested_height']
desktop=[s for s in initial if s['viewport']['inner_width']==1440];mobile=[s for s in initial if s['viewport']['inner_width']==390]
assert len(desktop)==len(mobile)==2 and all(not s['composer_overlaps_content'] and s['heading_center_hit'] for s in desktop)
assert all('heading' in s['composer_overlaps_content'] and not s['heading_center_hit'] for s in mobile) and len(g['findings'])==22
post=HERE/'product-v1-build08-post-visual01-root-readback.json';assert sha(post)=='d7ba6e4338f22f6ac9232cdc5f0eef221e96960c10490e4f217bf8dc0f8b0942';pv=read(post);assert pv['listed_files']==134 and not pv['mismatches'] and not pv['unlisted_paths']
review=BASE/'layout-visual-01/independent-runtime-review/actual-review-report.json';assert sha(review)=='45bc20de0b14a22985ace48321835e5599f182e8be14a8df6f5657b50dc9fa9a';rv=read(review);assert rv['decision']=='ACTUAL_MOBILE_LAYOUT_DEFECT_CONFIRMED_NOT_PRODUCT_ACCEPTED' and rv['formal_increment']==0
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
progress=dict(checkpoint_revision=652,at=now,status='BUILD08_REAL_DESKTOP_LAYOUT_PASS_MOBILE_STICKY_COMPOSER_DEFECT',main_head=cp['current_Main_HEAD'],consumed_scope='product-v1-layout-visual-01',automatic_retry=0,
 actual=dict(desktop_1440x1000_dark_light='NO_VISIBLE_WELCOME_COMPOSER_OVERLAP; CENTER_HITS_CONFIRMED',mobile_390x844_dark_light='COMPOSER_COVERS_HEADING; ACTIONS_INACCESSIBLE_AFTER_SCROLL',all_initial_scroll_zero=True,all_requested_viewports_exact=True,horizontal_overflow=False,findings=22,layout_cause_limit='Composer overlap with heading is proven; bottom navigation may also cover action region. No elementFromPoint occluder identity, so not every action miss is assigned to composer.',native_main_binding='CONFIRMED',app_close_resolved=True,original_job_processes=57,original_job_stop_proved=True,forced_termination=False,this_operation_task_submissions=0,this_operation_model_invocations=0),postbundle=dict(listed_files=134,mismatches=[],unlisted_paths=[]),
 real_model_requests=1,real_model_requests_unit='PRIOR_ONE_HOST_TASK_NATIVE_HARNESS_INVOCATION; INFERENCE_NOT_CONFIRMED',product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Keep consumed visual01 and real failure screenshots/geometry. Register isolated exact1 apps/web/src/workbench.css mobile-flow fix: composer normal document flow at narrow widths, preserve desktop behavior and accessibility to actions above fixed bottom nav; no task/auth changes. Existing07 capture may be retargeted to a fresh source-bound build after review. Separately review canonical-path MXC echo04 and register one local no-model availability scope; no admin/setup/permission relaxation/savedconfig change/model retry.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old);s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next']);s.setdefault('runtime_evidence',[]).append(dict(kind='ACTUAL_BUILD08_DESKTOP_PASS_MOBILE_COMPOSER_DEFECT',source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False));put(sf,s)
cp.update(revision=652,expected_previous_revision=651,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0);assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp652.new');assert not t.exists();t.write_bytes(('# Current resume CP652 — BUILD08 DESKTOP GEOMETRY PASS; REAL MOBILE COMPOSER OCCLUSION\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Main1b3a131/build08,actual4viewport-theme observations/allinitialscroll0/nohorizontaloverflow. Desktopfixed;mobileheading/actionsoccluded.57procJobzero/no force/134bundle intact. No new task/model;priorInvocation1/resourcefailed/no inferenceconfirmed. Next exact1mobileCSS lease+newbuild/scope;separateMXClocalechoonly. No completion/acceptance claim/history reset.\n\n').encode('utf8')+old);os.replace(t,hf);(OUT/'record_product_v1_layout_visual01_runtime.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
