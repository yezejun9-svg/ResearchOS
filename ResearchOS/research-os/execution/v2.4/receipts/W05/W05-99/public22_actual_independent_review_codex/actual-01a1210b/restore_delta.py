"""Prove the exact observed restore delta, without changing either database."""
import hashlib
import json
from pathlib import Path
import runpy
import sqlite3
N=Path(__file__).resolve().parent
x=runpy.run_path(str(N/'inspect_db.py'),run_name='read_only_definitions')
pin,read,save=x['pin'],x['read'],x['save'];CASE=x['CASE'];B=x['B']
F=B/'host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a/frozen_source'
def digest(rows):return 'sha256:'+hashlib.sha256(json.dumps(rows,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def snapshot(p):
 db=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  db.execute('PRAGMA query_only=ON')
  columns=[r[1] for r in db.execute('PRAGMA table_info(auth_credentials)')]
  rows=list(db.execute('SELECT * FROM auth_credentials ORDER BY token_hash'))
  schema=list(db.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name"))
  return columns,rows,schema
 finally:db.close()
paths=[CASE/'source22/researchos.sqlite',CASE/'verified22/state.sqlite',CASE/'backup22/manifest.json',CASE/'verified22/restore-report.json',CASE/'raw/backup22.stdout',CASE/'raw/verify22.stdout',N/'database-inspection.json',F/'internal/domain/backup_recovery.go',F/'internal/domain/backup.go',F/'internal/domain/contracts.go',F/'internal/canonical/jcs.go',Path(__file__)]
refs=[pin(p) for p in paths];guard=x['module'](x['G']).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
try:
 c1,r1,s1=snapshot(paths[0]);c2,r2,s2=snapshot(paths[1]);idx=c1.index('revoked')
 nonrevoked=lambda row:tuple(v for i,v in enumerate(row) if i!=idx)
 credentials=dict(columns=c1,row_counts=[len(r1),len(r2)],same_column_layout=c1==c2,all_non_revoked_columns_equal=[nonrevoked(r) for r in r1]==[nonrevoked(r) for r in r2],source_revoked_values=[r[idx] for r in r1],restored_revoked_values=[r[idx] for r in r2],raw_credential_values_emitted=False)
 inspection=read(paths[6]);delta=inspection['schema_delta'];recovery=paths[7].read_text(encoding='utf-8')
 start=recovery.index('CREATE TRIGGER IF NOT EXISTS backup_require_fresh_observation');end=recovery.index(' END;',start)+len(' END;')
 expected=recovery[start:end].replace('CREATE TRIGGER IF NOT EXISTS','CREATE TRIGGER').removesuffix(';')
 actual=delta[0]['after'][3] if len(delta)==1 else None
 schema_exact= len(delta)==1 and delta[0]['key']==['trigger','backup_require_fresh_observation'] and delta[0]['before'] is None and actual==expected
 without_trigger=[r for r in s2 if not (r[0]=='trigger' and r[1]=='backup_require_fresh_observation')]
 manifest=read(paths[2]);report=read(paths[3])
 checks=dict(credential_only_revoked_changes=credentials['same_column_layout'] and credentials['all_non_revoked_columns_equal'] and credentials['source_revoked_values']==[0] and credentials['restored_revoked_values']==[1],exact_frozen_restore_trigger=schema_exact,full_schema_except_exact_restore_trigger_equal=s1==without_trigger,backup_stdout_equals_manifest=read(paths[4])==manifest,restore_stdout_equals_report=read(paths[5])==report,backup_id_matches=report['backup_id']==manifest['id'],public_before_after_inventory_matches=report['before']==report['after']==manifest['inventory'],public_ledger_exact22=manifest['migrations']==list(range(1,23)),manifest_schema_hash_matches_independent_full_source_schema=digest(s1)==manifest['schema_hash'],all_82_other_table_rows_and_counts_equal=len(inspection['table_delta'])==1 and inspection['table_delta'][0]['table']=='auth_credentials' and len(inspection['source']['tables'])==83,restored_owner1_unchanged=inspection['source']['tables']['auth_principals']==inspection['restored']['tables']['auth_principals'] and inspection['restored']['tables']['auth_principals']['count']==1)
 for r in refs:assert pin(r['path'])==r
finally:closed=guard.close()
assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
gr=save('restore-delta.guard.closed.json',closed)
out=save('restore-delta-proof.json',dict(scope='READ_ONLY_EXISTING_PUBLIC22',checks=checks,credential_delta=credentials,exact_trigger_sql=expected,source_full_schema_hash=digest(s1),restored_full_schema_hash=digest(s2),restored_without_exact_trigger_schema_hash=digest(without_trigger),manifest_schema_hash=manifest['schema_hash'],source_refs=refs,source_guard_ref=gr,product_executions=0,private_key_or_owner_file_read=False,formal_acceptance=False))
print(json.dumps(dict(report=out,checks=checks,credential_delta=credentials,hashes=dict(source=digest(s1),restored=digest(s2),without_exact_trigger=digest(without_trigger),manifest=manifest['schema_hash'])),ensure_ascii=False),flush=True)
