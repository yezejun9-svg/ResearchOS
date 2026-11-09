from pathlib import Path
import datetime, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reviews'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
manifest=ROOT/'evidence/attempt-01/source-manifest.json'
frozen=json.loads(manifest.read_bytes())
source={f['path']:sha(ROOT/f['path']) for f in frozen['files']}
assert all(source[f['path']]==f['sha256'] for f in frozen['files'])
run=OUT/'run-01'
result=json.loads((run/'result.json').read_bytes())
assert result['source_unchanged'] and all(x['exit_code']==0 for x in result['results'])
evidence={str(path.relative_to(OUT)).replace('\\','/'):sha(path) for path in sorted(OUT.rglob('*')) if path.is_file() and 'private' not in path.relative_to(OUT).parts and path.name not in ('source-review.json','finalize-review.py')}
report={
 'schema':'researchos.independent-binding-prototype-review.v1',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'reviewer':'/root/implementation_review',
 'decision':'NO_BLOCKER_FOR_C_ONLY_INTEGRITY_PROTOTYPE; NOT_PRODUCT_INTEGRATION_OR_FORMAL_ACCEPTANCE',
 'scope':'Frozen C-only DDL, strict consumer, copied actual Go canonical helper; no production schema version, migration, D database, Host binding or LIVE gate.',
 'source_manifest_sha256':sha(manifest),
 'author_freeze_report_sha256':sha(ROOT/'evidence/freeze-report.json'),
 'source_sha256':source,
 'root_anchor_policy':{'path':'../contract-design/DECISION_ANCHORS_V1.md','sha256':sha(ROOT.parent/'contract-design/DECISION_ANCHORS_V1.md')},
 'source_unchanged_after_checks':True,
 'findings':[],
 'verified_boundaries':[
  'PRIMARY KEY(project,task_id) and unique(project,goal_id) do not partition authority by principal.',
  'Qualified approval and lineage/business-anchor uniqueness span all projects/principals in one DB. Owner/root is a required snapshot, excluded from the unique causal anchor.',
  'Required SQL JSON types use IS checks; closed 41-key DTO rejects absent/null/duplicate/escaped-equivalent/unknown aliases; row/body identities, hash shapes and distinct Task/Goal contracts are checked.',
  'BEFORE INSERT conflict guard aborts REPLACE, IGNORE and UPSERT independently of recursive_triggers; unconditional UPDATE/DELETE guards include no-op mutations.',
  'Actual copied canonical/jcs.go hash is 7aad384f03ced5d4033145d5bf2953909be72c658642bbfc1b7795fd037f4d8d. The helper performs strict raw validation then json.Marshal -> canonical.JSON -> SHA256; Python only transports the closed DTO.',
  'Creation writer/session snapshots are exact positive decimal strings through MaxInt64, including >2^53. No invented runtime/lease epoch is accepted.',
  'Consumer recomputes canonical body/hash, all row/body identities, and full synthetic expected context. Its result always has authentication/business acceptance false.',
  'Consumer checks FK enforcement/check plus exact schema/table/index/trigger/FK snapshot. Restore checks complete binding inventory and every expected record; missing schema objects, corrupt shape-valid digest, noncanonical bytes and foreign context are refused.',
  'Independent new-PK conflict probes for existing Goal/approval/anchor across recursive_triggers 0/1 and REPLACE/IGNORE/UPSERT abort without modifying old bytes. Disabled-FK orphan and mutable subject relation attacks are refused.'
 ],
 'independent_verification':{
  'root':str(run),'results':result['results'],
  'go_top_level_functions':2,'go_subtests':4,
  'python_tests':23,'author_tests_rerun_with_private_fixture_paths':18,'additional_boundary_tests':5,
  'helper_sha256':result['helper_sha256'],
  'profile_cache_temp':'Own C reviews/run-01/private only; offline Go, pinned Go/Python; no shared author cache mutation.',
  'evidence_sha256':evidence
 },
 'limits_and_required_followup':[
  'The expected context, schema snapshot and issuer/anchor strings are synthetic fixture inputs. SQL success proves neither Owner/root identity nor approved plan, canonical business intent or authority.',
  'A changed claimed issuer or a different DB can still carry the same native approval/lineage. Future Host must derive authoritative qualified values and prove original lineage across DBs; unsupported lineage must fail closed.',
  'Missing binding rows, rollback and empty valid backup inventory do not prove external/native approval is reusable. Original consumed/UNKNOWN journal remains mandatory and unimplemented.',
  'Immutable binding/source prototype is not current Host TaskRun/lease/origin validation, dual-contract creation/pending audit, trusted suite execution, sealed actual source inventory, canonical Host facts, ArtifactUse, Goal aggregation, or current Workspace correctness.',
  'Real production migration numbering/old-DB migration and real backup consumer integration are not assigned or exercised. Fresh fake-subject fixtures cannot certify those consumers.',
  'Integration must obtain trusted immutable expected context/schema values and serialize a consistent validation snapshot through existing Host transaction boundaries; the synthetic Python API is not a product auth gate.',
  'Ordinary LIVE Goal 503 and current permissions remain unchanged. No Task/Goal or formal use-case acceptance is granted.'
 ],
 'diagnostics':[],
 'operations':{'C_fresh_fixture_only':True,'source_writes':0,'D_writes':0,'old_database_connections':0,'native_model_provider_runs':0,'counter_reset':False,'formal_increment':0}
}
target=OUT/'source-review.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,indent=2,ensure_ascii=False);stream.write('\n')
print(json.dumps({'report':str(target),'sha256':sha(target),'decision':report['decision']}))
