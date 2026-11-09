import json, hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
    p=Path(p); b=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,d):
    with (O/n).open('xb') as f:
        f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(O/n)
e=json.loads((O/'evidence.json').read_bytes())
refs=e['refs']
assert len(refs)==68
for r in refs:
    assert pin(r['path'])==r, r['path']
names=['evidence.json','review.json','original-tool-io.json','diagnostics-after-cp356.json','seal-review.py']
assert sorted(p.name for p in O.iterdir())==sorted(names)
rv=json.loads((O/'review.json').read_bytes())
assert rv['orchestration_schema_rejection_after_evidence']['global_ordinal']==809
assert rv['receipt_write_process_creation_failure_after_evidence']['global_ordinal']==810
m=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(O/n) for n in names],base_refs=refs))
h=save('HDF.json',dict(schema='researchos.independent-review-handoff.v1',decision='CP356_CANONICAL_WRITE_AND_SCOPE_ACCEPTED_STOP',manifest_ref=m,review_ref=pin(O/'review.json'),evidence_ref=pin(O/'evidence.json'),diagnostics_ref=pin(O/'diagnostics-after-cp356.json'),counts=dict(members=5,files=7,base_refs=68,guards=48,CP356_registered=806,CP356_highest_ordinal=808),post_CP356_review_diagnostic_ordinals=[809,810],actual_execution_by_reviewer=False,authority='NONE',native9_or_Owner_or_original_trial_acceptance=False,original_Root_IO_post_manifest_separate_ref=True,controller_race_finding_still_open=True,stop=True))
for r in refs+json.loads((O/'MF.json').read_bytes())['members']:
    assert pin(r['path'])==r
assert len(list(O.iterdir()))==7
print(json.dumps(dict(HDF=h,manifest=m,members=5,files=7,base_refs=68,drift=0,diagnostics=[809,810]),ensure_ascii=True))
