import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((D/'evidence.json').read_bytes())['base_refs'];assert len(refs)==4097
for r in refs:assert pin(r['path'])==r
names=['verify-api-v3.py','evidence.json','review.json','original-tool-io.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='PUBLIC_PHASE_API_V3_PARTIAL_RETAINED_INSPECTION_SOURCE_ACCEPTED',manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),counts=dict(members=6,files=8,base_refs=4097),readonly_partial_inspection_can_proceed=True,release_or_retry_approved=False,Owner_or_native_actual_accepted=False,target_executions=0,new_mechanical_errors=0,authority='NONE',formal_acceptance=False,stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
print(json.dumps(dict(HDF=h,manifest=m,members=6,files=8,base_refs=4097,drift=0)))

