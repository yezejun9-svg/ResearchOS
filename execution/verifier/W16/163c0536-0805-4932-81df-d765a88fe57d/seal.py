import datetime,hashlib,json,pathlib
ROOT=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
RUN='163c0536-0805-4932-81df-d765a88fe57d';OUT=ROOT/'execution/verifier/W16'/RUN;PACK=ROOT/'execution/receipts/W16'/RUN;PRIOR=ROOT/'execution/verifier/W16/evolution-881e42e'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return p.relative_to(ROOT).as_posix()
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jcs(v):
 def inspect(x):
  if isinstance(x,float):raise ValueError('float not supported')
  if isinstance(x,dict):
   for k,w in x.items():
    if any(ord(c)>65535 for c in k):raise ValueError('non-BMP key')
    inspect(w)
  elif isinstance(x,list):
   for w in x:inspect(w)
 inspect(v)
 return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
audit=load(OUT/'audit-report.json');executor=load(PACK/'receipt.json');prior=load(PRIOR/'review.json')
assert audit['status']=='PASS' and audit['checks_passed']==2618
limits=[
 'Only frozen W16-G02 in FIXTURE and complete FIXTURE cases C09/C10/C12 are accepted. Whole W16, G01, G03, C20 complete case and formal A16 remain unaccepted.',
 'C20 numbered fixture assertions are supported, but complete frozen holdout evidence is absent. Public deterministic suite must not be described as protected holdout.',
 'Native AppContainer children, actual temporary SQLite backup/isolated-copy restore, old binary health and fixture task continuity do not qualify independent production OS supervisor, active data cutover or host crash/restart reconciliation.',
 'No successful real operating cycle or 6-24h LIVE canary observation was established. No model weights were trained or updated.',
 'Acceptance is pinned to source 1768c89ca8a4f2ba4f79240f281c92f3c4683367. Subsequent W15/main changes require their own integration verification; current main was not substituted for frozen Git blobs.',
 'This package review reran no unchanged native/product tests. It independently checked raw outputs and full hash chains and carries forward the prior independent real native/HTTP probes because all 135 prior product/spec source files remain byte-identical; only the reviewed runner differs.',
 'No production database, actual .local/data, secrets, protected service, external provider/network, UAC, installation or blocked action was accessed. Schema 0015 evidence is isolated fixture only.',
 'W14 LIVE, W15 and W18 whole-stage dependencies are not cleared by this signature.'
]
review={'artifact_kind':'INDEPENDENT_W16_FORMAL_PACKAGE_REVIEW','task_id':'W16','run_id':RUN,'verifier_identity':'codex:/root/evolution_verifier','verdict':'PASS_IN_SCOPE','scope':'W16-G02 and complete C09/C10/C12 FIXTURE only','source_revision':executor['code_revision'],'source_delta_assessment':{'original_source_revision':prior['source_revision'],'original_review_head':prior['review_head'],'compared_sources':136,'byte_identical':135,'changed':['ops/ci/evolution.py'],'runner_delta':'Only actual alias command_key, stdout assertion_ids and C20/A16 PARTIAL classification; assertion verifier/native behavior unchanged. test.orchestration strictly delegates W16 C10; exact dispatcher selectors are source-bound.'},'prior_review_reference':ref(PRIOR/'review.json'),'prior_review_sha256':sha(PRIOR/'review.json'),'audit_reference':ref(OUT/'audit-report.json'),'audit_sha256':sha(OUT/'audit-report.json'),'verification_summary':audit,'blocking_findings_in_accepted_scope':[],'retained_out_of_scope_findings':prior['findings'],'limits':limits,'whole_stage_accepted':False}
write(OUT/'review.json',review)
files=[{'path':ref(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='evidence-index.json']
index={'task_id':'W16','run_id':RUN,'files':files,'executor_manifest_reference':ref(PACK/'artifacts.json'),'executor_manifest_sha256':sha(PACK/'artifacts.json'),'prior_independent_review_reference':ref(PRIOR/'review.json'),'prior_independent_review_sha256':sha(PRIOR/'review.json')}
write(OUT/'evidence-index.json',index)
bases={
'C09':'Frozen native same-input comparison proves required failure blocks the candidate despite local gain; prior stable hash/control host preserved and unrelated fixture task independently accepted.',
'C10':'Four native/administrative tamper attempts preserve baseline, label, release permissions and stable binary; executor/self-release denied; independent rule proposal retains old-suite result and separate samples without self-approval. Both required registered commands have complete matching raw assertions.',
'C12':'Actual required canary degradation overrides self-score, records threshold/raw old-new hashes, restores real temporary SQLite to an isolated copy, checks exact old native binary health, freezes failed candidate and rejects repeated promotion. Production OS service and active database switching are not claimed.'}
cases=[]
for name in ['C09','C10','C12']:
 case=load(PACK/(name+'.json'));ids=[a['assertion_id'] for a in case['assertion_results']]
 cases.append({'case_id':name,'verdict':'PASS','mode':'FIXTURE','actual_runtime_scope':'REAL_NATIVE_WINDOWS_APPCONTAINER_AND_ISOLATED_HTTP_SQLITE_FIXTURE','assertion_ids':ids,'assertion_verdicts':{a:'PASS' for a in ids},'all_frozen_assertions_covered':True,'expected_actual_status_reference':ref(PACK/(name+'.json')),'executor_global_evidence_sha256':sha(PACK/(name+'.json')),'basis':bases[name]})
receipt={'artifact_kind':'INDEPENDENT_LIMITED_CONSTRUCTION_ACCEPTANCE_WITH_OWNED_CASE_VERDICTS','task_id':'W16','run_id':RUN,'project_id':executor['project_id'],'status':'PARTIAL_ACCEPTANCE','verdict':'PASS_IN_SCOPE','stage_accepted':False,'whole_W16_accepted':False,'W16_G02_accepted':True,'C09_accepted':True,'C10_accepted':True,'C12_accepted':True,'C20_accepted':False,'A16_accepted':False,'W16_G01_accepted':False,'W16_G03_accepted':False,'production_scheduler_upgrade_accepted':False,'independent_OS_service_accepted':False,'upstream_dependencies_cleared':False,'scope':'W16-G02 and complete frozen C09/C10/C12 assertions in FIXTURE mode only.','executor_identity':'codex:/root','verifier_identity':'codex:/root/evolution_verifier','independence_basis':'Verifier did not implement the product or prepare the executor package. Independently ran prior native/HTTP probes, matched source applicability, recomputed raw outcomes and receipt hashes, reconciled all five dispatcher chains and complete frozen case assertions.','executed_code_revision':executor['code_revision'],'executor_receipt_reference':ref(PACK/'receipt.json'),'executor_receipt_sha256':sha(PACK/'receipt.json'),'executor_receipt_jcs_hash':executor['receipt_hash'],'artifact_manifest_reference':ref(PACK/'artifacts.json'),'artifact_manifest_sha256':sha(PACK/'artifacts.json'),'artifact_count_verified':95,'acceptance_baseline_reference':'spec/v2.0/contracts/acceptance.json','acceptance_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/acceptance.json'),'task_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/tasks.json'),'task_gates':[{'check_id':'W16-G02','verdict':'PASS','mode':'FIXTURE','accepted':True,'basis':'All 18 exact frozen-gate fixture checks have hash-bound raw native evidence; independent prior probes and current raw recomputation establish tamper/self-approval rejection, degradation rollback and version/score separation. This gate does not waive full C20 holdout or A16 LIVE requirements.'},{'check_id':'W16-G01','verdict':'NOT_ACCEPTED','accepted':False,'mode':'DEVELOPMENT','basis':'W18 whole-stage and current real recovery qualification prerequisite not cleared.'},{'check_id':'W16-G03','verdict':'BLOCKED','accepted':False,'mode':'LIVE_WINDOWS','basis':'W14 LIVE, independent production supervisor, active canary cutover and host crash recovery remain unqualified.'}],'owned_case_verdicts':cases,'unaccepted_case_verdicts':[{'case_id':'C20','verdict':'PARTIAL','accepted':False,'basis':'Numbered fixture assertions pass; full frozen holdout result evidence absent.'},{'case_id':'A16','verdict':'PARTIAL_FIXTURE_ONLY','accepted':False,'basis':'Native negative fixture paths verified; formal independent control-plane, production data recovery and observation window absent.'}],'open_findings':prior['findings'],'open_blockers':executor['open_blockers'],'resource_request_ids':executor['resource_request_ids'],'verification_summary':audit,'limits':limits,'signed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence_index_reference':ref(OUT/'evidence-index.json'),'evidence_index_sha256':sha(OUT/'evidence-index.json'),'semantic_audit_reference':ref(OUT/'audit-report.json'),'semantic_audit_sha256':sha(OUT/'audit-report.json'),'review_reference':ref(OUT/'review.json'),'review_sha256':sha(OUT/'review.json'),'prior_independent_review_reference':ref(PRIOR/'review.json'),'prior_independent_review_sha256':sha(PRIOR/'review.json')}
receipt['receipt_hash']='sha256:'+hashlib.sha256(jcs(receipt)).hexdigest()
final=OUT.with_suffix('.json');write(final,receipt)
for row in index['files']:assert sha(ROOT/row['path'])==row['sha256']
assert receipt['receipt_hash']=='sha256:'+hashlib.sha256(jcs({k:v for k,v in load(final).items() if k!='receipt_hash'})).hexdigest()
print(json.dumps({'receipt_reference':ref(final),'receipt_sha256':sha(final),'receipt_jcs_hash':receipt['receipt_hash'],'index_sha256':sha(OUT/'evidence-index.json'),'audit_sha256':sha(OUT/'audit-report.json'),'checks_passed':audit['checks_passed'],'status':receipt['status'],'accepted':['W16-G02','C09','C10','C12']},indent=2))
