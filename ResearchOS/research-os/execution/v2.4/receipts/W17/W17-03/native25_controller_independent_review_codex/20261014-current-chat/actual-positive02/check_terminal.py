"""Independent fresh read-only retained fixture and actual broker outcome review."""
import ast,collections,datetime as dt,hashlib,json,os,sqlite3,struct,sys,types
from pathlib import Path
E=Path(__file__).parent/'terminal-review';E.mkdir(exist_ok=False)
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/positive-replay-02';C=P/'controller';H=P/'harness'
tree=ast.parse((E.parent/'check_release.py').read_text(encoding='utf8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'reviewed-readonly-utilities','exec'))
cfg=read(P/'controller.public.config.json');hc=read(P/'harness.public.config.json');fixture=read(H/'fixture.public.json')
S=C/'review-snapshot-fixture-retained-5422950b4c6443fb82f3abe3c8885163.json';s=read(S);g=read(H/'02-grant.payload.json');b=g['binding']
assert s['phase']=='fixture-retained' and s['job_binding_id']=='dbfaee8e699447c0addd66b8b3dd7567'
for pin in s['evidence_refs']:check(pin)
assert all(v['matches'] for v in s['declared_pin_observations']) and s['snapshot_guard_cleanup']['closed'] and not s['snapshot_guard_cleanup']['errors']
before=read(H/'before.rows.json');after=read(H/'after.rows.json');result=read(H/'05-case.result.json')
typed,info=inspect_db(fixture['database']);assert typed==after
assert max(info['schema_versions'])==25 and info['schema_sha256']==b['target_schema_sha256']==result['after_schema_sha256']
assert info['typed_rows_sha256']==result['after_rows_sha256'] and digest(canonical(before))==result['before_rows_sha256']==b['original_rows_sha256']
new=set(after)-set(before);assert len(new)==3
assert all(not after[n]['row_digests'] for n in new)
assert len(before)==88 and sum(len(v['row_digests']) for v in before.values())==249
for name,old in before.items():
 assert after[name]['columns']==old['columns']
 if name!='schema_migrations':assert after[name]['row_digests']==old['row_digests']
 else:
  diff=collections.Counter(after[name]['row_digests'])-collections.Counter(old['row_digests'])
  assert sum(diff.values())==1 and not (collections.Counter(old['row_digests'])-collections.Counter(after[name]['row_digests']))
assert info['fixture_run_status']=='RECONCILING' and info['unrevoked_fixture_credentials_count']==0
controller=types.ModuleType('terminal_readonly');controller.__file__=cfg['ControllerSource']['path'];exec(compile(Path(controller.__file__).read_bytes(),controller.__file__,'exec'),controller.__dict__)
ids={'root':controller.native_file_id(fixture['root'],True),'database':controller.native_file_id(fixture['database'],False)}
assert ids==s['measured_native_ids']=={'root':b['root_identity'],'database':b['database_identity']}
brokers=[]
for label,expected_exit in [('03-native',0),('04-replay',1)]:
 inv=read(H/label/'invocation.json');request=read(check(inv['PublicRequest']));res=inv['Result'];job=res['job_cleanup']
 assert request['Program']==hc['RootProgram'] and request['Args']==['schema24-to25']
 assert res['actual_exit']==expected_exit and not res['timed_out'] and res['error'] is None
 assert inv['ActualLifetimeClosed'] and not inv['PrivateInputPersisted']
 assert all(job[k] for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and job['active_processes_last_observed']==0 and not job['errors']
 stdout=Path(check(inv['Stdout'])).read_bytes();stderr=Path(check(inv['Stderr'])).read_bytes()
 if expected_exit==0:
  native=json.loads(stdout);assert native['status']=='SCHEMA25_COMMITTED_ORIGINAL_BUSINESS_ROWS_UNCHANGED' and native['committed'] and native['binding']==b
  assert native['after_rows_sha256']==info['typed_rows_sha256'] and native['target_schema_sha256']==info['schema_sha256']
  assert native['abandonment_performed'] is False and native['financial_closed'] is False and native['provider_requests'] is None
  assert dt.datetime.fromisoformat(g['issued_utc'].replace('Z','+00:00'))<=dt.datetime.fromisoformat(native['finished_at'].replace('Z','+00:00'))<dt.datetime.fromisoformat(g['expires_utc'].replace('Z','+00:00'))
 else:assert b'AUTHORITY_MIGRATION_GRANT_ALREADY_USED' in stderr
 brokers.append({'label':label,'invocation_ref':ref(H/label/'invocation.json'),'owned_pid':res['owned_child_pid'],'actual_exit':res['actual_exit'],'job_closed':True,'stdout_ref':inv['Stdout'],'stderr_ref':inv['Stderr']})
assert result['synthetic'] and result['formal'] is False and result['production_db_writes']==result['provider_requests']==0
assert result['inner_native_job_id_independently_observed'] is False
obs=read(check(s['observation_ref']));assert obs['job_binding_id']==s['job_binding_id'] and obs['result']['actual_exit'] is None and obs['held_job_handle']
report={'state':'ACTUAL_POSITIVE_AND_NONCE_REPLAY_RETAINED_FIXTURE_VERIFIED_OUTER_CLOSURE_PENDING','snapshot_ref':ref(S),'sqlite':info,'new_empty_tables':sorted(new),'before_tables':88,'before_rows':249,'old_business_rows_unchanged':True,'schema_migrations_added_rows':1,'ids':ids,'brokers':brokers,'replay_state_evidence':'Fresh full SQLite after actual replay equals pre-replay after.rows.json byte-typed row digest inventory and target schema.','inner_native_job_id_independently_observed':False,'outer_test_exit_zero_confirmed':False,'scope':'Read-only isolated synthetic fixture; exact signed grant public verification in grant-review-v3. No product DB/private key access or authority action.','formal_increment':0,'formal_accepted':'0/42','parents_open':22,'at':dt.datetime.now(dt.timezone.utc).isoformat()}
save('TERMINAL-report.json',report);print(json.dumps({'state':report['state'],'report_ref':ref(E/'TERMINAL-report.json')}))
