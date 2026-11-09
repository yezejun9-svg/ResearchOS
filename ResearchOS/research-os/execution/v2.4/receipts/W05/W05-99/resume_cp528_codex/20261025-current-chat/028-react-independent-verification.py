import json,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_independent_review_codex/20261025-current-chat';A=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat';W=R/'.local/worktrees/react-workbench-independent-review-20261025'
seen=set();refs=[];unresolved=[]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check(p,v=None):
 p=p.resolve();b=p.read_bytes();out={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if v:
  assert out['sha256']==v['sha256'],(str(p),'hash')
  if'bytes'in v:assert out['bytes']==v['bytes'],(str(p),'bytes')
 if str(p)not in seen:seen.add(str(p));refs.append(out)
 return out
def walk(v,trail,base):
 if isinstance(v,dict):
  if isinstance(v.get('sha256'),str):
   token=v.get('path',v.get('file',v.get('relative_path',trail.rsplit('/',1)[-1])))
   options=[Path(token),base/token,R/token,W/token];found=[p for p in options if p.is_file()]
   if found:check(found[0],v)
   else:unresolved.append({'trail':trail,'path':token,'keys':list(v)})
  for k,x in v.items():walk(x,trail+'/'+k,base)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,trail+'/'+str(i),base)
check(E/'FINAL-SEAL.json',{'sha256':'41420256422d91fba00767c2b96b4bc7bb76f5f7027a4d70737df634bcd09824'});walk(read(E/'FINAL-SEAL.json'),'FINAL-SEAL.json',E)
for name in ['LEDGER-SUPPLEMENT.json','SOURCE14-SUPPLEMENT-SEAL.json']:
 check(A/name);walk(read(A/name),name,A)
v=read(E/'REVIEW.json');check(E/'REVIEW.json');out={'verified_count':len(refs),'verified_refs':refs,'unresolved':unresolved,'review':v,'formal_increment':0,'root_adoption':False}
with(N/'React-independent-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'verified_count':len(refs),'unresolved':unresolved,'review_keys':list(v),'topfiles':[p.name for p in E.iterdir()if p.is_file()]},ensure_ascii=False))
t=(E/'FINAL.md').read_text(encoding='utf8');print('FINAL.md chars='+str(len(t)));print(t if len(t)<=18000 else t[:18000]+' [NEEDS_MORE]')
for name in ['LEDGER.jsonl','diagnostic-ledger.json']:
 p=E/name
 if p.is_file():
  if p.suffix=='.jsonl':rows=[json.loads(x)for x in p.read_text(encoding='utf8').splitlines()if x.strip()];rows=[x for x in rows if x.get('status')not in ['PASS','START']or x.get('kind')in ['DIAGNOSTIC','FAILURE']];print(json.dumps({'file':name,'nonpass':rows},ensure_ascii=False))
  else:print(name+' '+p.read_text(encoding='utf8'))
print('AUTHOR SUPPLEMENT '+json.dumps(read(A/'LEDGER-SUPPLEMENT.json'),ensure_ascii=False))
