import json,subprocess,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
wt=root/'.local/worktrees/cli-prompt-bridge-20261104'
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
base='fc2b1a50662580b1a0fca92559ca26be6e959f01'
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8').strip()
def put(path,value):
    temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==581 and git(root,'rev-parse','HEAD')==base
assert not wt.exists() and not out.exists(), 'Inspect uncertain state before retry'
out.mkdir(parents=True);(out/'author').mkdir();(out/'reviews').mkdir();(out/'tools').mkdir()
(out/'checkpoint.cp581.before.json').write_bytes(raw)
status=git(root,'status','--porcelain=v1','-uno');(out/'git-tracked.before.txt').write_text(status+'\n',encoding='utf-8')
protected={}
for line in status.splitlines():
    p=line[3:];file=root/p
    protected[p]=hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else 'ABSENT_BEFORE'
scope={'scope_id':'CLI_PROMPT_BRIDGE_20261104','base_head':base,'project_id':cp['project_id'],'construction_owner':'codex:/root/workbench_builder','integrator':'codex:/root','independent_reviewer':'codex:/root/implementation_review','max_construction_tasks':2,'worktree':str(wt),'authorized_source_paths':['apps/cli/main.go','apps/cli/cli_contract.go','apps/cli/cli_run_contract.go','apps/cli/cli_verbs.go','apps/cli/cli_stream.go','apps/cli/cli_prompt.go','apps/cli/cli_prompt_test.go'],'other_cli_test_additions':'Only new prompt-specific tests; disclose exact paths at freeze.','purpose':'Strict explicit task/run --prompt or --prompt-file parsing into existing authenticated finiteGoal session flow; preserve legacy task/cascade handlers.','validation':'All input validation before native/HTTP; preserve raw text including hyphen-leading prompts; reject duplicates, mixed legacy edit flags, empty/invalid UTF8/over 16384 Unicode scalars. Bound prompt file reads.','excluded':['No local business writer/checker','No direct database write','No new scheduler','No native/provider/model call','No altering discovery/auth/lease/CAS/settlement semantics','No registry/step_state changes','No acceptance claims or counter reset'],'protected_before':protected,'formal_increment':0,'at':datetime.now(timezone.utc).isoformat()}
put(out/'scope.json',scope)
git(root,'worktree','add','--no-checkout','-b','codex/cli-prompt-bridge-20261104',str(wt),base)
git(wt,'sparse-checkout','set','--no-cone','/go.mod','/go.sum','/apps/cli/','/internal/','/adapters/','/migrations/','/ops/','/eval/','/spec/v2.0/contracts/')
git(wt,'checkout','HEAD')
assert git(wt,'rev-parse','HEAD')==base and not git(wt,'status','--porcelain=v1','-uno')
resume={'checkpoint_revision':582,'status':'IMPLEMENTING_CLI_PROMPT_BRIDGE','base_head':base,'scope_ref':str((out/'scope.json').relative_to(root)),'worktree':str(wt),'active_construction_owner':scope['construction_owner'],'formal_accepted':0,'formal_required':42,'counter_reset':False,'next':'Implement and freeze minimal typed prompt bridge, targeted fixture checks, independent review, source-only integration; actual LIVE business delivery and runtime qualification remain open.'}
put(out/'RESUME.json',resume)
cp['expected_previous_revision']=581;cp['revision']=582;cp['updated_at']=scope['at'];cp['next_command']=resume['next']+' Read '+str((out/'RESUME.json').relative_to(root))
cp['current_implementation']={'status':resume['status'],'at':scope['at'],'resume_ref':str((out/'RESUME.json').relative_to(root)),'scope_ref':resume['scope_ref'],'active_construction_owners':[scope['construction_owner']],'formal_increment':0}
assert cpfile.read_bytes()==raw;put(cpfile,cp)
print(json.dumps({'checkpoint':582,'worktree':str(wt),'base_head':base,'receipt':str(out)}))
