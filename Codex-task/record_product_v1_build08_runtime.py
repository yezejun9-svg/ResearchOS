import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
CONTROL=HERE/'product-v1-owned-verification-20261104'
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/progress-cp650'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==649 and len(cp['failure_counters'])==2550 and not OUT.exists()
head='1b3a131320c09f553bd3c2c5e3bd39ee6ecb61f2';assert cp['current_Main_HEAD']==head
outer=CONTROL/'runs/product-v1-build-08/RESULT.json';r=read(outer)
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['root_exit_code']==0
assert r['stop_proved'] and r['job_active_zero'] and not r['errors'] and not r['input_drift']
assert r['terminate_job_attempts']==0 and r['terminate_original_root_attempts']==0
bundle=ROOT/'.local/worktrees/product-v1-build-08-20261105/.local/desktop-v1-build-08'
mf=bundle/'development-manifest.json';m=read(mf);assert m['source']['head']==head and not m['source']['candidate_delta']
assert sha(mf)=='7f18b5310a855039cef507ddd7093a568a53273a706d63e043ed6946fbc9dfbb'
listed={v['path'] for v in m['files']}
for v in m['files']:assert sha(bundle/v['path'])==v['sha256']
actual={p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
assert actual==listed|{'development-manifest.json'},sorted(actual-listed)
core=bundle/'apps/desktop/resources/control/researchos-control.exe';assert sha(core)==m['core']['sha256']
assert sha(core)=='95da2a4eedd60a5e38f8a08dbe43e38ebb640ee36b826ae37902e21bb6b13b85'
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
for name,p in [('development-manifest.json',mf),('build08.outer.RESULT.json',outer),('build08.registration.json',ROOT/'execution/product-v1/receipts/single-harness-20261104/build08-scope/registration.json')]:
 (OUT/name).write_bytes(p.read_bytes())
now=datetime.now(timezone.utc).isoformat()
progress=dict(checkpoint_revision=650,at=now,status='NATIVE_CONVERSATION_LAYOUT_BUILD08_COMPLETE_REAL_VISUAL_PENDING',main_head=head,
 desktop=dict(bundle=str(bundle),manifest_sha256=sha(mf),control_sha256=sha(core),listed_files_verified=len(listed),unlisted_paths=[],build_exit=0,original_job_stop_proved=True,forced_termination=False),
 native_conversation_layout='Independently reviewed exact1 wrapper integrated CP649; byte inverse restores baseline,18existing fake tests passed. Build08 full offline JSX/Core/Electron packaging succeeded. Real responsive canvas/composer geometry still pending; no layout acceptance from build alone.',
 model_branch='CP647 single request/Task/Run/native Harness invocation failed closed on Windows unelevated split-read profile before session creation; inference unconfirmed. Preserve original task/budget; no model retry. MXC local startup-only echo candidate undergoing source review; not executed/READY.',
 real_model_requests=1,real_model_requests_unit='ONE_HOST_TASK_NATIVE_HARNESS_INVOCATION_NOT_CONFIRMED_INFERENCE',product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Finish independent review of zero-model build08 visual controller with actual Native authority path, source wrapper060ce and new bundle/Core pins. Fresh scope must measure desktop/mobile dark/light viewport geometry/overflow, truthfully report overlaps, loading/resource statuses and exact original Job stop. No fake CSS/DOM or model calls. MXC branch only reviewed no-model startup availability; keep profile/OS/admin/account/firewall/savedconfig unchanged and original model task unreplayed.')
put(OUT/'RESUME.json',progress)
lf=ROOT/'execution/product-v1/leases.json';leases=read(lf);(OUT/'leases.before.json').write_bytes(lf.read_bytes())
for owner in leases['source_owners']:
 if owner['scope_id']=='PRODUCT_V1_NATIVE_CONVERSATION_LAYOUT':owner['status']='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
leases.update(revision=leases['revision']+1,at=now);put(lf,leases)
sf=ROOT/'execution/product-v1/state.json';sraw=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(sraw)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_scopes=leases['source_owners'],next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='ACTUAL_CLEAN_DESKTOP_BUILD08_NATIVE_CONVERSATION_LAYOUT_SOURCE',source_head=head,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False))
assert sf.read_bytes()==sraw;put(sf,s)
cp.update(revision=650,expected_previous_revision=649,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old)
tmp=hf.with_name(hf.name+'.cp650.new');assert not tmp.exists()
tmp.write_bytes(('# Current resume CP650 — CLEAN BUILD08 COMPLETE; REAL RESPONSIVE VISUAL PENDING\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Reviewed exact1 canvas wrapper fully rebuilt. Native authority flow CP643 already verified; actual model Task CP647 failed closed on sandbox,Invocation1/inferenceunconfirmed. New visual controller pending source review/scope; no model replay. Preserve original data/history/UNKNOWN; formal/V1accepted0.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(OUT/'record_product_v1_build08_runtime.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(progress))
