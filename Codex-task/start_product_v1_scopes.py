import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');HERE=Path(__file__).resolve().parent
OUT=ROOT/'execution/product-v1/receipts/single-harness-20261104'
HEAD='29f92310a0bdefefbb7c020c792a3565f7b71504'
BACKEND_PROD=['internal/domain/harness_v1.go','internal/domain/runtime_harness_windows.go','internal/host/harness_windows.go','internal/api/harness_v1.go','adapters/runtime/codex_driver_windows.go','apps/control/main.go','internal/api/server.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_dispatch.go','internal/domain/runtime_admission.go','internal/domain/runtime_recovery_windows.go','adapters/runtime/process_windows.go','adapters/runtime/codex.go']
BACKEND_TEST=['internal/domain/harness_v1_test.go','internal/domain/runtime_harness_windows_test.go','internal/host/harness_windows_test.go','internal/api/harness_v1_test.go','adapters/runtime/codex_driver_windows_test.go']
UI_PROD=['apps/web/src/workbench.jsx','apps/web/src/activity.js','apps/web/src/components/activity-rail.jsx','apps/web/src/harness.js','apps/desktop/preload/preload.js','apps/desktop/main/lib/ipc.js','apps/desktop/main/main.js','apps/desktop/main/lib/harness-wire.js']
UI_TEST=['tests/ui/desktop/harness-workbench.test.mjs','tests/ui/harness-bridge-fixture.cjs']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 t=p.with_name(p.name+'.new');assert not t.exists();t.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'));os.replace(t,p)
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
cpfile=ROOT/'execution/v2.4/checkpoint.json';cpraw=cpfile.read_bytes();cp=json.loads(cpraw)
assert cp['revision']==603 and len(cp['failure_counters'])==2449
assert git(ROOT,'rev-parse','HEAD').strip()==HEAD and not OUT.exists()
assert not set(BACKEND_PROD+BACKEND_TEST).intersection(UI_PROD+UI_TEST)
assert not set(git(ROOT,'diff','--name-only').splitlines()).intersection(BACKEND_PROD+BACKEND_TEST+UI_PROD+UI_TEST)
OUT.mkdir(parents=True);(OUT/'checkpoint.cp603.before.json').write_bytes(cpraw)
now=datetime.now(timezone.utc).isoformat();scopes=[]
for name,owner,prod,tests in [('backend','codex:/root/delivery_binding_impl',BACKEND_PROD,BACKEND_TEST),('workbench','codex:/root/resource_controller_review',UI_PROD,UI_TEST)]:
 wt=ROOT/('.local/worktrees/product-v1-'+name+'-20261104');assert not wt.exists()
 r=OUT/name;r.mkdir()
 for d in ('author','reviews','tools'):(r/d).mkdir()
 git(ROOT,'worktree','add','--no-checkout','-b','codex/product-v1-'+name+'-20261104',str(wt),HEAD)
 git(wt,'sparse-checkout','set','--no-cone','/AGENTS.md','/go.mod','/go.sum','/internal/','/adapters/','/apps/','/tests/ui/','/tests/runtime/','/migrations/sqlite/','/spec/v2.0/contracts/','/ops/','/docs/product-v1/','/execution/product-v1/')
 git(wt,'checkout','HEAD')
 evaluation=git(wt,'ls-tree','-r','--name-only','HEAD','--','evaluation/holdout/jev','evaluation/evolution','evaluation/skills').splitlines()
 selected=['/'+x for x in evaluation if x.endswith('.go') and not x.endswith('_test.go')]
 if selected:git(wt,'sparse-checkout','add',*selected)
 assert not git(wt,'status','--porcelain=v1','-uno').strip()
 scope=dict(scope_id='PRODUCT_V1_SINGLE_HARNESS_'+name.upper(),owner=owner,integrator='codex:/root',at=now,base_head=HEAD,worktree=str(wt),production_paths=prod,test_paths=tests,
  baseline_sha256={p:sha(ROOT/p) if (ROOT/p).is_file() else 'ABSENT_BEFORE' for p in prod+tests},
  contract_state='Root to freeze shared harness.v1 interface before client transport coding; backend producer must provide DTO pin early',
  purpose='Actual Codex readonly task through the existing Go Host/Coordinator and default React/Desktop UI, not a demo or second agent loop.',
  requirements=['Keep original Mu/V2 behavior and all old paused worktrees. No migration/adoption of existing user DB or Native addon.',
    'Use same domain Task/Run,leases,outbox,observations,receipts and one Coordinator. Do not create a parallel job scheduler/business DB.',
    'Versioned /harness/v1 with actual Host credential/project/workspace authority. Queued ACK is not Run completion; Run/epoch may initially be null.',
    'Codex owns native account/model/tools; application never reads/copies credentials. Hardcode safe argv, ignore user config, no dangerous bypass; permissions profile must not mix with --sandbox.',
    'Readonly first. Write/resume/pause/interactive permission bridge unverified or unsupported must be false. Requested policy is not verified Windows enforcement.',
    'Normalize real structured events and plain assistant text; do not invent token deltas,tool success,Git commits,usage,cost or model qualification.',
    'Cancel queued task vs exact active Run/epoch separately; CANCEL_REQUESTED until actual owned cleanup proof. Unknown execution is never auto-resubmitted.',
    'Validation uses locked offline narrow tests/fresh fixtures first. No live model/native qualification or old probe replay under this source scope; Root registers separately after source review.',
    'Preserve each failed attempt and evidence. Same-origin retries bounded; no rename/newGoal/counter reset. Source authors never self-sign product acceptance.'],
  forbidden=['No source outside exact scope without Root amendment','No Root control/registry/step_state/path_ownership edits','No secret files or unrelated project history','No installs/push/paid API keys/old qualification replay'],
  product_acceptance_increment=0)
 put(r/'scope.json',scope);scopes.append(dict(scope_id=scope['scope_id'],owner=owner,worktree=str(wt),scope_ref=str((r/'scope.json').relative_to(ROOT)),status='IMPLEMENTING'))
