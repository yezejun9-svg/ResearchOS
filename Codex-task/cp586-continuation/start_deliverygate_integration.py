import json,hashlib,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os');base=Path(__file__).resolve().parent
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/deliverygate-integration'
wt=root/'.local/worktrees/deliverygate-primitive-20261104'
head='556cdc353f47167e5609f23291bf2746e3c8896f'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(cwd,*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
def put(path,doc):
    temp=path.with_name(path.name+'.new');temp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)
cpfile=root/'execution/v2.4/checkpoint.json';raw=cpfile.read_bytes();cp=json.loads(raw)
assert cp['revision']==587 and len(cp['failure_counters'])==2386
assert git(root,'rev-parse','HEAD').strip()==head
assert not out.exists() and not wt.exists() and not (root/'internal/deliverygate').exists()
review=base/'pure-scalar/reviews/source-review.json';assert sha(review)=='598acb7bc0c8cc0c4f6bdb9a079d64fa5b0bbd1682abeabfa9e9f3467da38a5e'
files={'internal/deliverygate/validate.go':'5f4fe31f511375843ad793908def95e8c14dd91d2d80afbfb8722a244e08205e','internal/deliverygate/validate_test.go':'4094f1e5b5fc58939ede6a8dd7b4df66455a78dd96b02d7ec08e84db23b85ce3'}
for destination,digest in files.items():assert sha(base/'pure-scalar'/Path(destination).name)==digest
out.mkdir();(out/'tools').mkdir();(out/'reviews').mkdir();(out/'checkpoint.cp587.before.json').write_bytes(raw)
git(root,'worktree','add','--no-checkout','-b','codex/deliverygate-primitive-20261104',str(wt),head)
git(wt,'sparse-checkout','set','--no-cone','/AGENTS.md','/go.mod','/go.sum');git(wt,'checkout','HEAD')
for destination,digest in files.items():
    path=wt/destination;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((base/'pure-scalar'/Path(destination).name).read_bytes());assert sha(path)==digest
scope={'scope_id':'DELIVERYGATE_PRIMITIVE_INTEGRATION_20261104','base_head':head,'worktree':str(wt),'owner':'codex:/root frozen-component integrator','source_author':'codex:/root/workbench_builder completed C primitive','files':files,'prior_independent_review':{'path':str(review),'sha256':sha(review)},'purpose':'Lift the completed independently reviewed pure structural primitive into an isolated real repository package; no new API/checker registration or LIVE behavior.','excluded':['No Goal503 change','No database/migration/source-bundle integration','No model or Core process','No change to existing CLI/runtime/writer behavior'],'formal_increment':0,'counter_reset':False}
put(out/'scope.json',scope)
now=datetime.now(timezone.utc).isoformat();resume={'checkpoint_revision':588,'status':'VALIDATING_FROZEN_DELIVERYGATE_PACKAGE_IN_REAL_WORKTREE','main_head':head,'worktree':str(wt),'scope_ref':str((out/'scope.json').relative_to(root)),'formal_accepted':0,'formal_required':42,'formal_increment':0,'failure_records':len(cp['failure_counters']),'next':'Run locked offline Go tests for internal/deliverygate, independent final source/readback review, commit exact two files and integrate. Binding schema and server controller remain separate candidates; ordinary LIVE gate unchanged.'}
put(out/'RESUME.json',resume)
cp['expected_previous_revision']=587;cp['revision']=588;cp['updated_at']=now;cp['next_command']=resume['next']+' Read '+str((out/'RESUME.json').relative_to(root))
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((out/'RESUME.json').relative_to(root)),'frozen_component_integrator':'codex:/root','active_construction_owners':['codex:/root/workbench_builder C binding-schema','codex:/root/runtime_readiness C server-controller'],'formal_increment':0}
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=root/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(out/'handoff.cp587.before.md').write_bytes(before)
temp=handoff.with_name(handoff.name+'.cp588.new');temp.write_bytes(('# Current resume CP588\n\nRead '+str((out/'RESUME.json').relative_to(root))+'. Frozen structural primitive being validated in isolated real worktree; not a business verifier or LIVE exception. Two C construction scopes remain separate. No source acceptance/formal increment.\n\n').encode()+before);os.replace(temp,handoff)
print(json.dumps({'checkpoint':588,'worktree':str(wt),'source_files':2,'formal_increment':0}))
