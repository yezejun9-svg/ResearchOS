import sys
sys.dont_write_bytecode=True
import json,hashlib,importlib.util,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
C=B/'integration_codex/native-temp-controller-config-root-1791508950616'
S=B/'integration_codex/native-temp-positive-serve-root-1791509017626'
A=B/'integration_codex/native-temp-positive-root-api-1791509017626'
F=B/'integration_codex/native-temp-failed-root-release-1791509915469'
checks=[]
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def pin(p):
 p=Path(p); raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def norm(r):return {'path':str(Path(r['path'])),'sha256':r['sha256'].removeprefix('sha256:'),'bytes':r['bytes']}
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail})
def closed(g):
 return g.get('verification')=='PASSED' and g.get('closed') is True and g.get('retained_handles_count')==0 and g.get('failure') is None and not g.get('errors') and all(e.get('verified') and e.get('final_path_match') and e.get('closed') for e in g.get('entries',[]))
guard=None
def main():
 global guard
 cfg=json.loads((C/'controller.public.config.json').read_bytes())
 hc=json.loads((C/'native-harness.public.config.json').read_bytes())
 canon_paths=[R/'execution/v2.4'/n for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
 canon_before=[pin(p) for p in canon_paths]
 paths=[C/'controller.public.config.json',C/'native-harness.public.config.json',Path(__file__)]
 for d in [C/'controller-runtime',C/'harness-facts',S,A,F]:
  paths.extend(p for p in d.iterdir() if p.is_file())
 paths.extend(Path(cfg[k]['path']) for k in ['ControllerSource','ObservedOwnedHelper','OriginalOwnedHelper','SourceReadGuard'])
 paths.append(Path(hc['BrokerSource']['path']))
 paths=sorted(set(paths),key=str)
 refs=[pin(p) for p in paths]
 save('input-pins.json',refs)
 gr=norm(cfg['SourceReadGuard'])
 check('guard-source-fixed-pin',pin(gr['path'])==gr)
 spec=importlib.util.spec_from_file_location('independent_failure_source_guard',gr['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 guard=module.SourceReadGuard()
 guard.acquire(refs)
 def raw(p):return guard.get_buffer(str(Path(p)))
 def read(p):return json.loads(raw(p))
 def bound(ref):return pin(ref['path'])==norm(ref)
 snap_path=C/'controller-runtime/review-snapshot-fixture-retained-412f004bdb68481b83dc94781cdfc5d2.json'
 cfgp=C/'controller.public.config.json'; insp=read(A/'inspection-positive.json');snap=read(snap_path)
 inv=read(C/'controller-runtime/test.invocation.json');outer=read(S/'serve-outer.invocation.json')
 ctl=read(C/'controller-runtime/controller.closed.json');oc=read(S/'serve-outer.closed.json')
 rel=read(C/'controller-runtime/fixture-release.receipt.json');approval=read(F/'root-specific-fixture-release-approval.json')
 failure=read(F/'failure-origin.868.json');io=read(F/'original-root-native-tool-io.json')
 fixed=[(cfgp,'19c92dc0af96281b0d00b1cb767ef3715e9f97102669722550e07888213808af',1163646),(S/'serve-outer.closed.json','675075d2ec43f63ec3ef3db7788ecc1920145af2b7abac44ef88434e37379508',1131387),(A/'inspection-positive.json','7dfe6d48b8bfb560a31ea7830a22497440e2f62a1a27a3b325b54a37038d3409',98591),(F/'root-specific-fixture-release-approval.json','0c58479c8e227d32d6577b3b29d697ad57169c99c02f6c1d4e321adaa3bab802',936),(F/'failure-origin.868.json','d545edd01777e2866398e07c718da61c36d17f1cbd4b68647c7a16dc3309acdf',2714)]
 for p,h,n in fixed:check('exact-root-anchor:'+p.name,hashlib.sha256(raw(p)).hexdigest()==h and len(raw(p))==n)
 jobs=[]
 for name,d,pid,ft in [('Go',inv,59568,134359833014974083),('outer-Python',outer,64432,134359832888043283)]:
  r=d['result'];j=r['job_cleanup']
  check(name+'-actual-identity-and-failure',r['actual_exit']==1 and r['timed_out'] is False and r['error'] is None and r['owned_child_pid']==pid and type(r['creation_time_100ns']) is int and r['creation_time_100ns']==ft and r['resumed'])
  check(name+'-owned-job-closure',all(j[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and j['errors']==[])
  for k in ['config_ref','stdout_ref','stderr_ref']:check(name+'-reference:'+k,bound(d[k]))
  jobs.append({'name':name,'pid':pid,'creation_time_100ns_decimal':str(ft),'actual_exit':r['actual_exit'],'job_cleanup':j})
 save('actual-owned-jobs.json',jobs)
 check('controller-failed-and-completely-closed',ctl['job_and_guards_closed'] and not ctl['harness_test_exit_zero'] and not ctl['worker_still_alive'] and ctl['fixture_release_approval_exists'] and closed(ctl['source_guard_cleanup']))
 check('outer-record-binds-controller-and-invocation',oc['owned_outer_job_closed'] and bound(oc['controller_closed_ref']) and bound(oc['invocation_ref']) and not oc['formal_acceptance'])
 check('failure868-separates-broker-source-vs-held',failure['ordinal']==868 and failure['actual_outer_exit']==failure['actual_python_exit']==failure['actual_native_exit']==1 and failure['broker_python_exit_source_reported']==1 and failure['broker_python_exit_independently_held'] is None and failure['broker_private_helper_or_backup_child_launched'] is False)
 for k in ['original_tool_io_ref','actual_go_invocation_ref','actual_outer_invocation_ref','controller_closed_ref','root_outer_closed_ref']:check('failure868-ref:'+k,bound(failure[k]))
 serve=io['serve'];serve_done=serve['completion']['result']['value']
 check('original-serve-tool-exit1',serve['initial']['chunk_id']=='a85fcf' and serve['initial']['session_id']==2977 and serve_done['chunk_id']=='c99b6f' and serve_done['exit_code']==1 and 'ROOT_PYTHON_EXIT=1' in serve_done['output'])
 for name,chunk in [('inspection','59bc0c'),('approval','3fe408')]:
  rr=io[name]['result'];check('original-'+name+'-exit0',rr['chunk_id']==chunk and rr['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in rr['output'])
 release=io['release'];rd=release['completion']['result']['value']
 check('original-release-exit0',release['initial']['chunk_id']=='ad9aac' and release['initial']['session_id']==77504 and rd['chunk_id']=='6c484d' and rd['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in rd['output'])
 fixture=read(C/'harness-facts/fixture.public.json');ready=read(C/'harness-facts/06-fixture-retained.ready.json');before=read(C/'harness-facts/before.rows.json')
 check('snapshot-retained-failed-not-signed',snap['phase']=='fixture-retained' and snap['root_approval'] is False and all(snap[k] is None for k in ['payload_ref','ready_ref','sign_kind','signed_destination']) and ready['test_failed'] is True and ready['release_required'] is True)
 check('snapshot-inspection-config-binding',bound(insp['snapshot_ref']) and bound(insp['config_ref']) and snap['job_binding_id']==inv['job_binding_id']==ctl['job_binding_id'])
 for ref in snap['evidence_refs']:check('snapshot-evidence:'+Path(ref['path']).name,bound(ref))
 check('whole87-tables-equal-before',len(insp['typed_rows'])==87 and insp['typed_rows']==before)
 check('schema1-through23-and-synthetic',insp['schema_versions']==list(range(1,24)) and fixture['synthetic'] is True and fixture['formal'] is False and insp['synthetic_only'] is True and insp['schema_object_count']==296)
 check('whole-read-snapshot-reported-complete',all(insp[k] is True for k in ['fixture_read_complete','whole_row_schema_review_complete','transaction_snapshot_complete','primary_and_WAL_bytes_unchanged']) and insp['data_version_before']==insp['data_version_after']==2)
 check('schema-and-rows-pins-equal-fixture',insp['sqlite_schema_sha256']==fixture['schema_sha256'] and insp['typed_rows_sha256']==fixture['typed_rows_sha256'] and bound(insp['before_ref']) and insp['typed_rows_sha256'].removeprefix('sha256:')==hashlib.sha256(raw(C/'harness-facts/before.rows.json')).hexdigest())
 check('measured-native-ids-bound',insp['native_ids']==snap['measured_native_ids']=={'root':'ee413c31:00030000:00117b45','database':'ee413c31:00030000:00117b46'})
 check('SQL-share-label-not-immutable',insp['database_share_mode']=='READ_WRITE_SHARED_DELETE_DENIED' and insp['immutable_database_claim'] is False and insp['database_guard_cleanup']['share_mode']=='FILE_SHARE_READ_WRITE_DELETE_DENIED' and insp['database_guard_cleanup']['immutable_source_claim'] is False)
 check('failed-target-missing-baseline-qualified',insp['expected_state_matches'] is False and insp['expected_baseline_available'] is False and insp['expected_target_schema_sha256'] is None and insp['after_ref'] is None and insp['formal_acceptance'] is False)
 check('early-failure-label-is-filename-only',insp['early_failure_retained'] is False and Path(snap['fixture_public_ref']['path']).name=='fixture.public.json' and ready['test_failed'] is True)
 check('private-output-not-recorded',insp['private_credentials_recorded'] is False and insp['private_raw_rows_recorded'] is False)
 api=raw(A/'root_public_api_temp.actual.py').decode()
 check('inspection-source-readonly-whole-BEGIN',all(x in api for x in ['?mode=ro','PRAGMA query_only=ON','db.execute("BEGIN")','SELECT type,name,tbl_name,coalesce(sql,','for name in table_names:','native_ids_before==native_ids_after==snap["measured_native_ids"]','data_version_before==data_version_after','primary_and_WAL_bytes_unchanged']))
 check('specific-approval-five-keys',set(approval)=={'Schema','Action','ConfigSHA256','Snapshot','InspectionReceipt'} and approval['Schema']=='researchos.root-native-fixture-release.v1' and approval['Action']=='RELEASE_AFTER_INDEPENDENT_FIXTURE_INSPECTION' and approval['ConfigSHA256']==inv['config_ref']['sha256'] and bound(approval['Snapshot']) and bound(approval['InspectionReceipt']))
 for k in ['approval_ref','inspection_ref','published_ref']:check('release-reference:'+k,bound(rel[k]))
 check('released-exact-specific-fixture',norm(rel['approval_ref'])==pin(F/'root-specific-fixture-release-approval.json') and norm(rel['inspection_ref'])==pin(A/'inspection-positive.json') and read(C/'harness-facts/06-release-fixture.approval.json')=={'Action':'release-fixture'})
 db=Path(fixture['database']);absences=[db,Path(str(db)+'-wal'),Path(str(db)+'-shm'),db.parent,db.parent.parent]
 check('named-synthetic-database-and-parent-absent',all(not p.exists() for p in absences),[str(p) for p in absences])
 request=read(C/'harness-facts/00-rehearsal.request.json');broker=raw(hc['BrokerSource']['path']).decode()
 check('broker-source-fixed',pin(hc['BrokerSource']['path'])==norm(hc['BrokerSource']))
 check('actual-four-key-request-vs-two-key-broker',set(request['Environment'])=={'SystemRoot','WINDIR','TEMP','TMP'} and 'if set(request["Environment"]) != {"SystemRoot", "WINDIR"}:' in broker)
 order=[broker.index(x) for x in ['if set(request["Environment"])','output.mkdir(', 'spec.loader.exec_module(helper)','private_input = read_private_pipe()','result = helper.run_owned_private_stdin(']]
 check('environment-rejection-before-helper-private-and-backup',order==sorted(order) and not Path(request['OutputDirectory']).exists() and read(C/'harness-facts/00-rehearsal.broker.stderr.raw')=={'broker_failed':True,'error_type':'ValueError'})
 observations=[]
 def walk(v,where):
  if isinstance(v,dict):
   if v.get('schema') in ['researchos.source-read-guard-observation.v1','researchos.retained-sqlite-read-share-observation.v1']:
    observations.append({'location':where,'entry_count':len(v.get('entries',[])),'closed_verified':closed(v),'share_mode':v.get('share_mode')})
   else:
    for k,x in v.items():walk(x,where+'/'+k)
  elif isinstance(v,list):
   for i,x in enumerate(v):walk(x,where+'/'+str(i))
 for p in paths:
  if p.suffix=='.json':
   walk(read(p),str(p))
 check('all-historical-guard-observations-closed',len(observations)>10 and all(x['closed_verified'] for x in observations),len(observations))
 save('historical-guard-summary.json',observations)
 canon_after=[pin(p) for p in canon_paths]
 check('canonical-short-pins-unchanged-no-held-canonical',canon_before==canon_after)
 save('canonical-short-pins.json',{'before':canon_before,'after':canon_after,'canonical_held':False})
 cleanup=guard.close();save('guard-closure.json',cleanup)
 check('own-read-guard-truly-closed',closed(cleanup))
 report={'schema':'researchos.independent-native-temp-actual-failure-review.v1','decision':'LIMITED_FAILED_EXECUTION_WHOLE_SQL_SPECIFIC_RELEASE_ACCEPTED' if all(c['passed'] for c in checks) else 'REQUEST_CHANGES','authority':'NONE','formal_acceptance':False,'checks':checks,'guarded_input_count':len(refs),'original_failure_ordinal':868,'broker_python_exit_source_reported':1,'broker_python_exit_independently_held':None,'original_business_read':False,'Go_SQL_native_key_sign_context_model_executed_by_reviewer':False,'native_positive_accepted':False,'Owner_nine_original_business_formal_accepted':False,'historical_whole_SQL_receipt_audited':True,'database_live_currently_available':False,'global_provider_requests':None,'stop':True}
 save('review.json',report)
 print(json.dumps({'decision':report['decision'],'passed':sum(c['passed'] for c in checks),'total':len(checks),'failed':[c for c in checks if not c['passed']],'guarded_input_count':len(refs),'all_guards_closed':closed(cleanup)},ensure_ascii=False))
code=0
try:main()
except Exception:
 traceback.print_exc();code=1
finally:
 if guard is not None:
  cleanup=guard.close()
  if not (O/'guard-closure.json').exists():save('guard-closure.json',cleanup)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)

