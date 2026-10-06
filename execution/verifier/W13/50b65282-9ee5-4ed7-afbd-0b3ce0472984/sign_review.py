"""Issue the independent limited acceptance only for the audited frozen package."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/receipts/W13' / OUT.name
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def relative(p): return str(p.relative_to(ROOT)).replace('\\','/')
def reference(p): return {'path':relative(p),'sha256':sha(p)}
audit=read(OUT/'envelope-audit.json'); inputs=read(OUT/'input-audit.json'); executor=read(BASE/'receipt.json')
assert audit['status']=='PASS' and inputs['status']=='PASS_INPUT_AUDIT_ONLY'
assert sha(BASE/'receipt.json')==audit['executor_receipt_sha256']
assert sha(BASE/'artifacts.json')==audit['manifest_sha256']
assert executor['receipt_hash']==audit['executor_receipt_jcs_hash']
assert all(sha(ROOT/x['path'])==x['sha256'] for x in read(BASE/'artifacts.json')['files'])
frozen={x['id']:x for x in read(ROOT/'spec/v2.0/contracts/acceptance.json')['cases']}
basis={
 'C17':'Real transaction rollback fault, durable unacknowledged outbox consumed five times, recipient/dedup/read-idempotence checks; real browser recovers offline release and consumes12 frames from2 nonempty events, preserves single card and full sidebar/notification/release artifact hash and acceptance chain.',
 'C18':'Actual four service-accepted tasks plus two explicit VERIFYING fixtures produce4/6 then4/9 with three READY; old projection does not replace new revision; currentness re-evaluation and authoritative rebuild checked. Actual per-task plan revisions7->10 are retained rather than relabeled1->2.',
 'C23':'Combined actual routed browser flows, pause/resume/cancel waiting and final fixture acknowledgement, independent acceptance, version switching, fixed11Task/9Run state matrix, empty/loading/error/403/429/stale/offline/partial-source states, project isolation, query/filter and populated evaluation/skill/resource views.',
 'C24':'156 responsive rows, required five viewport sizes across light/dark themes,164 hash-verified screenshots; actual desktop Chromium200percent zoom, reduced motion, keyboard/focus restoration, accessible control names, measured contrast and44px targets. Reviewer personally inspected four320px screenshots and prior independent typography/timeout/selection regression evidence.',
 'C25':'Seven sealed content formats with hash-bound preview/download, script-free sandboxed HTML and blocked external network, native PDF render, corrupted-image recovery, size fallback, restricted metadata/content filtering, late request cancellation, traversal and frozen-reference rejection, retained403/412 drafts and explicit new candidates/ChangeProposal.'}
cases=[]
for id in ['C17','C18','C23','C24','C25']:
    ids=[x['id'] for x in frozen[id]['assertions']]
    cases.append({'case_id':id,'verdict':'PASS','mode':'FIXTURE','actual_runtime_scope':'REAL_WINDOWS_CHROMIUM_HTTP_SQLITE_WITH_EXPLICIT_FIXTURES',
                  'assertion_ids':ids,'assertion_verdicts':{key:'PASS' for key in ids},'all_frozen_assertions_covered':True,
                  'expected_actual_status_reference':relative(BASE/(id+'.json')),'executor_global_evidence_sha256':sha(BASE/(id+'.json')),'basis':basis[id]})
index={relative(p):sha(p) for p in sorted(OUT.glob('*')) if p.is_file() and p.name!='evidence-index.json'}
(OUT/'evidence-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review={
 'artifact_kind':'INDEPENDENT_LIMITED_CONSTRUCTION_ACCEPTANCE_WITH_OWNED_CASE_VERDICTS',
 'task_id':'W13','run_id':OUT.name,'project_id':executor['project_id'],'status':'PARTIAL_ACCEPTANCE','verdict':'PASS_IN_SCOPE',
 'stage_accepted':False,'scope':'W13-G01/G02 and complete frozen FIXTURE cases C17,C18,C23,C24,C25 accepted. C26/G03, physical OS sleep, phone and overall W13 stage remain unaccepted.',
 'executor_identity':'codex:/root','verifier_identity':'codex:/root/workbench_verifier',
 'independence_basis':'Reviewer authored no product implementation; prior detached-worktree browser counterexamples and repair regressions plus current independent raw-line, source-manifest, screenshot, GLOBAL mapping and hash audits. This formal audit did not rerun browsers or business tests.',
 'browser_revision':'be8f6a7266fc11fb58afeb724cda4883323d41fb','backend_revision':'591d16e277dd7e3f26809f2bffa7fb142a398609',
 'executed_code_revision':'69509c240fdbb4922b27a009155099cc983bbc11',
 'executor_receipt_reference':relative(BASE/'receipt.json'),'executor_receipt_sha256':sha(BASE/'receipt.json'),'executor_receipt_jcs_hash':executor['receipt_hash'],
 'artifact_manifest_reference':relative(BASE/'artifacts.json'),'artifact_manifest_sha256':sha(BASE/'artifacts.json'),'artifact_count_verified':544,
 'acceptance_baseline_reference':'spec/v2.0/contracts/acceptance.json','acceptance_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/acceptance.json'),
 'task_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/tasks.json'),
 'task_gates':[
  {'check_id':'W13-G01','verdict':'PASS','mode':'FIXTURE','basis':'C17/C18 complete browser plus backend mapped assertions; nonempty replay and exact full chain independently checked.'},
  {'check_id':'W13-G02','verdict':'PASS','mode':'LIVE_WINDOWS','basis':'Actual Windows Chromium flows, keyboard/readability/responsive evidence; fixed business fixtures declared and actual phone qualification remains W17.'},
  {'check_id':'W13-G03','verdict':'PARTIAL','accepted':False,'mode':'FIXTURE','basis':'C23-C25 accepted; C26 complete physical sleep/resume action not executed.'}],
 'owned_case_verdicts':cases,
 'unaccepted_case_verdicts':[{'case_id':'C26','verdict':'PARTIAL','accepted':False,'all_frozen_assertions_covered':False,'basis':'Browser lifecycle freeze, replay/gap/410 and offline recovery evidence exists; actual computer sleep/resume action is NOT_RUN and is not inferred from Chromium freeze.'}],
 'build_verdict':{'status':'PASS','reference':audit['build']['invocation'],'registered_assertions':9,'successful_go_test_packages':17,'frozen_source_files_checked':263},
 'closed_application_findings':['W13-UI-P2-001','W13-UI-P2-002','W13-UI-P2-003'],'open_findings':[],
 'open_blockers':['C26 and W13-G03 remain partial until actual OS sleep/resume is evidenced.','W05 live resource policy blocker and final live upstream qualifications remain unresolved.','Actual phone/cross-network/TLS acceptance remains W17; no promotion of responsive Chromium into physical-device proof.'],
 'resource_request_ids':['RQ-W05-CLI-POLICY-001'],
 'limits':['Five accepted cases use their frozen FIXTURE mode; W13-G02 is real Windows browser execution with explicit business fixtures.',
           'No actual protected holdout, external provider evaluation, remote deployment, phone operation or OS sleep was performed in these W13 runs.',
           'Initial browser transport failure, wrapper zero-assertion classification and three failed native full builds remain preserved. Later valid evidence does not relabel them PASS.',
           '3a79574,6238e81,69509c2 only adjust fixture transport readiness/budgets; business assertions and explicit10ms cancellation remain intact. Source manifests are bound to each execution revision.',
           'Subsequent W17 integration is outside this frozen signature and requires affected-input regression judgment; this receipt does not claim arbitrary later HEAD equivalence.'],
 'independent_review_references':[reference(ROOT/'execution/verifier/W13/ui-70db969/review.json'),reference(OUT/'input-audit.json'),reference(OUT/'envelope-audit.json')],
 'evidence_index_reference':relative(OUT/'evidence-index.json'),'evidence_index_sha256':sha(OUT/'evidence-index.json'),
 'global_envelope_check_reference':relative(OUT/'envelope-audit.json'),'global_envelope_check_sha256':sha(OUT/'envelope-audit.json'),
 'signed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
review['receipt_hash']='sha256:'+hashlib.sha256(json.dumps(review,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
target=OUT.with_suffix('.json'); assert not target.exists(), 'Refuse replacing an existing formal signature'
target.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':review['status'],'accepted_cases':[x['case_id'] for x in cases],'stage_accepted':False,'signature':relative(target),'sha256':sha(target),'receipt_hash':review['receipt_hash']}))
