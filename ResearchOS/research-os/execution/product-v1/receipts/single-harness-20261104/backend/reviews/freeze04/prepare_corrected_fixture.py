from pathlib import Path
import hashlib,json
here=Path(__file__).resolve().parent;run=here/'run-03'
overlay=json.loads((run/'overlay.json').read_bytes())
inputs=json.loads((run/'inputs.json').read_bytes())
wt=Path(inputs['source']['internal/domain/runtime_harness_windows.go'].get('worktree','D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104'))
changes=[]
for virtual,local in [('internal/domain/independent_harness_authority_test.go','independent_domain_test.go'),('internal/api/independent_harness_transport_test.go','independent_api_test.go')]:
 target=run/'corrected-tests'/local
 assert not target.exists()
 target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((here/local).read_bytes())
 old=overlay['Replace'][str(wt/virtual)]
 overlay['Replace'][str(wt/virtual)]=str(target)
 changes.append({'virtual_path':virtual,'prior':old,'prior_sha256':hashlib.sha256(Path(old).read_bytes()).hexdigest(),'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
target=run/'overlay-corrected.json';assert not target.exists()
target.write_text(json.dumps(overlay,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
correction={'origin_key':'backend-v1-review-canonical-high-sequence-fixture','classification':'REVIEW_FIXTURE_UNSUPPORTED_EXISTING_CANONICAL_STATE','original_result':'independent-counterexamples.result.json','root_decision':'Use highest IEEE-safe canonical producer9007199254740991; retain full-int64 string-only consumer and future-reset tests. Do not invade shared legacy domain numeric contracts for V1.','source_changed':False,'original_failure_preserved':True,'changes':changes,'overlay_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'limitation':'Existing shared JCS numeric producer ceiling remains a documented boundary/debt, not qualified full-int64 producer sustainability.'}
target=run/'fixture-correction.json';assert not target.exists()
target.write_text(json.dumps(correction,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared_corrected_fixture':True,'source_changed':False,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