statefile=ROOT/'execution/product-v1/state.json';stateraw=statefile.read_bytes();state=json.loads(stateraw)
(OUT/'state.before.json').write_bytes(stateraw);state['revision']+=1;state['updated_at']=now;state['status']='IMPLEMENTING_SINGLE_HARNESS_VERTICAL_SLICE';state['active_scopes']=scopes
for key in ('S01','S02','S03','S04'):state['slices'][key]['status']='IN_PROGRESS'
state['next']='Implement exact backend+workbench scopes, freeze shared DTO, test and independently review; Root then registers fresh real Codex qualification and Electron checks. No journey accepted from source/unit results.'
put(statefile,state)
leases=dict(schema='researchos.product-v1-source-leases/1',revision=1,at=now,integrator='codex:/root',source_owners=scopes,max_active_source_owners=2,legacy_ownership_preserved=True)
put(ROOT/'execution/product-v1/leases.json',leases)
resume=dict(checkpoint_revision=604,main_head=HEAD,status=state['status'],historical_diagnostic_records=2449,product_v1_journeys_accepted=0,product_v1_journeys_required=13,
 legacy_formal_accepted=0,legacy_formal_required=42,counter_reset=False,scopes=scopes,old_worktrees_preserved=True,real_model_qualification='NOT_RUN',next=state['next'])
put(OUT/'RESUME.json',resume)
cp['revision']=604;cp['expected_previous_revision']=603;cp['updated_at']=now;cp['next_command']=state['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT))
cp['current_implementation']=dict(status=state['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[s['owner'] for s in scopes],formal_increment=0)
cp['workers'].extend(scopes)
assert cpfile.read_bytes()==cpraw;put(cpfile,cp)
handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(OUT/'handoff.cp603.before.md').write_bytes(before)
t=handoff.with_name(handoff.name+'.cp604.new');assert not t.exists();t.write_bytes(('# Current resume CP604 — SINGLE HARNESS IMPLEMENTATION\n\nRead execution/product-v1/state.json and '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Two new isolated source scopes for same-Coordinator Codex readonly and default React/Desktop bridge. Shared interface must be pinned; narrow tests/independent review before separately registered real qualification.13 journeys NOT_RUN; old22/42/failures/UNKNOWN/worktrees preserved.\n\n').encode('utf-8')+before);os.replace(t,handoff)
(OUT/'start_product_v1_scopes.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=604,main_head=HEAD,source_scopes=scopes,backend_paths=18,workbench_paths=10,journeys_accepted=0)))
