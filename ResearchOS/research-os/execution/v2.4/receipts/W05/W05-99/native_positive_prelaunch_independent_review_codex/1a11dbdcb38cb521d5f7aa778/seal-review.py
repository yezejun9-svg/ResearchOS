import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((D/'evidence.json').read_bytes())['base_refs'];assert len(refs)==4091
for r in refs:assert pin(r['path'])==r
names=['verify-prelaunch.py','evidence.json','review.json','original-tool-io.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='REQUEST_MINIMAL_BOOTSTRAP_PIN_BEFORE_EXEC_FIX_NO_TARGET_EXECUTION',manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),counts=dict(members=6,files=8,base_refs=4091),blocking_static_findings=1,finding='BOOTSTRAP_SOURCE_EXEC_BEFORE_PIN_GUARD',future_runtime_acceptance_required_before_launch=False,target_executions=0,new_mechanical_errors=0,authority='NONE',formal_acceptance=False,stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
print(json.dumps(dict(HDF=h,manifest=m,members=6,files=8,base_refs=4091,drift=0)))

