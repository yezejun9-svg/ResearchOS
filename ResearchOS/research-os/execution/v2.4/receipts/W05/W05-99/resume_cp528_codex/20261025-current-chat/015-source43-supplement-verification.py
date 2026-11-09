import json,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat';W=R/'.local/worktrees/source43-b-stop-finalpath-20261015'
verified=[];unresolved=[];seen=set()
def check(p,want):
 b=p.read_bytes();v={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 assert v['sha256']==want['sha256'],(str(p),'hash')
 if 'bytes'in want:assert v['bytes']==want['bytes'],(str(p),'size')
 if str(p)not in seen:verified.append(v);seen.add(str(p))
def walk(v,trail):
 if isinstance(v,dict):
  if 'sha256'in v and isinstance(v['sha256'],str):
   path=v.get('path',v.get('file',v.get('relative_path')))
   if not path:unresolved.append({'trail':trail,'keys':list(v)})
   else:
    candidates=[Path(path),E/path,R/path,W/path]
    matches=[p.resolve()for p in candidates if p.is_file()]
    if not matches:unresolved.append({'trail':trail,'path':path})
    else:check(matches[0],v)
  for k,x in v.items():walk(x,trail+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,trail+'/'+str(i))
for name,sha in [('FINAL-supplement.json','5b7113cd39b8806efe6fe08f87ea598e2a81f3bc0abb1d494b5a60f4792497d4'),('FINAL-supplement-seal.json','2c219dc9ea2e07db94b86b98e196d5a70840be126384f80b87c80699fe6c962d')]:
 p=E/name;check(p,{'sha256':sha});v=json.loads(p.read_text(encoding='utf8'));walk(v,name)
for p in E.glob('054*/exit.json'):
 e=json.loads(p.read_text(encoding='utf8'));assert e.get('native_exit',e.get('exit_code',e.get('exit')))==0
 for q in p.parent.iterdir():
  if q.is_file():b=q.read_bytes();check(q,{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
out={'verified_refs':verified,'verified_count':len(verified),'unresolved':unresolved,'formal_increment':0,'source_author_adoption':False}
with (N/'Source43-author-supplement-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'verified_count':len(verified),'unresolved':unresolved},ensure_ascii=False))
