from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';D=B/'checkpoint_r357_independent_review_codex/1a11db9e0dff7ad081d6e06d'
def walk(x):
 if isinstance(x,dict):
  if 'path' in x and 'sha256' in x:print(json.dumps(x,ensure_ascii=False))
  else:
   for k,v in x.items():
    if any(w in k.lower() for w in ('canonical','unchanged','checkpoint','before','after')):print('KEY',k)
    walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
print('FILES',[p.name for p in D.iterdir() if p.is_file()])
for name in ('HDF.json','MF.json','evidence.json'):
 p=D/name;print('FILE',name);walk(json.loads(p.read_text(encoding='utf-8')))
