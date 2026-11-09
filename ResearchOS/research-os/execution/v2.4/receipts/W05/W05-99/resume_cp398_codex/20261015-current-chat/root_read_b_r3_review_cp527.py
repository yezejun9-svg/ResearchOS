from pathlib import Path
import json,hashlib
R=Path(r'D:\\作品集\\ResearchOS\\research-os');B=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
for n in ['review.md','review.json','diagnostic-ledger.json','FINAL-manifest.json','FINAL-seal.json','command-index.json']:
 p=E/n
 if not p.exists():
  print('MISSING_OPTIONAL',n);continue
 print('REF',ref(p))
 if n=='review.md':print(p.read_text(encoding='utf-8-sig'))
 else:
  v=json.loads(p.read_text(encoding='utf-8-sig'));print('KEYS',n,list(v)if isinstance(v,dict)else {'list':len(v)})
  if n in ['review.json','diagnostic-ledger.json','FINAL-seal.json']:
   if n=='review.json':
    print(json.dumps({k:z for k,z in v.items()if k not in ['coverage','source_boundaries','commands','inputs']},ensure_ascii=False))
    if 'coverage'in v:print('COVERAGE',json.dumps(v['coverage'],ensure_ascii=False))
   else:print(json.dumps(v,ensure_ascii=False))
  elif n=='FINAL-manifest.json':
   print(json.dumps({k:z for k,z in v.items()if k not in ['files','entries','artifacts','records']},ensure_ascii=False))
   for k in ['files','entries','artifacts','records']:
    if k in v: print(k,'COUNT',len(v[k]),'FIRST',json.dumps(v[k][:2]if isinstance(v[k],list)else dict(list(v[k].items())[:2]),ensure_ascii=False))
  elif n=='command-index.json':
   print(json.dumps({k:z for k,z in v.items()if not isinstance(z,(list,dict))},ensure_ascii=False));print('TOPLISTS',[(k,len(z))for k,z in v.items()if isinstance(z,(list,dict))])
