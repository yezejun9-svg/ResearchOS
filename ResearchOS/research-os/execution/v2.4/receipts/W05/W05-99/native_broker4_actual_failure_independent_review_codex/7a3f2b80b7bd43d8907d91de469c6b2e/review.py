import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,importlib.util,traceback,datetime
P=pathlib.Path
O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
C=B/'integration_codex/native-broker4-controller-config-root-1791513411000';S=B/'integration_codex/native-broker4-positive-serve-root-1791513411000';A=B/'integration_codex/native-broker4-positive-root-api-1791513411000'
checks=[];guard=None
def pin(p):
 p=P(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def norm(r):return {'path':str(P(r['path'])),'sha256':r['sha256'].removeprefix('sha256:'),'bytes':r['bytes']}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def check(n,v,d=None):checks.append({'check':n,'passed':bool(v),'detail':d})
def good(g):return g['verification']=='PASSED' and g['closed'] is True and g['retained_handles_count']==0 and g['failure'] is None and g['errors']==[] and all(x['verified'] and x['final_path_match'] and x['closed'] for x in g['entries'])
def main():
 global guard
 cfg=json.loads((C/'controller.public.config.json').read_bytes());hc=json.loads((C/'native-harness.public.config.json').read_bytes())
 go=P(hc['BuildRoot'])/'internal/domain/native_migration_authority_harness_windows_test.go'
 factory=P(hc['BuildRoot'])/'internal/domain/backup_prepared_abandonment_upgrade_windows_test.go'
 paths=[C/'controller.public.config.json',C/'native-harness.public.config.json',P(__file__),go,factory]
 for d in [C/'controller-runtime',C/'harness-facts',S,A]:paths.extend(p for p in d.rglob('*') if p.is_file())
 paths.extend(P(cfg[k]['path']) for k in ['ControllerSource','SourceReadGuard','ObservedOwnedHelper','OriginalOwnedHelper'])
 paths.extend([P(hc['BrokerSource']['path']),P(hc['PrivateStdinHelper']['path'])])
 paths=sorted(set(paths),key=str);refs=[pin(p) for p in paths]
 outer0=json.loads((S/'serve-outer.closed.json').read_bytes());canon_before=[pin(r['path']) for r in outer0['canonical_unchanged_refs']]
 gr=norm(cfg['SourceReadGuard']);assert pin(gr['path'])==gr and gr['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
 spec=importlib.util.spec_from_file_location('independent_t10_closed_guard',gr['path']);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm)
 guard=gm.SourceReadGuard();guard.acquire(refs)
 def raw(p):return guard.get_buffer(str(P(p)))
 def read(p):return json.loads(raw(p))
 def verified(r):return hashlib.sha256(raw(r['path'])).hexdigest()==r['sha256'].removeprefix('sha256:') and len(raw(r['path']))==r['bytes']
 save('input-pins.json',refs)
 fixed=[(C/'controller.public.config.json','48c06dc2c88326a98cd785b364d6daf5fad363292a7a4f97fd209938d54273b2',1178613),(C/'controller-runtime/controller.closed.json','062393463cc93a22669effe1200f26e15d8f4b0575200a3ac49826770ff3307b',1232140),(S/'serve-outer.closed.json','24ede9579ad21a82382c5b4a3edac8b3fd474005104a92464511e75de89cee5e',1146037),(S/'original-root-terminal-tool-io.json','42600e84cbebe3619dc120dd51de487acdf8e0813a25f8a1a53e6d04f24a5096',860),(go,'972166b2744d1048dc747e8a5b4991cd0b06cbbdc8a523c90fef12e27e02e0e9',35845)]
 for p,h,n in fixed:check('fixed-anchor:'+p.name,hashlib.sha256(raw(p)).hexdigest()==h and len(raw(p))==n)
 inv=read(C/'controller-runtime/test.invocation.json');outer=read(S/'serve-outer.invocation.json');ctl=read(C/'controller-runtime/controller.closed.json');oc=read(S/'serve-outer.closed.json')
 terminal=read(S/'original-root-terminal-tool-io.json');t=terminal['output'];t=json.loads(t) if isinstance(t,str) else t
 check('Root-original-terminal892-exit1',terminal['input']['session_id']==51425 and t['chunk_id']=='338949' and t['exit_code']==1 and 'ROOT_PYTHON_EXIT=1' in t['output'] and terminal['failure_ordinal']==892)
 check('terminal-binds-exact-outerclosed',verified(json.loads(t['output'].splitlines()[0])['outer_closed_ref']))
 jobs=[]
 records=[('Go-harness',inv['result'],42244,134359866411023123,1),('outer-Python',outer['result'],79092,134359866284665514,1)]
 for name,r,pid,ft,ex in records:
  j=r['job_cleanup']
  check(name+'-actual-identity-exit',r['owned_child_pid']==pid and type(r['creation_time_100ns']) is int and r['creation_time_100ns']==ft and r['actual_exit']==ex and r['resumed'])
  check(name+'-not-timeout-or-termination',r['timed_out'] is False and r['error'] is None and j['termination_requested'] is False and j['unassigned_suspended_child_termination_requested'] is False)
  check(name+'-closed-job',all(j[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and not j['errors'])
  jobs.append({'name':name,'pid':pid,'creation_time_100ns_decimal':str(ft),'actual_exit':ex,'elapsed_seconds':r['elapsed_seconds'],'timed_out':r['timed_out'],'job_cleanup':j})
 for name,d in [('Go',inv),('outer',outer)]:
  for k in ['config_ref','stdout_ref','stderr_ref']:check(name+'-raw-binding:'+k,verified(d[k]))
 check('Go-lifetime-about20min',1200<=inv['result']['elapsed_seconds']<1260 and outer['result']['elapsed_seconds']<1320)
 check('controller-closed-failed-no-fixture-release',ctl['job_and_guards_closed'] and not ctl['harness_test_exit_zero'] and not ctl['worker_still_alive'] and ctl['fixture_release_approval_exists'] is False and ctl['error_type'] is None and ctl['worker_error_type'] is None and verified(ctl['invocation_ref']))
 check('outer-completely-closed',oc['owned_outer_job_closed'] and verified(oc['controller_closed_ref']) and verified(oc['invocation_ref']) and oc['formal_acceptance'] is False)
 stdout=raw(C/'controller-runtime/test.stdout.raw').decode();gos=raw(go).decode()
 check('same-invocation-two-context-failures',stdout.count('Root review window ended context deadline exceeded')==2 and 'windows_test.go:626:' in stdout and 'windows_test.go:468:' in stdout and stdout.count('--- FAIL: TestNativeMigrationAuthorityHarness')==1)
 check('20minute-shared-context-source','context.WithTimeout(context.Background(), 20*time.Minute)' in gos and 'nativeHarnessWait(t, ctx, filepath.Join(cfg.OutputDirectory, "02-grant.approval.json"), "grant-signed-and-invoke")' in gos and 'nativeHarnessWait(t, ctx, filepath.Join(cfg.OutputDirectory, "06-release-fixture.approval.json"), "release-fixture")' in gos)
 check('cleanup-register-after-tempdirs','opt, f, run := preparedUpgradePublicFixture(t)' in gos and gos.index('opt, f, run := preparedUpgradePublicFixture(t)')<gos.index('t.Cleanup(func() {') and '"06-fixture-retained.ready.json"' in gos)
 ctls=raw(cfg['ControllerSource']['path']).decode()
 check('enclosing-deadlines-not-triggered','"-test.timeout=25m"' in ctls and 'env, stdout, stderr, 1260,' in ctls and inv['result']['timed_out'] is False)
 ready=read(C/'harness-facts/06-fixture-retained.ready.json');fixture=read(C/'harness-facts/fixture.public.json')
 check('retained-ready-is-failed-historical-marker',ready['test_failed'] and ready['release_required'] and ready['database']==fixture['database'])
 snapshot=read(C/'controller-runtime/review-snapshot-grant-966f1d5d2bde46e88a30d1ec34e1e628.json');grant=read(C/'harness-facts/02-grant.payload.json');grready=read(C/'harness-facts/02-grant.ready.json')
 ids=snapshot['measured_native_ids']
 check('historical-root-db-identities-match-grant',ids=={'root':'ee413c31:00040000:00118352','database':'ee413c31:00040000:00118353'} and ids['root']==grant['binding']['root_identity'] and ids['database']==grant['binding']['database_identity'] and grant['binding']['database']==fixture['database'] and grant['binding']['root']==fixture['root'])
 check('grant-issued-and-expiry-exact',grant['issued_utc']=='2026-10-09T02:38:36.7336808Z' and grant['expires_utc']==grready['expires_utc']=='2026-10-09T02:42:36.7336808Z')
 check('grant-expired-now',datetime.datetime.now(datetime.timezone.utc)>datetime.datetime(2026,10,9,2,42,37,tzinfo=datetime.timezone.utc))
 sg=read(C/'controller-runtime/sign-grant.receipt.json');sc=read(C/'controller-runtime/sign-grant.consumed.json')
 check('one-grant-sign-success-not-published',sc['one_attempt'] is True and sg['success'] is True and sg['sign_kind']=='migration-grant' and sg['phase']=='grant' and sg['result']['actual_exit']==0 and sg['harness_approval_published'] is False and sg['payload_ref']==sc['payload_ref'] and sg['approval_ref']==sc['approval_ref'] and verified(sg['payload_ref']) and verified(sg['approval_ref']))
 sr=read(C/'controller-runtime/sign-release.receipt.json');pub=read(C/'controller-runtime/publish-release.receipt.json')
 check('initial-release-distinct-sign-and-publication',sr['success'] is True and sr['phase']=='release' and verified(pub['approval_ref']) and verified(pub['published_ref']))
 for name,d in [('sign-release',sr),('sign-grant',sg),('backup-rehearsal',read(C/'harness-facts/00-rehearsal/invocation.json'))]:
  r=d['Result'] if name=='backup-rehearsal' else d['result'];j=r['job_cleanup']
  check(name+'-successful-owned-job-closed',r['actual_exit']==0 and r['timed_out'] is False and r['error'] is None and all(j[k] is True for k in ['assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and not j['errors'])
  jobs.append({'name':name,'pid':r['owned_child_pid'],'creation_time_100ns_decimal':str(r['creation_time_100ns']),'actual_exit':r['actual_exit'],'job_cleanup':j,'observation_scope':'historical receipt, no new process action'})
 save('historical-owned-jobs.json',jobs)
 absent_names=['02-grant.approval.json','03-native-invocation','04-after.ready.json','after.rows.json','06-release-fixture.approval.json']
 absence={n:not (C/'harness-facts'/n).exists() for n in absent_names}
 absence['publish-grant.receipt.json']=not (C/'controller-runtime/publish-grant.receipt.json').exists()
 absence['fixture-release.receipt.json']=not (C/'controller-runtime/fixture-release.receipt.json').exists()
 check('no-grant-publication-or-specific-release',absence['02-grant.approval.json'] and absence['publish-grant.receipt.json'] and absence['06-release-fixture.approval.json'] and absence['fixture-release.receipt.json'])
 # These are exact public fixture paths only. No private-key path, trial content or SQL is opened.
 db=P(fixture['database']);reh=read(C/'harness-facts/rehearsal.public.json')
 targets=[db,P(str(db)+'-wal'),P(str(db)+'-shm'),db.parent,db.parent.parent]+[P(reh['options'][k]) for k in ['Snapshot','Destination','SourceRoot','TargetRoot']]
 states=[{'path':str(p),'exists':p.exists(),'current_native_file_id':None,'reason_current_id_unavailable':'path absent; no handle opened'} for p in dict.fromkeys(targets)]
 check('original-fixture-and-rehearsal-artifacts-absent',all(not x['exists'] for x in states))
 before=read(C/'harness-facts/before.rows.json')
 check('before-digest-only-survives',len(before)==87 and 'sha256:'+hashlib.sha256(raw(C/'harness-facts/before.rows.json')).hexdigest()==fixture['typed_rows_sha256']==grant['binding']['original_rows_sha256'])
 save('fixture-current-state.json',{'historical_recorded_ids':ids,'current_paths':states,'database_live_available':False,'current_identity_remeasured':False,'specific_release_performed':False,'whole_SQL_after_failure_available':False,'SQL_executed_by_reviewer':False,'historical_before_row_digest_tables':87,'safe_next_route':'No read-only SQL can inspect these deleted originals. A new case needs an independently reviewed lifetime that retains its fixture through actual whole-SQL inspection and explicit release; any separately preserved copy would need its own exact identity and provenance and cannot substitute for missing original fixture evidence.','absent_phase_markers':absence})
 summaries=[]
 def walk(x,loc):
  if isinstance(x,dict):
   if x.get('schema')=='researchos.source-read-guard-observation.v1':summaries.append({'location':loc,'entry_count':len(x['entries']),'verified_closed':good(x),'retained_handles_count':x['retained_handles_count']})
   else:
    for k,v in x.items():walk(v,loc+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):walk(v,loc+'/'+str(i))
 for p in paths:
  if p.suffix=='.json':walk(read(p),str(p))
 check('all-recorded-sourceguards-truly-closed',len(summaries)>=15 and all(x['verified_closed'] for x in summaries),len(summaries))
 save('historical-source-guard-closure-summary.json',summaries)
 canon_after=[pin(r['path']) for r in oc['canonical_unchanged_refs']]
 check('canonical-short-pins-unchanged',canon_before==canon_after and canon_before==[norm(r) for r in oc['canonical_unchanged_refs']])
 save('canonical-short-pins.json',{'before':canon_before,'after':canon_after,'canonical_held_by_this_reviewer':False})
 cleanup=guard.close();save('guard-closure.json',cleanup);check('reviewer-guard-closed',good(cleanup))
 report={'schema':'researchos.independent-native-T10-closed-failure-facts.v1','decision':'FAILED_EXECUTION_CLOSURE_CONFIRMED_FIXTURE_LOST_NO_SQL_OR_SPECIFIC_RELEASE' if all(x['passed'] for x in checks) else 'REVIEW_INCOMPLETE','authority':'NONE','formal_acceptance':False,'checks':checks,'guarded_public_inputs':len(refs),'native_failure_ordinal':892,'same_attempt_two_context_failure_lines':True,'hard_kill_or_helper_timeout':False,'graceful_Go_failure_exit':1,'recorded_retained_marker_is_current_live_proof':False,'whole_SQL_after_failure_accepted':False,'specific_release_accepted':False,'native_positive_Owner_nine_original_business_formal_accepted':False,'global_provider_requests':None,'original_trial_provider_requests':None,'new_mechanical_errors':0,'history_reset':False,'stop':True}
 save('review.json',report)
 print(json.dumps({'decision':report['decision'],'passed':sum(x['passed'] for x in checks),'total':len(checks),'failed':[x for x in checks if not x['passed']],'guarded_public_inputs':len(refs),'historical_guard_count':len(summaries),'all_guards_closed':cleanup['closed'],'current_fixture_available':False},ensure_ascii=False))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:
 if guard is not None:
  cleanup=guard.close()
  if not (O/'guard-closure.json').exists():save('guard-closure.json',cleanup)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)

