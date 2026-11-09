import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;O=B/'continuation-cp471'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp471.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==470 and ow['revision']==256 and len(cp['failure_counters'])==1413
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==cp['head']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
e=R/'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry09_codex/20261014-current-chat/01-shutdown-refused-native.json';assert any(x['Name']=='SHUTDOWN_REFUSED' for x in read(e)['observed'])
cp['failure_counters'].append({'origin_key':'20261014|normal-desktop-retry08-shutdown-refused','attempts':1,'status':'OPEN_DIAGNOSIS','detail':'Ordinary exact WM_CLOSE65728 refused by product native warning SHUTDOWN_REFUSED. Dismissed warning, retained Electron/Core and owned wait94341; no kill, no new instance, no DB mutation by observer, no new model. Independent readonly diagnosis active.','counter_reset':False,'evidence':ref(e)})
resume=read(B/'continuation-cp470/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v49',at=now,checkpoint_revision=471,ownership_revision=257,failure_records_preserved=len(cp['failure_counters']),normal_package_activation='HELD_AFTER_REAL_SHUTDOWN_REFUSED',shutdown_refusal_ref=ref(e),next_command='Resolve actual normal-close SHUTDOWN_REFUSED through readonly exact oldpackage diagnosis and product path; do not kill/retry blindly/start secondinstance. Fresh package remains independently approved, not activated. Core16/native22 source work continues.')
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=471,expected_previous_revision=470,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp471=rr,normal_shutdown_refusal_ref=ref(e));cp['evidence_index'].append({'kind':'ACTUAL_NORMAL_DESKTOP_SHUTDOWN_REFUSED','ref':rr,'formal_increment':0});ow.update(revision=257,expected_previous_revision=256,updated_at=now,updated_by='codex:/root')
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP471\n\nRead `'+rr['path']+'` first. Actual oldDesktop close refused SHUTDOWN_REFUSED; preserve PID65728/Core61952/ownedwait94341, fresh approved package not yet active. Two isolated source cards continue. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':471,'ownership':257,'failures':len(cp['failure_counters']),'resume':rr}))
