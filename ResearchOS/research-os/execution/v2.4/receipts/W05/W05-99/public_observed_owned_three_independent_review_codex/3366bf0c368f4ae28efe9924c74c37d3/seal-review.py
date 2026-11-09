import json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
refs=json.loads((O/'evidence.json').read_bytes())['base_refs']
assert len(refs)==118
for r in refs:assert pin(r['path'])==r
names=['verify-actual.py','evidence.json','review.json','original-tool-io.json','report.md','seal-review.py']
assert sorted(p.name for p in O.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(O/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='THREE_PUBLIC_OBSERVED_OWNED_ACTUAL_ACCEPTED_COMPONENT_ONLY_STOP',manifest_ref=m,review_ref=pin(O/'review.json'),report_ref=pin(O/'report.md'),counts=dict(members=6,files=8,base_refs=118,actual_cases=3,closed_jobs=4,inner_guard_refs=94,outer_guard_refs=94),scope='Public normal/cancel/timeout helper actual only',authority='NONE',controller_race_finding_still_open=True,Owner_or_native9_or_original_trial_accepted=False,descendant_boolean_is_count_threshold_only=True,new_mechanical_errors=0,formal_acceptance=False,stop=True))
for r in refs+json.loads((O/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
assert len(list(O.iterdir()))==8
print(json.dumps(dict(HDF=h,manifest=m,members=6,files=8,base_refs=118,drift=0,new_mechanical_errors=0),ensure_ascii=True))
