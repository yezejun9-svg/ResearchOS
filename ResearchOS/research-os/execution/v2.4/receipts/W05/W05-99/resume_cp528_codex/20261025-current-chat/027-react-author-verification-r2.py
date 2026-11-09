import json,hashlib,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat';W=R/'.local/worktrees/react-workbench-redesign-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
refs=[];seen=set()
def check(p,want=None):
 p=p.resolve();b=p.read_bytes();v={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if want:assert v['sha256']==(want if isinstance(want,str)else want['sha256']),(str(p),'hash')
 if str(p)not in seen:seen.add(str(p));refs.append(v)
 return v
s=read(E/'SOURCE14-SEAL.json');check(E/'SOURCE14-SEAL.json')
for path,sha in s['source_sha256'].items():check(W/path,sha)
for path,sha in s['active_dist_sha256'].items():check(W/'apps/web/dist'/path,sha)
check(E/'source14-full.patch',s['full_patch_sha256']);check(E/'source14-ci.patch',s['ci_delta_patch_sha256']);check(E/'SOURCE14-CI-PROBE.json',s['ci_ast_probe_sha256'])
git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
assert subprocess.check_output(git+['diff','--binary','--full-index',s['base_commit'],s['final_commit']],cwd=W)==(E/'source14-full.patch').read_bytes()
assert subprocess.check_output(git+['diff','--binary','--full-index',s['source13_commit'],s['final_commit']],cwd=W)==(E/'source14-ci.patch').read_bytes()
reports={}
for name in ['browser-fixture-05/report.json','real-isolated-03/report.json']:
 p=E/name;v=read(p);check(p);assert v['status']=='PASS';checks=v['checks'];assert all(x.get('status','PASS')=='PASS'for x in checks if isinstance(x,dict))
 images=v.get('screenshots',[])+([v['screenshot']]if'screenshot'in v else[])
 for x in images:check(Path(x['path']),x['sha256'])
 reports[name]={'checks':len(checks),'images':len(images),'status':v['status']}
probe=read(E/'SOURCE14-CI-PROBE.json');assert probe['status']=='PASS' and probe['original_patterns_preserved']
for path,sha in probe['required_sha256'].items():check(W/path,sha)
all_paths=subprocess.check_output(['rg','--files','--hidden','--no-ignore',str(E)],cwd=R).decode('utf8').splitlines()
native=[];result_shapes=[]
for path in all_paths:
 p=Path(path);check(p)
 if 'commands'in p.parts and p.suffix=='.json' and p.name in ['result.json','exit.json','receipt.json']:
  v=read(p);found=False
  for key in ['native_exit','exit_code','exit','returncode','return_code']:
   if key in v and isinstance(v[key],int):native.append({'path':str(p),'exit':v[key]});found=True;break
  if not found:result_shapes.append({'path':str(p),'keys':list(v)})
ledger=[json.loads(x)for x in(E/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()if x.strip()]
out={'status':'AUTHOR_FROZEN_REACT_SOURCE_AND_EVIDENCE_VERIFIED_NOT_INDEPENDENT_ACCEPTANCE','source_commit':s['final_commit'],'source_tree':s['final_tree'],'actual_changed_count':len(s['source_sha256']),'allowed_count':s['allowed_paths'],'verified_count':len(refs),'verified_refs':refs,'reports':reports,'exact_patches_match_git':True,'recorded_command_results':native,'unclassified_result_shapes':result_shapes,'ledger_failures':[x for x in ledger if x['status']=='FAIL'],'author_manifest_ref':check(E/'SOURCE14-SEAL.json'),'unresolved':[],'formal_increment':0}
with (N/'React-author-root-verification-r2.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'verified_count':len(refs),'actual_changed_count':len(s['source_sha256']),'reports':reports,'command_result_count':len(native),'native_nonzero':[x for x in native if x['exit']!=0],'unclassified_result_shapes':result_shapes,'ledger_failure_count':len(out['ledger_failures'])},ensure_ascii=False,indent=2))
