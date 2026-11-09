"""Issue the actual reviewer's bounded development decision, not formal authority."""
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
def ref(p):
    raw=p.read_bytes();return {'path':p.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
audit=json.loads((OUT/'evidence-audit.json').read_text(encoding='utf-8'))
assert audit['status']=='PASS_BOUNDED_DEVELOPMENT_EVIDENCE'
assert ref(REPO/audit['result_ref']['path'])==audit['result_ref']
assert ref(REPO/audit['manifest_ref']['path'])==audit['manifest_ref']
review={'schema':'researchos.w09.current-main-development-independent-review.v1',
 'decision':'DEVELOPMENT_COMPONENT_ACCEPTED','scope':'CURRENT_MAIN24_COMPONENT_REGRESSION_ONLY',
 'reviewer_id':'/root/w09_header_gate_review','author_id':'/root/resume_audit',
 'issued_at':datetime.now(timezone.utc).isoformat(),'source_result_ref':audit['result_ref'],
 'handoff_manifest_ref':audit['manifest_ref'],'git_head':'549ad6924ad43d27bbe533f4ba020ef383a0888f',
 'checks':{'source_and_archive_pins':'PASS','actual_invocations':'PASS','preserved_first_failure':'PASS',
 'selected_go_lifecycle':'PASS','actual_assertions':'PASS_DEVELOPMENT_ONLY','owned_raw_pins':'PASS',
 'original_a06_oracle':'PASS','source_drift_accounting':'PASS'},
 'limits':['12 W0901 expected:null exports remain development-only; actual Go predicates checked.',
 'Revoked root -> backup -> restore -> search composition not executed.',
 'Distinct historical/current program 23-to-24 handoff not executed by this selector.',
 'C19 transitive input revalidation not established.',
 'Exact Native/mode/dispatcher/GLOBAL/independent formal chain not executed or accepted.'],
 'formal_acceptance_issued':False,'formal_cases_accepted_delta':0,'parent_accepted_delta':0,
 'canon_modified':False,'product_commands_rerun':False,
 'evidence_refs':[ref(OUT/name) for name in ('REVIEW.md','evidence-audit.json','verify_development_evidence.py')]}
target=OUT/'independent-review.json';assert not target.exists()
target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':review['decision'],'review_ref':ref(target)},ensure_ascii=False,indent=2))
