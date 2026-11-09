import json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
refs=json.loads((D/'evidence.json').read_bytes())['base_refs'];assert len(refs)==31
for r in refs:assert pin(r['path'])==r
names=['verify-source.py','evidence.json','review.json','original-tool-io.json','report.md','seal-review.py']
assert sorted(p.name for p in D.iterdir())==sorted(names)
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(D/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='ATOMIC_PUBLICATION_SOURCE_FIX_ACCEPTED_FOR_FOUR_PUBLIC_COMPONENT_CASES_ONLY_STOP',manifest_ref=m,review_ref=pin(D/'review.json'),report_ref=pin(D/'report.md'),counts=dict(members=6,files=8,base_refs=31),finding='NATIVE_CONTROLLER_NONATOMIC_PUBLIC_JSON_PUBLICATION',finding_source_fixed=True,finding_actual_fixed=False,Root_public_cases_source_accepted=['complete-publication','duplicate-after-precheck-no-clobber','forced-rename-failure-own-temp-cleanup','partial-ready-running-then-complete-release-phase'],controller_overall_or_Owner_or_native9_accepted=False,preserved_source_failure_ordinal=813,new_mechanical_errors=0,authority='NONE',formal_acceptance=False,stop=True))
for r in refs+json.loads((D/'MF.json').read_bytes())['members']:assert pin(r['path'])==r
assert len(list(D.iterdir()))==8
print(json.dumps(dict(HDF=h,manifest=m,members=6,files=8,base_refs=31,drift=0,new_mechanical_errors=0),ensure_ascii=True))
