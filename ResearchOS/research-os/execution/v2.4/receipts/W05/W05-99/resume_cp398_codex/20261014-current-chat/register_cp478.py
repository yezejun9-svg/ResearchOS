import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;O=B/'continuation-cp478'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp478.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf8').strip()
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==477 and ow['revision']==263 and len(cp['failure_counters'])==1443
head=git('rev-parse','HEAD');assert head=='c8b7adab9f0c15eb33f235f8d0d9eb205794e376'
assert ref(R/'execution/project_identity.json')['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
assert git('config','user.name')=='ResearchOS Codex' and git('config','user.email')=='researchos-codex@localhost'
baseline=read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')
for x in baseline['protected_source']:assert ref(R/x['path'])['sha256']==x['sha256']
assert len(baseline['protected_source'])==9 and len(git('diff','--name-status').splitlines())==20 and git('diff','--cached','--name-only')==''
native=R/'execution/v2.4/receipts/W17/W17-03/schema24_to25_source_codex/20261014-current-chat/revision01/manifest.json';assert ref(native)['sha256']=='678eb7697a703cae67a65275507c507ca73c7d07647bfece7e825be7d2bf2686'
controller=R/'execution/v2.4/receipts/W17/W17-03/native25_controller_adaptation_codex/20261014-current-chat/adaptation.json'
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
argv=[sys.executable,'-B','-X','utf8',str(R/'.local/worktrees/v24-continuation/spec/v2.4/tools/task_packet.py'),'next','--state',str(sp)]
p=subprocess.run(argv,cwd=R,capture_output=True)
(O/'task-packet.stdout.raw.json').write_bytes(p.stdout);(O/'task-packet.stderr.raw.txt').write_bytes(p.stderr)
assert p.returncode==0;selector=json.loads(p.stdout);assert selector['state_source']=='VALIDATED_FILE' and sp.read_bytes()==raw[sp]
new(O/'verification.json',{'at':now,'head':head,'gitdir':git('rev-parse','--absolute-git-dir'),'common_dir':git('rev-parse','--git-common-dir'),'protected9_unchanged':True,'tracked_dirty_count':20,'staged_empty':True,'identity_ref':ref(R/'execution/project_identity.json'),'git_config_ref':ref(R/'.git/config'),'argv':argv,'native_exit':p.returncode,'state_source':selector['state_source'],'state_ref':ref(sp),'selector_stdout_ref':ref(O/'task-packet.stdout.raw.json'),'formal_increment':0})
resume=read(B/'continuation-cp477/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v56',at=now,checkpoint_revision=478,ownership_revision=264,active_source_cards=[],failure_records_preserved=1443,native25_source_state='REVISION_SUBSET6_FROZEN_PENDING_INDEPENDENT_RECHECK_NATIVE_NOT_RUN',native25_source_head='f80955594bdd0373ae1c961cd02ab6be96f2c196',native25_source_tree='5bce20214223e8292f16a117a83407f52b4bca4a',native25_revision_manifest_ref=ref(native),native25_controller_draft_ref=ref(controller),mu_m1_02_source_state='FROZEN_INDEPENDENT_REVIEW_ACTIVE',mu_m1_02_reviewer='codex:/root/mu_v5_review_resume',next_command='Finish profile Desktop package and independent review, then Root normal reopen preserving committed configmc3f932/schema24. Bridge2 and Core17 independent reviews active; Native25 subset6 frozen for recheck. Root Native25 controller adaptation remains draft pending fixture tests and independent review; no Native signing/original DB action. Formal0/42 all22open, no duplicate codingCONFIRM.')
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=478,expected_previous_revision=477,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp478=rr,native25_revision_manifest_ref=ref(native),native25_controller_draft_ref=ref(controller));cp['evidence_index'].append({'kind':'NATIVE25_SUBSET6_FREEZE_CORE17_INDEPENDENT_REVIEW_CONTROLLER_DRAFT','ref':rr,'formal_increment':0})
ow.update(revision=264,expected_previous_revision=263,updated_at=now,updated_by='codex:/root');ow['special_paths']['native25_signed_stage_revision_status']={'state':'FROZEN_SOURCE_SLOT_RELEASED','source_head':resume['native25_source_head'],'manifest_ref':ref(native)};ow['special_paths']['mu_m1_02_independent_review']={'owner':resume['mu_m1_02_reviewer'],'model':'gpt-6-astra','reasoning_effort':'high','reason':'Independent architectural and Windows runtime review of another author frozen17','source_head':resume['mu_m1_02_source_head'],'write_scope':'execution/v2.4/receipts/W17/W17-03/mu_m1_02_independent_review_codex/20261014-current-chat','product_source_read_only':True}
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/n).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP478\n\nRead `'+rr['path']+'` first. Main c8b7adab; protected9 and dirty20 preserved; selector VALIDATED_FILE. Native25 subset6 frozen, Core17/bridge2 review active, Desktop package pending. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':478,'ownership':264,'failures':1443,'resume':rr,'selector':selector['state_source']}))
