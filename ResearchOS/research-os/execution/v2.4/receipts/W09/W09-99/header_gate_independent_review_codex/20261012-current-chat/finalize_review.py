"""Pin the actual independent negative decision; never create authority."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
SOURCE=REPO/'execution/v2.4/receipts/W09/W09-99/resume_cp398_formal_audit_codex/20261012-current-chat'
def ref(path):
    raw=path.read_bytes()
    return {'path':path.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
manifest=json.loads((SOURCE/'candidate-v2-manifest.json').read_text(encoding='utf-8'))
assert ref(SOURCE/'candidate-v2-manifest.json')['sha256']=='bbbe73ff9b1188ac72f68d87191181571e6f88461274cef1159beea1e1799bd3'
cert_ref=ref(REPO/manifest['certificate_ref']['path'])
assert cert_ref==manifest['certificate_ref']
for item in manifest['files']:
    assert ref(REPO/item['frozen_ref']['path'])==item['frozen_ref']
    assert hashlib.sha256(Path(item['candidate_path']).read_bytes()).hexdigest()==item['sha256']
cert=json.loads((REPO/cert_ref['path']).read_text(encoding='utf-8'))
assert ref(REPO/cert['old_profile_ref']['path'])['sha256']==cert['old_profile_ref']['sha256']
assert ref(REPO/cert['index_ref']['path'])['sha256']==cert['index_ref']['sha256']
assert not (REPO/'execution/v2.4/w09_header_correction.py').exists()
report={
 'schema':'researchos.w09.correction-independent-review.v1',
 'scope':'INTERPRETER_RECOVERY_ONLY','decision':'REQUEST_CHANGES',
 'reviewer_id':'/root/w09_header_gate_review','author_id':'/root/resume_audit',
 'issued_at':datetime.now(timezone.utc).isoformat(),'certificate_ref':cert_ref,
 'checks':{'certificate_pins':'PASS','header_delta':'PASS','business_ranges':'PASS',
           'project_bindings':'PASS','interpreter_diff':'FAIL','negative_controls':'FAIL'},
 'evidence_refs':[ref(OUT/name) for name in ('review_controls.py','candidate22-tests.txt','controls-result.json','REVIEW.md')]
}
(OUT/'source-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':report['decision'],'review_ref':ref(OUT/'source-review.json'),
 'certificate_ref':cert_ref,'profile_ref':manifest['files'][0]['frozen_ref'],
 'helper_ref':manifest['files'][1]['frozen_ref']},ensure_ascii=False,indent=2))
