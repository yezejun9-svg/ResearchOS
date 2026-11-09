from pathlib import Path
import hashlib,json
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/react_frontend_intake_codex/20261025-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
for n in ['FRONTEND-INTAKE.md','paths.txt','ledger.json']:
 p=E/n;print('FILE',n,ref(p));print(p.read_text(encoding='utf-8-sig'))
v=read(E/'FRONTEND-INTAKE.json');print('INTAKE_JSON_KEYS',list(v))
for k in ['recommended_edit_paths','new_paths','verification_commands','preserved_contracts','risks','limits']:
 if k in v:print(k,json.dumps(v[k],ensure_ascii=False))
m=read(E/'manifest.json');print('MANIFEST_KEYS',list(m))
checked=[];bad=[]
def walk(x,label=''):
 if isinstance(x,dict):
  h=x.get('sha256',x.get('hash'));p=x.get('path',x.get('file'))
  if isinstance(h,str)and isinstance(p,str):
   q=Path(p);cs=[q]if q.is_absolute()else[E/q,R/q]
   found=[q for q in cs if q.is_file()and ref(q)['sha256']==h.removeprefix('sha256:')]
   if found:checked.append(ref(found[0]))
   else:bad.append({'label':label,'path':p,'sha256':h})
  for k,z in x.items():walk(z,label+'.'+k)
 elif isinstance(x,list):
  for i,z in enumerate(x):walk(z,label+'.'+str(i))
walk(m)
out=N/'frontend-intake-root-verification.json'
with out.open('x',encoding='utf8')as f:json.dump({'manifest':ref(E/'manifest.json'),'verified_refs':checked,'verified_count':len(checked),'unresolved':bad,'source_edits':False,'formal_increment':0},f,ensure_ascii=False,indent=2);f.write(chr(10))
print('VERIFICATION',ref(out),'COUNT',len(checked),'UNRESOLVED',bad)
assert not bad
