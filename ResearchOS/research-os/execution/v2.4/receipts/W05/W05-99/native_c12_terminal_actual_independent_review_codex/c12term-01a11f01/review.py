from pathlib import Path
import hashlib,importlib.util,json,re
O=Path(__file__).resolve().parent;B=O.parent.parent
def load(p):return json.loads(Path(p).read_bytes())
def norm(ref):return dict(path=str(Path(ref['path']).resolve()),sha256=ref['sha256'].removeprefix('sha256:'),bytes=ref['bytes'])
def same(a,b):return norm(a)==norm(b)
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
checks=[];inputs={};guards=[]
def check(name,value):checks.append(dict(name=name,passed=bool(value)))
def record(ref):
 ref=norm(ref);key=ref['path'].casefold();check('pin:'+ref['path'],pin(ref['path'])==ref);assert key not in inputs or inputs[key]==ref;inputs[key]=ref
def save(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
record(load(O/'initial-pin.json'));record(load(O/'terminal-tool-io.pin.json'));record(load(O/'partial-tool-io.pin.json'))
packet=load(O/'packet-pins.json');detail=load(O/'detail-pins.json');actions=load(O/'public-action-pins.json')
for row in packet+detail+actions:record(row['original']);check('captured copy equals pinned original:'+row['copy'],Path(row['copy']).read_bytes()==Path(row['original']['path']).read_bytes())
outer=load(O/'serve-outer.input.json');oi=load(packet[0]['copy']);ctl=load(packet[1]['copy']);snap=load(packet[2]['copy']);request=load(packet[3]['copy']);ni=load(O/'test.invocation.input.json');record(ctl['invocation_ref'])
lookup={Path(row['copy']).name:row for row in detail};act={Path(row['copy']).name:row for row in actions}
ins=load(lookup['inspection-positive.json']['copy']);before=load(lookup['before.rows.json']['copy']);fixture=load(lookup['fixture.public.json']['copy']);ready=load(lookup['06-fixture-retained.ready.json']['copy']);observed=load(lookup['observe-9778385afad54982abf292ebd814024b.response.json']['copy']);cfg=load(lookup['controller.public.config.json']['copy']);hc=load(lookup['native-harness.public.config.json']['copy'])
check('outer controller native invocation chain',same(outer['invocation_ref'],packet[0]['original']) and same(outer['controller_closed_ref'],packet[1]['original']) and same(ctl['invocation_ref'],pin(O/'test.invocation.input.json')) is False)
# Copy locations differ; bind original paths by content pin explicitly.
checks.pop()
check('outer controller invocation chain',same(outer['invocation_ref'],packet[0]['original']) and same(outer['controller_closed_ref'],packet[1]['original']))
check('native original invocation exact',norm(ctl['invocation_ref'])['sha256']=='075c8ab013bd3df5c02d02c98c398f7853a3b05fb48da65c237c7b9d5851e94b' and ctl['invocation_ref']['bytes']==3762 and hashlib.sha256((O/'test.invocation.input.json').read_bytes()).hexdigest()==norm(ctl['invocation_ref'])['sha256'])
check('same case and held job binding',ctl['case_id']==snap['case_id']=='t12cl149d6f49321' and ctl['job_binding_id']==ni['job_binding_id']==observed['job_binding_id']==snap['job_binding_id'])
job_results={'outer-controller-child':oi['result'],'native-harness':ni['result']}
for name in ('sign-release.receipt.json','sign-grant.receipt.json'):
 receipt=load(act[name]['copy']);job_results[name]=receipt['result'];check(name+' actual success',receipt['success'] is True and receipt['error_type'] is None and receipt['result']['actual_exit']==0)
def job(name,r):
 c=r['job_cleanup'];check('Job exited idle handles closed:'+name,all(c[k] is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed')) and c['active_processes_last_observed']==0 and c['errors']==[])
 check('no forced termination or owned timeout:'+name,r['timed_out'] is False and r['error'] is None and c['termination_requested'] is False and c['termination_succeeded'] is None and c['termination_code_requested'] is None and c['unassigned_suspended_child_termination_requested'] is False)
 check('exact uint64 FILETIME:'+name,type(r['creation_time_100ns']) is int and r['creation_time_100ns']>2**53)
for name,r in job_results.items():job(name,r)
check('failed exit recorded at both owned levels',oi['actual_native_exit']==oi['result']['actual_exit']==ni['result']['actual_exit']==1)
check('exact Native PID and FILETIME match held live observation',ni['result']['owned_child_pid']==observed['result']['owned_child_pid']==41120 and ni['result']['creation_time_100ns']==observed['result']['creation_time_100ns']==134359959252875798)
check('exact outer PID and FILETIME',oi['result']['owned_child_pid']==40900 and oi['result']['creation_time_100ns']==134359959132671515)
for source_file,expected in ((Path(packet[0]['copy']),134359959132671515),(O/'test.invocation.input.json',134359959252875798),(Path(lookup['observe-9778385afad54982abf292ebd814024b.response.json']['copy']),134359959252875798)):
 raw=source_file.read_text(encoding='utf-8');matches=re.findall(r'"creation_time_100ns"\s*:\s*(\d+)',raw);check('raw decimal FILETIME preserved:'+source_file.name,str(expected) in matches)
check('controller and outer closure flags',ctl['job_and_guards_closed'] is True and ctl['worker_still_alive'] is False and ctl['harness_test_exit_zero'] is False and ctl['error_type'] is None and ctl['worker_error_type'] is None and outer['owned_outer_job_closed'] is True)
def audit_guard(label,g):
 entries=g.get('entries',[]);check('guard closed:'+label,g.get('verification')=='PASSED' and g.get('closed') is True and g.get('retained_handles_count')==0 and g.get('errors')==[] and g.get('failure') is None)
 check('all guard entries verified closed:'+label,all(e['verified'] and e['final_path_match'] and e['closed'] for e in entries))
 guards.append(dict(label=label,entries=len(entries),closed=g.get('closed'),retained_handles=g.get('retained_handles_count'),share_mode=g.get('share_mode')))
audit_guard('controller',ctl['source_guard_cleanup'])
for name in ('serve-outer-source-guard.cleanup.actual.json','serve-child-source-guard.cleanup.actual.json'):
 data=load(lookup[name]['copy'])
 for index,g in enumerate(data.get('guards',[data])):audit_guard(name+':'+str(index),g)
audit_guard('retained-snapshot',snap['snapshot_guard_cleanup']);audit_guard('SQL-inspection-reader',ins['reader_guard_cleanup']);audit_guard('SQL-inspection-database-share',ins['database_guard_cleanup'])
for name,row in act.items():
 data=load(row['copy'])
 for k in ('source_guard_cleanup','key_metadata_guard_cleanup'):
  if k in data:audit_guard(name+':'+k,data[k])
for name in ('initial-guard.closed.json','packet-guard.closed.json','detail-guard.closed.json','public-action-guard.closed.json'):audit_guard('reviewer:'+name,load(O/name))
expected={norm(ref)['path'].casefold():norm(ref) for ref in cfg['FrozenInputs']};actual={norm(e)['path'].casefold():norm(e) for e in ctl['source_guard_cleanup']['entries']}
check('controller actual guard covers4185 frozen inputs',len(expected)==4185 and all(actual.get(k)==v for k,v in expected.items()))
outerexpected={norm(ref)['path'].casefold():norm(ref) for ref in outer['frozen_source_refs']}
for name in ('serve-outer-source-guard.cleanup.actual.json','serve-child-source-guard.cleanup.actual.json'):
 data=load(lookup[name]['copy']);actual={norm(e)['path'].casefold():norm(e) for g in data.get('guards',[data]) for e in g['entries']};check('serve guard4187 exact coverage:'+name,len(outerexpected)==4187 and actual==outerexpected)
stdout=Path(lookup['test.stdout.raw']['copy']).read_text(encoding='utf-8');source=Path(lookup['native_migration_authority_harness_windows_test.go']['copy']).read_text(encoding='utf-8')
check('one Native test FAIL with two deadline reports','--- FAIL: TestNativeMigrationAuthorityHarness (1440.06s)' in stdout and stdout.count('Root review window ended context deadline exceeded')==2 and ':630:' in stdout and ':472:' in stdout and stdout.rstrip().endswith('FAIL'))
check('main20min and fresh cleanup4min Source unchanged','context.WithTimeout(context.Background(), 20*time.Minute)' in source and 'func nativeHarnessCleanupReviewContext(_ context.Context)' in source and 'return context.WithTimeout(context.Background(), 4*time.Minute)' in source)
lines=source.splitlines();check('line630 waits grant publication', '02-grant.approval.json' in lines[629] and 'grant-signed-and-invoke' in lines[629]);check('line472 waits explicit fixture release','06-release-fixture.approval.json' in lines[471] and 'cleanupCtx' in lines[471])
check('explicit fixture release absent at controller close',ctl['fixture_release_approval_exists'] is False)
check('retained record says failed release required',ready['test_failed'] is True and ready['release_required'] is True and snap['phase']=='fixture-retained')
check('SQL whole fixture snapshot completed',ins['fixture_read_complete'] and ins['whole_row_schema_review_complete'] and ins['transaction_snapshot_complete'] and ins['data_version_before']==ins['data_version_after']==2 and ins['primary_and_WAL_bytes_unchanged'])
check('all87 baseline table digests identical',len(before)==87 and ins['typed_rows']==before)
check('before exact hash equals inspected typed rows',same(ins['before_ref'],lookup['before.rows.json']['original']) and ins['typed_rows_sha256']==ins['before_ref']['sha256']=='sha256:c2963ebce40b597033c9fced769a580562309acf60df0ce4afe890a31f4795bf')
check('schema baseline unchanged versions1to23',ins['schema_versions']==list(range(1,24)) and ins['sqlite_schema_sha256']==fixture['schema_sha256'] and ins['schema_object_count']==296)
check('migration not accepted by inspection',ins['expected_state_matches'] is False and ins['after_ref'] is None and ins['expected_target_schema_sha256']!=ins['sqlite_schema_sha256'])
check('only target-specific migration invariant false',[name for name,value in ins['original_table_invariants'].items() if value is False]==['schema_migrations'])
check('same native fixture identity',ins['native_ids']==snap['measured_native_ids'] and ins['database_ref']['path']==fixture['database']==ready['database'])
check('inspection preserves read share limitations',ins['immutable_database_claim'] is False and ins['database_share_mode']=='READ_WRITE_SHARED_DELETE_DENIED' and ins['private_credentials_recorded'] is False and ins['private_raw_rows_recorded'] is False and ins['database_guard_cleanup']['existing_SQLite_writer_handles_permitted'] is True)
api=(O/'root-api-source.input.py').read_text(encoding='utf-8');record(load(O/'root-api-source.pin.json'));check('positive invariant expects one added migration', 'len(current["row_digests"])==len(old["row_digests"])+1' in api and 'versions==list(range(1,25))' in api)
term=load(O/'terminal-tool-io.input.json')['entries'];partial=load(O/'partial-tool-io.input.json');result=term['root_c12_serve_terminal_poll'];failure=term['root_c12_approval_release_fixture_actual']
check('original Root terminal shell/Python1',result['chunk_id']=='9dbcf2' and result['exit_code']==1 and 'ROOT_PYTHON_EXIT=1' in result['output'])
check('failure923 one refused NH1 invocation',failure['chunk_id']=='2c7cf4' and failure['exit_code']==1 and 'ROOT_PYTHON_EXIT=1' in failure['output'] and 'controller lifecycle already terminal' in failure['output'])
check('release request expected unchanged-failed',request['ExpectedFixtureState']=='unchanged-failed' and same(request['InspectionReceipt'],lookup['inspection-positive.json']['original']))
check('no grant publication Apply replay acceptance',partial['grantPublished'] is False and partial['migrationApplyNotStarted'] is True and partial['partialAttemptNotAccepted'] is True and ctl['fixture_release_approval_exists'] is False)
archive_dir=B/'native_grant_archive_actual_independent_review_codex/gpa-actual-01a11f01';ahref=dict(path=str(archive_dir/'HDF.json'),sha256='bed8ec295ab46144527283d5cbc688af46dc0dc63e206e75b90c8cb5b9113604',bytes=5433);record(ahref);ah=load(archive_dir/'HDF.json');record(ah['manifest_ref']);am=load(ah['manifest_ref']['path'])
for ref in am['members']:record(ref)
check('accepted61 archive reused only',ah['status']=='FULL_TEMP_PIN_CLOSURE_ACCEPTED_ARCHIVE_COMPONENT_ONLY' and ah['identical_raw_pairs']==61 and ah['Native_migration_pass'] is False and ah['STOP'] and ah['FINAL'])
prior_binding=load(B/'native_grant_bounded_read_independent_review_codex/gbr-review-01a11f01/resource-gate-binding.json');check('canonical bound at closure to acceptedCP364',{Path(r['path']).stem:norm(r) for r in outer['canonical_unchanged_refs']}=={k:norm(v) for k,v in prior_binding['canonical_refs'].items()} and prior_binding['checkpoint_revision']==364)
presence=dict(database_path=ins['database_ref']['path'],database_exists=Path(ins['database_ref']['path']).exists(),fixture_root=fixture['root'],fixture_root_exists=Path(fixture['root']).exists(),grant_approval_exists=(Path(hc['OutputDirectory'])/'02-grant.approval.json').exists(),fixture_release_approval_exists=(Path(hc['OutputDirectory'])/'06-release-fixture.approval.json').exists(),operation='Path.exists only; no database opened')
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85';s=importlib.util.spec_from_file_location('g',G);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);guard=m.SourceReadGuard()
try:guard.acquire(list(inputs.values()))
finally:cleanup=guard.close()
audit_guard('reviewer-final',cleanup);save('reviewer-guard.final.json',cleanup);save('input-pins.json',list(inputs.values()));save('checks.json',checks);save('guard-summary.json',guards);save('fixture-presence-observation.json',presence)
save('failure-disposition.json',dict(existing_failure923=dict(chunk='2c7cf4',outer_shell_exit=1,python_exit=1,product_native_exit=None,reason='NH1 rejected already terminal lifecycle',invocation_count=1),existing_failure924=dict(original_start_chunk='86638d',original_session_id=95590,terminal_chunk='9dbcf2',outer_shell_exit=1,python_exit=1,outer_controller_child_exit=1,primary_native_exit=1,primary_pid=41120,primary_creation_time_100ns_decimal='134359959252875798',original_native_invocation_ref=ctl['invocation_ref'],invocation_count=1,two_deadline_logs_not_two_invocations=True),new_review_failures=[],counter_reset=False))
save('review.json',dict(status='FAILED_ACTUAL_CLOSURE_CONFIRMED_NATIVE_CASE_NOT_ACCEPTED',checks=len(checks),failed_checks=sum(not x['passed'] for x in checks),jobs={name:dict(actual_exit=r['actual_exit'],pid=r['owned_child_pid'],creation_time_100ns_decimal=str(r['creation_time_100ns']),timed_out=r['timed_out'],termination_requested=r['job_cleanup']['termination_requested'],active_processes_last_observed=r['job_cleanup']['active_processes_last_observed'],handles_closed=r['job_cleanup']['handles_closed']) for name,r in job_results.items()},Native_test_acceptance=False,termination='natural main context deadline then independent cleanup context deadline; no owned Job termination requested',explicit_fixture_release=False,SQL_state='UNCHANGED_BASELINE_23',SQL_tables_identical=87,archive_handoff_ref=ahref,archive_accepted=True,canonical_binding_revision=364,current_canonical_revalidation_required=False,current_canonical_read_or_locked=False,private_references_followed=False,new_SQL_or_Native_or_helper_execution=False,full20_to24='OPEN',formal_acceptance=False,new_failure_ordinals=[],existing_failure_ordinals=[923,924]))
print(json.dumps(dict(checks=len(checks),failed=[x['name'] for x in checks if not x['passed']],inputs=len(inputs),status='FAILED_ACTUAL_CLOSURE_CONFIRMED_NATIVE_CASE_NOT_ACCEPTED',primary_native_exit=1,guard_closed=cleanup['closed'],new_failure_ordinals=[])))
