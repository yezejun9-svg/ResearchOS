import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent/'continuation-cp463'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp463.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==462 and ow['revision']==248 and len(cp['failure_counters'])==1405
integration=R/'execution/v2.4/receipts/W17/W17-03/mu_m1_01_source_codex/20261014-current-chat/integration.json';ir=read(integration);assert ref(integration)['sha256']=='8a3e032499976b23f0df0305214ebb3b7f2c92b49ab727ff048550e523ac920a'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();assert head==ir['after'] and cp['head']==ir['before']
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
for m in read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(R/m['path'])['sha256']==m['sha256']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['failure_counters'].append({'origin_key':'20261014|storage-r2-empty-subtest-path','attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':'Independent R2 rerun found empty subtest name #00 URI path truncation reused escaped SQLite fixture and duplicate schema_migrations version. Original evidence retained; case named valid, author12top PASS; independent final rerun pending. store.Open URI issue retained as separate debt.','counter_reset':False,'actual_models':0})
resume={'schema':'researchos.current-chat-resume.v41','at':now,'checkpoint_revision':463,'ownership_revision':249,'head':head,'project_id':cp['project_id'],'current_step_id':'W05-99','goal_status':'ACTIVE','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,'failure_records_preserved':len(cp['failure_counters']),'mu_m1_source_integration_ref':ref(integration),'coding_any_scope_ref':ref(Path(__file__).parent/'continuation-cp462/source-scope.json'),'live_desktop_pid':65728,'live_core_pid':61952,'live_launcher_session':94341,'root_storage':'isolated storage candidate, author12top PASS after fixture correction; independent final pending; must remain OUT of normal Main/package until reviewed backup+production upgrade entry exists','M1_02':'bounded readonly implementation scope preparation underway','phone_ready':False,'next_command':'Finish exact2 Go any checker source review/build/normal GUI retry. Keep schema25 isolated while final storage review and M1-02 scope progress; create safe upgrade entry before real database migration. Mu M1 source integrated but no live candidate SDK activation.'}
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=463,expected_previous_revision=462,head=head,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp463=rr,mu_m1_source_integration_ref=ref(integration));cp['evidence_index'].append({'kind':'REVIEWED_MU_M1_SOURCE_INTEGRATION_AND_STORAGE_HOLD','ref':rr,'formal_increment':0})
ow.update(revision=249,expected_previous_revision=248,updated_at=now,updated_by='codex:/root');ow['special_paths']['mu_m1_01_integrated']={'owner':'codex:/root','ref':ref(integration),'status':'SOURCE_NATIVE_SYNTHETIC_INTEGRATED_NO_LIVE_ACTIVATION'}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]: (O/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP463\n\nRead `'+rr['path']+'` first. Main includes independently reviewed M1-01 exact8; coding any repair ongoing. schema25 remains isolated pending upgrade entry. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':463,'ownership':249,'head':head,'failures':len(cp['failure_counters']),'resume':rr}))
