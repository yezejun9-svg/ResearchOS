import pathlib,json,hashlib
N=pathlib.Path(__file__).parent
data=json.loads((N/'source-input.json').read_text(encoding='utf-8'))
T=pathlib.Path(data['t6'])
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(p,ref):
 got=pin(p);assert got['sha256']==ref['sha256'] and got['bytes']==ref['bytes'],str(p);return got
def js(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')
refs=[]
for name in data['files']:
 p=T/name;refs.append(pin(p))
for name in data['publicDriver']:refs.append(pin(pathlib.Path(name)))
A=pathlib.Path(data['att3'])
for name in ['HDF','MF']:refs.append(verify(A/(name+'.json'),data['ATT3'+name]))
for name,ref in json.loads((A/'MF.json').read_text(encoding='utf-8'))['members'].items():refs.append(verify(A/name,ref))
js('sourceguard.initial.json',{'scope':'all explicitly declared T6/public-driver/ATT3 inputs; excludes mutable Root canonical work','refs':refs})
# Evidence copies preserve exact bytes. No candidate, SQL connection or native runtime is created.
for name in data['files']:
 p=N/'frozen-inputs/T6'/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((T/name).read_bytes())
for name in data['publicDriver']:
 p=N/'frozen-inputs/modernc-sqlite-v1.60.1'/pathlib.Path(name).name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(pathlib.Path(name).read_bytes())
session=(T/'internal/domain/client_session_fence.go').read_text(encoding='utf-8')
backup=(T/'internal/domain/backup_recovery.go').read_text(encoding='utf-8')
runtime=(T/'internal/domain/runtime.go').read_text(encoding='utf-8')
guard=(T/'internal/domain/backup_migration.go').read_text(encoding='utf-8')
store=(T/'internal/domain/store.go').read_text(encoding='utf-8')
checks={
'epoch_column_declared_INTEGER':'epoch INTEGER NOT NULL CHECK(epoch>0)' in (T/'migrations/sqlite/0005_runtime.sql').read_text(),
'session_trigger_missing_observation_epoch_binding':"AND o.epoch=" not in session and "o.observed_at >" in session,
'backup_epoch_comparison_uses_json_extract':"json_extract(NEW.body,'$.lease_epoch')>json_extract(OLD.body,'$.lease_epoch')" in backup,
'backup_time_text_comparison':"o.observed_at>b.restored_at" in backup,
'latest_observation_text_order':"ORDER BY observed_at DESC LIMIT 1" in runtime,
'startup_guard_precedes_install':store.index('CheckMigrationSafety(db, files)')<store.index('installClientSessionFence(context.Background(), tx, false)'),
'expected_template_calls_shared_installer':'installClientSessionFence(context.Background(), expected, false)' in guard,
'guard_includes_raw_trigger_sql':"SELECT type,name,tbl_name,sql FROM sqlite_master WHERE tbl_name IN ('client_sessions','backup_restore_barriers')" in guard,
'guard_requires_schema_hash_equality':'if Hash(got) != Hash(want)' in guard,
'old_trigger_kept_by_if_not_exists':'CREATE TRIGGER IF NOT EXISTS client_session_require_fresh' in session}
assert all(checks.values()),checks
js('static-blocker-evidence.json',{'checks':checks,'meaning':'source-level findings only; no SQLite/Go execution and no observed runtime failure inferred','source_candidate_created':False})
print(json.dumps({'status':'BLOCKER_EVIDENCE_PREPARED_NOT_SEALED','input_refs':len(refs),'checks':checks}))

