import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104'
OUT=BASE/'public-health';PROGRESS=BASE/'progress-cp616'
WT=ROOT/'.local/worktrees/product-v1-public-health-20261104'
HEAD='c4029c0b57599e1aafed6d01ea4034b0cf465ccd'
PROD=['apps/desktop/main/lib/ipc.js'];TEST=['tests/ui/desktop/public-health-bridge.test.mjs']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'));os.replace(t,p)
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf8')
def stopped(name):
 p=HERE/'product-v1-owned-verification-20261104/runs'/name/'RESULT.json';v=json.loads(p.read_bytes())
 assert v['status']=='COMPLETED_OWNED_JOB_STOPPED' and v['stop_proved'] and not v['errors'] and not v['input_drift'] and v['terminate_job_attempts']==0
 return p
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=json.loads(raw)
assert cp['revision']==615 and len(cp['failure_counters'])==2501 and git(ROOT,'rev-parse','HEAD').strip()==HEAD
assert not OUT.exists() and not PROGRESS.exists() and not WT.exists() and not git(ROOT,'diff','--cached','--name-only').strip()
build=stopped('product-v1-build-03');smoke=stopped('product-v1-desktop-smoke-02')
state=HERE/'product-v1-desktop-smoke-02-20261104/smoke-state-01';sr=json.loads((state/'SMOKE-RESULT.json').read_bytes())
assert sr['native_report_verdict']['status']=='NATIVE_SMOKE_CONFIRMED' and sr['model_submission_actions']==0
manifest=ROOT/'.local/worktrees/product-v1-build-03-20261104/.local/desktop-v1-build-03/development-manifest.json'
assert sha(manifest)=='a800bca4a7fe808a85c6b175547c5e1788e7d4f10b59fe58e17a94f7f4a713fa'
assert sha(state/'home.png')==sr['screenshot']['sha256']=='35a26fba2c90af77dee8af2808ecd33b575a0161f64075142a6e0a8685b70cc4'
diagnosis=HERE/'product-v1-public-health-independent-review-20261104/report.json'
assert sha(diagnosis)=='581db6d53a2b160da5aba24fee362d69bd69c20f777242b16e57452ed3d4468c'
OUT.mkdir();PROGRESS.mkdir();(PROGRESS/'checkpoint.cp615.before.json').write_bytes(raw)
for name in ['home.png','SMOKE-RESULT.json','WRAPPER-CONSUMED.json','electron.stdout.raw','electron.stderr.raw']:(PROGRESS/name).write_bytes((state/name).read_bytes())
for name,p in [('build03.outer.RESULT.json',build),('smoke02.outer.RESULT.json',smoke),('development-manifest.json',manifest),('health-diagnosis.json',diagnosis)]:(PROGRESS/name).write_bytes(p.read_bytes())
git(ROOT,'worktree','add','--no-checkout','-b','codex/product-v1-public-health-20261104',str(WT),HEAD)
git(WT,'sparse-checkout','set','--no-cone','/.gitignore','/AGENTS.md','/apps/desktop/main/','/apps/desktop/preload/','/apps/web/src/startup.js','/tests/ui/','/docs/product-v1/');git(WT,'checkout','HEAD')
assert not git(WT,'status','--porcelain=v1').strip()
now=datetime.now(timezone.utc).isoformat()
scope=dict(scope_id='PRODUCT_V1_PUBLIC_HEALTH_BRIDGE',owner='codex:/root/resource_controller_review',integrator='codex:/root',at=now,base_head=HEAD,worktree=str(WT),production_paths=PROD,test_paths=TEST,baseline_sha256={p:sha(ROOT/p) if (ROOT/p).is_file() else 'ABSENT_BEFORE' for p in PROD+TEST},purpose='Fix real fresh-Native public health bridge incorrectly requiring absent legacy principal; preserve all authority boundaries.',requirements=['Only client=status and method=health may omit legacy principal, using fixed GET /healthz and empty caller-independent payload/headers.', 'Keep ensureCore and validated discovery first. No arbitrary URL, caller headers, token, principal or request method allowed.', 'Every other route, authenticated read, provider, session and mutation keeps original principal check and behavior.', 'Do not loosen UI strict ready/DEVELOPMENT_ONLY/sqlite health predicate or fabricate connectivity.', 'Meaningful actual callCore tests for public healthy reply, missing/malformed principal, missing discovery, transport failure/malformed/not-ready response and unchanged non-health blocks.', 'Exact two-source freeze for independent review, no GUI/model/native execution in author scope.'],forbidden=['No additional source paths without Root scope amendment','No old data, auth file, credential or user configuration reading/copying','No fake principals or authority weakening','No new dependency/install','No reset/replay of failures or consumed scopes'],formal_increment=0,product_acceptance_increment=0)
put(OUT/'scope.json',scope)
lf=ROOT/'execution/product-v1/leases.json';lr=lf.read_bytes();leases=json.loads(lr);(PROGRESS/'leases.before.json').write_bytes(lr)
for entry in leases['source_owners']:entry['status']='SOURCE_INTEGRATED_NOT_LIVE_QUALIFIED'
entry=dict(scope_id=scope['scope_id'],owner=scope['owner'],worktree=str(WT),scope_ref=str((OUT/'scope.json').relative_to(ROOT)),status='IMPLEMENTING')
leases['source_owners'].append(entry);leases.update(revision=leases['revision']+1,at=now);put(lf,leases)
origin='product-v1-public-health-blocked-by-legacy-principal'
assert not any(x.get('origin_key')==origin for x in cp['failure_counters'])
cp['failure_counters'].append(dict(at=now,origin_key=origin,classification='REAL_DESKTOP_INTEGRATION',attempts=1,counter_reset=False,detail='Dark real Desktop smoke02 has healthy Native Host but false disconnected badge. Independent6 actual callCore cases prove public GET /healthz is blocked before transport by absent legacy principal. Strict renderer predicate stays unchanged.'))
progress=dict(checkpoint_revision=616,at=now,status='REAL_DARK_DESKTOP_OBSERVED_PUBLIC_HEALTH_FIX_LEASED',main_head=HEAD,desktop_manifest_sha256=sha(manifest),desktop_startup=dict(native_host_status='COMPLETED',renderer_mounted=True,screenshot_sha256=sha(state/'home.png'),original_core_identity=sr['native_report_verdict']['owned_core_identity'],normal_shutdown=True,outer_job_stop_proved=True,forced_termination=False,model_submission_actions=0),actual_ui_result='Dark clean assistant home observed; stale presentation error gone; public health badge remains incorrect and is not accepted.',active_scope=entry,historical_records=len(cp['failure_counters']),old_records_reset=False,real_model_requests=0,product_journeys_accepted=0,product_journeys_required=13,next='Implement/review exact2 public-health bridge; integrate and rebuild for real health smoke. In parallel build actual CLI artifact and review fresh full-GUI Codex controller. Do not replay consumed scopes or resubmit UNKNOWN.')
put(PROGRESS/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';oldstate=sf.read_bytes();s=json.loads(oldstate);(PROGRESS/'state.before.json').write_bytes(oldstate)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((PROGRESS/'RESUME.json').relative_to(ROOT)),active_scopes=leases['source_owners'],next=progress['next'])
s.setdefault('runtime_evidence',[]).append(dict(kind='ZERO_MODEL_REAL_DARK_DESKTOP_STARTUP_SMOKE',source_head=HEAD,resume_ref=str((PROGRESS/'RESUME.json').relative_to(ROOT)),business_acceptance=False,health_badge_accepted=False));put(sf,s)
cp.update(revision=616,expected_previous_revision=615,updated_at=now,next_command=progress['next']+' Read '+str((PROGRESS/'RESUME.json').relative_to(ROOT)))
cp['workers'].append(entry);cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((PROGRESS/'RESUME.json').relative_to(ROOT)),active_construction_owners=[scope['owner']],formal_increment=0)
assert cpf.read_bytes()==raw;put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(PROGRESS/'handoff.before.md').write_bytes(old);tmp=hf.with_name(hf.name+'.cp616.new');assert not tmp.exists();tmp.write_bytes(('# Current resume CP616 — REAL DARK DESKTOP OBSERVED; PUBLIC HEALTH BRIDGE LEASED\n\nRead '+str((PROGRESS/'RESUME.json').relative_to(ROOT))+'. Actual build03 and smoke02 completed with original Core normal shutdown and owned outer Job stop, models0. Dark UI observed; false disconnected badge remains a real integration defect, exact2 fix leased. V1 journeys0/13, histories/UNKNOWN preserved.\n\n').encode('utf8')+old);os.replace(tmp,hf)
(PROGRESS/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=616,main_head=HEAD,historical_records=len(cp['failure_counters']),worktree=str(WT),scope=str(OUT/'scope.json'),model_tasks=0)))
