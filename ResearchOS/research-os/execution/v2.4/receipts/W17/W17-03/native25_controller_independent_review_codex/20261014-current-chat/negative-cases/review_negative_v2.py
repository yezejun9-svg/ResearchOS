"""Read-only negative-case review. Never approves, signs, publishes, serves or releases.

Every invocation creates one new reviewer evidence directory and persists failures.
Only release/grant/terminal/closure stages explicitly requested on the command line run.
"""
import argparse,ast,collections,datetime as dt,hashlib,json,os,re,sqlite3,struct,subprocess,sys,traceback,types
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

HOME=Path(__file__).resolve().parent
EXPECTED=json.loads((HOME.parent/'negative-review-preparation/expected-cases.json').read_bytes())['cases']
ROOT=Path('D:/作品集/ResearchOS/research-os')
ACTUAL=ROOT/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat'
CONTROLLER_SHA='sha256:c95ed27b644368fd846bd5ddbd4fc8268cbfea65eb2a8165691456e707a221fa'
TEST_SHA='sha256:a3e2f46ffad34d32b7384a4694dc3338ac1ee8e546a52c1a7dbc0a1450c992ac'
SQL_SHA='sha256:6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0'
PURPOSE='RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1'

def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def ref(path):
 p=Path(path);raw=p.read_bytes();return {'path':str(p.resolve()),'sha256':digest(raw),'bytes':len(raw)}
def read(path):return json.loads(Path(path).read_bytes())
def samepath(a,b):return Path(a)==Path(b)
def check(pin):
 p=Path(pin['path']);assert p.is_absolute() and p.resolve()==p,'noncanonical public input'
 v=ref(p);assert v['sha256']==pin['sha256'] and v['bytes']==pin['bytes'],'public pin drift: '+p.name
 return p
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def save(name,value):
 with (E/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=True,indent=2);f.write('\n')
def verify_job(result,zero=None):
 j=result['job_cleanup'];assert result['actual_exit'] is not None and result['error'] is None and not result['timed_out'] and result['resumed']
 if zero is True:assert result['actual_exit']==0
 if zero is False:assert result['actual_exit']!=0
 assert all(j[k] for k in ['assigned_before_resume','unnamed_exclusive_job','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed'])
 assert j['active_processes_last_observed']==0 and not j['errors']
def verify_guard(guard):
 assert guard['closed'] and not guard['errors']
 assert all(x['closed'] and x['verified'] and x['final_path_match'] for x in guard['entries'])
def broker(label,program,arguments,zero):
 inv=read(H/label/'invocation.json');request=read(check(inv['PublicRequest']))
 assert request['Program']==hc[program] and request['Arguments']==arguments
 assert inv['ActualLifetimeClosed'] and not inv['PrivateInputPersisted'] and inv['NativeAuthorityAcceptance'] is False
 verify_job(inv['Result'],zero)
 private=inv['Result']['private_stdin']
 for key in ['anonymous_pipe','file_type_pipe_verified','complete_input_written','writer_closed_before_launch','input_buffer_cleared','capacity_verified','empty_before_write','write_deadline_checked_before_and_after']:assert private[key]
 out=Path(check(inv['Stdout'])).read_bytes();err=Path(check(inv['Stderr'])).read_bytes()
 return inv,request,out,err
def typed_row(row):
 data=bytearray()
 for value in row:
  if value is None:t,b=b'N',b''
  elif isinstance(value,int):t,b=b'I',str(value).encode()
  elif isinstance(value,float):t,b=b'F',struct.pack('>d',value)
  elif isinstance(value,str):t,b=b'T',value.encode()
  elif isinstance(value,bytes):t,b=b'B',value
  else:raise TypeError(type(value).__name__)
  data+=t+struct.pack('>Q',len(b))+b
 return digest(data)
