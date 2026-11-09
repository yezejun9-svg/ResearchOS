import datetime,json,os
from pathlib import Path
from preserve_desktop_main_ecc28 import verify
from preserve_main_baseline import read,ref,git,R,N
BASE='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419';W=R/'.local/worktrees/desktop-installed-delivery-20261025';BRANCH='desktop-installed-delivery-20261025'
def new(p,v):
 with p.open('x',encoding='utf8')as s:json.dump(v,s,ensure_ascii=False,indent=2);s.write('\n')
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp557.pending')
 with q.open('xb')as s:s.write(v)
 assert p.read_bytes()==b;os.replace(q,p)
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']];raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==556 and ow['revision']==342 and len(cp['failure_counters'])==2251
preserved=verify();assert not W.exists()and not git(R,'branch','--list',BRANCH).strip()
V=N.parent.parent/'desktop_main7d_independent_review_codex/20261025-current-chat/delivery-contract-audit-20261025'
assert ref(V/'AUDIT-SEAL.json')['sha256']=='c6172593c0029a6d2f6aaf6fb9aa2e7b2b5f4ebf72c04965c2a5d746ae0eee6d'
seal=read(V/'AUDIT-SEAL.json');assert ref(V/'AUDIT-MANIFEST.json')['sha256']==seal['manifest_sha256'];manifest=read(V/'AUDIT-MANIFEST.json');assert manifest['verdict']=='DELIVERY_GAPS_CONFIRMED_OWNED_IMPLEMENTATION_CAN_PROCEED'
refs=[]
for x in manifest['refs']:
 a=ref(V/x['path']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
assert len(refs)==seal['refs']==39
O=N/'continuation-cp557';O.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
scope={'schema':'researchos.installed-delivery-worktree-setup.v1','at':now,'owner':'codex:/root','operation':'CREATE_NEW_ISOLATED_WORKTREE_ONLY','base':BASE,'worktree':str(W),'branch':BRANCH,'source_edit_authority':False,'authoritative_contract_audit_ref':ref(V/'AUDIT-SEAL.json'),'purpose':'Prepare actual installed CLI/Desktop delivery development; persistent user state/shared Core and installation lifecycle are requirements, not replaced by fresh-state-only launcher','source_scope_requires_followup_registration':True,'no_original_data_or_process_actions':True,'C57_admin_status':'USER_PREPARING_NOT_VERIFIED','card_acceptance':False,'formal_increment':0}
new(O/'Installed-delivery-setup-scope.json',scope);new(O/'Root-contract-audit-verification.json',{'verified_refs':refs,'preserved':preserved,'formal_increment':0})
prior=read(N/'continuation-cp556/RESUME.current.json');resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v135',at=now,checkpoint_revision=557,ownership_revision=343,installed_delivery_setup_scope_ref=ref(O/'Installed-delivery-setup-scope.json'))
resume['next_command']='Root create fresh Desktop installed-delivery worktree from Main ecc28 under registered setup-only scope, then register exact source implementation after architecture review. Actual per-user persistent CLI/Desktop shared Core and install/upgrade/uninstall required; fresh dev launcher cannot substitute. No W20 dependency bypass or formal acceptance. C57 admin USER_PREPARING_NOT_VERIFIED; all history preserved, mixed2251.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=557,expected_previous_revision=556,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp557=rr,installed_delivery_setup_scope_ref=ref(O/'Installed-delivery-setup-scope.json'));cp['evidence_index'].append({'kind':'INSTALLED_DELIVERY_CONTRACT_GAPS_VERIFIED_AND_NEW_WORKTREE_SETUP_SCOPED','ref':rr,'formal_increment':0});ow.update(revision=343,expected_previous_revision=342,updated_at=now,updated_by='codex:/root');ow['special_paths']['Installed_delivery_development']={'owner':'codex:/root','state':'SETUP_REGISTERED_SOURCE_WRITES_CLOSED','worktree':str(W),'source_edit_authority':False,'scope_ref':ref(O/'Installed-delivery-setup-scope.json')}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as s:s.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());swap(hp,raw[hp],('# Current verified continuation CP557\n\nRead '+rr['path']+' first. Installed-delivery requirements independently audited; setup-only scope for new ecc28 worktree. No source edit authority yet. Main/old candidates/data protected. C57 administrator preparing, not verified. Mixed2251;formal0/42/all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':557,'ownership':343,'scope':ref(O/'Installed-delivery-setup-scope.json'),'resume':rr,'verified_contract_refs':39,'formal_increment':0},ensure_ascii=False))
