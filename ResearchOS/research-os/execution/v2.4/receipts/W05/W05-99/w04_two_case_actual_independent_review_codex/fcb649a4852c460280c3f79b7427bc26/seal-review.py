import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((D/'evidence.json').read_bytes())['base_refs'];assert len(refs)==4355
for r in refs:assert pin(r['path'])==r
names=['verify-actual.py','verify-actual-v2.py','evidence.json','review.json','original-tool-io.json','diagnostics-816-817.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='W04_TWO_CASE_OBSERVED_PASS_ACCEPTED_COMPONENT_ONLY_RUNTIME_CLOSURE_PARTIAL_STOP',manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),diagnostics_ref=pin(D/'diagnostics-816-817.json'),counts=dict(members=8,files=10,base_refs=4355,actual_pass=2,actual_fail=0,actual_skip=0,assertions=5,existing_closed_guards=4337),common_go_wrapper_closure='PARTIAL',legacy_child_python_closure='PARTIAL',current_case_legacy_python_gap_applies=False,all_runtime_inputs_accepted=False,diagnostic_ordinals=[816,817],authority='NONE',formal_or_FULL_or_Owner_or_native9_accepted=False,stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
assert len(list(D.iterdir()))==10
print(json.dumps(dict(HDF=h,manifest=m,members=8,files=10,base_refs=4355,drift=0,diagnostic_ordinals=[816,817]),ensure_ascii=True))
