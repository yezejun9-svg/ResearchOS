import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
CONTROL=HERE/'product-v1-owned-verification-20261104'
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/progress-cp635'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists()
 t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==634 and len(cp['failure_counters'])==2532 and not OUT.exists()
head='2b39fe3a6e8d69981a4079bb585086dca98b283e';assert cp['current_Main_HEAD']==head
outer=CONTROL/'runs/product-v1-build-07/RESULT.json';r=read(outer)
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['root_exit_code']==0
assert r['stop_proved'] and r['job_active_zero'] and not r['errors'] and not r['input_drift']
assert r['terminate_job_attempts']==0 and r['terminate_original_root_attempts']==0
bundle=ROOT/'.local/worktrees/product-v1-build-07-20261104/.local/desktop-v1-build-07'
mf=bundle/'development-manifest.json';m=read(mf);assert m['source']['head']==head and not m['source']['candidate_delta']
listed={v['path'] for v in m['files']}
for v in m['files']:assert sha(bundle/v['path'])==v['sha256']
actual={p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
assert actual==listed|{'development-manifest.json'},sorted(actual-listed)
core=bundle/'apps/desktop/resources/control/researchos-control.exe';assert sha(core)==m['core']['sha256']
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
for name,p in [('development-manifest.json',mf),('build07.outer.RESULT.json',outer),('build07.registration.json',ROOT/'execution/product-v1/receipts/single-harness-20261104/build07-scope/registration.json')]:
 (OUT/name).write_bytes(p.read_bytes())
now=datetime.now(timezone.utc).isoformat()
progress=dict(checkpoint_revision=635,at=now,status='NATIVE_PATH_ENTRY_BUILD07_COMPLETE_REAL_UI_PENDING',main_head=head,
 desktop=dict(bundle=str(bundle),manifest_sha256=sha(mf),control_sha256=sha(core),listed_files_verified=len(listed),unlisted_paths=[],build_exit=0,original_job_stop_proved=True,forced_termination=False),
 native_path_entry='Independently reviewed exact2 integrated CP634; BIF_EDITBOX+BIF_VALIDATE Unicode warning. Real invalid/valid path flow controller still preparing/reviewing, not run. Typed edit text is not authority; actual Shell PIDL/canonical/reparse/consent required.',
 real_model_requests=0,product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,
 next='Finish independent review and pin new zero-model Native invalid/valid UI controller to build07. Register a fresh one-use scope, verify real warning/dialog retained then real Shell-confirmed fixture registration, app close and original Job stop. Recheck complete bundle after runtime. Only after zero-model flow passes prepare separately authorized one-task ChatGPT-gated readonly flow; never replay consumed scopes or repost UNKNOWN.')
put(OUT/'RESUME.json',progress)
lf=ROOT/'execution/product-v1/leases.json';leases=read(lf);(OUT/'leases.before.json').write_bytes(lf.read_bytes())
for owner in leases['source_owners']:
 if owner['scope_id']=='PRODUCT_V1_NATIVE_PATH_ENTRY':owner['status']='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
leases.update(revision=leases['revision']+1,at=now);put(lf,leases)
sf=ROOT/'execution/product-v1/state.json';sraw=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(sraw)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_scopes=leases['source_owners'],next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='ACTUAL_CLEAN_DESKTOP_BUILD07_NATIVE_EDITBOX_SOURCE',source_head=head,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False))
assert sf.read_bytes()==sraw;put(sf,s)
cp.update(revision=635,expected_previous_revision=634,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old)
tmp=hf.with_name(hf.name+'.cp635.new');assert not tmp.exists()
tmp.write_bytes(('# Current resume CP635 — NATIVE PATH ENTRY BUILD07 COMPLETE; REAL UI PENDING\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Fresh source-bound offline build07 succeeded with original Job zero. Real invalid/valid Native path UI not run; no model submit, no journey acceptance. Preserve all old changes/history/UNKNOWN.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(OUT/'record_product_v1_build07_runtime.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(progress))
