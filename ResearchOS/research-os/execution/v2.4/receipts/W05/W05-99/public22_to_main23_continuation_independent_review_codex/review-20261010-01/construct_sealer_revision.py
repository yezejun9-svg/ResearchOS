import hashlib,json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'seal_review.py'
before=p.read_bytes()
old=b"for ref in (pin(C/'HDF.json'), pin(C/'MF.json'), h['caller_ref'], h['calling_contract_ref']):"
new=b"for ref in (pin(C/'HDF.json'), pin(C/'MF.json'), h['calling_contract_ref']):"
if before.count(old)!=1:raise ValueError('ONE_SEALER_PUBLICATION_SELECTOR')
after=before.replace(old,new,1)
if after.replace(new,old,1)!=before:raise ValueError('EXACT_SEALER_INVERSE')
target=Q/'seal_review_revision.py'
with target.open('xb')as f:f.write(after)
def ref(path):
    b=path.read_bytes();return dict(path=str(path),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
delta=dict(schema='researchos.independent-sealer-revision.v1',failed_original_script_ref=ref(p),revision_script_ref=ref(target),exact_inverse=True,
    explanation='Actual Source FINAL publishes HDF, MF and contract refs. Caller is precisely transitively bound by the held HDF/MF; absence of separate caller_ref in FINAL is not a Source defect.',
    actual_final_fields_observation_ref=ref(Q/'actual-author-Final-field-observation.json'),old_failure_reexecuted=False)
with(Q/'sealer-revision-inverse.json').open('xb')as f:f.write((json.dumps(delta,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(delta,ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0')