def quote(name):return '"'+name.replace('"','""')+'"'
def inspect_db(path):
 p=Path(path);assert p.is_relative_to(Path(cfg['Environment']['TEMP'])) and p.is_file()
 for ext in ['-wal','-journal']:
  q=Path(str(p)+ext);assert not q.exists() or q.stat().st_size==0,'nonempty SQLite sidecar'
 before=ref(p);db=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  db.execute('PRAGMA query_only=ON');assert db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
  schema=db.execute("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name").fetchall();typed={}
  for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
   columns=[d[0] for d in db.execute('SELECT * FROM '+quote(name)+' LIMIT 0').description]
   rows=db.execute('SELECT '+','.join('CASE WHEN 1 THEN '+quote(col)+' END' for col in columns)+' FROM '+quote(name))
   typed[name]={'columns':columns,'row_digests':sorted(typed_row(row) for row in rows)}
  versions=[row[0] for row in db.execute('SELECT version FROM schema_migrations ORDER BY version')]
  run=db.execute("SELECT body FROM domain_objects WHERE kind='Run' AND id=?",(fixture['run_id'],)).fetchone()
  status=json.loads(run[0])['status'];live=db.execute('SELECT count(*) FROM auth_credentials WHERE revoked=0').fetchone()[0]
 finally:db.close()
 assert ref(p)==before,'SQLite drift during read'
 return typed,{'database_ref':before,'mode':'mode=ro&immutable=1;query_only=ON','tables':len(typed),'rows':sum(len(v['row_digests']) for v in typed.values()),'typed_rows_sha256':digest(canonical(typed)),'schema_sha256':digest(canonical(schema)),'versions':versions,'fixture_run_status':status,'synthetic_live_credentials_count':live,'raw_values_saved':False}
def raw_member(path,key):
 text=Path(path).read_text(encoding='utf8');i=text.index('"'+key+'":')+len(key)+3
 while text[i].isspace():i+=1
 _,end=json.JSONDecoder().raw_decode(text,i);return text[i:end].encode()
def signature(phase,required):
 receiptpath=C/('sign-'+phase+'.receipt.json')
 if not receiptpath.exists():
  assert not required,'missing signing receipt';return None
 rec=read(receiptpath);assert rec['success'] and rec['private_path_recorded'] is False and rec['private_key_read_by_controller'] is False
 verify_job(rec['result'],True);verify_guard(rec['source_guard_cleanup']);signed=check(rec['signed_ref']);payload=check(rec['payload_ref'])
 doc=read(signed);raw=raw_member(signed,'payload');assert raw==Path(payload).read_bytes()
 purpose='RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1/release' if phase=='release' else ('RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1/grant' if case=='wrong-purpose' else PURPOSE+'/grant')
 publicsrc=Path(hc['BuildRoot'])/'internal/recoveryauthority/types.go';issuer=re.search(r'const enrolledIssuerPublicKeyHex = "([a-f0-9]{64})"',publicsrc.read_text(encoding='utf8')).group(1)
 Ed25519PublicKey.from_public_bytes(bytes.fromhex(issuer)).verify(bytes.fromhex(doc['signature']),purpose.encode()+b'\0'+raw)
 approval=read(check(rec['approval_ref']));check(approval['Snapshot']);assert approval['Payload']==rec['payload_ref'] and samepath(approval['SignedDestination'],signed)
 assert (C/('sign-'+phase+'.consumed.json')).is_file()
 return {'receipt_ref':ref(receiptpath),'signed_ref':rec['signed_ref'],'signature_verified':True,'signer_job_closed':True}
