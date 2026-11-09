"""Archive only independent review evidence and write the final source verdict."""
from pathlib import Path
import datetime,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'run-01'
MAIN=Path('D:/作品集/ResearchOS/research-os')
CANDIDATE=MAIN/'.local/worktrees/coding-delivery-binding-20261104'
RECEIPT=MAIN/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding'
DEST=RECEIPT/'reviews/independent-qa-01'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
pins=json.loads((ROOT/'FINAL-PINS.json').read_bytes())
summary=json.loads((RUN/'result.json').read_bytes())
assert summary['status']=='FOUNDATION_QA_PASSED_NOT_PRODUCT_ACCEPTANCE' and summary['frozen_source_unchanged']
assert all(sha(CANDIDATE/name)==digest for name,digest in pins['source_sha256'].items())
assert all(item['exit_code']==0 and item['source_unchanged'] for item in summary['results'])
assert all(item['run_pass_rosters_equal'] and not item['failed'] and not item['skipped'] and item['package_terminal_pass'] for item in summary['results'] if item['name'].endswith('tests'))
DEST.mkdir(parents=True,exist_ok=False)
evidence={}
for path in sorted(RUN.rglob('*')):
 relative=path.relative_to(RUN)
 if not path.is_file() or 'private' in relative.parts:continue
 target=DEST/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
 assert sha(path)==sha(target)
 evidence[str(relative).replace('\\','/')]={'sha256':sha(target),'bytes':target.stat().st_size}
shutil.copyfile(Path(__file__),DEST/'review-finalizer.py.txt')
initial=json.loads((ROOT/'initial-blocker-review.json').read_bytes())
diagnostics=initial['diagnostics']+[
 {'raw_chunk_id':'f37451','outer_exit_code':0,'classification':'CHILD_READ_ONLY_EXPECTED_HASH_LITERAL_TYPO_NOT_SOURCE_DRIFT','message':'Child initially displayed test match=false because its hand-typed expected literal had an extra ae. The actual frozen test SHA was correct and matches the Root-provided full pin. No source drift, test or DB operation occurred.'}
]
author_evidence={}
for attempt in ('attempt-01','attempt-02','attempt-03','attempt-04','attempt-05','attempt-06'):
 folder=RECEIPT/'author'/attempt
 if not folder.is_dir():continue
 files={}
 for path in sorted(folder.glob('*.result.json')):
  files[path.name]={'sha256':sha(path),'result':json.loads(path.read_bytes())}
 author_evidence[attempt]=files
