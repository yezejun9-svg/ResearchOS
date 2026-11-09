import json,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/source43_independent_review_codex/20261025-current-chat';W=R/'.local/worktrees/source43-independent-review-20261025'
seen=set();verified=[];unresolved=[]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check(p,want=None):
 p=p.resolve();b=p.read_bytes();v={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if want:
  assert v['sha256']==want['sha256'],(str(p),'hash')
  if 'bytes'in want:assert v['bytes']==want['bytes'],(str(p),'bytes')
 if str(p)not in seen:seen.add(str(p));verified.append(v)
 return v
def walk(v,trail):
 if isinstance(v,dict):
  if isinstance(v.get('sha256'),str):
   token=v.get('path',v.get('file',v.get('relative_path',trail.rsplit('/',1)[-1])))
   matches=[p for p in [Path(token),E/token,R/token,W/token]if p.is_file()]
   if not matches:unresolved.append({'trail':trail,'keys':list(v),'path':token})
   else:check(matches[0],v)
  for k,x in v.items():walk(x,trail+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,trail+'/'+str(i))
for name,sha in [('FINAL-manifest.json','a73a448587f4042263269c8bf9dfab95683384f2e54fd747975cc2b1a61016cd'),('FINAL-seal.json','35dcd7039b8b67d90f97fa1792ab17c501d0436437da40a8251d2432ac3f4fc0')]:
 p=E/name;check(p,{'sha256':sha});walk(read(p),name)
for p in E.glob('048*/exit.json'):
 e=read(p);assert e.get('native_exit',e.get('exit_code',e.get('exit')))==0
 for q in p.parent.iterdir():
  if q.is_file():check(q)
review=read(E/'review.json');check(E/'review.json',{'sha256':'b693b4f8c6a8cad5a24cc465c98a79a9420c9256e37c649fa92ba0b99c0bdbc8'})
out={'verified_count':len(verified),'verified_refs':verified,'unresolved':unresolved,'review':review,'formal_increment':0,'root_adoption':False}
with (N/'Source43-independent-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'verified_count':len(verified),'unresolved':unresolved,'review_keys':list(review),'top_files':[p.name for p in E.iterdir()if p.is_file()]},ensure_ascii=False))
p=E/'REVIEW.md';check(p);v=p.read_text(encoding='utf8');print('REVIEW.md '+str(len(v))+' chars');print(v if len(v)<=18000 else v[:18000]+' [NEEDS_SECOND_CHUNK]')
for name in ['diagnostic-ledger.json','ledger.json']:
 p=E/name
 if p.is_file():
  v=read(p);t=json.dumps(v,ensure_ascii=False,indent=2);print(name+' '+str(len(t))+' chars');print(t if len(t)<=9000 else json.dumps({'keys':list(v),'requires_bounded_read':True}))
