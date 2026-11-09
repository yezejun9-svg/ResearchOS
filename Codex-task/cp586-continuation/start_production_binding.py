import json,hashlib,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding'
wt=root/'.local/worktrees/coding-delivery-binding-20261104';head='b84b065739d64a61407ca815651880b6c06ae36a'
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
def put(path,doc):
    temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==589 and len(cp['failure_counters'])==2390
assert git(root,'rev-parse','HEAD').strip()==head and not out.exists() and not wt.exists()
paths=['internal/domain/coding_delivery_binding.go','internal/domain/coding_delivery_binding_store.go','internal/domain/contracts/coding_delivery_bindings.sql','internal/domain/coding_delivery_binding_test.go']
for path in paths:assert not (root/path).exists(),path
out.mkdir();(out/'author').mkdir();(out/'reviews').mkdir();(out/'tools').mkdir();(out/'checkpoint.cp589.before.json').write_bytes(raw)
git(root,'worktree','add','--no-checkout','-b','codex/coding-delivery-binding-20261104',str(wt),head)
git(wt,'sparse-checkout','set','--no-cone','/AGENTS.md','/go.mod','/go.sum','/internal/','/adapters/','/migrations/sqlite/','/spec/v2.0/contracts/','/ops/')
git(wt,'checkout','HEAD')
source=git(wt,'ls-tree','-r','--name-only','HEAD','--','evaluation/holdout/jev','evaluation/evolution','evaluation/skills').splitlines()
go_files=[p for p in source if p.endswith('.go') and not p.endswith('_test.go')]
git(wt,'sparse-checkout','add',*['/'+p for p in go_files])
assert not git(wt,'status','--porcelain=v1','-uno').strip()
now=datetime.now(timezone.utc).isoformat()
scope={'scope_id':'PRODUCTION_CODING_DELIVERY_BINDING_FOUNDATION_V1','base_head':head,'worktree':str(wt),'owner':'codex:/root/delivery_binding_impl','integrator':'codex:/root','source_paths':paths,'allowed_behavior':'Unexported closed Go DTO/integrity validation plus unnumbered embedded immutable binding schema/read+insert Tx helpers and real fresh domain_objects SQLite tests. No authentication claim. Missing schema remains unsupported.','stable_origin_policy':'Original problem anchor+original requirement content hash+original business input content hash+stable suite semantic ref/hash/version only. Excludes project/Owner/root/new object/approval/command/time; full ref vectors stored separately as provenance. Source inputs must later come from original trusted lineage.','identity_policy':'Separate required Owner/root/Host/workspace/profile snapshots; qualified approval+lineage anchor DB-wide unique. Missing row/rollback never refunds consumed or UNKNOWN native approval.','forbidden':['No numbered migration or migration runner changes','No existing database connection/migration','No public API/normal session.send/planning/finite goal contract changes','No Goal LIVE503 relaxation','No SDK reportRun/modelStream sole-output change','No registry/step_state/failed-count edits','No model/native/paid/provider calls','No automatic schema initialization or backup-production-list change'],'qualification_limits':'Foundational integrity code only; trusted Host producer, approval journal, private plan registration, schema adoption/backup, actual checker and Goal aggregator remain unimplemented.','formal_increment':0,'counter_reset':False,'at':now}
put(out/'scope.json',scope)
resume={'checkpoint_revision':590,'status':'IMPLEMENTING_PRODUCTION_PRIVATE_BINDING_FOUNDATION','main_head':head,'scope_ref':str((out/'scope.json').relative_to(root)),'worktree':str(wt),'formal_accepted':0,'formal_required':42,'formal_increment':0,'failure_records':len(cp['failure_counters']),'next':'Author exact four files, locked offline fresh-SQLite checks, freeze and independent review. Resource controller awaits TOCTOU repair/review and must not run before separate startup scope.'}
put(out/'RESUME.json',resume)
cp['expected_previous_revision']=589;cp['revision']=590;cp['updated_at']=now;cp['next_command']=resume['next']+' Read '+str((out/'RESUME.json').relative_to(root))
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'active_construction_owners':[scope['owner'],'codex:/root/runtime_readiness resource controller repair'],'formal_increment':0}
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp589.before.md').write_bytes(before)
temp=handoff.with_name(handoff.name+'.cp590.new');temp.write_bytes(('# Current resume CP590\n\nRead '+str((out/'RESUME.json').relative_to(root))+'. Production Go private-binding foundation in isolated worktree, exact4newfiles; no numbered migration or old DB/LIVE change. Resource controller TOCTOU fix under independent review; no service started. Formal0/42.\n\n').encode()+before);os.replace(temp,handoff)
print(json.dumps({'checkpoint':590,'base_head':head,'worktree':str(wt),'source_paths':paths,'formal_increment':0}))
