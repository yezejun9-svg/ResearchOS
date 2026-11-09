import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;O=B/'continuation-cp470'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp470.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==469 and ow['revision']==255 and len(cp['failure_counters'])==1412
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==cp['head']=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
review=R/'execution/v2.4/receipts/W05/W05-99/coding_any_desktop_package_review_codex/20261014-current-chat';rp=review/'FINAL-report.json';mp=review/'FINAL-manifest.json'
assert ref(rp)['sha256']=='c03c6e240fd7758668a3b2650e1dd60b5e24c526e1d09a1e622d1ee81a0254da'
assert ref(mp)['sha256']=='734733dd8bd30dbf04a9da9491ef968e699b153af7dbe7a08e48e97ebd3fa7f7'
report=read(rp);assert report['verdict']=='APPROVE_PACKAGE_FOR_ROOT_CONTROLLED_ACTIVATION' and not report['findings']
audit=read(review/'package-audit.json');assert len(audit['package_members'])==58
for m in audit['package_members']:assert ref(Path(m['path']))['sha256']==m['sha256']
for m in read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(R/m['path'])['sha256']==m['sha256']
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
scope={'schema':'researchos.normal-desktop-activation-coding-any/1','at':now,'owner':'codex:/root','review_ref':ref(rp),'review_manifest_ref':ref(mp),'package':report['package_root'],'package_member_count_rehashed':58,'old_desktop_pid':65728,'old_core_pid':61952,'old_launcher_session':94341,'old_window':921388,'cdp_port':13769,'data_root':str(R/'.local/live/current-chat-normal-desktop-first-use-20261012/data'),'user_data':str(R/'.local/live/current-chat-normal-desktop-first-use-20261012/electron-user-data'),'receipts':'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry09_codex/20261014-current-chat','requirements':['Capture visible original UI, exact observed WM_CLOSE only, retain owned numeric process.wait from session94341. No kill or second active Desktop/Core','Launch reviewed normal package through owned launch_and_wait.py preserving original data/userData and defaultMu8df; migrations only1..24; never initialize/migrate schema25','Actual DOM/native folder selection config retry uses unchanged CP454 scope read326/write2, prepare and review native consent only; model0/tool0. New qualification/task require actual new binding','Do not resubmit old consumed qualification request. Native/Core exit are separate from Electron exit; no inferred stderr or private frame claims'],'coding_configuration_scope_ref':ref(B/'continuation-cp454/normal-coding-configuration-scope.json'),'model_calls':0,'tool_calls':0,'formal_increment':0}
new(O/'normal-activation-scope.json',scope)
cp['failure_counters'].append({'origin_key':'20261014|coding-any-independent-react-layout','attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':'Independent small React fixture omitted relative design-tokens layout. Original failure retained; corrected exact source layout produced byte-identical three assets exit0.','counter_reset':False,'evidence':ref(rp)})
resume=read(B/'continuation-cp469/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v48',at=now,checkpoint_revision=470,ownership_revision=256,failure_records_preserved=len(cp['failure_counters']),normal_package_review_ref=ref(rp),normal_package_review='APPROVE_PACKAGE_FOR_ROOT_CONTROLLED_ACTIVATION',activation_scope_ref=ref(O/'normal-activation-scope.json'),next_command='Normal WM_CLOSE oldDesktop65728 and actual owned wait94341, launch reviewed fresh package preserving data, retry unchanged coding GUI scope. Two isolated source cards continue.')
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=470,expected_previous_revision=469,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp470=rr,normal_coding_any_activation_scope_ref=ref(O/'normal-activation-scope.json'));cp['evidence_index'].append({'kind':'INDEPENDENT_NORMAL_PACKAGE_ACCEPTED_ACTIVATION_SCOPE','ref':rr,'formal_increment':0});ow.update(revision=256,expected_previous_revision=255,updated_at=now,updated_by='codex:/root');ow['special_paths']['normal_coding_any_activation']={'owner':'codex:/root','ref':ref(O/'normal-activation-scope.json'),'source_writes':False}
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP470\n\nRead `'+rr['path']+'` first. Normal package independently accepted for controlled activation. Source Core exact16/native upgrade exact22 continue. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':470,'ownership':256,'failures':len(cp['failure_counters']),'scope':ref(O/'normal-activation-scope.json'),'resume':rr}))
