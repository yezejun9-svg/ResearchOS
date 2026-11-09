import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/progress-cp610';CONTROL=HERE/'product-v1-owned-verification-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpfile=ROOT/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==609 and len(cp['failure_counters'])==2483 and not OUT.exists()
scope=CONTROL/'scopes/product-v1-build-01.json';assert sha(scope)=='6309df793cc362bd8701c0942a6542a76363ac177253a37c72109122fac0fb94'
run=CONTROL/'runs/product-v1-build-01';consumed=json.loads((run/'CONSUMED.json').read_bytes());assert consumed['scope_sha256']==sha(scope)
rp=run/'RESULT.json';result=json.loads(rp.read_bytes()) if rp.exists() else None
status='WINDOWS_DESKTOP_BUILD_RESULT_AWAITING_REVIEW' if result else 'WINDOWS_DESKTOP_BUILD_RUNNING_OUTCOME_PENDING'
now=datetime.now(timezone.utc).isoformat();OUT.mkdir();(OUT/'checkpoint.cp609.before.json').write_bytes(raw)
progress=dict(checkpoint_revision=610,at=now,status=status,main_head=cp['current_Main_HEAD'],reviewed_source_files_integrated=30,
 source_reviews=dict(workbench='APPROVED_SOURCE_FIXTURE_ONLY',managed_environment='APPROVED_SOURCE_FIXTURE_ONLY',backend='APPROVED_SOURCE_FIXTURE_ONLY'),
 build=dict(scope_path=str(scope),scope_sha256=sha(scope),run_root=str(run),original_tool_session=90686,launch_chunk='b2d736',consumed=True,result=result,result_sha256=sha(rp) if result else None,automatic_retry=False,source_worktree='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-20261104',source_head=cp['current_Main_HEAD']),
 real_model_requests=0,real_electron_qualification='NOT_RUN',product_v1_journeys_accepted=0,product_v1_journeys_required=13,historical_diagnostic_records=2483,old_records_reset=False,old_worktrees_and_data_untouched=True,
 gui_preparation='C-only; unsafe custom WM_USER pointer path rejected before any launch; actual UIA-only candidate pending Root review.',
 next='Reconcile the single consumed build result, never rerun it blindly. If successful, validate source-bound bundle then register new owned real Electron/Codex user-flow scope. Otherwise preserve failure and fix its exact cause. CLI remains a separate newly leased source slice.')
put(OUT/'RESUME.json',progress);(OUT/'build.scope.json').write_bytes(scope.read_bytes());(OUT/'supervisor-root-review.json').write_bytes((HERE/'product-v1-owned-supervisor-root-review.json').read_bytes())
leasesfile=ROOT/'execution/product-v1/leases.json';lr=leasesfile.read_bytes();leases=json.loads(lr);(OUT/'leases.before.json').write_bytes(lr)
for s in leases['source_owners']:s['status']='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
leases.update(revision=leases['revision']+1,at=now);put(leasesfile,leases)
statefile=ROOT/'execution/product-v1/state.json';sr=statefile.read_bytes();state=json.loads(sr);(OUT/'state.before.json').write_bytes(sr)
state.update(revision=state['revision']+1,updated_at=now,status=status,last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'],active_scopes=leases['source_owners']);state['slices']['S10']['status']='IN_PROGRESS';state['slices']['S10']['evidence'].append(str((OUT/'RESUME.json').relative_to(ROOT)));put(statefile,state)
cp.update(revision=610,expected_previous_revision=609,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=status,at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[],active_verification_owner='codex:/root',formal_increment=0)
assert cpfile.read_bytes()==raw;put(cpfile,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.cp609.before.md').write_bytes(old);t=hf.with_name(hf.name+'.cp610.new');assert not t.exists();t.write_bytes(('# Current resume CP610 — ALL30 REVIEWED SOURCE INTEGRATED; WINDOWS BUILD CONSUMED\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Do not replay build01: inspect its CONSUMED/RESULT and original session90686 first. Desktop and real Codex NOT_RUN; V1 journeys0/13. All original changes, failure records and paused worktrees retained.\n\n').encode('utf8')+old);os.replace(t,hf)
(OUT/'checkpoint_product_v1_build.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(dict(checkpoint=610,status=status,build_result=result['status'] if result else None,main_head=cp['current_Main_HEAD'],failure_records=2483)))
