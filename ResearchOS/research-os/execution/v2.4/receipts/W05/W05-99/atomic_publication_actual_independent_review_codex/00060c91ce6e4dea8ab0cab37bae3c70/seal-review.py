import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((D/'evidence.json').read_bytes())['base_refs'];assert len(refs)==4104
for r in refs:assert pin(r['path'])==r
names=['verify-evidence.py','evidence.json','review.json','original-tool-io.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
review=json.loads((D/'review.json').read_bytes())
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision=review['decision'],manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),counts=dict(members=6,files=8,base_refs=4104),publication_finding_closed_component_scope=True,positive_public_config_preparation_accepted=True,concrete_launch_or_signing_approved=False,controller_overall_or_Owner_or_native9_accepted=False,new_mechanical_errors=0,authority='NONE',formal_acceptance=False,stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
assert len(list(D.iterdir()))==8
print(json.dumps(dict(HDF=h,manifest=m,members=6,files=8,base_refs=4104,drift=0,new_mechanical_errors=0),ensure_ascii=True))