def setup(snapshot_required=True):
 global cfg,hc,P,C,H,case,fixture,controller,snap
 assert ref(args.config)['sha256']=='sha256:'+args.config_sha256.removeprefix('sha256:')
 cfg=read(args.config);hc=read(check(cfg['HarnessConfig']));case=hc['Case'];assert case in EXPECTED
 assert cfg['Schema']=='researchos.root-native-pause-migration-controller.v1' and hc['Schema']=='researchos.synthetic-native-pause-migration-config.v1'
 assert hc['CaseID']==case_id and Path(args.config).parent.is_relative_to(ACTUAL)
 P=Path(args.config).parent;C=Path(cfg['ControllerDirectory']);H=Path(hc['OutputDirectory']);assert C.parent==P and H.parent==P
 assert cfg['ControllerSource']['sha256']==CONTROLLER_SHA and cfg['TestProgram']['sha256']==TEST_SHA
 pins={str(Path(p['path'])).casefold():p for p in cfg['FrozenInputs']};assert len(pins)==len(cfg['FrozenInputs'])==args.expected_pins
 for pin in cfg['FrozenInputs']:check(pin)
 for key in ['ControllerSource','HarnessConfig','TestProgram','ObservedOwnedHelper','OriginalOwnedHelper','SourceReadGuard','CompilerInventory','BuildInvocation']:
  pin=cfg[key];assert pins[str(Path(pin['path'])).casefold()]==pin
 for key in ['SourceBackupProgram','RootProgram','ControlProgram','BackupProgram','EnrollmentProgram','PythonProgram','BrokerSource','PrivateStdinHelper']:
  pin={k:v for k,v in hc[key].items() if k!='role'};assert pins[str(Path(pin['path'])).casefold()]==pin
 inventory=read(check(cfg['CompilerInventory']))
 assert inventory['build_tag']=='' and inventory['includes_actual_test_and_embed_inputs'] is True
 for pin in inventory['build_inputs']+inventory['product_inventory']:
  actual=pins[str(Path(pin['path'])).casefold()];assert actual['sha256']=='sha256:'+pin['sha256'].removeprefix('sha256:') and actual['bytes']==pin['bytes']
 build=read(check(cfg['BuildInvocation']));assert build['actual_native_exit']==0;verify_job(build['result'],True)
 report['frozen_pins_checked']=len(pins)
 controller=types.ModuleType('negative_review_readonly_controller');controller.__file__=str(check(cfg['ControllerSource']));exec(compile(Path(controller.__file__).read_bytes(),controller.__file__,'exec'),controller.__dict__)
 if not snapshot_required:return
 assert ref(args.snapshot)['sha256']=='sha256:'+args.snapshot_sha256.removeprefix('sha256:');snap=read(args.snapshot)
 assert snap['case']==case and snap['case_id']==case_id and snap['root_approval'] is False
 assert snap['config_ref']['sha256']==ref(args.config)['sha256'] and snap['harness_config_ref']==cfg['HarnessConfig']
 assert snap['phase']=={'terminal':'fixture-retained'}.get(args.stage,args.stage)
 for pin in snap['evidence_refs']:check(pin)
 verify_guard(snap['snapshot_guard_cleanup'])
 fixture=read(check(snap['fixture_public_ref']));assert fixture['synthetic'] and not fixture['formal'] and fixture['provider_requests']==fixture['production_db_writes']==0
 ids={'root':controller.native_file_id(fixture['root'],True),'database':controller.native_file_id(fixture['database'],False)};assert ids==snap['measured_native_ids']
 obs=read(check(snap['observation_ref']));assert obs['job_binding_id']==snap['job_binding_id'] and obs['held_job_handle'] and obs['held_primary_handle']
 assert obs['result']['actual_exit'] is None and obs['result']['resumed'] and obs['result']['job_cleanup']['assigned_before_resume'] and obs['result']['job_cleanup']['active_processes_last_observed']>0
 report.update(snapshot_ref=ref(args.snapshot),job_binding_id=snap['job_binding_id'],recorded_held_job_observation_ref=snap['observation_ref'],native_ids=ids,observation_boundary='Root-held observation artifact inspected; reviewer issued no poll request.')
def baseline():
 assert args.baseline_report,'release baseline report is required'
 p=Path(args.baseline_report);assert p.is_relative_to(HOME);v=read(p);assert v['state']=='PASS' and v['stage']=='release' and v['case_id']==case_id and v['config_ref']['sha256']==ref(args.config)['sha256']
 return v
