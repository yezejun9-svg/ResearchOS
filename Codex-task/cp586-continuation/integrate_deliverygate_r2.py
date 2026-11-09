import json,hashlib,subprocess
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/deliverygate-integration'
scope=json.loads((out/'scope.json').read_bytes());wt=Path(scope['worktree'])
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=wt,stderr=subprocess.STDOUT).decode()
journal=out/'integration-journal.json';old=journal.read_bytes()
assert json.loads(old)['status']=='VERIFIED_BEFORE_COMMIT'
assert git('rev-parse','HEAD').strip()==scope['base_head'] and not git('diff','--cached','--name-only').strip()
for name,digest in scope['files'].items():assert hashlib.sha256((wt/name).read_bytes()).hexdigest()==digest
saved=out/'integration-journal.before-sparse-repair.json';assert not saved.exists();saved.write_bytes(old)
patterns=git('sparse-checkout','list')
assert '/internal/deliverygate/' not in patterns
git('sparse-checkout','add','/internal/deliverygate/')
for name,digest in scope['files'].items():assert hashlib.sha256((wt/name).read_bytes()).hexdigest()==digest
(out/'sparse-reconciliation.json').write_text(json.dumps({'original_tool':'299dab/83d16d','git_add_exit':1,'inspection':'61d2d4 proved index empty/Main unchanged/target outside sparse patterns','source_preserved':True,'repair':'Added exactly /internal/deliverygate/ to existing non-cone sparse patterns; no source changes','counter_reset':False},indent=2)+'\n',encoding='utf-8')
source=Path(__file__).with_name('integrate_deliverygate.py').read_text(encoding='utf-8')
source=source.replace("assert not (out/'integration-journal.json').exists(),'Inspect uncertain state, do not replay'", "assert json.loads((out/'integration-journal.json').read_bytes())['status']=='VERIFIED_BEFORE_COMMIT' # reconciled index was empty; prior journal archived")
source=source.replace("events=[{", "events=[{'origin_key':'20261104|deliverygate-integration|sparse-add-refusal','status':'INTEGRATION_TOOLING_FAILURE','tool_chunk':'299dab/83d16d','exit':1,'detail':'Exact new package files were outside sparse patterns; Git add refused with empty index. Inspected before continuing and extended only this directory; source/tests unchanged.'},{",1)
exec(compile(source,'integrate_deliverygate_r2.generated','exec'))
