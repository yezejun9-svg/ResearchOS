import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); B=Path(__file__).parent; O=B/'continuation-cp469'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp469.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==468 and ow['revision']==254 and len(cp['failure_counters'])==1411
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==cp['head']=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
prior=B/'continuation-cp466/mu-m1-02-source-scope.json';scope=read(prior);assert len(scope['paths'])==15
scope.update(schema='researchos.mu-m1-02-source-scope/2',at=now,supersedes=ref(prior));scope['paths'].append('internal/domain/durability.go')
scope['requirements'].extend(['Exact16 extension permits only prepareEffectTx/beginEffectTx pause admission/drain fences in durability.go; no generic ResumeCheckpoint rewrite','New effect keys cannot be admitted during pause even through internal PrepareEffect. Idempotent query of existing key does not authorize redispatch. Only already durable PREPARED cut-before effect at exact current epoch/activeRun with PAUSE_REQUESTED may start while Task BLOCKED; preserve Goal/lease/budget/context/cancel gates','Tests must cover legal cut-before PREPARED once, ordinary BLOCKED, stale epoch, newkey/no extra reservation, cancel races, expired lease, STARTED/UNKNOWN replay denial. No old schema or unrelated flow acceptance weakening'])
new(O/'mu-m1-02-source-scope-v2.json',scope)
cp['failure_counters'].append({'origin_key':'20261014|root-desktop-coding-wildcard-query','attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':'rg received literal Windows path apps/desktop/main/coding* and rejected syntax; source search corrected to directory with globs. No mutation or model call.','counter_reset':False})
resume=read(B/'continuation-cp468/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v47',at=now,checkpoint_revision=469,ownership_revision=255,failure_records_preserved=len(cp['failure_counters']),mu_m1_02_extended_scope_ref=ref(O/'mu-m1-02-source-scope-v2.json'),active_source_cards=['CP469 CoreM1-02 exact16','CP467 schema24to25 native exact22'])
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=469,expected_previous_revision=468,updated_at=now,updated_by='codex:/root');cp['work_in_progress'].update(current_chat_continuation_cp469=rr,mu_m1_02_extended_scope_ref=ref(O/'mu-m1-02-source-scope-v2.json'));cp['evidence_index'].append({'kind':'PAUSE_DURABLE_EFFECT_EXACT16_SCOPE_EXTENSION','ref':rr,'formal_increment':0});ow.update(revision=255,expected_previous_revision=254,updated_at=now,updated_by='codex:/root');ow['special_paths']['mu_m1_02_extended_source']={'owner':scope['owner'],'ref':ref(O/'mu-m1-02-source-scope-v2.json'),'paths':scope['paths'],'worktree':scope['worktree']};ow['path_lease_transfers'].append({'at':now,'actor':'codex:/root','new_owner':scope['owner'],'new_subtask':'W17-03/M1-02-durable-effect-drain','new_worktree':scope['worktree'],'paths':['internal/domain/durability.go'],'scope_ref':ref(O/'mu-m1-02-source-scope-v2.json'),'kind':'ISOLATED_SOURCE_LEASE_EXTENSION'})
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP469\n\nRead `'+rr['path']+'` first. Core pause source scope exact16 includes durable-effect drain fence; native upgrade exact22; normal package review pending. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':469,'ownership':255,'failures':len(cp['failure_counters']),'scope':ref(O/'mu-m1-02-source-scope-v2.json'),'resume':rr}))