def release():
 setup();payload=read(check(snap['payload_ref']));ready=read(check(snap['ready_ref']))
 assert payload['schema']=='researchos.recovery-release.v1' and payload['purpose']=='RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1'
 assert payload['id']=='synthetic-native-'+case_id and samepath(payload['source_root'],hc['BuildRoot'])
 assert payload['root_image']==hc['RootProgram'] and payload['control_image']==hc['ControlProgram'] and payload['root_signing_public_key']==hc['RootSigningPublicKey']
 now=dt.datetime.now(dt.timezone.utc);assert dt.datetime.fromisoformat(payload['not_before_utc'].replace('Z','+00:00'))<=now<dt.datetime.fromisoformat(payload['expires_utc'].replace('Z','+00:00'))
 sid=subprocess.run(['C:/Windows/System32/whoami.exe','/user','/fo','csv','/nh'],capture_output=True,timeout=10);assert sid.returncode==0 and payload['sid'].encode() in sid.stdout
 assert ready['payload_sha256']==snap['payload_ref']['sha256'] and ready['sign_kind']==snap['sign_kind']=='release'
 assert samepath(ready['fixed_signed_path'],snap['signed_destination']) and Path(snap['signed_destination'])==Path(hc['RootProgram']['path']).parent/'recovery-release.json'
 product=read(check(cfg['CompilerInventory']))['product_inventory'];expected={str(Path(p['path'])).casefold():p for p in product};source=payload['source_files'];assert len(source)==len(expected)==648
 mismatch=[]
 for index,pin in enumerate(source):
  actual=ref(pin['path']);exp=expected[str(Path(pin['path'])).casefold()];assert actual['sha256']=='sha256:'+exp['sha256'].removeprefix('sha256:') and actual['bytes']==exp['bytes']
  assert pin['role']=='source:'+Path(pin['path']).relative_to(Path(hc['BuildRoot'])).as_posix() and pin['bytes']==actual['bytes']
  if pin['sha256']!=actual['sha256']:mismatch.append(index);assert case=='release-pin-mismatch' and index==0 and pin['sha256']==digest(b'SYNTHETIC_INVALID_SOURCE_PIN')
 assert mismatch==([0] if case=='release-pin-mismatch' else [])
 assert len([p for p in snap['declared_pin_observations'] if not p['matches']])==len(mismatch)
 before=read(H/'before.rows.json');typed,sql=inspect_db(fixture['database']);assert typed==before and max(sql['versions'])==24 and sql['typed_rows_sha256']==fixture['typed_rows_sha256'] and sql['schema_sha256']==fixture['schema_sha256']
 rh=read(H/'rehearsal.public.json');assert rh['original_rows_sha256']==sql['typed_rows_sha256'] and rh['source_schema_sha256']==sql['schema_sha256']
 restored,restoredsql=inspect_db(Path(rh['options']['upgrade']['Destination'])/'researchos.sqlite');assert max(restoredsql['versions'])==25 and restoredsql['typed_rows_sha256']==rh['post_ddl_rows_sha256'] and restoredsql['schema_sha256']==rh['restored_schema25_sha256']
 for flag in ['original_unchanged','rollback_verified','existing_rows_unchanged','new_pause_tables_empty']:assert rh[flag]
 for label,program in [('00-source-backup','SourceBackupProgram'),('00-rehearsal','BackupProgram')]:
  inv=read(H/label/'invocation.json');req=read(check(inv['PublicRequest']));assert req['Program']==hc[program] and inv['ActualLifetimeClosed'] and not inv['PrivateInputPersisted'];verify_job(inv['Result'],True);check(inv['Stdout']);check(inv['Stderr'])
 report.update(payload_ref=snap['payload_ref'],source_pins_checked=648,intentional_release_pin_mismatch_indices=mismatch,source24=sql,restored25=restoredsql,release_signature=signature('release',False))
def expected_grant_pins():
 rh=read(H/'rehearsal.public.json');up=rh['options']['upgrade']
 fixed={'target-rehearsal-program':hc['BackupProgram']['path'],'handoff-binding':H/'00-handoff-binding.json','backup-producer-stdout':H/'00-source-backup/stdout.raw','backup-producer-observation':H/'00-source-backup/invocation.json','source-program':hc['SourceBackupProgram']['path'],'target-program':hc['ControlProgram']['path'],'migration-sql':Path(hc['BuildRoot'])/'migrations/sqlite/0025_runtime_pause_activations.sql','encrypted-backup-manifest':Path(up['Snapshot'])/'manifest.json','isolated-restore-rehearsal':Path(up['Destination'])/'runtime-pause-schema-rehearsal.json'}
 roles={k:{'role':k,**ref(p)} for k,p in fixed.items()};inventories={}
 for name,root,count in [('source',hc['SourceReleaseRoot'],24),('target',hc['BuildRoot'],25)]:
  root=Path(root);rels=[p.relative_to(root).as_posix() for p in sorted((root/'migrations/sqlite').glob('0*.sql'))]
  assert len(rels)==count
  rels+=['spec/v2.0/contracts/domain.schema.json','spec/v2.0/contracts/openapi.json','internal/api/contracts/client.protocol.schema.json','internal/api/contracts/domain.schema.json','migrations/sqlite/next_v24_sessions.sql']
  inv={}
  for rel in rels:
   role=name+'-inventory:'+rel;pin=ref(root/rel);inv[rel]=pin['sha256'];roles[role]={'role':role,**pin}
  inventories[name]=inv
 for p in sorted(Path(up['Snapshot']).glob('*.enc')):
  role='encrypted-backup-payload:'+p.name;roles[role]={'role':role,**ref(p)}
 for name in ['before.rows.json','fixture.public.json','00-rehearsal/invocation.json','00-rehearsal/stdout.raw','00-rehearsal/stderr.raw']:
  role='fixture-evidence:'+name;roles[role]={'role':role,**ref(H/name)}
 assert len(roles)==76;return roles,inventories
