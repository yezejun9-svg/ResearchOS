import argparse,hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
parent=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
out=parent/'builder-stdout-fix';wt=root/'.local/worktrees/desktop-builder-stdout-20261104'
base='e0fc197321a92fcb5952e7d112f3f6c356bd309a'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','-c','user.name=Codex','-c','user.email=codex@local.invalid','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
def put(path,doc):
    temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--review',required=True);p.add_argument('--review-sha',required=True);args=p.parse_args()
manifest=json.loads((out/args.manifest).read_bytes())
files=manifest['files'];files=files if isinstance(files,dict) else {r['path']:r['sha256'] for r in files}
assert list(files)==['apps/desktop/build-validator.py']
assert sha(out/args.review)==args.review_sha
assert not (out/'integration-journal.json').exists()
assert git(root,'rev-parse','HEAD').strip()==base and git(wt,'rev-parse','HEAD').strip()==base
assert not git(wt,'diff','--cached','--name-only').strip()
protected=json.loads((parent/'integration.json').read_bytes())['protected_preserved']
for path,digest in protected.items():assert (sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE')==digest,path
for path,digest in files.items():assert sha(wt/path)==digest,path
git(wt,'diff','--check');put(out/'integration-journal.json',{'status':'VERIFIED_BEFORE_COMMIT','base':base,'files':files})
git(wt,'add','--',*files)
assert set(git(wt,'diff','--cached','--name-only').splitlines())==set(files)
message=git(wt,'commit','-m','fix(build): preserve native junction command output as raw bytes')
head=git(wt,'rev-parse','HEAD').strip();put(out/'integration-journal.json',{'status':'COMMITTED','base':base,'candidate':head,'files':files,'commit_output':message})
git(root,'merge','--ff-only',head)
assert git(root,'rev-parse','HEAD').strip()==head
for path,digest in files.items():assert sha(root/path)==digest,path
for path,digest in protected.items():assert (sha(root/path) if (root/path).is_file() else 'ABSENT_BEFORE')==digest,path
result={'status':'INDEPENDENT_SOURCE_REVIEWED_AND_INTEGRATED','base_head':base,'main_head':head,'main_tree':git(root,'rev-parse','HEAD^{tree}').strip(),'source_files':files,'review_ref':{'path':str((out/args.review).relative_to(root)),'sha256':args.review_sha},'protected_preserved':True,'failure_origin':'compatibility-development-bundle-20261104','failed_attempt1_retained':True,'next_attempt_index':2,'formal_increment':0}
put(out/'integration.json',result)
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw);assert cp['revision']==584 and len(cp['failure_counters'])==2376
(out/'checkpoint.cp584.before-integration.json').write_bytes(raw)
now=datetime.now(timezone.utc).isoformat();initial=cp['failure_counters'][:]
for relative in ['author/diagnostics.json',args.review]:
    file=out/relative;doc=json.loads(file.read_bytes())
    events=doc.get('records',doc.get('diagnostics',[]))
    for i,event in enumerate(events):cp['failure_counters'].append({'at':now,'origin_key':f'20261104|builder-stdout-fix|{relative}|{i}','attempts':1,'status':'PRESERVED_DEVELOPMENT_OR_TOOL_DIAGNOSTIC','detail':event,'source_ref':{'path':str(file.relative_to(root)),'sha256':sha(file)},'counter_reset':False})
assert cp['failure_counters'][:2376]==initial
cp['expected_previous_revision']=584;cp['revision']=585;cp['updated_at']=now;cp['head']=head;cp['current_Main_HEAD']=head;cp['current_Main_tree']=result['main_tree']
cp['current_effective_formal_status']['current_head']=head;cp['current_effective_formal_status']['needs_rederive_after_source_change']=True
next_command='Run same-origin development-build attempt2 with tools/compatibility-development-build-r2.py '+head+' into fresh r4; preserve r2/r3 and first failed logs. Then build standalone CLI with tools/build_cli_development_r2.py '+head+'. Independent artifact review required. No Core/GUI/model or consumed-scope replay.'
resume={'checkpoint_revision':585,'status':'BUILDER_STDOUT_FIX_INTEGRATED_DEVELOPMENT_ARTIFACTS_PENDING','main_head':head,'main_tree':result['main_tree'],'integration_ref':str((out/'integration.json').relative_to(root)),'failure_records':len(cp['failure_counters']),'failure_origin':result['failure_origin'],'next_build_attempt':2,'first_failure_retained':True,'counter_reset':False,'formal_accepted':0,'formal_required':42,'formal_increment':0,'next':next_command}
put(out/'RESUME.json',resume)
cp['next_command']=next_command;cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'active_construction_owners':[],'formal_increment':0}
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp584.before-integration.md').write_bytes(before)
temp=handoff.with_name(handoff.name+'.cp585.new');temp.write_bytes(('# Current resume CP585\n\nRead '+str((out/'RESUME.json').relative_to(root))+'. One-file native stdout fix reviewed and integrated. Same-origin attempt2 r4 and separate CLI build pending; old r2/r3 retained. Full goal unfinished/formal0of42.\n\n').encode()+before);os.replace(temp,handoff)
print(json.dumps({'checkpoint':585,'main_head':head,'main_tree':result['main_tree'],'failure_records':len(cp['failure_counters']),'formal_increment':0}))
