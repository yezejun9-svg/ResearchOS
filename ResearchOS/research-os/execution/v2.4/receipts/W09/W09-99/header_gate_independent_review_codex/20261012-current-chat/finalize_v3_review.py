"""Issue this reviewer's real source-only decision for the exact frozen v3."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
def ref(p):
    raw=p.read_bytes()
    return {'path':p.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
summary=json.loads((OUT/'v3-controls-result.json').read_text(encoding='utf-8'))
assert summary['candidate26_passed'] and all(x['status']=='PASS' for x in summary['additional_controls'])
certificate_ref=summary['certificate_ref']
assert ref(REPO/certificate_ref['path'])==certificate_ref
manifest=json.loads((REPO/summary['manifest_ref']['path']).read_text(encoding='utf-8'))
for item in manifest['files']:
    assert ref(REPO/item['frozen_ref']['path'])==item['frozen_ref']
    assert hashlib.sha256(Path(item['candidate_path']).read_bytes()).hexdigest()==item['sha256']
assert ref(OUT/'source-review.json')['sha256']=='7ca513749bd2725bc4309e6806ac7c80796f6193cb0d73a83885196ae50c844e'
review={'schema':'researchos.w09.correction-independent-review.v1','scope':'INTERPRETER_RECOVERY_ONLY',
 'decision':'ACCEPTED_RECOVERY_SOURCE_ONLY','reviewer_id':'/root/w09_header_gate_review',
 'author_id':'/root/resume_audit','issued_at':datetime.now(timezone.utc).isoformat(),
 'certificate_ref':certificate_ref,
 'checks':{k:'PASS' for k in ('certificate_pins','header_delta','business_ranges','project_bindings','interpreter_diff','negative_controls')},
 'evidence_refs':[ref(OUT/f) for f in ('review_v3_controls.py','v3-candidate26-tests.txt','v3-controls-result.json','V3_REVIEW.md')]}
target=OUT/'source-review-v3.json'
assert not target.exists()
target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'review_ref':ref(target),'certificate_ref':certificate_ref,
 'profile_ref':manifest['files'][0]['frozen_ref'],'helper_ref':manifest['files'][1]['frozen_ref']},ensure_ascii=False,indent=2))