def grant():
 setup();pre=baseline();g=read(check(snap['payload_ref']));ready=read(check(snap['ready_ref']));rh=read(H/'rehearsal.public.json')
 assert len(bytes.fromhex(g['nonce']))==32 and ready['payload_sha256']==snap['payload_ref']['sha256']
 expected,inv=expected_grant_pins();omitted=[]
 if case=='missing-dynamic-pin':
  key=sorted(k for k in expected if k.startswith('source-inventory:'))[0];omitted=[key];expected.pop(key)
 actual={p['role']:p for p in g['pins']};assert len(actual)==len(g['pins'])==len(expected)
 for role,pin in actual.items():
  check(pin);exp=expected[role];assert samepath(pin['path'],exp['path']) and pin['sha256']==exp['sha256'] and pin['bytes']==exp['bytes']
 start=dt.datetime.fromisoformat(g['issued_utc'].replace('Z','+00:00'));end=dt.datetime.fromisoformat(g['expires_utc'].replace('Z','+00:00'));assert (end-start).total_seconds()==(90 if case=='expired-grant' else 240)
 assert ready['expires_utc']==g['expires_utc'] and ready['synthetic_case']==case and ready['intentional_negative'] is True
 assert samepath(ready['fixed_signed_path'],snap['signed_destination']) and Path(snap['signed_destination'])==Path(hc['RootProgram']['path']).parent/'current-schema24-to25-grant.json'
 rel=signature('release',True);assert g['release_sha256']==rel['signed_ref']['sha256']
 if case=='wrong-purpose':
  assert g['schema']=='researchos.recovery-grant.v1' and g['purpose']=='RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1' and snap['sign_kind']==ready['sign_kind']=='grant'
  assert samepath(g['root'],fixture['root']) and samepath(g['database'],fixture['database']) and g['root_identity']==snap['measured_native_ids']['root'] and g['database_identity']==snap['measured_native_ids']['database']
  assert 'binding' not in g and 'options' not in g
  assert set(g)=={'schema','purpose','release_sha256','nonce','issued_utc','expires_utc','root','root_identity','database','database_identity','tuple','pins'}
  assert g['tuple']=={'project_id':'','task_id':'','run_id':'','runtime_id':'','owner_root':'','epoch':0,'run_revision':0,'task_revision':0,'dispatch_key':'','manifest_hash':''}
 else:
  assert g['schema']=='researchos.pause-schema-migration-grant.v1' and g['purpose']==PURPOSE and g['stage']=='APPLY_ORIGINAL' and snap['sign_kind']==ready['sign_kind']=='pause-migration-grant'
  b=g['binding'];assert b['plan_id']=='schema24-to25-runtime-pause-v1' and b['owner_root']=='fixture-author' and b['project_id']==fixture['project_id']
  assert samepath(b['root'],fixture['root']) and samepath(b['database'],fixture['database']) and b['root_identity']==snap['measured_native_ids']['root']
  if case=='mismatched-database':
   others=list(Path(cfg['Environment']['TEMP']).rglob('other-native-file-*'));assert len(others)==1 and others[0].is_file()
   assert b['database_identity']!=snap['measured_native_ids']['database'] and b['database_identity']==controller.native_file_id(others[0],False)
   report['intentional_other_file_identity_observation']={'public_path':str(others[0]),'native_identity':b['database_identity'],'actual_database_identity':snap['measured_native_ids']['database'],'file_contents_read':False}
  else:assert b['database_identity']==snap['measured_native_ids']['database']
  assert b['source_release_sha256']==hc['SourceBackupProgram']['sha256'] and b['target_release_sha256']==hc['ControlProgram']['sha256'] and b['sql_sha256']==SQL_SHA
  assert b['source_inventory_sha256']==digest(canonical(inv['source'])) and b['target_inventory_sha256']==digest(canonical(inv['target']))
  assert b['original_rows_sha256']==pre['source24']['typed_rows_sha256'] and b['source_schema_sha256']==pre['source24']['schema_sha256'] and b['target_schema_sha256']==rh['target_schema_sha256']
  assert g['options']==rh['options'] and b['options_sha256']==digest(raw_member(snap['payload_ref']['path'],'options'))
  assert b['backup']==actual['encrypted-backup-manifest'] and b['rehearsal']==actual['isolated-restore-rehearsal']
 assert all(x['matches'] for x in snap['declared_pin_observations'])
 report.update(payload_ref=snap['payload_ref'],grant_pins_checked=len(actual),intentionally_omitted_roles=omitted,interval_seconds=(end-start).total_seconds(),release_signature=rel,grant_signature=signature('grant',False),baseline_report_ref=ref(args.baseline_report))
