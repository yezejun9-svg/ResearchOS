import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=Path(__file__).parent;S=E/'owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
mp=S/'FINAL-manifest.json';assert ref(mp)['sha256']=='1e3c2f08f9dd2b4d2b05c71ad2d5f82b20adb2a3c4b5431d81eef1123bf695b7';m=read(mp)
verified=[];unresolved=[]
def check(v,parent):
 p=Path(v['path']);opts=[p]if p.is_absolute()else[parent/p,R/p,S/p]
 for q in opts:
  if q.is_file()and ref(q)['sha256']==v['sha256']:
   a=ref(q)
   if 'bytes'in v:assert a['bytes']==v['bytes']
   verified.append(a);return
 unresolved.append(v)
def nested(v,parent):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):check(v,parent)
  for x in v.values():nested(x,parent)
 elif isinstance(v,list):
  for x in v:nested(x,parent)
nested(m,S)
if isinstance(m.get('files'),dict):
 for name,v in m['files'].items():check(dict(v,path=v.get('path',name)),S)
v=read(S/'review.json');print('SUMMARY',json.dumps({k:x for k,x in v.items()if k in ['verdict','status','source_commit','source_tree','candidate','tree','findings','limits','source_acceptance','actual_authority','formal_increment']},ensure_ascii=False))
print('REVIEW_MD\n'+(S/'review.md').read_text(encoding='utf-8-sig'))
print('TOPFILES',json.dumps([p.name for p in S.iterdir()if p.is_file()and('ledger'in p.name or'command-index'in p.name)],ensure_ascii=False))
for p in S.glob('*ledger*.json'):print('LEDGER',p.name,json.dumps(read(p),ensure_ascii=False))
print('MANIFEST_SHAPE',json.dumps({k:({'type':type(x).__name__,'len':len(x)}if isinstance(x,(dict,list))else x)for k,x in m.items()},ensure_ascii=False))
out={'manifest':ref(mp),'verified_ref_count':len(verified),'refs':verified,'unresolved':unresolved,'review':ref(S/'review.json'),'review_md':ref(S/'review.md'),'Root_read_only':True,'actual_authority':False,'formal_increment':0}
p=B/'stop-r5-review-root-input-verification.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('VERIFICATION',json.dumps({'path':ref(p),'verified':len(verified),'unresolved':unresolved},ensure_ascii=False))
