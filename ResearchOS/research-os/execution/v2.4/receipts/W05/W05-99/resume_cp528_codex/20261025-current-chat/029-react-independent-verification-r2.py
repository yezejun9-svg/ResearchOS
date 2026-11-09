import json,hashlib,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_independent_review_codex/20261025-current-chat';A=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat';W=R/'.local/worktrees/react-workbench-independent-review-20261025'
seen=set();refs=[]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check(p,v=None):
 p=p.resolve();b=p.read_bytes();out={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if v:
  assert out['sha256']==v['sha256'],(str(p),'hash')
  if'bytes'in v:assert out['bytes']==v['bytes'],(str(p),'bytes')
 if str(p)not in seen:seen.add(str(p));refs.append(out)
 return out
s=read(E/'FINAL-SEAL.json');check(E/'FINAL-SEAL.json',{'sha256':'41420256422d91fba00767c2b96b4bc7bb76f5f7027a4d70737df634bcd09824'})
for rel,v in s['manifest'].items():check(E/rel,v)
assert len(s['manifest'])==189
old=read(N/'React-independent-root-verification.json')
for x in old['verified_refs']:check(Path(x['path']),x)
r=read(E/'REVIEW.json');assert r['verdict']=='NO_BLOCKING_FINDINGS'and not r['findings'];git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=W).decode().strip()==r['candidate_commit']
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all'],cwd=W)
stop_results=[]
for run in ['real-isolated-01','real-isolated-02','real-isolated-03']:
 p=A/run/'commands/02-core-service/stop.json';x=read(p);check(p);stop_results.append({'run':run,'content':x})
out={'status':'INDEPENDENT_REACT_SOURCE14_REVIEW_EVIDENCE_VERIFIED','verified_count':len(refs),'verified_refs':refs,'independent_manifest_count':189,'review':r,'author_stop_results':stop_results,'unresolved':[],'formal_increment':0,'root_adoption':False,'corrects_root028':'Manifest keys contain full relative paths; previous generic parser stripped directory prefix, causing false unresolved entries. Original result retained.'}
with(N/'React-independent-root-verification-r2.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'verified_count':len(refs),'independent_manifest_count':189,'verdict':r['verdict'],'candidate_commit':r['candidate_commit'],'findings':r['findings'],'unresolved':[],'limits':r['limits'],'matrix':r['matrix'],'author_stop_results':stop_results},ensure_ascii=False,indent=2))
p=E/'SEAL-EMISSION-DIAGNOSTIC.json';print('SEAL DIAGNOSTIC '+p.read_text(encoding='utf8'))