def terminal():
 setup();pre=baseline();before=read(H/'before.rows.json');after=read(H/'after.rows.json');result=read(H/'05-case.result.json');typed,sql=inspect_db(fixture['database'])
 assert typed==before==after and max(sql['versions'])==24 and sql['typed_rows_sha256']==pre['source24']['typed_rows_sha256']==result['after_rows_sha256']==result['before_rows_sha256']
 assert sql['schema_sha256']==pre['source24']['schema_sha256']==result['before_schema_sha256']==result['after_schema_sha256']
 assert sql['fixture_run_status']==pre['source24']['fixture_run_status'] and sql['synthetic_live_credentials_count']==pre['source24']['synthetic_live_credentials_count']
 assert result['case']==case and result['synthetic'] and not result['formal'] and result['production_db_writes']==result['provider_requests']==0 and result['inner_native_job_id_independently_observed'] is False
 spec=EXPECTED[case];program=spec.get('native_program','RootProgram');arguments=spec.get('native_arguments',['schema24-to25']);inv,req,out,err=broker('03-native',program,arguments,False)
 expected=spec['expected_rejection'];lease=None
 if case=='lease-occupied':
  lease=read(H/'03-live-lease.public.json');closed=read(H/'03-live-lease.closed.json');obs=read(snap['observation_ref']['path'])
  assert lease['held_before_native'] and lease['second_acquire_win32_code']==32 and lease['holder_pid']==obs['result']['owned_child_pid'] and lease['holder_creation_time_100ns']==obs['result']['creation_time_100ns']
  assert samepath(lease['root'],fixture['root']) and closed['held_through_native_closure'] and closed['close_succeeded'] and not closed['held_after_close'];expected=lease['expected_native_error']
 lines=[line.rstrip('\r') for line in err.decode('utf8').split('\n') if line.rstrip('\r')]
 assert lines,'missing actual rejection stderr'
 first=lines[0]
 if len(first)>=20 and first[19]==' ':
  try:dt.datetime.strptime(first[:19],'%Y/%m/%d %H:%M:%S');first=first[20:]
  except ValueError:pass
 assert first==expected and result['expected_rejection']==expected
 if case=='expired-grant':
  g=read(H/'02-grant.payload.json');created=dt.datetime(1601,1,1,tzinfo=dt.timezone.utc)+dt.timedelta(microseconds=inv['Result']['creation_time_100ns']//10)
  assert created>=dt.datetime.fromisoformat(g['expires_utc'].replace('Z','+00:00'))
 assert not (H/'04-replay/invocation.json').exists()
 report.update(sqlite=sql,actual_native_exit=inv['Result']['actual_exit'],actual_native_pid=inv['Result']['owned_child_pid'],actual_rejection=expected,native_invocation_ref=ref(H/'03-native/invocation.json'),native_stderr_ref=inv['Stderr'],signed_release=signature('release',True),signed_grant=signature('grant',True),lease_evidence_present=lease is not None,whole_original_rows_and_schema_unchanged=True,baseline_report_ref=ref(args.baseline_report),outer_exit_zero_confirmed=False)
def closure():
 setup(False);assert args.terminal_report and Path(args.terminal_report).is_relative_to(HOME);terminal=read(args.terminal_report);assert terminal['state']=='PASS' and terminal['case_id']==case_id and terminal['stage']=='terminal'
 assert ref(args.snapshot)['sha256']=='sha256:'+args.snapshot_sha256.removeprefix('sha256:');closed=read(args.snapshot);assert Path(args.snapshot)==C/'controller.closed.json'
 assert closed['case']==case and closed['case_id']==case_id and closed['job_binding_id']==terminal['job_binding_id'] and closed['job_and_guards_closed'] and closed['harness_test_exit_zero'] and closed['fixture_release_approval_exists'] and not closed['worker_still_alive'] and closed['error_type'] is None and closed['worker_error_type'] is None
 iv=read(check(closed['invocation_ref']));verify_job(iv['result'],True);verify_guard(closed['source_guard_cleanup']);assert len(closed['source_guard_cleanup']['entries'])==args.expected_pins+1
 assert Path(check(iv['stdout_ref'])).read_bytes()==b'PASS\n' and Path(check(iv['stderr_ref'])).read_bytes()==b'' and iv['same_owned_job_for_all_harness_pauses']
 archive_root=P/'public-retained-inputs';archive=read(archive_root/'retention.json');g=read(H/'02-grant.payload.json')
 expected={str(Path(pin['path'])):pin for pin in g['pins'] if Path(pin['path']).is_relative_to(Path(cfg['Environment']['TEMP']))};actual={}
 assert archive['public_refs_only'] and archive['private_key_or_database_read'] is False and archive['copied_files']==len(archive['mapping'])==len(expected)==5
 for item in archive['mapping']:
  old,new=item['original_ref'],item['archived_ref'];check(new);assert Path(new['path']).is_relative_to(archive_root)
  assert old['sha256']==new['sha256']==expected[str(Path(old['path']))]['sha256'] and old['bytes']==new['bytes']==expected[str(Path(old['path']))]['bytes'];actual[str(Path(old['path']))]=new
 assert set(actual)==set(expected)
 report.update(controller_closed_ref=ref(args.snapshot),test_invocation_ref=closed['invocation_ref'],outer_test_exit=0,source_guards_closed=len(closed['source_guard_cleanup']['entries']),terminal_report_ref=ref(args.terminal_report),acceptance='ONE_ISOLATED_NATIVE_NEGATIVE_ONLY',retention_mapping_ref=ref(archive_root/'retention.json'),retained_temp_public_files_verified=len(actual))

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage',choices=['release','grant','terminal','closure'],required=True)
parser.add_argument('--config',required=True);parser.add_argument('--config-sha256',required=True)
parser.add_argument('--snapshot',required=True);parser.add_argument('--snapshot-sha256',required=True)
parser.add_argument('--expected-pins',type=int,default=4375);parser.add_argument('--attempt',required=True)
parser.add_argument('--baseline-report');parser.add_argument('--terminal-report')
args=parser.parse_args();preconfig=read(args.config);prehc=read(preconfig['HarnessConfig']['path']);case_id=prehc['CaseID']
assert re.fullmatch('[A-Za-z0-9_-]+',case_id) and re.fullmatch('[A-Za-z0-9_-]+',args.attempt)
assert prehc['Case'] in EXPECTED,'only the eight explicitly mapped negative cases are accepted'
E=HOME/case_id/(args.stage+'-'+args.attempt);E.mkdir(parents=True,exist_ok=False)
report={'schema':'researchos.independent-native25-negative-review/1','state':'IN_PROGRESS','stage':args.stage,'case':prehc['Case'],'case_id':case_id,'config_ref':ref(args.config),'reviewer_script_ref':ref(__file__),'inner_native_job_id_independently_observed':False,'formal_increment':0,'formal_accepted':'0/42','open_parents':22,'root_authority_actions':0,'private_resource_reads':0,'product_database_reads':0}
code=0
try:
 globals()[args.stage]();report['state']='PASS'
except BaseException as exc:
 code=1;report.update(state='REVIEW_FAILED_NOT_ACCEPTED',error_type=type(exc).__name__,error=str(exc));(E/'traceback.raw.txt').write_text(traceback.format_exc(),encoding='utf8')
finally:
 report['at']=dt.datetime.now(dt.timezone.utc).isoformat();save('report.json',report)
 print(json.dumps({'state':report['state'],'stage':args.stage,'case_id':case_id,'report_ref':ref(E/'report.json')}))
raise SystemExit(code)
