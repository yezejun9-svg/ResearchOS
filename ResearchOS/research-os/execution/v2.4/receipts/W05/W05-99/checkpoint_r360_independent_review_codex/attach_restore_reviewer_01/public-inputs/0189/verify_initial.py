from pathlib import Path
import json,hashlib,collections
O=Path(__file__).resolve().parent
B=O.parent.parent
PRE=B/'native_ttl_prelaunch_independent_review_codex/1a11dfd4106-fa062434'
P=B/'integration_codex/native-migration-positive-ttl-root-26c5c890ef5144d4'
C=B/'integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4'
A=B/'integration_codex/native-positive-ttl-root-api-a4a432c97c744d98'
T=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-ttl-c54ba9df088e45ea94adb56457af2979')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
 raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def dump(name,v): (O/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def refs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=set(v):yield v
  for x in v.values():yield from refs(x)
 elif isinstance(v,list):
  for x in v:yield from refs(x)
def canon(v):
 if type(v) is dict:return {k:canon(v[k]) for k in sorted(v,key=lambda x:x.encode('utf-16-be'))}
 if type(v) is list:return [canon(x) for x in v]
 return v
def digest(v):return 'sha256:'+hashlib.sha256(json.dumps(canon(v),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def copy(p,name):
 q=O/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
cfg=read(C/'controller.public.config.json')
pre=read(PRE/'MF.json')
inspection=read(A/'inspection-positive.json')
snapshot=read(C/'controller-runtime/review-snapshot-fixture-retained-7fa2cdeac67644fa8426ac16e2d2edce.json')
before=read(P/'facts/before.rows.json');fixture=read(P/'facts/fixture.public.json')
inv=read(P/'facts/00-rehearsal/invocation.json')
req=read(P/'facts/00-rehearsal.request.json')
checks=[];seen=set()
for category,obj in [('prelaunch-members',pre['members']),('prelaunch-HDF',read(PRE/'HDF.json')),('config',cfg),('snapshot',snapshot),('invocation',inv),('inspection',inspection)]:
 for ref in refs(obj):
  key=(ref['path'].casefold(),ref['sha256'].removeprefix('sha256:'),ref['bytes'])
  if key in seen:continue
  seen.add(key);p=Path(ref['path'])
  if p.suffix.lower() in ('.sqlite','.db') or str(p).lower().endswith(('-wal','-shm')):
   checks.append(dict(category=category,expected=ref,state='HISTORICAL_DATABASE_RECEIPT_ONLY_NOT_READ'));continue
  if not p.is_file():
   checks.append(dict(category=category,expected=ref,state='MISSING_AT_REVIEW'));continue
  actual=pin(p);ok=actual['sha256']==key[1] and actual['bytes']==key[2]
  checks.append(dict(category=category,expected=ref,actual=actual,state='MATCH' if ok else 'DRIFT'))
dump('initial-input-pins.json',checks)
guards={}
for k in ('reader_guard_cleanup','database_guard_cleanup'):
 g=inspection[k]
 guards[k]=dict(entries=len(g['entries']),closed=g['closed'],retained_handles_count=g['retained_handles_count'],verification=g['verification'],failures=[x for x in g['entries'] if not x.get('closed') or not x.get('verified') or not x.get('final_path_match')],errors=g['errors'],share_mode=g['share_mode'])
summary=dict(authority='NONE',formal_acceptance=False,status='AWAIT_FINAL_JOB_CLOSURE',checks=collections.Counter(x['state'] for x in checks),input_count=len(checks),frozen_inputs=len(cfg['FrozenInputs']),prelaunch_member_count=len(pre['members']),db_not_read_by_reviewer=True,typed_table_count=len(inspection['typed_rows']),schema_object_count=inspection['schema_object_count'],typed_rows_recomputed_digest=digest(inspection['typed_rows']),typed_rows_digest_matches=digest(inspection['typed_rows'])==inspection['typed_rows_sha256'],all87_typed_tables_equal_before=inspection['typed_rows']==before,original_invariant_false=[k for k,v in inspection['original_table_invariants'].items() if not v],schema_digest_matches_fixture=inspection['sqlite_schema_sha256']==fixture['schema_sha256'],schema_versions=inspection['schema_versions'],expected_baseline_available=inspection['expected_baseline_available'],expected_state_matches=inspection['expected_state_matches'],guard_summary=guards,backup_environment=req['Environment'],backup_result=inv['Result'],private_input_persisted=inv['PrivateInputPersisted'],mechanical_failures_this_review=0)
dump('initial-verification.json',summary)
for p in sorted(PRE.rglob('*')):
 if p.is_file():copy(p,'inputs/prelaunch/'+p.relative_to(PRE).as_posix())
for p in sorted((P/'facts').rglob('*')):
 if p.is_file():copy(p,'inputs/initial-facts/'+p.relative_to(P/'facts').as_posix())
for name in ('controller.public.config.json','controller-runtime/review-snapshot-fixture-retained-7fa2cdeac67644fa8426ac16e2d2edce.json'):
 copy(C/name,'inputs/controller/'+name)
for name in ('inspection-positive.json','inspection-reader-guards-b12973f6613e4bcbb8b2bf05811f23b8.json','root_public_api_ttl.actual.py'):
 copy(A/name,'inputs/api/'+name)
for key in ('ControllerSource','ObservedOwnedHelper','OriginalOwnedHelper','SourceReadGuard'):
 p=Path(cfg[key]['path']);copy(p,'inputs/sources/'+p.name)
for name in ('native_migration_authority_harness_windows_test.go','backup_prepared_abandonment_upgrade.go'):
 p=T/'internal/domain'/name;copy(p,'inputs/sources/'+name)
print(json.dumps(summary,ensure_ascii=False))

