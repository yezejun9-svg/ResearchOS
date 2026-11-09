import datetime,hashlib,json,sqlite3,struct,sys
from pathlib import Path
E=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def check(v):
 p=Path(v['path']);assert ref(p)['sha256']==v['sha256'] and p.stat().st_size==v['bytes'];return p
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
SP=Path(sys.argv[1]).resolve();assert len(sys.argv)==2 and SP.parent==E/'controller'
s=load(SP);cfg=load(E/'controller.public.config.json');hc=load(check(cfg['HarnessConfig']));p=load(check(s['payload_ref']));f=load(check(s['fixture_public_ref']));before=load(E/'harness/before.rows.json');reh=load(E/'harness/rehearsal.public.json')
assert s['phase']=='release' and s['case']=='wrong-purpose' and s['job_binding_id']==load(E/'controller/controller.started.json')['job_binding_id']
assert s['snapshot_guard_cleanup']['closed'] and not s['snapshot_guard_cleanup']['errors']
assert p['schema']=='researchos.recovery-release.v1' and p['purpose']=='RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1'
assert p['id']=='synthetic-native-root-wrong-purpose-01' and p['sid']=='S-1-5-21-2314176124-1781180693-2759285857-1001'
assert p['root_image']==hc['RootProgram'] and p['control_image']==hc['ControlProgram'] and p['source_root']==hc['BuildRoot']
assert p['root_signing_public_key']=='d5d735ecd3296beb4ee68d59da4f7503d7db34b310e0642d9f8b19c5c454e4b5'
now=datetime.datetime.now(datetime.timezone.utc);nb=datetime.datetime.fromisoformat(p['not_before_utc']);exp=datetime.datetime.fromisoformat(p['expires_utc']);assert nb<now<exp and (exp-nb).total_seconds()<=1801
assert len(p['source_files'])==648 and len(s['declared_pin_observations'])==650
for pin in [p['root_image'],p['control_image']]+p['source_files']:check(pin)
for pin in p['source_files']:assert Path(pin['path']).resolve().is_relative_to(Path(hc['BuildRoot']).resolve())
assert all(x['matches'] for x in s['declared_pin_observations'])
assert f['synthetic'] and not f['formal'] and f['production_db_writes']==f['provider_requests']==0
db=Path(f['database']).resolve();assert db.is_relative_to((R/'.local/native25-cases-20261014/wrong-purpose-01/temp').resolve())
assert reh['plan']=='schema24-to25-runtime-pause-v1' and reh['status']=='ISOLATED_REHEARSAL_COMPLETE_ORIGINAL_UNCHANGED'
assert all(reh[k] for k in ['original_unchanged','rollback_verified','existing_rows_unchanged','new_pause_tables_empty']) and not reh['automatic_promotion']
assert reh['options']['upgrade']['Source']==str(db) and reh['original_rows_sha256']==sha((E/'harness/before.rows.json').read_bytes())
c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
try:
 tables=[x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")];actual={}
 for table in tables:
  cur=c.execute('SELECT * FROM '+q(table));cols=[x[0] for x in cur.description];actual[table]={'columns':cols,'row_digests':sorted(digestrow(row) for row in cur)}
 assert actual==before
 version=c.execute('SELECT max(version) FROM schema_migrations').fetchone()[0];assert version==24
 assert c.execute('PRAGMA integrity_check').fetchall()==[('ok',)] and not c.execute('PRAGMA foreign_key_check').fetchall()
finally:c.rollback();c.close()
out={'schema':'researchos.root-native-concrete-release-inspection/1','at':now.isoformat(),'snapshot_ref':ref(SP),'payload_ref':s['payload_ref'],'pins_rehashed':650,'source_files':648,'fixture_only':True,'fixture_schema':version,'all_original_typed_tables_equal':True,'tables':len(actual),'rows':sum(len(v['row_digests']) for v in actual.values()),'sqlite_mode':'ro/query_only/read_transaction','db_mutations':0,'private_credentials_read':False,'signed':False,'published':False,'formal_increment':0}
with (E/'root-release-inspection.json').open('x',encoding='utf8') as w:json.dump(out,w,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=True))
