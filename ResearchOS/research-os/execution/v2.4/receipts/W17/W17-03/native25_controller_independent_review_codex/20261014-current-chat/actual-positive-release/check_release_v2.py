"""Independent concrete release review. Read-only synthetic SQLite; no authority actions."""
import datetime as dt,hashlib,json,os,sqlite3,struct,subprocess,sys,types
from pathlib import Path
E=Path(__file__).resolve().parent/'revision02'
E.mkdir(exist_ok=False)
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/positive-replay-01'
H=P/'harness';C=P/'controller'
S=C/'review-snapshot-release-8543ad52761d4166905b14b67bdfd1af.json'
def digest(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def ref(p):
 raw=Path(p).read_bytes();return {'path':str(p),'sha256':digest(raw),'bytes':len(raw)}
def read(p):return json.loads(Path(p).read_bytes())
def check(v):
 p=Path(v['path']);assert p.is_absolute() and str(p.resolve()).casefold()==str(p).casefold()
 actual=ref(p);assert actual['sha256']==v['sha256'] and actual['bytes']==v['bytes'],str(p)
 return p
def save(name,v):
 with (E/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def canonical(v):
 text=json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
 return text.encode()  # JCS removes HTML/Unicode escaping; all hashed values here are strings/arrays/maps.
def quoted(name):return '"'+name.replace('"','""')+'"'
def rowhash(row):
 data=bytearray()
 for v in row:
  if v is None:t,b=b'N',b''
  elif isinstance(v,int):t,b=b'I',str(v).encode()
  elif isinstance(v,float):t,b=b'F',struct.pack('>d',v)
  elif isinstance(v,str):t,b=b'T',v.encode()
  elif isinstance(v,bytes):t,b=b'B',v
  else:raise TypeError(type(v))
  data+=t+struct.pack('>Q',len(b))+b
 return digest(data)
def inspect_db(p):
 p=Path(p);assert p.is_file() and p.is_relative_to(Path(cfg['Environment']['TEMP']))
 for ext in ['-wal','-journal']:
  side=Path(str(p)+ext)
  assert not side.exists() or side.stat().st_size==0,'nonempty journal requires explicit WAL-aware reader'
 beforefile=ref(p)
 db=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  db.execute('PRAGMA query_only=ON')
  assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
  schema=db.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name").fetchall()
  tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
  typed={}
  for name in tables:
   cur=db.execute('SELECT * FROM '+quoted(name)+' LIMIT 0');cols=[d[0] for d in cur.description]
   cur=db.execute('SELECT '+','.join('CASE WHEN 1 THEN '+quoted(n)+' END' for n in cols)+' FROM '+quoted(name))
   typed[name]={'columns':cols,'row_digests':sorted(rowhash(row) for row in cur)}
  versions=[row[0] for row in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
  run=db.execute("SELECT body FROM domain_objects WHERE kind='Run' AND id=?",(fixture['run_id'],)).fetchone()
  runstatus=json.loads(run[0])['status']
  live=db.execute('SELECT count(*) FROM auth_credentials WHERE revoked=0').fetchone()[0]
 finally:db.close()
 assert ref(p)==beforefile,'read-only fixture file drift'
 return typed,{'database_ref':beforefile,'mode':'mode=ro&immutable=1; query_only=ON; nonempty WAL/journal rejected','quick_check':'ok','table_count':len(typed),
  'row_count':sum(len(v['row_digests']) for v in typed.values()),'typed_rows_sha256':digest(canonical(typed)),'schema_sha256':digest(canonical(schema)),
  'schema_versions':versions,'fixture_run_status':runstatus,'unrevoked_fixture_credentials_count':live,'raw_credentials_persisted':False,'file_bytes_unchanged_by_read':True}

report={'schema':'researchos.native25-concrete-release-independent-review/1','reviewer':'codex:/root/native25_controller_review','state':'IN_PROGRESS','native_authority_actions':0,'signatures_created':0,'root_approvals_created':0,'formal_increment':0}
try:
 assert ref(S)['sha256']=='sha256:d3b57cb1edf8533883b75e5626223ca2ed2067c3e4008c2f5b4c3934a41daafa'
 snap=read(S);cfg=read(check(snap['config_ref']));hc=read(check(snap['harness_config_ref']))
 assert snap['config_ref']['sha256']=='sha256:f21d508263674ca57672fddf2db897e78ffd06b355a6512acc47738b46f2c7fc'
 assert snap['phase']=='release' and snap['case']=='positive-replay' and snap['case_id']=='root-positive-replay-01' and snap['root_approval'] is False
 assert snap['job_binding_id']=='0b86c202a2cf48b18edaea0248453eff'
 payload=read(check(snap['payload_ref']));ready=read(check(snap['ready_ref']));fixture=read(check(snap['fixture_public_ref']))
 assert payload['schema']=='researchos.recovery-release.v1' and payload['purpose']=='RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1'
 assert payload['id']=='synthetic-native-root-positive-replay-01' and payload['source_root']==hc['BuildRoot']
 assert payload['root_image']==hc['RootProgram'] and payload['control_image']==hc['ControlProgram']
 assert payload['root_signing_public_key']==hc['RootSigningPublicKey']
 now=dt.datetime.now(dt.timezone.utc)
 assert dt.datetime.fromisoformat(payload['not_before_utc'].replace('Z','+00:00'))<=now<dt.datetime.fromisoformat(payload['expires_utc'].replace('Z','+00:00'))
 sid=subprocess.run(['C:/Windows/System32/whoami.exe','/user','/fo','csv','/nh'],capture_output=True,timeout=10)
 assert sid.returncode==0 and payload['sid'].encode() in sid.stdout
 assert ready['payload_sha256']==snap['payload_ref']['sha256'] and ready['sign_kind']==snap['sign_kind']=='release'
 assert ready['fixed_signed_path']==snap['signed_destination'] and Path(snap['signed_destination'])==Path(hc['RootProgram']['path']).parent/'recovery-release.json'
 frozen={str(Path(p['path']).resolve()).casefold():p for p in cfg['FrozenInputs']}
 for pin in cfg['FrozenInputs']:check(pin)
 product=read(check(cfg['CompilerInventory']))['product_inventory']
 assert len(payload['source_files'])==648
 got={str(Path(p['path']).resolve()).casefold():(p['sha256'],p['bytes']) for p in payload['source_files']}
 expected={str(Path(p['path']).resolve()).casefold():('sha256:'+p['sha256'].removeprefix('sha256:'),p['bytes']) for p in product}
 assert got==expected
 for pin in payload['source_files']:
  assert pin['role']=='source:'+Path(pin['path']).relative_to(Path(hc['BuildRoot'])).as_posix();check(pin)
 for pin in snap['evidence_refs']:check(pin)
 assert all(v['matches'] and v['actual']['sha256']==v['declared']['sha256'] and v['actual']['bytes']==v['declared']['bytes'] for v in snap['declared_pin_observations'])
 assert snap['snapshot_guard_cleanup']['closed'] and not snap['snapshot_guard_cleanup']['errors']
 obs=read(check(snap['observation_ref']));assert obs['phase']=='release' and obs['job_binding_id']==snap['job_binding_id']
 assert obs['owner_pid']==67436 and obs['result']['owned_child_pid']==51788 and obs['result']['actual_exit'] is None
 assert obs['held_job_handle'] and obs['held_primary_handle'] and obs['result']['resumed'] and obs['result']['job_cleanup']['assigned_before_resume']
 assert obs['result']['job_cleanup']['active_processes_last_observed']>0 and not obs['result']['job_cleanup']['errors']
 controller=types.ModuleType('release_review_readonly');controller.__file__=cfg['ControllerSource']['path']
 exec(compile(Path(controller.__file__).read_bytes(),controller.__file__,'exec'),controller.__dict__)
 measured={'root':controller.native_file_id(fixture['root'],True),'database':controller.native_file_id(fixture['database'],False)}
 assert measured==snap['measured_native_ids']
 assert fixture['synthetic'] and not fixture['formal'] and fixture['provider_requests']==0 and fixture['production_db_writes']==0
 before=read(H/'before.rows.json');rehearsal=read(H/'rehearsal.public.json');handoff=read(H/'00-handoff-binding.json')
 assert ref(H/'before.rows.json')['sha256']==fixture['typed_rows_sha256']==rehearsal['original_rows_sha256']
 assert handoff['source_database']==fixture['database'] and handoff['observed_backup_exit']==0
 for field,hkey in [('source_program_sha256','SourceBackupProgram'),('target_program_sha256','ControlProgram'),('rehearsal_program_sha256','BackupProgram')]:
  assert handoff[field]==rehearsal[field]==hc[hkey]['sha256']
 assert ref(H/'00-handoff-binding.json')['sha256']==rehearsal['handoff_binding_sha256']
 for label,program in [('00-source-backup',hc['SourceBackupProgram']),('00-rehearsal',hc['BackupProgram'])]:
  inv=read(H/label/'invocation.json');req=read(check(inv['PublicRequest']));assert req['Program']==program
  result=inv['Result'];job=result['job_cleanup'];assert result['actual_exit']==0 and result['error'] is None and not result['timed_out']
  assert all(job[k] for k in ['assigned_before_resume','unnamed_exclusive_job','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and job['active_processes_last_observed']==0 and not job['errors']
  assert inv['ActualLifetimeClosed'] and not inv['PrivateInputPersisted'];check(inv['Stdout']);check(inv['Stderr'])
  assert req['Environment']['TEMP']==cfg['Environment']['TEMP'] and req['Environment']['TMP']==cfg['Environment']['TMP']
 manifest=Path(handoff['backup_directory'])/'manifest.json';assert ref(manifest)['sha256']==handoff['backup_manifest_sha256']==rehearsal['backup_manifest_sha256']
 assert read(manifest)==read(H/'00-source-backup/stdout.raw')
 for flag in ['original_unchanged','rollback_verified','existing_rows_unchanged','new_pause_tables_empty']:assert rehearsal[flag]
 assert rehearsal['status']=='ISOLATED_REHEARSAL_COMPLETE_ORIGINAL_UNCHANGED' and rehearsal['automatic_promotion'] is False
 typed,dbinfo=inspect_db(fixture['database']);assert typed==before
 assert dbinfo['typed_rows_sha256']==fixture['typed_rows_sha256'] and dbinfo['schema_sha256']==fixture['schema_sha256']
 assert max(dbinfo['schema_versions'])==24
 restored=Path(rehearsal['options']['upgrade']['Destination'])/'researchos.sqlite'
 restoredtyped,restoredinfo=inspect_db(restored)
 assert max(restoredinfo['schema_versions'])==25 and restoredinfo['typed_rows_sha256']==rehearsal['post_ddl_rows_sha256']
 assert restoredinfo['fixture_run_status']=='RECONCILING' and restoredinfo['unrevoked_fixture_credentials_count']==0
 assert not (C/'controller.closed.json').exists() and not (H/'01-release.approval.json').exists() and not Path(snap['signed_destination']).exists()
 assert not (C/'sign-release.consumed.json').exists()
 assert controller.native_file_id(fixture['database'],False)==measured['database']
 assert ref(S)['sha256']=='sha256:d3b57cb1edf8533883b75e5626223ca2ed2067c3e4008c2f5b4c3934a41daafa'
 save('sqlite-readonly-summary.json',{'source24':dbinfo,'restored25':restoredinfo,'source_rows_equal_before_snapshot':True,'raw_row_values_saved':False,'measured_native_ids':measured})
 report.update(state='EXACT_RELEASE_PAYLOAD_CHECKED_READY_FOR_SEPARATE_ROOT_SIGN_DECISION',findings=[],snapshot_ref=ref(S),payload_ref=snap['payload_ref'],
  sign_kind='release',signed_destination=snap['signed_destination'],config_ref=snap['config_ref'],job_binding_id=snap['job_binding_id'],
  recorded_held_job_observation_ref=snap['observation_ref'],native_ids=measured,frozen_refs_checked=len(cfg['FrozenInputs']),source_file_pins_checked=len(payload['source_files']),
  sqlite_summary_ref=ref(E/'sqlite-readonly-summary.json'),source24_whole_rows_match=True,source24_schema_match=True,restored25_matches_rehearsal_typed_rows=True,
  old24_producer_and_new25_rehearsal_broker_closure_checked=True,sid_matches_current_user=True,expires_utc=payload['expires_utc'],
  scope='This one exact release payload only. It is not a migration grant, does not approve the later grant payload or publish either harness approval.',
  decision='Root may independently decide one sign-reviewed release call for these exact bytes after its current live held-Job check. Reviewer created no approval and did not sign/publish.',
  limitation='Job membership continuity is bound to the Root-held observation artifact; reviewer did not write a fresh poll request. Native file IDs and both isolated SQLite contents were freshly measured read-only.',
  private_key_reads=0,original_product_db_reads=0,fixture_databases_read=2,formal_accepted_cases='0/42',parent_tasks_open=22)
except BaseException as exc:
 report.update(state='FINDINGS_OR_REVIEW_CHECK_FAILED',error_type=type(exc).__name__,error=str(exc));raise
finally:
 report['at']=dt.datetime.now(dt.timezone.utc).isoformat();save('RELEASE-report.json',report)
 print(json.dumps({'state':report['state'],'report_ref':ref(E/'RELEASE-report.json')},ensure_ascii=True))
