"""Write an independent scoped construction acceptance; no product mutation."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE=ROOT/'execution/receipts/W11'/OUT.name
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p)}
audit=read(OUT/'audit-report.json')
assert audit['status']=='PASS' and audit['manifest_files_verified']==252
assert len(read(OUT/'negative-and-continuity.json'))==6
receipt=read(BASE/'receipt.json')
bases={
 'A08-01':'Public independent objective labeler and source-family review, unchanged frozen generator/rubric/development hashes, installed source/binary binding and authenticated completed protected service summary establish the original frozen sequence. Formal private labels were not read or independently recomputed by this reviewer.',
 'A08-02':'Each exact evidence-validity / language / typesafe / jev-1.13.0 / objective-source-records-v1 key has 30 development and15 holdout, below60+30. Both actual persisted product qualifications are FAILED/ADVISORY. Aggregate counts grant no key automatic authority.',
 'A08-03':'Derived per-key FA/negative-label=0/8, nonabstained coverage6/15 and7/15, accept coverage1/15 and2/15; actual automatic action coverage0. Abstentions9/15 and8/15 retained, no low-confidence promotion; latency sum30753ms and costUNKNOWN disclosed. No improvement claim over16/30 always-reject baseline.',
 'A08-04':'60 original development calls plus30 service-attested protected holdout calls complete the initial evaluation. Two independent actual product acceptance receipts and result writes are hash-bound and persisted. A08 explicitly permits a complete negative evaluation with safe downgrade; qualification failure remainsFAILED/ADVISORY/NONE.',
 'A08-05':'Prior accepted C07/C08 deterministic failure/version/missing-evidence counterexamples retained in FIXTURE scope. Current actual product verifier differs from both input registrars, checks exact frozen subject/input/contract/policy bindings and immutable public-summary hashes; JCS hashes independently recomputed. Model confidence grants no real-world success or final authority.',
 'A08-06':'Native installed service has distinct OS identity;16 canary assertions and8 actual formal-object read/write handle attempts deny access. Actual formal artifact isVERIFIER_ONLY; ordinary OWNER direct/content/list/search/events/context paths disclose no private body, restrictedVERIFIER content returns503. Concrete FrozenProvider.Read always refuses bytes; fixed validated aggregate is the only declassified product output. Prior synthetic recursive-classification and fail-closed content/materialization/backup source evidence is retained in its original scope; no live backup/export/restart claim.'}
notes={
 'status':'PASS_IN_SCOPE','reviewer':'codex:/root/workbench_verifier',
 'assertion_review':[{'id':k,'verdict':'PASS','basis':v} for k,v in bases.items()],
 'runner_review':[
  'Inspected safe_path allowlist and resolve containment; repeated pin/read always hashes bytes before returning already-indexed data. Mock byte replacement and four disallowed paths independently rejected.',
  'Four dispatcher selections bind W11-G02,G03,G04,A08 and240 unique checks each; repeated selections are replayed admission checks, not960 separate live measurements.',
  'Original modes retained: G02/G03/A08 LIVE_SERVICE; G04 and earlier C07/C08 FIXTURE, supplemented by real native OS and HTTP access observations.',
  'Current frozen service source inventory equals its original f0f88cb bytes. Product affected qualification/protectedstore/API paths have no changes between591d16e andd6acd16.',
  'Product executable reports591d16e with vcs.modified=true; its recorded process and binary hashes are retained. No claim of a clean build provenance is substituted for the actual source/binary evidence.'
 ],
 'time_semantics':[
  'A08 run interval13:12:25.4730389Z to13:23:23.5130455Z means original protected freeze marker through last product AcceptanceReceipt creation.',
  'Earlier60-development evidence and later native formal-object check at13:27:47.7081773Z are separately timestamped supplemental evidence; the native reviewer report completed13:29:09.318076Z.',
  'admission_verified_at and current independent review are subsequent read-only verification, never substituted for provider execution time.',
  'Public frozen_at is a durable run marker; freeze-before-first-request order is established by reviewed create/fsync implementation, not independently observed private per-call timestamps.'
 ],
 'source_read_review':[
  'frozen_engine_windows.go persists full batch and batch-commit hash before any request, stores intent before each call and terminal summary afterward; completed aggregate does not reread every private batch on each public query.',
  'frozen_provider_windows.go exports descriptors/public aggregate only; Read returns ErrIsolation. Qualification registration uses exact descriptor metadata and trusted service attestation rather than reading private bodies.',
  'qualification_live.go reauthenticates independent verifier, binds exact qualification/input hashes, recomputes checks, stores public fixed aggregate and failed result; public content handler uses no-store/sandbox/attachment after authorization, and protected formal bytes remain unexportable.',
  'Earlier PROTECTED-MATERIALIZE-REFUSED, recursive protected classification, PUBLIC role deny and protected backup refusal are fixture/source evidence. They are not relabeled actual live context/export tests.'
 ],
 'open_findings':[], 'new_provider_calls':0,'service_operations':[],'private_body_or_labels_read':False,
 'reviewed_at':datetime.now(timezone.utc).isoformat()}
(OUT/'assertion-review.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
index={'files':[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='evidence-index.json']}
(OUT/'evidence-index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
prior=ROOT/'execution/verifier/W11/8a5ca295-69c0-4ebd-9ae3-8a8e266bc942.json'
result={
 'artifact_kind':'INDEPENDENT_LIMITED_CONSTRUCTION_ACCEPTANCE_WITH_OWNED_CASE_VERDICTS',
 'task_id':'W11','run_id':OUT.name,'project_id':receipt['project_id'],
 'status':'PARTIAL_ACCEPTANCE','verdict':'PASS_IN_SCOPE','stage_accepted':False,'whole_W11_accepted':False,
 'scope':'A08 six frozen assertions andW11-G02/G03/G04 accepted on original live evidence plus scoped fixture/native/source evidence. PriorC07/C08/G01 preserved. OverallW11 dependency acceptance and cross-system gates are not signed.',
 'executor_identity':'codex:/root','verifier_identity':'codex:/root/workbench_verifier',
 'independence_basis':'This verifier authored no W11 implementation, label generator, live run or product acceptance actions. Independently reviewed original signed source/native/product evidence, rehashed252 manifest files and278 source files, recomputed240 public-only admission checks, audited complete frozen assertion mapping and product receipt JCS hashes. No new provider/service/private-body access.',
 'executed_code_revision':receipt['code_revision'],
 'original_frozen_service_source_revision':'f0f88cb6bd65120ccb354ec92fdedf45bde25dc1',
 'original_product_source_revision':'591d16e277dd7e3f26809f2bffa7fb142a398609',
 'executor_receipt_reference':str((BASE/'receipt.json').relative_to(ROOT)).replace('\\','/'),
 'executor_receipt_sha256':sha(BASE/'receipt.json'),'executor_receipt_jcs_hash':receipt['receipt_hash'],
 'artifact_manifest_reference':str((BASE/'artifacts.json').relative_to(ROOT)).replace('\\','/'),
 'artifact_manifest_sha256':sha(BASE/'artifacts.json'),'artifact_count_verified':252,
 'acceptance_baseline_reference':'spec/v2.0/contracts/acceptance.json',
 'acceptance_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/acceptance.json'),
 'task_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/tasks.json'),
 'task_gates':[
  {'check_id':'W11-G02','verdict':'PASS','mode':'LIVE_SERVICE','basis':bases['A08-01']+' '+bases['A08-04']},
  {'check_id':'W11-G03','verdict':'PASS','mode':'LIVE_SERVICE','basis':bases['A08-02']+' '+bases['A08-03']},
  {'check_id':'W11-G04','verdict':'PASS','mode':'FIXTURE','actual_runtime_scope':'FIXTURE_AND_SOURCE_WITH_ACTUAL_NATIVE_FORMAL_OBJECT_AND_HTTP_DENIALS','basis':bases['A08-06']}
 ],
 'owned_case_verdicts':[{'case_id':'A08','verdict':'PASS','mode':'LIVE_SERVICE',
  'actual_runtime_scope':'ORIGINAL_COMPLETED_PROTECTED_LIVE_EVALUATION_AND_PRODUCT_ACCEPTANCE_ADMITTED_READ_ONLY',
  'assertion_ids':list(bases),'assertion_verdicts':{k:'PASS' for k in bases},'all_frozen_assertions_covered':True,
  'expected_actual_status_reference':str((BASE/'A08.json').relative_to(ROOT)).replace('\\','/'),
  'executor_global_evidence_sha256':sha(BASE/'A08.json'),'basis':'; '.join(bases.values())}],
 'preserved_prior_acceptance':{'reference':ref(prior),'case_ids':['C07','C08'],'gate_ids':['W11-G01'],'mode':'FIXTURE','reissued':False},
 'qualification_state':{'per_key_development':30,'per_key_holdout':15,'sample_gate':'INSUFFICIENT','qualification':'FAILED','maximum_mode':'ADVISORY','automatic_authority':'NONE','actual_automatic_action_coverage':0,'overall_correct':13,'overall_abstain':17,'overall_holdout':30,'cost_status':'UNKNOWN','improvement_claim':False},
 'product_receipt_hashes':audit['product_acceptance_jcs_hashes'],
 'original_live_interval':audit['original_live_interval'],
 'supplemental_native_boundary_checked_at':audit['supplemental_native_boundary_checked_at'],
 'limits':[
  'This signature accepts completed A08 and specified gates, not model automatic qualification or overall project release.',
  'Original60-development and30-holdout calls are generated objective source-record tasks, including translation-paired groups; zero independent empirical sources. No general research accuracy claim.',
  'Formal private inputs, labels and per-call results were never inspected by this reviewer. Trusted original source/binary/service chain and opaque dataset hash support execution; private item-level recomputation is not claimed.',
  'Detailed formal bodies cannot be exported through the concrete service provider. Actual file/HTTP deny observations and earlier source/fixture boundary checks do not completeC22 backup/export/cache/process/restart acceptance.',
  'Full W11 upstreamW09/W10 dependency readiness, W05 live runtime, C20 cross-system and whole-release gates remain separate.',
  'All historical negative runs and reviewer harness corrections remain preserved. Original live, product, supplemental native and subsequent admission times retain distinct meanings.',
  'No new provider calls, service restart/configuration, browser run, full build, private data read or product mutation occurred in this review.'
 ],
 'open_findings':[], 'open_blockers':['Overall W11 dependencies and other cross-system gates are outside this limited acceptance; no automatic stage promotion.'],
 'resource_request_ids':['RQ-W05-CLI-POLICY-001'],
 'independent_review_references':[ref(OUT/'audit-report.json'),ref(OUT/'assertion-review.json'),ref(OUT/'negative-and-continuity.json')],
 'evidence_index_reference':str((OUT/'evidence-index.json').relative_to(ROOT)).replace('\\','/'),
 'evidence_index_sha256':sha(OUT/'evidence-index.json'),
 'signed_at':datetime.now(timezone.utc).isoformat()}
result['receipt_hash']='sha256:'+hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
target=OUT.with_suffix('.json')
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'path':str(target),'sha256':sha(target),'receipt_hash':result['receipt_hash'],'gates':['W11-G02','W11-G03','W11-G04'],'cases':['A08'],'stage_accepted':False}))
