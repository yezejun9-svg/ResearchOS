"""Freeze this non-author source-only review with exact candidate/evidence pins."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
OUT=Path(__file__).resolve().parent
REPO=next(p for p in OUT.parents if (p/'execution/project_identity.json').is_file())
WT=REPO/'.local/worktrees/w05-loopback-local-model-20261012'
def ref(p):
    raw=p.read_bytes();return {'path':p.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
audit=json.loads((OUT/'evidence-audit.json').read_text(encoding='utf-8'))
assert ref(REPO/audit['manifest_ref']['path'])==audit['manifest_ref']
assert not subprocess.check_output(['git','-C',str(WT),'status','--porcelain'])
for r in audit['nine_commit_files_verified']:assert hashlib.sha256((WT/r['path']).read_bytes()).hexdigest()==r['sha256']
files=['REVIEW.md','evidence-audit.json','verify_and_probe.py','independent_loopback_windows_test.go.txt',
 'independent-invocation.json','independent-go-test.jsonl','independent-go-test.stderr.txt',
 'attempt-002/independent-invocation.json','attempt-002/independent-go-test.jsonl','attempt-002/independent-go-test.stderr.txt']
review={'schema':'researchos.w05.strict-loopback-independent-source-review.v1',
 'decision':'SOURCE_AND_DEVELOPMENT_COMPONENT_ACCEPTED','scope':'STRICT_LOOPBACK_SOURCE_AND_LOCAL_FIXTURE_ONLY',
 'reviewer_id':'/root/w09_header_gate_review','author_id':'/root/w05_main24','issued_at':datetime.now(timezone.utc).isoformat(),
 'candidate_commit':audit['candidate_commit'],'base_commit':audit['base_commit'],'manifest_ref':audit['manifest_ref'],
 'reviewed_files':audit['nine_commit_files_verified'],
 'checks':{k:'PASS' for k in ('exact_source_and_commit','frozen_contract_boundary','literal_loopback_only','no_credential_or_inherited_secret','frozen_route_binding','remote_tls_credential_unchanged','redirect_proxy_vault_controls','unknown_retry_fence','original10_tests','independent2_tests')},
 'limits':['No real Ollama/qwen model called or qualified.','SDK transport tests are FIXTURE; LIVE local admission predicates are unit-tested and statically traced.',
 'CLI set-model still HTTPS-only; ordinary local model product setup not complete.','No W05/A04 formal acceptance or parent acceptance.'],
 'main_or_canon_modified':False,'formal_cases_accepted_delta':0,'paid_calls':0,
 'evidence_refs':[ref(OUT/f) for f in files]}
target=OUT/'independent-review.json';assert not target.exists()
target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'decision':review['decision'],'review_ref':ref(target),'manifest_ref':audit['manifest_ref'],'candidate_commit':audit['candidate_commit']},ensure_ascii=False,indent=2))
