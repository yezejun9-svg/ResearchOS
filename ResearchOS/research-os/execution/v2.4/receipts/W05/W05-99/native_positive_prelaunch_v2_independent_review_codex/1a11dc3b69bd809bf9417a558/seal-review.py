import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((D/'evidence.json').read_bytes())['base_refs'];assert len(refs)==4094
for r in refs:assert pin(r['path'])==r
names=['verify-prelaunch.py','evidence.json','review.json','original-tool-io.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='PRELAUNCH_V2_SOURCE_ACCEPTED_SINGLE_ISOLATED_POSITIVE_CAN_PROCEED',manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),counts=dict(members=6,files=8,base_refs=4094),source_finding_fixed=True,source_level_launch_can_proceed=True,future_actual_results_required_before_launch=False,signature_approval_or_Owner_or_native_actual_accepted=False,target_executions=0,new_mechanical_errors=0,authority='NONE',formal_acceptance=False,stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
print(json.dumps(dict(HDF=h,manifest=m,members=6,files=8,base_refs=4094,drift=0)))

