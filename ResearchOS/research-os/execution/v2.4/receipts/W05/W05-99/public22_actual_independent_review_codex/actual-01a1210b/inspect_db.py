"""Existing case only, immutable read-only SQLite; no key or credential reads."""
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import types
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
CASE=B/'integration_codex/schema22-public-89c0459006654891bf3c540af6b525aa'
CALLER=CASE.parent/'schema22-public-caller-89c0459006654891bf3c540af6b525aa'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def module(p):
 m=types.ModuleType('db_review_guard');m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def observation(p):
 for suffix in ('-wal','-shm','-journal'):
  q=Path(str(p)+suffix);assert not q.exists() or q.stat().st_size==0
 db=sqlite3.connect(p.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  db.execute('PRAGMA query_only=ON')
  schemas=list(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))
  names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
  tables={}
  for name in names:
   q='"'+name.replace('"','""')+'"';rows=db.execute('SELECT * FROM '+q)
   encoded=[]
   for row in rows:
    row=[{'blob_base64':base64.b64encode(v).decode('ascii')} if isinstance(v,bytes) else v for v in row]
    encoded.append(json.dumps(row,ensure_ascii=False,separators=(',',':')))
   tables[name]=dict(count=len(encoded),rows_sha256=hashlib.sha256('\n'.join(sorted(encoded)).encode()).hexdigest())
  return dict(database_ref=pin(p),versions=[r[0] for r in db.execute('SELECT version FROM schema_migrations ORDER BY version')],schema_sha256=hashlib.sha256(json.dumps(schemas,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),schema_rows=schemas,tables=tables,integrity=[r[0] for r in db.execute('PRAGMA integrity_check')],foreign_key_violations=len(list(db.execute('PRAGMA foreign_key_check'))),sqlite_runtime=sqlite3.sqlite_version,query_only=db.execute('PRAGMA query_only').fetchone()[0],raw_rows_emitted=False)
 finally:db.close()
def main():
 paths=[CASE/'source22/researchos.sqlite',CASE/'verified22/state.sqlite',CASE/'backup22/manifest.json',CASE/'verified22/restore-report.json',CALLER/'runner-returned-state.root.json',G,Path(__file__)]
 refs=[pin(p) for p in paths];guard=module(G).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
 try:
  a,b=[observation(p) for p in paths[:2]];state=read(paths[4])
  schema_a={(r[0],r[1]):r for r in a['schema_rows']};schema_b={(r[0],r[1]):r for r in b['schema_rows']}
  schema_delta=[dict(key=k,before=schema_a.get(k),after=schema_b.get(k)) for k in sorted(set(schema_a)|set(schema_b)) if schema_a.get(k)!=schema_b.get(k)]
  table_delta=[dict(table=k,before=a['tables'].get(k),after=b['tables'].get(k)) for k in sorted(set(a['tables'])|set(b['tables'])) if a['tables'].get(k)!=b['tables'].get(k)]
  own_matches={name:all(ob[k]==state['observations'][name][k] for k in ('database_ref','versions','schema_sha256','tables','integrity','foreign_key_violations')) for name,ob in [('sealed22',a),('verify22',b)]}
  assert all(own_matches.values())
  assert all(pin(r['path'])==r for r in refs)
 finally:closed=guard.close()
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 gr=save('database-inspection.guard.closed.json',closed)
 out=save('database-inspection.json',dict(mode='EXISTING_SQLITE_URI_RO_IMMUTABLE_QUERY_ONLY',source=a,restored=b,schema_delta=schema_delta,table_delta=table_delta,exact_leaf_observation_reproduced=own_matches,input_refs=refs,source_guard_ref=gr,key_or_credential_files_read=False))
 print(json.dumps(dict(report=out,source_schema=a['schema_sha256'],restored_schema=b['schema_sha256'],source_tables=len(a['tables']),restored_tables=len(b['tables']),schema_delta=schema_delta,table_delta=table_delta,exact_leaf_observation_reproduced=own_matches),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