author04vet=RECEIPT/'author/attempt-04/vet.result.json'
assert not author04vet.exists(),'Do not silently rewrite historical author04 UNKNOWN'
scope=RECEIPT/'scope.json'
report={
 'schema':'researchos.production-binding-foundation-independent-review.v1',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'/root/implementation_review',
 'static_subreviewer':'/root/implementation_review/prompt_flow_review',
 'decision':'APPROVE_FOUNDATION_ONLY_NOT_PRODUCT_ACCEPTANCE',
 'formal_increment':0,
 'base_head':pins['base_head'],
 'worktree':str(CANDIDATE),
 'scope_sha256':sha(scope),
 'source_sha256':pins['source_sha256'],
 'final_author_source_manifest_sha256':sha(RECEIPT/'author/attempt-06/source-manifest.json'),
 'source_freeze_verified_before_and_after_independent_QA':True,
 'candidate_git_readback':{'raw_chunk_id':'a0089d','head':'b84b065739d64a61407ca815651880b6c06ae36a','tracked_changes':0,'untracked_exactly_four_source_paths':list(pins['source_sha256']),'optional_locks':0,'gc_auto':0,'maintenance_auto':False,'qualification':'Candidate status only; Root integrator independently guards the old protected Main changes and control-state baseline.'},
 'findings':[],
 'resolved_findings':[
  {'id':'PDB-001','status':'CLOSED_IN_EXACT_FINAL_PINS','evidence':'store:223-265 and fresh SQLite positive/negative evidence. Public Task has no origin/candidate extra fields. Goal, Task and NoProgressRecord validate through real service-loaded Contracts. Same-project NPR id/project/origin/candidate/input_hash and recomputed unchanged legacy key match binding.NoProgressRef/NoProgressInputKey; Goal problem/task rosters match. Nonzero failure/progress counters remain byte-identical after insert/read.'},
  {'id':'PDB-002','status':'CLOSED_IN_EXACT_FINAL_PINS','evidence':'store:172-214 and independent required-command cases. Mandatory identity is command_key with required=true/kind=DETERMINISTIC; check_id is a unique independent label. Wrong commands under old matching labels and duplicate mandatory commands (even optional duplicates) are refused; correct commands under other valid labels pass.'}
 ],
 'verified_foundation_properties':[
  'Closed44-field private DTO with exact names/UTF8/nonempty/hash checks, distinct Task/Goal contract digests, canonical same-byte decoding and existing Marshal->JCS->Digest domain.Hash compatibility. Creation writer/session snapshots retain all positive int64 values as canonical decimal strings, not invented current lease/Run authorization.',
  'Stable original-origin anchor includes original problem anchor, original requirement/business-input content hashes and stable suite semantic ref/hash; excludes project/Owner/root/new Goal/Task/approval/command and storage ref-vector provenance. Changed original causal dimensions alter the anchor; permission/storage renaming does not.',
  'Dedicated immutable table has PK(project,task), unique(project,goal) and DB-wide qualified approval/lineage-anchor claims. Required JSON types avoid CHECK(NULL), closed names reject duplicates/unknown fields, row/body identities are checked, REPLACE/IGNORE/UPSERT cannot silently replace existing claims even with recursive triggers off; UPDATE/DELETE/no-op are rejected.',
  'Schema validation checks FK enabled, exact dedicated table/index/index-columns/trigger/FK fingerprint and current FK violations. Missing capability fails closed without initializing target schema. Tx helpers perform reads/one insert only, no external effects, auto commit or target DB open.',
  'Catalog is the actual explicit trusted Service.Contracts dependency. Existing LoadContracts plus normal persistenceSchemaName and Validate routing are preserved. Nil/empty/absent primary or selected current schemas fail closed; no direct weak base validation or alternate schema fallback.',
  'Readback verifies canonical body/hash, identity columns, full explicit expected binding context and canonical Goal/Task/NPR relations. Standalone restored binding inventory requires the complete exact expected key set; it is not production backup integration.'
 ],
 'independent_QA':{
  'root':str(DEST),
  'original_frozen_tests':summary['results'][0],
  'additional_overlay_tests':summary['results'][1],
  'additional_test_source_sha256':sha(RUN/'independent_relationship_test.go.txt'),
  'source_mutations':0,
  'actual_run_and_pass_rosters_equal':True,
  'input_ref':str(DEST/'inputs.json'),
  'archive_sha256':evidence,
  'isolation':'Locked tool hashes verified, GOPROXY/GOSUMDB/GOENV/telemetry off, no CGO; private C cache/profile/temp/module copies. Existing D dependency cache read only. Fresh C t.TempDir SQLite databases only; no Core/Desktop/native/model/provider or old DB.',
  'new_QA_failures':[]
 },
 'independent_vet':{'exit_code':0,'ref':str(DEST/'independent-vet.result.json'),'sha256':sha(DEST/'independent-vet.result.json'),'command_ref':str(DEST/'independent-vet.command.json'),'stdout_ref':str(DEST/'independent-vet.stdout.txt'),'stderr_ref':str(DEST/'independent-vet.stderr.txt'),'source_unchanged':True},
 'historical_author_evidence_preserved':author_evidence,
 'author_attempt04_vet':{'status':'UNKNOWN_PRESERVED','result_missing':True,'reason':'No retained terminal result exists. This independent fresh vet0 and author06 vet0 are separate checks, not replacements for or invented completion of attempt04.'},
 'old_initial_blocker_report':{'path':str(RECEIPT/'reviews/relationship-and-command-blockers-01.json'),'sha256':sha(RECEIPT/'reviews/relationship-and-command-blockers-01.json'),'status':'REQUIRES_CHANGES_HISTORICAL_RETAINED'},
 'limits_not_promoted_to_acceptance':[
  'Foundation source only; no registered caller, trusted Host producer/private plan, authoritative original-origin derivation, current Owner/root/Host/TaskRun/lease checks, approval journal/UNKNOWN settlement or cross-DB lineage proof.',
  'The *Contracts object is a trusted constructor dependency, not a self-authenticating capability. A future caller must pass the exact owning Service.Contracts; request/env-provided catalogs are not authorized by this source.',
  'Qualified uniqueness applies to supplied values within this DB. Missing rows/rollback/new DBs do not refund consumed or UNKNOWN native approvals and do not prove a business intent is new.',
  'Required command identities are structurally frozen, not registered or runtime-qualified here. Schema-valid nonnil rubric_ref/qualification_id can still make existing acceptance dispatch leave a required check NOT_RUN/BLOCKED; this source neither makes it executable nor turns that into PASS. Future actual producer/checker adoption must enforce its intended execution shape.',
  'Production schema adoption/numbered migration/backup inventory/typed restore are not implemented. Existing backupSchema hashes DDL but fixed backupInventory and integrity consumers do not fully cover this binding. No old or real product DB was opened or migrated.',
  'No actual pure-scalar business suite/source sealing/checker registration, canonical Host REPORT/ArtifactUse aggregation, split Task/Goal construction/pending audit or LIVE Goal503 exception is implemented by this scope. SDK sole output is unchanged.',
  'No Task/Goal/business acceptance, current Workspace correctness or formal22-parent/42-case completion is established.'
 ],
 'diagnostics':diagnostics,
 'operations':{'four_source_writes':0,'target_schema_installations_outside_fresh_fixtures':0,'old_database_connections':0,'native_model_provider_calls':0,'registry_control_state_writes':0,'counter_reset':False,'formal_increment':0},
 'evidence_chunks':['cd1b84','db6e45','2e787f','425b6d','a0089d','c446f5']
}
data=(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
c=ROOT/'source-review.json';d=RECEIPT/'reviews/source-review.json'
for path in (c,d):
 with path.open('xb') as stream:stream.write(data)
print(json.dumps({'C':str(c),'D':str(d),'sha256':sha(d),'decision':report['decision'],'independent_vet_exit_code':0},ensure_ascii=False))
