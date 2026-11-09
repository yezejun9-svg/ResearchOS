import json,hashlib,re
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent;R=B.parents[4]
A=B/'integration_codex/native-positive-failed-root-release-00ebc1bba04e4d4f'
S=B/'integration_codex/native-positive-serve-v2-root-75dc3afca9b34a99'
C=B/'integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13'
W=C/'controller-runtime'
P=B/'integration_codex/native-positive-root-api-v4-7e971c417d4d4d2a'
F=B/'integration_codex/native-migration-positive-root-73df768bc70b4f64/facts'
P2=B/'integration_codex/native-positive-root-api-v2-d4491126fbd148f8'
P3=B/'integration_codex/native-positive-root-api-v3-61a10e989dfd4c19'
E=B/'integration_codex/root-inspection-diagnostic-821-sharing-a51cfb0f/failure-origin.821.json'
PREV=B/'native_positive_root_api_v4_independent_review_codex/1a11dd12cabc1d69f8a4f37d8'
refs={};historical={};guards=[]
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def norm(r):return dict(path=str(Path(r['path'])),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes'])
inspection=json.loads((P/'inspection-positive.json').read_bytes())
dbkeys={str(Path(e['path'])).casefold() for e in inspection['database_guard_cleanup']['entries']}
def add(r):
 r=norm(r);k=r['path'].casefold();target=historical if k in dbkeys else refs
 assert k not in target or target[k]==r,('conflicting pin',r['path'])
 target[k]=r
def walk(v):
 if isinstance(v,dict):
  if all(k in v for k in ('path','sha256','bytes')):add(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
def read(p):
 add(pin(p));d=json.loads(Path(p).read_bytes());walk(d);return d
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
for folder in (A,S,W,P,F,P2,P3):
 for p in folder.iterdir():
  if p.is_file():
   if p.suffix=='.json':read(p)
   else:add(pin(p))
read(E)
for r in json.loads((PREV/'evidence.json').read_bytes())['base_refs']:add(r)
add(pin(PREV/'HDF.json'));add(pin(PREV/'MF.json'))
i=read(P/'inspection-positive.json')
assert pin(P/'inspection-positive.json')['sha256']=='a795cb5b8f6d28469783464bfff1850df8721147374ae01a876708b0efece4f0'
assert len(i['typed_rows'])==87 and sum(len(v['row_digests']) for v in i['typed_rows'].values())==280
assert i['schema_object_count']==296 and i['schema_versions']==list(range(1,24))
assert i['fixture_read_complete'] and i['whole_row_schema_review_complete'] and i['transaction_snapshot_complete']
assert not i['private_credentials_recorded'] and not i['private_raw_rows_recorded'] and not i['formal_acceptance']
assert i['early_failure_retained'] and not i['expected_baseline_available'] and not i['expected_state_matches']
assert i['before_ref'] is None and i['after_ref'] is None and i['expected_target_schema_sha256'] is None
assert i['data_version_before']==i['data_version_after']==2 and i['primary_and_WAL_bytes_unchanged']
assert not i['immutable_database_claim']
for name,t in i['typed_rows'].items():
 assert set(t)=={'columns','row_digests'} and all(type(v) is str for v in t['columns'])
 assert t['row_digests']==sorted(t['row_digests'])
 assert all(re.fullmatch('sha256:[0-9a-f]{64}',d) for d in t['row_digests'])
def canon(v):
 if isinstance(v,str):v.encode('utf-16-be');return v
 if isinstance(v,list):return [canon(x) for x in v]
 assert isinstance(v,dict)
 return {k:canon(v[k]) for k in sorted(v,key=lambda k:k.encode('utf-16-be'))}
typed_hash='sha256:'+hashlib.sha256(json.dumps(canon(i['typed_rows']),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
assert typed_hash==i['typed_rows_sha256']
def guard(name,g,count=None,live=False):
 assert g['closed'] and not g['errors'] and g['retained_handles_count']==0
 assert g['verification']=='PASSED' and not g['failure']
 assert all(e['verified'] and e['final_path_match'] and e['closed'] for e in g['entries'])
 if count is not None:assert len(g['entries'])==count
 assert g['share_mode']==('FILE_SHARE_READ_WRITE_DELETE_DENIED' if live else 'FILE_SHARE_READ_ONLY')
 guards.append(dict(name=name,count=len(g['entries']),live_database=live,closed=True,retained=0))
for folder in (S,P,P2,P3):
 for p in folder.glob('*guard*cleanup*.json'):
  data=read(p)
  for j,g in enumerate(data.get('guards',[])):guard(str(p)+f'#{j}',g,4085)
outer=read(S/'serve-outer.invocation.json');outerclosed=read(S/'serve-outer.closed.json')
ctrl=read(W/'controller.closed.json');test=read(W/'test.invocation.json')
def job(r):
 assert r['actual_exit']==1 and r['error'] is None and not r['timed_out']
 j=r['job_cleanup']
 assert not j['errors'] and j['active_processes_last_observed']==0 and not j['termination_requested']
 assert all(j[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'))
job(outer['result']);job(test['result'])
assert outer['result']['owned_child_pid']==57288 and test['result']['owned_child_pid']==53352
assert test['result']['creation_time_100ns']==134359747687806045
assert ctrl['job_binding_id']==test['job_binding_id']=='1583058f817849358683646372bc85bd'
assert ctrl['job_and_guards_closed'] and not ctrl['harness_test_exit_zero'] and not ctrl['worker_still_alive']
assert ctrl['error_type'] is None and ctrl['worker_error_type'] is None and ctrl['fixture_release_approval_exists']
assert outerclosed['owned_outer_job_closed'] and not outerclosed['formal_acceptance']
guard('controller lifetime',ctrl['source_guard_cleanup'],4084)
guard('SQL source reader',i['reader_guard_cleanup'],156)
guard('SQL live DB',i['database_guard_cleanup'],2,True)
assert set(Path(e['path']).name for e in i['reader_guard_cleanup']['entries'])>={'_sqlite3.pyd','sqlite3.dll','dbapi2.py','dbapi2.cpython-314.pyc'}
snap=read(i['snapshot_ref']['path'])
guard('snapshot',snap['snapshot_guard_cleanup'],2)
assert snap['measured_native_ids']==i['native_ids'] and snap['job_binding_id']==ctrl['job_binding_id']
assert snap['payload_ref'] is None and snap['ready_ref'] is None and snap['signed_destination'] is None
for p in W.glob('observe-*.response.json'):
 o=read(p)
 assert o['job_binding_id']==ctrl['job_binding_id'] and o['held_job_handle'] and o['held_primary_handle']
 assert o['result']['owned_child_pid']==53352 and o['result']['creation_time_100ns']==test['result']['creation_time_100ns']
 assert o['phase']=='fixture-retained'
release=read(W/'fixture-release.receipt.json');approval=read(A/'root.fixture-release.approval.json');decision=read(A/'root.concrete-cleanup.decision.json')
guard('fixture release',release['source_guard_cleanup'],5)
assert norm(release['approval_ref'])==pin(A/'root.fixture-release.approval.json')
assert norm(approval['InspectionReceipt'])==pin(P/'inspection-positive.json')
assert approval['Snapshot']==i['snapshot_ref'] and norm(decision['fixture_inspection_ref'])==pin(P/'inspection-positive.json')
assert decision['decision']=='RELEASE_SYNTHETIC_FIXTURE_AFTER_COMPLETE_READ_ONLY_INSPECTION_PRESERVE_FAILED_ATTEMPT'
assert read(F/'06-release-fixture.approval.json')=={'Action':'release-fixture'}
assert sorted(p.name for p in F.iterdir())==['06-fixture-retained.ready.json','06-release-fixture.approval.json']
cfg=read(C/'controller.public.config.json');hc=read(cfg['HarnessConfig']['path'])
root=Path(hc['RootProgram']['path']).parent
assert not any((root/n).exists() for n in ('recovery-release.json','current-schema23-to24-grant.json','consumed-schema23-to24-grants'))
stdout=(W/'test.stdout.raw').read_text()
assert '--- FAIL: TestNativeMigrationAuthorityHarness' in stdout and 'native_migration_authority_harness_windows_test.go:468: INVALID_REQUEST: credential TTL must be at most 15 minutes' in stdout
assert '\nPASS' not in stdout
failure=read(A/'failure-origin.820.closed-qualified.json')
assert failure['actual_exits']==dict(outer=1,python=1,native_child_controller=1,harness_native=1)
assert failure['observed_ordinal']==820 and not failure['counter_reset'] and failure['signatures_created']==failure['migration_grants_published']==0
io=read(A/'original-tool-io.json')['operations']
assert io['root_native_positive_serve_v2_actual_completion']['exit_code']==1
assert 'ROOT_PYTHON_EXIT=1' in io['root_native_positive_serve_v2_actual_completion']['output']
for key in ('root_native_positive_failed_snapshot_completion','root_native_positive_failed_inspection_v4_result','root_native_positive_failed_release_actual_completion'):
 assert io[key]['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in io[key]['output']
assert io['root_native_positive_failed_inspection_result']['exit_code']==1 and 'ROOT_PYTHON_EXIT=1' in io['root_native_positive_failed_inspection_result']['output']
assert 'BrokenPipeError: [Errno 32] CreateFileW' in io['root_native_positive_failed_inspection_result']['output']
assert len(historical)==2 and all(not Path(r['path']).exists() for r in historical.values())
for r in outerclosed['canonical_unchanged_refs']:assert pin(r['path'])==norm(r)
assert json.loads((R/'execution/v2.4/checkpoint.json').read_bytes())['revision']==357
for r in refs.values():assert pin(r['path'])==r,('drift',r['path'])
e=save('evidence.json',dict(base_refs=list(refs.values()),historical_deleted_fixture_refs=list(historical.values()),historical_DB_refs_not_required_current=True,guards=guards,outer_job=outer['result'],Go_job=test['result'],job_binding_id=ctrl['job_binding_id'],inspection=dict(schema_version=23,schema_objects=296,tables=87,row_digests=280,typed_rows_hash_recomputed=typed_hash,schema_hash=i['sqlite_schema_sha256'],expected_baseline_available=False,expected_state_matches=False,raw_private_rows_recorded=False,data_version_before=2,data_version_after=2,primary_and_initial_WAL_bytes_unchanged=True,SQL_reader_closed=True,live_DB_guard_closed=True),Root_release_after_inspection=True,failed_execution_closed=True,actual_exits=failure['actual_exits'],native_case_pass=False,exact_error=failure['exact_native_error'],source_guards_closed=True,diagnostics_preserved=[820,821],new_mechanical_errors=0,canonical_unchanged_refs=outerclosed['canonical_unchanged_refs'],reviewer_SQL_executions=0,reviewer_target_executions=0,authority='NONE',formal_acceptance=False))
print(json.dumps(dict(evidence_ref=e,base_refs=len(refs),historical_deleted_refs=len(historical),guards=len(guards),tables=87,rows=280,jobs_closed=2,Go_exit=1,drift=0,new_mechanical_errors=0)))

