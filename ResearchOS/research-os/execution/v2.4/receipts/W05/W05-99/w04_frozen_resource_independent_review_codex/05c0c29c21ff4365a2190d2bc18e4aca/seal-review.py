import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((D/'evidence.json').read_bytes())['base_refs'];assert len(refs)==309
for r in refs:assert pin(r['path'])==r
names=['verify-resources.py','evidence.json','review.json','original-tool-io.json','diagnostic-812.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='W04_FROZEN_RESOURCE_COMPONENT_ACCEPTED_STOP',manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),diagnostic_ref=pin(D/'diagnostic-812.json'),counts=dict(members=7,files=9,base_refs=309,manifest_members=147,snapshot_files=148,closed_guards=299),authority='NONE',W04_actual_accepted=False,W04_formal_accepted=False,target_script_or_Go_native_SQL_Owner_model_executions_by_reviewer=0,new_mechanical_error_ordinals=[812],stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
assert len(list(D.iterdir()))==9
print(json.dumps(dict(HDF=h,manifest=m,members=7,files=9,base_refs=309,drift=0,diagnostic_ordinals=[812]),ensure_ascii=True))
