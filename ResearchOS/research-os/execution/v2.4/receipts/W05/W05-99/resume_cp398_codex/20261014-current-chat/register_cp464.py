import datetime,hashlib,json,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;O=B/'continuation-cp464'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp464.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==463 and ow['revision']==249 and len(cp['failure_counters'])==1406
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
old=B/'continuation-cp459/root-schema25-scope.json';scope=read(old);scope.update(schema='researchos.root-schema25-scope-amendment/2',at=now,prior_ref=ref(old),reason_for_amendment='Schema25 is now supported, old future25 test asserts obsolete error category. Preserve fail-closed future-version coverage at26, and malformed25 still rejects.');scope['paths'].append('internal/domain/backup_prepared_abandonment_upgrade_test.go');scope['production_integration']='FORBIDDEN_UNTIL_SEPARATE_SAFE_UPGRADE_ENTRY_REVIEW';new(O/'root-schema25-scope.json',scope)
cp['failure_counters'].append({'origin_key':'20261014|storage-backup-old-future25-assertion','attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':'Broader backup regression17pass1fail. Malformed version25 correctly rejected BACKUP_PAUSE_SCHEMA but old test expected BACKUP_CONFIGURATION_VERSION. Update future test to26, preserve malformed25 assertions; no production gate relaxation.','counter_reset':False,'actual_models':0})
cp['failure_counters'].append({'origin_key':'20261014|root-windows-rg-wildcard-followups','attempts':2,'status':'DIAGNOSTIC_PRESERVED','detail':'Two rg literal backup*.go paths rejected Windows wildcard; corrected directory --glob queries, read only. Tool chunks cc45c3 and 5ccd1e.','counter_reset':False,'actual_models':0})
resume={'schema':'researchos.current-chat-resume.v42','at':now,'checkpoint_revision':464,'ownership_revision':250,'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99','goal_status':'ACTIVE','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,'failure_records_preserved':len(cp['failure_counters']),'storage_scope_ref':ref(O/'root-schema25-scope.json'),'storage_review':'R3 source-fixture accepted; broaderbackup17pass1 obsoletefuture25 assertion; boundedtestscopeamendment underway','coding_any':'exact2 source final freezing; independent review pending','phone_ready':False,'next_command':'Complete any checker independent source review and new normal Core package. Correct bounded future-version test and verify old backup regressions; retain schema25 isolated until safe upgrade entry. Continue M1-02 scope.'}
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=464,expected_previous_revision=463,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp464=rr,root_schema25_scope_ref=ref(O/'root-schema25-scope.json'));cp['evidence_index'].append({'kind':'SCHEMA25_BACKUP_REGRESSION_TEST_SCOPE_AMENDMENT','ref':rr,'formal_increment':0});ow.update(revision=250,expected_previous_revision=249,updated_at=now,updated_by='codex:/root');ow['special_paths']['root_schema25_storage']={'owner':'codex:/root','ref':ref(O/'root-schema25-scope.json'),'paths':scope['paths'],'worktree':scope['worktree']}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]: (O/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP464\n\nRead `'+rr['path']+'` first. Schema25 storage accepted only within isolated fixture scope; old future-version regression needs bounded update. Main d9fc/M1-01, any checker pending. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':464,'ownership':250,'failures':len(cp['failure_counters']),'resume':rr,'scope':ref(O/'root-schema25-scope.json')}))
