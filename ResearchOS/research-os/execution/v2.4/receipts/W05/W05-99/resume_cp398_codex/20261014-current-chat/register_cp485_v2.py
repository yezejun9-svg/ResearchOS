import datetime,hashlib,json,os,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os'); B=Path(__file__).parent; O=B/'continuation-cp485'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
 assert p.read_bytes()==b
 t=p.with_name(p.name+'.cp485.pending')
 with t.open('xb') as f:f.write(v)
 assert p.read_bytes()==b;os.replace(t,p)
cp_p=R/'execution/v2.4/checkpoint.json';ow_p=R/'execution/v2.4/path_ownership.json';hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';sp=R/'execution/v2.4/step_state.json';raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==484 and ow['revision']==270 and len(cp['failure_counters'])==1466
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='c8b7adab9f0c15eb33f235f8d0d9eb205794e376'
assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
assert len(subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=R,text=True).splitlines())==20
e=R/'execution/v2.4/receipts/W05/W05-99';n=R/'execution/v2.4/receipts/W17/W17-03';case=n/'native25_actual_root_codex/20261014-current-chat/positive-replay-02';review=n/'native25_controller_independent_review_codex/20261014-current-chat/actual-positive02';author=n/'mu_m1_02_second_pause_source_codex/20261014-current-chat'
assert ref(review/'FINAL-report.json')['sha256']=='aebd803403ace3474d18a1cac845beec1992234b08f6ca34cd1207bff655c330'
assert ref(review/'manifest.json')['sha256']=='ae25ee1fec7a3ce8fa0c0b305a008492116167f4a452a2a8798c912ff7112da8'
assert ref(author/'source-manifest.json')['sha256']=='b1b58c12a003dbe39395c632cedae3e100a2eefbf5bf7bf0eedd9b8ff9c59556'
assert ref(author/'attempt-ledger.json')['sha256']=='8d950ba5f7d3548ee7ad58c175e2f6788ce8b31c88882a8564b50078d242ad14'
assert read(review/'FINAL-report.json')['outer_test_exit']==0
assert ref(R/'execution/project_identity.json')['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
for x in read(e/'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert ref(R/x['path'])['sha256']==x['sha256']
O.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
records=[('core-second-pause-final-author-reconciliation',8,'Final 23 attempts:11FAIL/11PASS/1SKIP. Prior CP483 aggregate lowerbound3 retained; add remaining8 only. Author maps lowerbound to02-04 but historical description also named06; aggregate subtraction avoids double count and keeps both histories.',ref(author/'attempt-ledger.json')),('core-second-pause-native-omitted-enable-skip',1,'13-native-budget exited0 but SKIP because required flags omitted; never treated as PASS.',ref(author/'attempt-ledger.json')),('native25-case02-independent-checker-failures',5,'Two grant, two terminal, one final closure checker failures retained; later corrections passed without source/fixture mutation.',ref(review/'FINAL-report.json')),('root-native25-final-report-wrong-cwd-read',1,'Relative final-report read from sparse source worktree failed; corrected read from main receipt root. Evidence and Source unchanged.',None)]
records.append(('root-cp485-manifest-filename-read',1,'Initial CP485 registrar used FINAL-manifest.json but reviewer file is manifest.json. Failed before O mkdir or shared mutation; original script preserved.',None))
for key,count,detail,evidence in records:
 entry={'origin_key':'20261014|'+key,'attempts':count,'status':'FAILED_OR_NONPASS_PRESERVED','detail':detail,'counter_reset':False}
 if evidence:entry['evidence_ref']=evidence
 assert not any(x.get('origin_key')==entry['origin_key'] for x in cp['failure_counters']);cp['failure_counters'].append(entry)
resume=read(B/'continuation-cp484/RESUME.current.json');resume.update(schema='researchos.current-chat-resume.v63',at=now,checkpoint_revision=485,ownership_revision=271,native25_positive_state='CASE02_INDEPENDENTLY_ACCEPTED_ISOLATED_POSITIVE_REPLAY_OUTER_EXIT0_ALL_CLOSED',native25_actual={'state':'CLOSED','owned_exec_session':30975,'actual_outer_exit':0,'config_ref':ref(case/'controller.public.config.json'),'closed_ref':ref(case/'controller/controller.closed.json'),'independent_report_ref':ref(review/'FINAL-report.json'),'independent_manifest_ref':ref(review/'manifest.json'),'negative_cases_run':0,'negative_cases_required':8},core_second_pause_frozen={'commit':'36b2634bfebe6201a14b7661f2dce32b7f1a5098','tree':'bea72c5cdbb341e4d67bd91331803ec6e8013e3b','manifest_ref':ref(author/'source-manifest.json'),'attempts_ref':ref(author/'attempt-ledger.json'),'independent_review':'ACTIVE_NO_ACCEPTANCE','suspected_periodic_heartbeat_after_second_pause':'Independent actual17second native probe pending'},next_command='Continue8 Native25 negatives in fresh namespaces with concrete Root reviews; positive02 fully closed/accepted isolated only. Core exact9 frozen independent reviewer probing >15second PAUSE heartbeat and full successor rollback. Verifier exact8 source+Windows tests underway. No actualDesktop qualification until formal verifier replacement implemented/reviewed/installed. Formal0/42 all22open; no reset.')
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json');cp.update(revision=485,expected_previous_revision=484,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp485=rr,native25_actual=resume['native25_actual'],core_second_pause_frozen=resume['core_second_pause_frozen']);cp['evidence_index'].append({'kind':'NATIVE25_POSITIVE_REPLAY_INDEPENDENT_CLOSED_CORE_EXACT9_FROZEN','ref':rr,'formal_increment':0});ow.update(revision=271,expected_previous_revision=270,updated_at=now,updated_by='codex:/root');ow['special_paths']['native25_controller'].update(native_execution='CASE02_CLOSED_ISOLATED_ACCEPTED_NEGATIVES0_OF8')
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:(O/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());replace(hp,raw[hp],('# Current verified continuation CP485\n\nRead `'+rr['path']+'` first. Native25positive02 independent accepted isolated only, outer30975 actual0/allclosed; negatives0/8. Core9 frozen36b2634b independent review active. Verifier8 implementation/tests active. ActualDesktop65576/68388 owned26133 remains schema24; no qualification retry. Formal0/42 all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':485,'ownership':271,'failure_records':len(cp['failure_counters']),'resume':rr}))
