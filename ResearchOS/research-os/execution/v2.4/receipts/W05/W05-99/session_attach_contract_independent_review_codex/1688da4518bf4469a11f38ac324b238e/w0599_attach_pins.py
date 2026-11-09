from pathlib import Path
import json,hashlib
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';Q=B/'session_attach_contract_revision_codex/1a11ded594f5378b7512125d';O=B/'session_attach_contract_independent_review_codex/1688da4518bf4469a11f38ac324b238e'
def pin(p):
 p=Path(p).resolve();d=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(d).hexdigest(),bytes=len(d))
def walk(x):
 if isinstance(x,dict):
  if all(k in x for k in ('path','sha256','bytes')):yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
refs=[]
for name in ('HDF.json','MF.json','public-input-pins.json'):
 data=json.loads((Q/name).read_text(encoding='utf-8'))
 for ref in walk(data):
  p=Path(ref['path']);actual=pin(p) if p.is_file() else None
  refs.append(dict(container=name,expected=ref,actual=actual,matched=actual is not None and actual['sha256']==ref['sha256'].removeprefix('sha256:') and actual['bytes']==ref['bytes']))
summary=dict(HDF=pin(Q/'HDF.json'),MF=pin(Q/'MF.json'),refs=refs,all_matched=all(x['matched'] for x in refs))
with (O/'input-pin-check.initial.json').open('xb') as f:f.write((json.dumps(summary,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(HDF=summary['HDF'],MF=summary['MF'],all_matched=summary['all_matched'],ref_count=len(refs),failures=[x for x in refs if not x['matched']]),ensure_ascii=False))
