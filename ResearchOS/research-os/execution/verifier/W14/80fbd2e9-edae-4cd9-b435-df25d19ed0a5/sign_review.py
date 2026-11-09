"""Sign only the integrated W14-G01 fixture gate."""
from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
BASE=ROOT/'execution/receipts/W14'/OUT.name
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)}
audit=read(OUT/'audit-report.json');receipt=read(BASE/'receipt.json')
assert audit['status']=='PASS' and audit['assertions']==32
prior=ROOT/'execution/verifier/W14/fixture-f84f17a/review.json'
index={'files':[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='evidence-index.json']}
(OUT/'evidence-index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
result={
 'artifact_kind':'INDEPENDENT_LIMITED_CONSTRUCTION_ACCEPTANCE_WITH_OWNED_CASE_VERDICTS',
 'task_id':'W14','run_id':OUT.name,'project_id':receipt['project_id'],
 'status':'PARTIAL_ACCEPTANCE','verdict':'PASS_IN_SCOPE','stage_accepted':False,
 'whole_W14_accepted':False,'A13_accepted':False,'W14_G02_accepted':False,
 'scope':'W14-G01 cross-module FIXTURE gate only. No owned acceptance case, live combined cycle, autonomous session or overall stage acceptance.',
 'executor_identity':'codex:/root','verifier_identity':'codex:/root/workbench_verifier',
 'independence_basis':'Verifier authored no W14 implementation or execution package. Reviewed frozen contract, source delta, raw32-assertion integrated flow,96 product HTTP records, six persisted-object hashes and independent product receipt JCS; verified44 manifest files,261 source Git blobs and25 previous independent replay evidence files. Existing independent orchestration verifier reran three processes and checked DB principals; no further product execution was needed.',
 'executed_code_revision':receipt['code_revision'],
 'prior_independent_fixture_source_revision':'f84f17a4af7f51763a6c27ab6f69161dad8afbe1',
 'executor_receipt_reference':ref(BASE/'receipt.json')['path'],
 'executor_receipt_sha256':sha(BASE/'receipt.json'),
 'executor_receipt_jcs_hash':receipt['receipt_hash'],
 'artifact_manifest_reference':ref(BASE/'artifacts.json')['path'],
 'artifact_manifest_sha256':sha(BASE/'artifacts.json'),'artifact_count_verified':44,
 'task_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/tasks.json'),
 'fixture_contract_reference':'evaluation/project_cycle/fixture_contract.json',
 'fixture_contract_sha256':sha(ROOT/'evaluation/project_cycle/fixture_contract.json'),
 'task_gates':[{'check_id':'W14-G01','verdict':'PASS','mode':'FIXTURE',
  'actual_runtime_scope':'REAL_WINDOWS_LOOPBACK_HTTP_SQLITE_WITH_EXPLICIT_SYNTHETIC_SOURCE_JEV_RUNTIME_SEAMS',
  'basis':'Integrated registered invocation matches32 frozen assertions. Covers source/body binding, stale semantic and task input rejection, frozen plan mismatch, unfinished experiment rejection, result tamper rejection, real deterministic service acceptance, legal NO_IMPROVEMENT, counterevidence defeating maximum synthetic score, independently applied negative decision, unsupported adoption rejection, completed negative cycle/release/notification, new-process state continuity, and missing-source honest PARTIAL.'},
  {'check_id':'W14-G02','verdict':'NOT_RUN','accepted':False,'mode':'LIVE_WINDOWS_AND_SERVICE',
   'basis':'No combined real three-source/Jev/executor research cycle evidence. SourceLIVE metadata in the injected fixture does not change evidence scope.'}],
 'owned_case_verdicts':[],
 'unaccepted_case_verdicts':[{'case_id':'A13','verdict':'NOT_RUN','accepted':False,'all_frozen_assertions_covered':False,'basis':'This evidence is W14-G01 fixture only; A13 needs its own complete live case.'}],
 'verification_summary':{'assertions':32,'product_http_requests':96,'http_rejections':7,'additional_trusted_service_rejection':1,
  'registered_invocation_reference':receipt['verification_results'][0]['actual_invocation_reference'],
  'three_process_pids':audit['phase_pids'],'resumed_object_hashes':audit['resume_object_hashes_recomputed'],
  'product_acceptance_receipt_jcs':audit['independent_acceptance_receipt_jcs'],'source_hashes_checked':261,
  'prior_independent_replay_assertions':32,'prior_independent_audit_checks':434,
  'temporary_product_database_removed':True,'new_product_or_provider_runs_in_this_review':0},
 'integration_assessment':'Fixture Go source and frozen contract unchanged from the prior independent rerun. Runner delta only bindsG01 and emits assertion_ids/receipt for dispatcher. W17 authentication/migration integration is covered for this fixture flow by the new integrated execution; W17 upgrade-constructor/security qualification remains outside this signature.',
 'open_findings':[],
 'open_blockers':['W14-G02/A13 and completeW14 remain unaccepted.','W05 policy-blocked live executor remains unresolved.'],
 'resource_request_ids':['RQ-W05-CLI-POLICY-001'],
 'limits':[
  'Three source pages and Jev response are synthetic; source metadataLIVE is produced by the package-local injection seam and is not provider evidence.',
  'ObserveRuntime injects explicit fixture completion. Real Windows child-process execution and loopback HTTP do not prove executor sandbox isolation or actual provider calls.',
  'Resume proves separate process persisted-state reconstruction. Goal remainsACTIVE and next taskDRAFT; no autonomous model-session or Goal acceptance claim.',
  'No measurable improvement was observed: fixed baseline1 andcandidate1 preserveNO_IMPROVEMENT. Negative cycle completion is allowed; it is not an adoption claim.',
  'Credential-bearing wire fields are redacted; original raw byte hashes are retained without claiming the redacted records reproduce credential-bearing bytes.',
  'Only frozenff134971 execution and exact affected source binding are accepted; arbitrary later constructor/security changes need their own review.',
  'Original failure history and previous independent replay retain their source/mode boundaries. No product code, executor evidence or existing review was modified.'
 ],
 'independent_review_references':[ref(prior),ref(OUT/'audit-report.json')],
 'evidence_index_reference':ref(OUT/'evidence-index.json')['path'],
 'evidence_index_sha256':sha(OUT/'evidence-index.json'),
 'signed_at':datetime.now(timezone.utc).isoformat()}
result['receipt_hash']='sha256:'+hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
target=OUT.with_suffix('.json');target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
check=read(target);assert check.pop('receipt_hash')=='sha256:'+hashlib.sha256(json.dumps(check,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
for item in index['files']:assert sha(ROOT/item['path'])==item['sha256']
print(json.dumps({'path':str(target),'sha256':sha(target),'receipt_hash':result['receipt_hash'],'accepted_gate':'W14-G01','stage_accepted':False}))
