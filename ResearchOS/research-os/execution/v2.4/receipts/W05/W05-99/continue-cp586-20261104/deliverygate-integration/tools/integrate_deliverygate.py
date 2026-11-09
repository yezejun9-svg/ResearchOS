import argparse,json,hashlib,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os');cbase=Path(__file__).resolve().parent
parent=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104';out=parent/'deliverygate-integration'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):
    temporary=path.with_name(path.name+'.new');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
p=argparse.ArgumentParser();p.add_argument('--review-sha',required=True);args=p.parse_args()
review=out/'reviews/integration-readiness.json';assert sha(review)==args.review_sha
scope=json.loads((out/'scope.json').read_bytes());wt=Path(scope['worktree']);files=scope['files']
checks=json.loads((out/'checks-03/result.json').read_bytes());assert checks['exit_code']==0 and not checks['failed']
assert git(root,'rev-parse','HEAD').strip()==scope['base_head'] and git(wt,'rev-parse','HEAD').strip()==scope['base_head']
assert not git(wt,'diff','--cached','--name-only').strip()
assert not (out/'integration-journal.json').exists(),'Inspect uncertain state, do not replay'
protected=json.loads((root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']
for path,digest in protected.items():assert (sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE')==digest,path
for path,digest in files.items():assert sha(wt/path)==digest,path
assert sha(wt/'go.mod')==sha(root/'go.mod') and sha(wt/'go.sum')==sha(root/'go.sum')
git(wt,'diff','--check');put(out/'integration-journal.json',{'status':'VERIFIED_BEFORE_COMMIT','files':files,'review_sha256':args.review_sha})
git(wt,'add','--',*files);assert set(git(wt,'diff','--cached','--name-only').splitlines())==set(files)
commit=git(wt,'commit','-m','feat(delivery): add bounded pure scalar source validation primitive')
head=git(wt,'rev-parse','HEAD').strip();put(out/'integration-journal.json',{'status':'COMMITTED','candidate':head,'files':files,'commit_output':commit})
git(root,'merge','--ff-only',head)
for path,digest in files.items():assert sha(root/path)==digest,path
for path,digest in protected.items():assert (sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE')==digest,path
result={'status':'SOURCE_PRIMITIVE_INTEGRATED_NOT_BUSINESS_ACCEPTANCE_WIRING','main_head':head,'main_tree':git(root,'rev-parse','HEAD^{tree}').strip(),'base_head':scope['base_head'],'files':files,'review_sha256':args.review_sha,'checks_ref':str((out/'checks-03/result.json').relative_to(root)),'protected_preserved':True,'ordinary_LIVE503_unchanged':True,'registry41_unchanged':True,'business_DB_unchanged':True,'formal_increment':0}
put(out/'integration.json',result)
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw);assert cp['revision']==588 and len(cp['failure_counters'])==2386
(out/'checkpoint.cp588.before-integration.json').write_bytes(raw)
now=datetime.now(timezone.utc).isoformat();initial=cp['failure_counters'][:]
events=[{'origin_key':'20261104|deliverygate-integration|test-harness-parent','status':'TEST_CONTROLLER_PRE_TEST_FAILURE','tool_chunk':'a963be','exit':1,'go_tests_executed':0,'detail':'New worktree .local parent missing. Original checks01 preserved; only controller path creation repaired.'},{'origin_key':'20261104|deliverygate-integration|standalone-test-import','status':'TEST_PACKAGE_SETUP_FAILURE','tool_chunk':'809ec3','exit':1,'go_tests_executed':0,'detail':'C standalone module import remained in external test package. Original checks02 retained; only test import adapted to real internal path and existing offline module cache. Checks03 passed; validator implementation unchanged.'}]
for event in events:cp['failure_counters'].append(dict(at=now,attempts=1,counter_reset=False,**event))
doc=json.loads(review.read_bytes())
for i,event in enumerate(doc.get('diagnostics',[])):cp['failure_counters'].append({'at':now,'origin_key':f'20261104|deliverygate-integration|independent-read|{i}','attempts':1,'status':'READONLY_REVIEW_DIAGNOSTIC','detail':event,'counter_reset':False})
assert cp['failure_counters'][:2386]==initial
cp['expected_previous_revision']=588;cp['revision']=589;cp['updated_at']=now;cp['head']=head;cp['current_Main_HEAD']=head;cp['current_Main_tree']=result['main_tree']
cp['current_effective_formal_status']['current_head']=head;cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
resume={'checkpoint_revision':589,'status':result['status'],'main_head':head,'main_tree':result['main_tree'],'source_files':2,'integration_ref':str((out/'integration.json').relative_to(root)),'failure_records':len(cp['failure_counters']),'counter_reset':False,'formal_accepted':0,'formal_required':42,'formal_increment':0,'next':'Review/freeze C binding schema and owned-server metadata controller. Integrate tested private binding/source bundle/dual-contract pieces only under new real scopes, and implement W14 trusted handoff without weakening active-writer safety. Resource stageB must be explicitly recorded before one metadata-only owned startup; no inference or consumed-scope replay.'}
put(out/'RESUME.json',resume)
cp['next_command']=resume['next']+' Read '+str((out/'RESUME.json').relative_to(root))
cp['current_implementation']={'status':result['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'active_construction_owners':['codex:/root/runtime_readiness server-controller candidate'],'formal_increment':0}
cp['workers'].append({'step_id':'W05-99','slice_id':'DELIVERYGATE_PRIMITIVE_V1','owner':'codex:/root completed frozen component integration','worktree':str(wt),'state':'INDEPENDENT_SOURCE_REVIEWED_AND_INTEGRATED_NOT_LIVE_BUSINESS_CHECKER','main_source_head':head,'integration_ref':str((out/'integration.json').relative_to(root))})
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp588.before.md').write_bytes(before)
temp=handoff.with_name(handoff.name+'.cp589.new');temp.write_bytes(('# Current resume CP589\n\nRead '+str((out/'RESUME.json').relative_to(root))+'. Pure structural source validator integrated after real worktree tests and peer readback. It is not wired as business acceptance; Goal503/SDK output gates unchanged. Old failures preserved, formal0/42.\n\n').encode()+before);os.replace(temp,handoff)
for name in ['start_deliverygate_integration.py','test_deliverygate_worktree.py','test_deliverygate_worktree_r2.py','test_deliverygate_worktree_r3.py','integrate_deliverygate.py']:
    target=out/'tools'/name;assert not target.exists();target.write_bytes((cbase/name).read_bytes())
print(json.dumps({'checkpoint':589,'head':head,'failure_records':len(cp['failure_counters']),'formal_increment':0}))
