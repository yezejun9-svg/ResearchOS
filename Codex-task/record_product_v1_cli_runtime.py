import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104'
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104/progress-cp617'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf);assert cp['revision']==616 and len(cp['failure_counters'])==2502 and not OUT.exists()
artifact=ROOT/'.local/worktrees/product-v1-build-03-20261104/.local/cli-v1-artifact-01';manifest=artifact/'artifact-manifest.json';m=read(manifest)
assert sha(manifest)=='ef603e5dc373d01a67f5a0d9b6b2c56e82bd03b89f58d3dbb10bfcc6feb5b3b9'
assert sha(Path(m['binary']['path']))==m['binary']['sha256']=='881e26a2784cab412c21e3f6b3e562d031d9f10479911953a83ef5888a7a4da7'
for name in ['product-v1-cli-build-01','product-v1-cli-help-01']:
 v=read(CONTROL/'runs'/name/'RESULT.json');assert v['status']=='COMPLETED_OWNED_JOB_STOPPED' and v['stop_proved'] and not v['errors'] and not v['input_drift'] and v['terminate_job_attempts']==0
helpout=read(CONTROL/'runs/product-v1-cli-help-01/stdout.raw');assert helpout['command']=='harness help' and helpout['status']=='COMPLETED' and helpout['completion_scope']=='USAGE' and helpout['exit_code']==0
cli_review=HERE/'product-v1-cli-build-independent-review-20261104/after-build-report.json';assert sha(cli_review)=='2d38a04d38551e82fbb016e8e0f8278108a8e3cfa0b3805937b1b89703336aa1'
gui_review=HERE/'product-v1-real-electron-independent-review-20261104/revision03/review.json';assert sha(gui_review)=='97538836b6104c82c076d9d189eb0b4a485cebeab8d86f67e2a17b0364d582cf'
OUT.mkdir();(OUT/'checkpoint.cp616.before.json').write_bytes(raw)
sources={'cli-artifact-manifest.json':manifest,'cli-build-result.json':artifact/'receipts/result.json','cli-build-outer.RESULT.json':CONTROL/'runs/product-v1-cli-build-01/RESULT.json','cli-help-outer.RESULT.json':CONTROL/'runs/product-v1-cli-help-01/RESULT.json','cli-help.stdout.raw':CONTROL/'runs/product-v1-cli-help-01/stdout.raw','cli-independent-review.json':cli_review,'gui-controller03-independent-review.json':gui_review}
for name,p in sources.items():(OUT/name).write_bytes(p.read_bytes())
now=datetime.now(timezone.utc).isoformat();known={x.get('origin_key') for x in cp['failure_counters']}
events=[('cli-component-plan-python-alias','AUTHOR_C_SYNTAX_CHECK_TRANSPORT','Default WindowsApps Python alias unavailable before wrapper execution; final pinned Python syntax check succeeded.'),('product-v1-build03-review-checker-alias-overconstraint','INDEPENDENT_REVIEW_FIXTURE','Read-only optional build03 checker over-restricted expected NVM junction; no product or artifact failure. Original incomplete report retained; not replayed.'),('product-v1-cli-build-review-goproxy-off-misclassified','INDEPENDENT_REVIEW_FIXTURE','Read-only CLI reviewer checker initially treated explicit GOPROXY=off as unsafe proxy. Original failure retained; corrected same metadata check passed without any product change.')]
for origin,classification,detail in events:
 if origin not in known:cp['failure_counters'].append(dict(at=now,origin_key=origin,classification=classification,detail=detail,attempts=1,counter_reset=False))
progress=dict(checkpoint_revision=617,at=now,status='ACTUAL_CLI_ARTIFACT_AND_USAGE_VERIFIED_HEALTH_SOURCE_IN_REVIEW',main_head=cp['current_Main_HEAD'],cli=dict(source_head=m['source']['head'],binary_sha256=m['binary']['sha256'],bytes=m['binary']['bytes'],artifact_manifest_sha256=sha(manifest),offline_build_exit=0,help_usage_exit=0,outer_jobs_stopped=True,forced_termination=False,host_or_model_tasks=0,independent_review_sha256=sha(cli_review)),gui_controller=dict(revision=3,decision='APPROVED_SOURCE_FIXTURE_ONLY',review_sha256=sha(gui_review),executed=False),real_model_requests=0,product_journeys_accepted=0,product_journeys_required=13,historical_records=len(cp['failure_counters']),old_records_reset=False,next='Finish independent public-health exact2 review and integrate; build04 from complete latest source, verify actual green health smoke, then execute newly registered real owned GUI/Codex readonly task. CLI build/help are not Host/task or product acceptance.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';old=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(old);s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next']);s.setdefault('runtime_evidence',[]).append(dict(kind='ACTUAL_WINDOWS_CLI_BUILD_AND_USAGE',source_head=m['source']['head'],resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),business_acceptance=False));put(sf,s)
cp.update(revision=617,expected_previous_revision=616,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)));cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),formal_increment=0);assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old);tmp=hf.with_name(hf.name+'.cp617.new');assert not tmp.exists();tmp.write_bytes(('# Current resume CP617 — REAL CLI ARTIFACT AND USAGE VERIFIED\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. CLI build and actual harness help exit0, independent artifact review approved, both owned Jobs stopped without forced termination. Health exact2 source frozen/in independent review; GUI controller03 approved fixtures only. Models0, V1 journeys0/13; histories/UNKNOWN unchanged.\n\n').encode('utf8')+old);os.replace(tmp,hf)
print(json.dumps(dict(checkpoint=617,historical_records=len(cp['failure_counters']),cli_build_and_help_passed=True,models=0,journeys_accepted=0)))
