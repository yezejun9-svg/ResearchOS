import collections,datetime,hashlib,json,sqlite3,struct,sys
from pathlib import Path
E=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def q(s):return '"'+s.replace('"','""')+'"'
def digestrow(row):
 out=bytearray()
 for v in row:
  if v is None:t,b=b'N',b''
  elif isinstance(v,int):t,b=b'I',str(v).encode()
  elif isinstance(v,float):t,b=b'F',struct.pack('>d',v)
  elif isinstance(v,str):t,b=b'T',v.encode()
  elif isinstance(v,bytes):t,b=b'B',v
  else:raise TypeError(type(v).__name__)
  out.extend(t+struct.pack('>Q',len(b))+b)
 return sha(out)
assert len(sys.argv)==2
sp=Path(sys.argv[1]).resolve();assert sp.parent==E/'controller'
s=load(sp);assert s['phase']=='fixture-retained' and s['case']=='missing-native-channel'
f=load(Path(s['fixture_public_ref']['path']));db=Path(f['database']).resolve();assert db.is_relative_to((R/'.local/native25-cases-20261014/missing-native-channel-04/temp').resolve())
before=load(E/'harness/before.rows.json');reh=load(E/'harness/rehearsal.public.json')
c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
try:
 actual={}
 for (table,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
  cur=c.execute('SELECT * FROM '+q(table));cols=[x[0] for x in cur.description];actual[table]={'columns':cols,'row_digests':sorted(digestrow(row) for row in cur)}
 schema=sha(json.dumps(c.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name").fetchall(),ensure_ascii=False,separators=(',',':')).encode())
 version=c.execute('SELECT max(version) FROM schema_migrations').fetchone()[0]
 assert c.execute('PRAGMA integrity_check').fetchall()==[('ok',)] and not c.execute('PRAGMA foreign_key_check').fetchall()
finally:c.rollback();c.close()
new_tables=set()
assert version==24 and schema==reh['source_schema_sha256'] and actual==before
assert actual==load(E/'harness/after.rows.json')
result=load(E/'harness/05-case.result.json');assert result['production_db_writes']==result['provider_requests']==0 and result['synthetic'] and not result['formal']
out={'schema':'researchos.root-native-retained-fixture-inspection/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config_ref':s['config_ref'],'snapshot_ref':ref(sp),'fixture_read_complete':True,'whole_row_schema_review_complete':True,'private_credentials_recorded':False,'version':version,'schema_sha256':schema,'new_tables_empty':sorted(new_tables),'old_tables_preserved':len(before),'all_typed_rows_match_harness':True,'all_old_rows_preserved_exactly':True,'sqlite_mode':'ro/query_only/read_transaction','db_mutations':0,'case_result_ref':ref(E/'harness/05-case.result.json'),'final_outer_job_result':'PENDING_AFTER_FIXTURE_RELEASE','formal_increment':0}
with (E/'root-retained-fixture-inspection.json').open('x',encoding='utf8') as w:json.dump(out,w,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=True))
