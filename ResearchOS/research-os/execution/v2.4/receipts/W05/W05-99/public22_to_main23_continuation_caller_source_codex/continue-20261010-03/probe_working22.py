"""One isolated readonly difference probe of original1201 working copy only."""
from pathlib import Path
import base64, hashlib, json, sqlite3
O=Path(__file__).resolve().parent
B=O.parent/'continue-20261010-02'
W=O.parents[1]
C=W/'integration_codex/public22-continuation-fe9482816efe4843ba728962d99ee06c/case.closed.json'
def digest(b):return hashlib.sha256(b).hexdigest()
def pin(p):
    b=Path(p).read_bytes();return dict(path=str(p),sha256=digest(b),bytes=len(b))
def checked(r):
    assert pin(Path(r['path']))==r
    return json.loads(Path(r['path']).read_bytes())
def encode(v):return {'blob_base64':base64.b64encode(v).decode('ascii')} if isinstance(v,bytes) else v
def rows_digest(rows):return digest('\n'.join(sorted(json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in rows)).encode())
assert pin(C)['sha256']=='b663b3b63259da289805e01d948887777ff36bcefd8cdf7bcc174fd496aacb6c'
closed=json.loads(C.read_bytes());assert closed['phase']=='prepare' and closed['calls']==[] and closed['new_native_children_attempted']==0
working=closed['working_copy_before_ref'];p=Path(working['path'])
assert p.parent==C.parent/'working22' and pin(p)==working
assert all(not Path(str(p)+x).exists() or Path(str(p)+x).stat().st_size==0 for x in ['-wal','-shm','-journal'])
i=json.loads((B/'source-inputs.json').read_bytes());retained=checked(i['evidence']['returned_state_ref'])['observations']['sealed22'];manifest=checked(i['evidence']['backup_manifest_ref'])
con=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
try:
    con.execute('PRAGMA query_only=ON')
    schema=[list(x) for x in con.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name")]
    tables={}
    for (name,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        rows=[[encode(v) for v in r] for r in con.execute('SELECT * FROM "'+name.replace('"','""')+'"')]
        tables[name]=dict(count=len(rows),rows_sha256=rows_digest(rows))
        del rows
finally:con.close()
assert pin(p)==working
actual_schema=digest(json.dumps(schema,ensure_ascii=False,separators=(',',':')).encode())
legacy_rows=[r for r in schema if not r[1].startswith('sqlite_')]
differences={k:dict(retained=retained['tables'].get(k),observed=tables.get(k)) for k in sorted(set(tables)|set(retained['tables'])) if tables.get(k)!=retained['tables'].get(k)}
result=dict(schema='researchos.public22-copy-schema-difference-probe.v1',original_ordinal=1201,
    case_closed_ref=pin(C),working_copy_ref=working,retained_state_ref=i['evidence']['returned_state_ref'],backup_manifest_ref=i['evidence']['backup_manifest_ref'],
    retained_observation_keys=list(retained),current_table_keys=list(tables),table_count=len(tables),table_differences=differences,
    retained_schema_sha256=retained['schema_sha256'],current_schema_sha256=actual_schema,
    manifest_schema_hash=manifest['schema_hash'],manifest_current_equal=manifest['schema_hash']=='sha256:'+actual_schema,
    legacy_exclude_sqlite_compact_sha256=digest(json.dumps(legacy_rows,ensure_ascii=False,separators=(',',':')).encode()),
    legacy_exclude_sqlite_default_sha256=digest(json.dumps(legacy_rows,ensure_ascii=False,sort_keys=True).encode()),
    schema_row_count=len(schema),sqlite_internal_rows=[r[:3] for r in schema if r[1].startswith('sqlite_')],
    working_bytes_unchanged=True,original_source_db_opened=False,private_key_accessed=False,raw_rows_emitted=False,
    SQL_write_statements=0,SQL_integrity_or_foreign_key_checks_replayed=0,Native_calls=0,Root_stages_run=0,MainCanonScope_writes=0,
    sqlite_connection_closed=True,formal_acceptance=False)
with (O/'working22-difference-probe.json').open('xb') as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({k:v for k,v in result.items() if k not in ['current_table_keys','sqlite_internal_rows']},ensure_ascii=False))
