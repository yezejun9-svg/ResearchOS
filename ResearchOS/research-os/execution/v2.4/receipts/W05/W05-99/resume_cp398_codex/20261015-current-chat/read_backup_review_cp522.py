import json,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=Path(__file__).parent;Q=E/'online_backup_fixture_independent_review_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
mp=Q/'FINAL-manifest.json';assert ref(mp)['sha256']=='bbc588df1e8c76cfe77a82ead887d5ff72220c2621bce46b6173ae3accac75c4';m=read(mp);verified=[];unresolved=[]
def check(v):
 p=Path(v['path']);opts=[p]if p.is_absolute()else[Q/p,R/p]
 for q in opts:
  if q.is_file()and ref(q)['sha256']==v['sha256']:
   a=ref(q)
   if 'bytes'in v:assert a['bytes']==v['bytes']
   verified.append(a);return
 unresolved.append(v)
def nested(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):check(v)
  for x in v.values():nested(x)
 elif isinstance(v,list):
  for x in v:nested(x)
nested(m)
if isinstance(m.get('files'),dict):
 for n,v in m['files'].items():check(dict(v,path=v.get('path',n)))
v=read(Q/'review.json');md=(Q/'review.md').read_text(encoding='utf-8-sig')
print('SEMANTIC',json.dumps({k:x for k,x in v.items()if k in ['verdict','status','findings','limits','actual_authority','formal_increment']},ensure_ascii=False))
print('MD_LENGTH',len(md),'PART1_0_6000\n'+md[:6000])
print('LEDGER_FILES',json.dumps([p.name for p in Q.iterdir()if p.is_file()and'ledger'in p.name],ensure_ascii=False))
print('MANIFEST_META',json.dumps({k:({'type':type(x).__name__,'count':len(x)}if isinstance(x,(dict,list))else x)for k,x in m.items()},ensure_ascii=False))
out={'manifest':ref(mp),'verified':len(verified),'refs':verified,'unresolved':unresolved,'review':ref(Q/'review.json'),'review_md':ref(Q/'review.md'),'read_part1_chars':min(6000,len(md)),'total_md_chars':len(md),'actual_authority':False,'formal_increment':0}
p=B/'backup-review-root-input-verification.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('VERIFICATION',json.dumps({'ref':ref(p),'verified':len(verified),'unresolved':unresolved},ensure_ascii=False))
