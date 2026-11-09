"""Mirror independently reviewed package and checkpoint controlled normal activation."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path
ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = Path(__file__).parent
OUT = BASE / 'continuation-cp461'
REVIEW = Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/status-package-independent-review-20261014')
MIRROR = ROOT / 'execution/v2.4/receipts/W05/W05-99/qualification_status_package_review_codex/20261014-current-chat'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path': p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size}
def new(p,v):
    with p.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,b,v):
    assert p.read_bytes()==b
    t=p.with_name(p.name+'.cp461.pending')
    with t.open('xb') as f:f.write(v)
    assert p.read_bytes()==b
    os.replace(t,p)
assert sha(REVIEW/'FINAL-report.json')=='063724b8449cb356ab62d0792b6b8b7e04e381e0b15a6ba3d82f385d51f4fe4b'
assert sha(REVIEW/'FINAL-manifest.json')=='a7900144f0b243c4b4731abcc9bb8fb2bd6752db07969fdd9d9d15614676a9d7'
report=read(REVIEW/'FINAL-report.json');assert report['verdict']=='APPROVE_PACKAGE_FOR_ROOT_CONTROLLED_ACTIVATION'
MIRROR.mkdir(parents=True,exist_ok=False)
for m in read(REVIEW/'FINAL-manifest.json')['files']:
    p=REVIEW/m['path'];dest=MIRROR/m['path'];assert p.resolve().is_relative_to(REVIEW.resolve())
    assert sha(p)==m['sha256'] and p.stat().st_size==m['bytes']
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as f:f.write(p.read_bytes())
for name in ['FINAL-report.json','FINAL-manifest.json']:
    dest=MIRROR/name
    if dest.exists(): assert sha(dest)==sha(REVIEW/name)
    else:
        with dest.open('xb') as f:f.write((REVIEW/name).read_bytes())
cp_p=ROOT/'execution/v2.4/checkpoint.json';ow_p=ROOT/'execution/v2.4/path_ownership.json';h_p=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';s_p=ROOT/'execution/v2.4/step_state.json'
raw={p:p.read_bytes() for p in [cp_p,ow_p,h_p,s_p]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==460 and ow['revision']==246 and len(cp['failure_counters'])==1389
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==cp['head']=='454492f78fc0536966c8c8343d4bdd2fd99250b7'
assert sha(ROOT/'.git/config')=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
for m in read(ROOT/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:assert sha(ROOT/m['path'])==m['sha256']
OUT.mkdir(exist_ok=False);now=datetime.datetime.now(datetime.timezone.utc).isoformat()
diagnostics=[
 ('missing-desktop-test-search','rg missing apps/desktop/test; corrected tests/ui/desktop; command e88167'),
 ('missing-backup-test-search','rg missing backup_migration_test.go; corrected directory search; command b0973d'),
 ('review-thread-limit','Two followup_task attempts rejected by active thread limit; no product mutation'),
 ('package-count-wrapper','Builder wrapper expected216 but selected214; child214/214 exit0, wrapper exit1 retained and correction recorded'),
 ('cp460-script-path-read','Read of nonexistent continuation-cp460/register_cp460.py failed; located existing registration scripts; b7f812'),
 ('package-review-initial-checker','Independent checker initial REQUEST value/hash expectation corrected, original raw retained'),
 ('package-review-utf8-read','Independent report default-locale read failed, corrected explicit UTF8, original raw retained')]
for key,detail in diagnostics:
    origin='20261014|'+key
    assert not any(x.get('origin_key')==origin for x in cp['failure_counters'])
    cp['failure_counters'].append({'origin_key':origin,'attempts':2 if key=='review-thread-limit' else 1,'status':'DIAGNOSTIC_PRESERVED','detail':detail,'counter_reset':False,'actual_models':0,'evidence_ref':ref(MIRROR/'FINAL-report.json') if key.startswith('package') else {'tool_output_or_history':detail}})
activation={'schema':'researchos.root-normal-desktop-activation/1','at':now,'package':report['package_root'],'review_ref':ref(MIRROR/'FINAL-report.json'),'review_manifest_ref':ref(MIRROR/'FINAL-manifest.json'),'source_main':cp['head'],'old_electron_pid':65164,'old_core_pid':66364,'old_owned_launcher_session':92285,'normal_close_only':True,'existing_data':'.local/live/current-chat-normal-desktop-first-use-20261012/data','existing_user_data':'.local/live/current-chat-normal-desktop-first-use-20261012/electron-user-data','new_launch_receipts':'execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry08_codex/20261014-current-chat','old_qualification_request':'f04497200c9825ee55142fbb45a6c21d','old_request_confirm':'FORBIDDEN_CONSUMED','next_coding_scope_ref':ref(BASE/'continuation-cp454/normal-coding-configuration-scope.json'),'qualification_calls_authorized_by_activation':0,'task_calls_authorized_by_activation':0,'formal_increment':0}
new(OUT/'activation-scope.json',activation)
resume={'schema':'researchos.current-chat-resume.v39','at':now,'checkpoint_revision':461,'ownership_revision':247,'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99','goal_status':'ACTIVE','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,'failure_records_preserved':len(cp['failure_counters']),'activation_scope_ref':ref(OUT/'activation-scope.json'),'root_schema25':'isolated candidate9 storage/backup tests pass; independent review pending; no Main or realDB integration','mu_m1':'c6f39e84 source/native synthetic frozen, independent review pending; no installed SDK changes','phone_ready':False,'next_command':'Normally close old Desktop and capture owned wait; activate independently reviewed package retaining original data; actual GUI coding configuration then exact new-ref qualification and product-agent repair. Continue independent Mu M1 and Root schema25 review.'}
new(OUT/'RESUME.current.json',resume);rr=ref(OUT/'RESUME.current.json')
cp.update(revision=461,expected_previous_revision=460,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp461=rr,qualification_status_package_review_ref=ref(MIRROR/'FINAL-report.json'),qualification_status_activation_scope_ref=ref(OUT/'activation-scope.json'))
cp['evidence_index'].append({'kind':'DESKTOP_PACKAGE_REVIEW_AND_CONTROLLED_ACTIVATION','ref':rr,'formal_increment':0})
ow.update(revision=247,expected_previous_revision=246,updated_at=now,updated_by='codex:/root')
ow['special_paths']['normal_desktop_activation_cp461']={'owner':'codex:/root','ref':ref(OUT/'activation-scope.json'),'status':'REGISTERED_NORMAL_ACTIVATION'}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(h_p,'handoff.before.raw.md')]: (OUT/name).write_bytes(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode())
replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode())
replace(h_p,raw[h_p],('# Current verified continuation CP461\n\nRead `'+rr['path']+'` first. Reviewed package ready for controlled normal activation preserving original data; all22 parents open and formal0/42.\n\n').encode()+raw[h_p])
assert s_p.read_bytes()==raw[s_p]
print(json.dumps({'checkpoint':461,'ownership':247,'failure_records':len(cp['failure_counters']),'resume':rr,'activation_scope':ref(OUT/'activation-scope.json')}))
