import datetime, hashlib, json, os, subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp468'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p): return {'path': p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}
def new(p, v):
    with p.open('x', encoding='utf8') as f: json.dump(v, f, ensure_ascii=False, indent=2); f.write('\n')
def replace(p, before, value):
    assert p.read_bytes() == before
    t = p.with_name(p.name + '.cp468.pending')
    with t.open('xb') as f: f.write(value)
    assert p.read_bytes() == before
    os.replace(t, p)

cp_p=R/'execution/v2.4/checkpoint.json'; ow_p=R/'execution/v2.4/path_ownership.json'; hp=R/'execution/v2.4/HANDOFF_RESUME_PACK.md'; sp=R/'execution/v2.4/step_state.json'
raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]}; cp=read(cp_p); ow=read(ow_p)
assert cp['revision']==467 and ow['revision']==253 and len(cp['failure_counters'])==1409
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==cp['head']=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2'
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
assert ref(R/'execution/project_identity.json')['sha256']=='03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
for m in read(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R/m['path'])['sha256']==m['sha256']
build=R/'execution/v2.4/receipts/W05/W05-99/coding_any_desktop_build_codex/20261014-current-chat/FINAL-manifest.json'
assert ref(build)['sha256']=='544657c2e5b8f121289ac5de133ae010d432653561806c12bca8bf601cca3d98'
O.mkdir(exist_ok=False); now=datetime.datetime.now(datetime.timezone.utc).isoformat()
argv=['python','-B','-X','utf8',str(R/'.local/worktrees/v24-continuation/spec/v2.4/tools/task_packet.py'),'next','--state',str(sp)]
p=subprocess.run(argv,cwd=R,capture_output=True)
(O/'task-packet.stdout.raw.json').write_bytes(p.stdout); (O/'task-packet.stderr.raw.txt').write_bytes(p.stderr)
packet=json.loads(p.stdout); assert p.returncode==0 and packet['state_source']=='VALIDATED_FILE' and packet['product_acceptance']=='NOT_ASSERTED' and packet['step']['id']=='W05-99'
new(O/'task-packet.command.json',{'argv':argv,'exit':p.returncode,'stdout':ref(O/'task-packet.stdout.raw.json'),'state':ref(sp)})
cp['failure_counters'].extend([
 {'origin_key':'20261014|coding-any-package-validator-cwd','attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':'Author first validator suite used incorrect working directory; raw failure retained in frozen package manifest. Corrected invocation passed. Package independent review pending.','counter_reset':False,'evidence':ref(build)},
 {'origin_key':'20261014|root-native-harness-source-path','attempts':1,'status':'DIAGNOSTIC_PRESERVED','detail':'Read of guessed Main internal/domain/native_migration_authority_harness_windows_test.go failed; actual historical harness located in immutable formal evidence. No source or authority mutation.','counter_reset':False}
])
resume={'schema':'researchos.current-chat-resume.v46','at':now,'checkpoint_revision':468,'ownership_revision':254,'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99','goal_status':'ACTIVE','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,'failure_records_preserved':len(cp['failure_counters']),'normal_package_build_ref':ref(build),'normal_package_review':'codex:/root/attach_review_resume ACTIVE; not activated','active_source_cards':['CP466 CoreM1-02 exact15','CP467 schema24to25 native exact22'],'live_desktop_pid':65728,'live_core_pid':61952,'live_launcher_session':94341,'native_enrollment_resource':'Existing same-project purpose-specific resources located; author cannot self-sign; Root to review fresh exact isolated fixture before any official enrollment CLI signing. No original product DB action.','phone_ready':False,'next_command':'Finish independent new normal package review, register activation scope, normal WM_CLOSE/wait and launch with preserved data; real GUI retry unchanged coding scope. Continue isolated Core/native source cards.'}
new(O/'RESUME.current.json',resume); rr=ref(O/'RESUME.current.json')
cp.update(revision=468,expected_previous_revision=467,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp468=rr,coding_any_normal_package_ref=ref(build)); cp['evidence_index'].append({'kind':'FRESH_NORMAL_PACKAGE_FROZEN_REVIEW_PENDING','ref':rr,'formal_increment':0})
ow.update(revision=254,expected_previous_revision=253,updated_at=now,updated_by='codex:/root'); ow['special_paths']['coding_any_normal_package_review']={'owner':'codex:/root/attach_review_resume','source_writes':False,'package_writes':False,'ref':ref(build)}
for p,n in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]: (O/n).write_bytes(raw[p])
for p,b in raw.items(): assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode()); replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode()); replace(hp,raw[hp],('# Current verified continuation CP468\n\nRead `'+rr['path']+'` first. Fresh normal package frozen, independent review pending; old Desktop retained. Two isolated source cards active. Formal0/42 all22open.\n\n').encode()+raw[hp]); assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':468,'ownership':254,'failures':len(cp['failure_counters']),'resume':rr}))
