import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
e=json.loads((D/'evidence.json').read_bytes());refs=e['base_refs'];assert len(refs)==4145
for r in refs:assert pin(r['path'])==r
assert len(e['historical_deleted_fixture_refs'])==2
names=['verify-failed-closed.py','evidence.json','review.json','original-tool-io.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs,historical_deleted_fixture_refs=e['historical_deleted_fixture_refs']))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='FAILED_EXECUTION_CLOSED_SQL_INSPECTION_AND_ROOT_CLEANUP_ACCEPTED_COMPONENT_ONLY',manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),counts=dict(members=6,files=8,base_refs=4145,historical_deleted_refs=2),Go_actual_exit=1,two_Jobs_closed=True,guard_observations_closed=11,SQL_read_component_accepted=True,Root_cleanup_component_accepted=True,native_case_pass=False,Owner_or_Original_business_accepted=False,diagnostics_preserved=[820,821],new_mechanical_errors=0,authority='NONE',formal_acceptance=False,stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
print(json.dumps(dict(HDF=h,manifest=m,members=6,files=8,base_refs=4145,historical_deleted_refs=2,drift=0)))

