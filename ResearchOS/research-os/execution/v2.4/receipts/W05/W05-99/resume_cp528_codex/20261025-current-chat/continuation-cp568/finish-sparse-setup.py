"""Populate the verified empty, newly created worktree; no existing work touched."""
import json,subprocess,sys,datetime
from pathlib import Path
N=Path(__file__).parents[1];sys.path.insert(0,str(N))
from preserve_main_baseline import R,read,ref,git
from preserve_desktop_main_ecc28 import verify
out=Path(__file__).parent;scope=read(out/'Installer-P1a-source-scope.json');W=Path(scope['worktree'])
assert W.resolve()==(R/'.local/worktrees/installer-p1a-20261028').resolve()
assert sorted(p.name for p in W.iterdir())==['.git']
assert git(W,'rev-parse','HEAD').decode().strip()==scope['base_commit']
before=git(W,'status','--porcelain=v1','--untracked-files=all');assert len(before.splitlines())==36201 and all(r.startswith(b'D  ') for r in before.splitlines())
(out/'sparse-unpopulated-status.raw').write_bytes(before)
argv=['git','-c','gc.auto=0','-c','maintenance.auto=false','read-tree','-mu','HEAD']
result=subprocess.run(argv,cwd=W,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
(out/'setup-3.stdout.raw').write_bytes(result.stdout);(out/'setup-3.stderr.raw').write_bytes(result.stderr)
with (out/'setup-3.json').open('x',encoding='utf-8') as f:json.dump({'argv':argv,'cwd':str(W),'exit':result.returncode,'reason':'--no-checkout created empty index; sparse-checkout set did not populate it. Populate only verified empty newly owned worktree.','prior_setup_assertion_exit':1,'stdout':ref(out/'setup-3.stdout.raw'),'stderr':ref(out/'setup-3.stderr.raw')},f,indent=2)
assert result.returncode==0 and not git(W,'status','--porcelain=v1','--untracked-files=all')
assert (W/'go.mod').is_file() and (W/'AGENTS.md').is_file()
with (out/'setup-complete.json').open('x',encoding='utf-8') as f:json.dump({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':scope['base_commit'],'scope_ref':ref(out/'Installer-P1a-source-scope.json'),'preserved_after':verify(),'original_setup_failure_retained':True},f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'SPARSE_WORKTREE_READY','worktree':str(W),'scope_sha256':ref(out/'Installer-P1a-source-scope.json')['sha256']}))
