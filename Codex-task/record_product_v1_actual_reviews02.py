import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';OUT=BASE/'progress-cp659'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==658 and len(cp['failure_counters'])==2561 and not OUT.exists()
vr=BASE/'layout-visual-02/independent-runtime-review/product-v1-layout-visual-actual02-review-20261105/actual-review-report.json';assert sha(vr)=='6be6e0c55e561fc5a8603b83649610fbbdeb3dfb6b5a3107c80c05ba9391b033';v=read(vr)
xr=BASE/'mxc-resource-check/actual-05/product-v1-mxc-availability-actual05-independent-review/REVIEW.json';assert sha(xr)=='9f744ce40e1679f64118d9b232bcf353d5815e32ac63e816b45d0e609feb6fc9';x=read(xr)
assert v['decision']=='ACTUAL_RESIDUAL_MOBILE_NAVIGATION_OCCLUSION_CONFIRMED_NOT_PRODUCT_ACCEPTED' and v['formal_increment']==v['product_increment']==0
assert x['decision']=='VERIFIED_FIXED_LOCAL_MXC_ECHO_STARTUP_ONLY_NOT_PRODUCT_ACCEPTANCE' and x['formal_increment']==x['product_increment']==x['model_increment']==0
post=HERE/'product-v1-build09-post-visual02-root-readback.json';assert sha(post)=='c442dbc176d3aab33033add6c36585f338e4ff077cfaa54828ca10cf299d54da'
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
for name,p in [('visual02.independent-review.json',vr),('mxc05.independent-review.json',xr),('postbundle.json',post)]:(OUT/name).write_bytes(p.read_bytes())
flow=HERE/'product-v1-layout-visual-中文-run-02'
for d in ['receipts','screenshots']:
 dest=OUT/d;dest.mkdir()
 for p in (flow/d).iterdir():
  if p.is_file() and p.name!='launch-input.json':
   assert p.suffix.lower() not in ['.db','.sqlite','.exe','.dll'] and p.stat().st_size<16*1024*1024;(dest/p.name).write_bytes(p.read_bytes())
now=datetime.now(timezone.utc).isoformat();old=list(cp['failure_counters']);known={e.get('origin_key') for e in old}
for e in list(v.get('diagnostic_events',[]))+list(x.get('diagnostic_events',[])):
 assert e.get('origin_key') and e.get('classification')
 if e['origin_key'] not in known:cp['failure_counters'].append({'at':now,'attempts':1,'counter_reset':False,**e});known.add(e['origin_key'])
assert cp['failure_counters'][:len(old)]==old
progress=dict(checkpoint_revision=659,at=now,status='ACTUAL_VISUAL02_RESIDUAL_NAV_DEFECT_AND_MXC_FIXED_STARTUP_INDEPENDENTLY_REVIEWED',main_head=cp['current_Main_HEAD'],visual02=dict(independent_review_ref=str(vr.relative_to(ROOT)),independent_review_sha256=sha(vr),findings=2,all_composer_heading_overlaps_empty=True,all_12_scroll_focus_actions_hit=True,initial_scroll_all_zero=True,postbundle_134_intact=True,job_processes=57,job_zero=True,forced_termination=False),mxc05=dict(independent_review_ref=str(xr.relative_to(ROOT)),independent_review_sha256=sha(xr),exact_echo_observed=True,exit_code=0,job_processes=7,job_zero=True,forced_termination=False,diagnostic_attempt=2,cumulative_local_native_checks=2,max_local_native_checks=2,prior_failure_preserved=True,claim='FIXED_LOCAL_MXC_ECHO_STARTUP_ONLY',split_read_enforcement='UNVERIFIED',resource_ready=False,model_retry_authorized=False),real_model_requests=1,real_model_requests_unit='PRIOR_ONE_HOST_TASK_NATIVE_HARNESS_INVOCATION; INFERENCE_NOT_CONFIRMED',product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,next='Finish leased exact1 mobile viewport CSS/review then build10; prepare reviewed controller09 that resets/records/asserts main-area initial scroll0 with unchanged geometry/hit checks. Use new actual visual03 scope. MXC availability-only diagnosis is complete at2/2, no further echo or original model task replay; product read-profile enforcement/model/cancel/resume still unverified. Keep permissions/admin/config and old failure history unchanged.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';sr=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(sr);s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next']);s.setdefault('resource_state',{}).setdefault('codex',{})['local_mxc_startup']=dict(status='OBSERVED_FIXED_ECHO_ONLY',scope_id='mxc_availability_20261105_f602',diagnostic_attempts=2,max_attempts=2,evidence_ref=str(xr.relative_to(ROOT)),permissions_verified=False,model_retry_authorized=False)
for kind in ['ACTUAL_VISUAL02_RESIDUAL_MOBILE_NAVIGATION_OCCLUSION','ACTUAL_FIXED_LOCAL_MXC_STARTUP_ECHO_ONLY']:s.setdefault('runtime_evidence',[]).append(dict(kind=kind,source_head=cp['current_Main_HEAD'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False))
put(sf,s);cp.update(revision=659,expected_previous_revision=658,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=['codex:/root/mobile_viewport_impl'],formal_increment=0);assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp659.new');assert not t.exists();t.write_bytes(('# Current resume CP659 - ACTUAL REVIEWS: RESIDUAL MOBILE NAV DEFECT; FIXED LOCAL MXC STARTUP ONLY\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Visual02 has2nav findings, normal composer and allscrollfocus. New exact1 bounded mobile main viewport in progress. MXC05 exactecho/7Jobzero independently audited;budget2/2 consumed, no split-read/READY/model retry. Prior04failure and all history remain. New build10/controller09/actualvisual03 required.\n\n').encode('utf8')+old);os.replace(t,hf);(OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(progress))
