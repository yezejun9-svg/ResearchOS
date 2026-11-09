import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); B=Path(__file__).parent; O=B/'continuation-cp488'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp488.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)



cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==487 and ow['revision']==273 and len(cp['failure_counters'])==1483
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='c8b7adab9f0c15eb33f235f8d0d9eb205794e376'
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
e=R/'execution/v2.4/receipts/W05/W05-99';n=R/'execution/v2.4/receipts/W17/W17-03';a=n/'mu_m1_02_second_pause_source_codex/20261014-current-chat/revision02';nb=n/'native25_actual_root_codex/20261014-current-chat'
assert ref(a/'source-manifest.json')['sha256']=='5602a05c2e61c07aadf1bf6d4a39a8474bbbd26321f2690be50ab8c37224ef41'
assert ref(nb/'missing-native-channel-03/controller/controller.closed.json')['sha256']=='6193e5491e59a6e7589e6d3685b1bda463a8e79291b2bf19553659ad9e234ba8'
assert ref(R/'execution/project_identity.json')['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
for x in read(e/'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(R/x['path'])['sha256']==x['sha256']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for key,count,detail in [('core-r2-author-compile',1,'revision02 initial native compile failed test bracket syntax; later6 commandsPASS, no skip. Prior histories unchanged.'),('native25-missing-channel03-deadline',1,'Native65408 actualexit1 precise private-channel rejection and signatures independently verified, but harness62164 cleanup hold1200s deadline and owned48946 exit1. No fixture releaseapproval; not accepted.'),('native25-missing-channel03-fresh-sql',2,'Root readonly SQL and independent reviewer native ID reads failed because fixture already removed at20min deadline; no fabricated freshSQL or acceptance.'),('verifier-builder-context-recovery',1,'Builder context reset/recovery tool unavailable; Root redelivered exactCP487 scope and existing revision plan. No state reset/source discard authorized.')]:
 cp['failure_counters'].append({'origin_key':'20261014|'+key,'attempts':count,'status':'FAILED_OR_DIAGNOSTIC_PRESERVED','detail':detail,'counter_reset':False})
resume=read(B/'continuation-cp487/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v66',at=now,checkpoint_revision=488,ownership_revision=274,core_r2_frozen={'commit':'8f50cb57ff821554aef17e9a9bd5208935489d50','tree':'361ead86ee812d5e040fe1d2cde2a92297eb639f','manifest_ref':ref(a/'source-manifest.json'),'attempt_ledger_ref':ref(a/'attempt-ledger.json'),'state':'FROZEN_INDEPENDENT_REVIEW_ACTIVE'},native25_negative_state={'accepted':0,'required':8,'attempt03_closed_ref':ref(nb/'missing-native-channel-03/controller/controller.closed.json'),'attempt03_outer_exit':1,'attempt03_native_rejection_observed_but_freshSQL_and_outer_completion_failed':True,'attempt04_config_ref':ref(nb/'missing-native-channel-04/controller.public.config.json'),'attempt04_state':'PREPARED_NOT_STARTED_WAITING_INDEPENDENT_READONLY_OBSERVER','root_explicit_phase_helper_ref':ref(nb/'root_explicit_phase_v2.py')},next_command='Start nativecase04 only after independently-owned readonly observer is actually ready; execute prepared Root explicit phase helper per exact reviewed snapshot to meet originalTTL. RootfinalfreshSQL/release/actualwait mandatory. Core8f50 independent reviewactive. VerifierF1F2 revision implementation active. No actualproduct change; formal0/42 all22open.')
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=488,expected_previous_revision=487,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp488=rr,core_r2_frozen=resume['core_r2_frozen'],native25_negative_state=resume['native25_negative_state']);cp['evidence_index'].append({'kind':'CORE_R2_FROZEN_NATIVE_NEGATIVE03_FAILED04_PREPARED','ref':rr,'formal_increment':0});ow.update(revision=274,expected_previous_revision=273,updated_at=now,updated_by='codex:/root')
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP488\n\nRead `'+rr['path']+'` first. Core8f50 frozen independent review; verifierF1F2 revision active. Nativecase03 observed rejection butdeadlineclosedfailed,04prepared notstarted. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':488,'ownership':274,'failure_records':len(cp['failure_counters']),'resume':rr}))
