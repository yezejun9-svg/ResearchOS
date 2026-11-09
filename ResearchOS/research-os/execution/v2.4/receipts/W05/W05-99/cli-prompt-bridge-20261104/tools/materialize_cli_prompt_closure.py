import json,hashlib,subprocess
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
wt=root/'.local/worktrees/cli-prompt-bridge-20261104'
out=root/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=wt,stderr=subprocess.STDOUT)
assert git('rev-parse','HEAD').decode().strip()=='fc2b1a50662580b1a0fca92559ca26be6e959f01'
files=git('ls-tree','-r','--name-only','HEAD','--','evaluation/holdout/jev','evaluation/evolution','evaluation/skills').decode().splitlines()
source=[p for p in files if p.endswith('.go') and not p.endswith('_test.go')]
assert source
cli=['apps/cli/'+p for p in ['main.go','cli_contract.go','cli_run_contract.go','cli_verbs.go','cli_stream.go','cli_prompt.go','cli_prompt_test.go']]
before={p:hashlib.sha256((wt/p).read_bytes()).hexdigest() for p in cli}
result=git('sparse-checkout','add','--no-cone',*['/'+p for p in source]).decode()
after={p:hashlib.sha256((wt/p).read_bytes()).hexdigest() for p in cli}
assert before==after,'Concurrent CLI edit or sparse drift; inspect before next test'
record={'action':'MATERIALIZED_TRACKED_GO_DEPENDENCY_CLOSURE_ONLY','source_files':source,'not_materialized_non_go_paths':[p for p in files if not p.endswith('.go')],'cli_source_preserved':True,'go_get_or_network':False,'holdout_inputs_or_labels_read':False,'git_output':result,'prior_failure_preserved':'author/checks-01'}
target=out/'source-closure-repair.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'materialized_go_source_files':len(source),'cli_source_preserved':True,'network':False}))
