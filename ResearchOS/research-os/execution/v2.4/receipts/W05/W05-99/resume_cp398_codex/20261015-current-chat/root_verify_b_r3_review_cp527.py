from pathlib import Path
import hashlib,json
R=Path(r'D:\\作品集\\ResearchOS\\research-os');B=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat';W=R/'.local/worktrees/qualification-failure-b-r3-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
verified=[];unresolved=[]
def walk(v,where):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str)and isinstance(v.get('sha256'),str):
   p=Path(v['path']);candidates=[p]if p.is_absolute()else[E/p,W/p,R/p]
   matches=[p for p in candidates if p.is_file()and ref(p)['sha256']==v['sha256']]
   if not matches:unresolved.append({'where':where,'entry':v})
   else:
    x=ref(matches[0]);assert 'bytes'not in v or v['bytes']==x['bytes'];verified.append(x)
  for k,x in v.items():walk(x,where+'.'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk(x,where+'.'+str(i))
for n in ['FINAL-manifest.json','FINAL-seal.json','final-source-pins.json','command-index.json']:
 v=read(E/n);walk(v,n)
 if n=='final-source-pins.json':print('SOURCE_PINS',json.dumps(v,ensure_ascii=False))
for n in ['diagnostic-ledger.jsonl','test-summary.json','B-r3-review-015.result.json']:
 p=E/n;print('DETAIL',n,p.read_text(encoding='utf-8-sig'))
v={'schema':'researchos.B-r3-independent-root-evidence-verification.v1','manifest':ref(E/'FINAL-manifest.json'),'seal':ref(E/'FINAL-seal.json'),'review':ref(E/'review.json'),'verified_refs':verified,'verified_count':len(verified),'unresolved':unresolved,'manifest_own_entries':len(read(E/'FINAL-manifest.json')['files']),'source_actual_formal_acceptance':False}
p=B/'B-r3-independent-root-evidence-verification.json'
with p.open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\\n')
print('OUTPUT',json.dumps(ref(p),ensure_ascii=False),'VERIFIED',len(verified),'UNRESOLVED',json.dumps(unresolved,ensure_ascii=False))
assert not unresolved
