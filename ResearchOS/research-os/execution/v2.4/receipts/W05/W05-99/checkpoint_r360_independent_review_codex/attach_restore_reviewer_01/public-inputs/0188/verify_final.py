from pathlib import Path
import json,hashlib,collections
O=Path(__file__).resolve().parent; B=O.parent.parent
P=B/'integration_codex/native-migration-positive-ttl-root-26c5c890ef5144d4'
C=B/'integration_codex/native-ttl-controller-config-v2-root-4a61fbed032643e4'
A=B/'integration_codex/native-positive-ttl-root-api-a4a432c97c744d98'
S=B/'integration_codex/native-positive-ttl-serve-root-052db2c7da5645f6'
L=B/'integration_codex/native-positive-ttl-failed-root-release-1791505647184'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def dump(name,v):(O/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def walk(v,trace=''):
 if isinstance(v,dict):
  yield trace,v
  for k,x in v.items():yield from walk(x,trace+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from walk(x,trace+'/'+str(i))
def copy(p,name):
 q=O/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
docs=[]
for label,d in [('server',S),('runtime',C/'controller-runtime'),('api',A),('release',L),('facts',P/'facts')]:
 for p in sorted(d.rglob('*')):
  if not p.is_file():continue
  copy(p,'inputs/final-'+label+'/'+p.relative_to(d).as_posix())
  if p.suffix=='.json':docs.append((label+'/'+p.relative_to(d).as_posix(),read(p)))
controller=read(C/'controller-runtime/controller.closed.json')
outer=read(S/'serve-outer.closed.json')
harness=read(C/'controller-runtime/test.invocation.json')
outerinv=read(S/'serve-outer.invocation.json')
backup=read(P/'facts/00-rehearsal/invocation.json')
inspection=read(A/'inspection-positive.json')
approval=read(L/'root-concrete-release.approval.json')
release=read(C/'controller-runtime/fixture-release.receipt.json')
cfg=read(C/'controller.public.config.json')
historical_canonical={x['path'].casefold() for x in outer['canonical_unchanged_refs']}
guardrows=[];allrefs=[];seen=set()
for label,doc in docs:
 for loc,node in walk(doc):
  if {'entries','closed','retained_handles_count','verification'}<=set(node):
   valid=node['closed'] is True and node['retained_handles_count']==0 and not node.get('errors') and not node.get('failure') and node['verification']=='PASSED'
   invalid=[e for e in node['entries'] if not all(e.get(k) is True for k in ('closed','verified','final_path_match'))]
   guardrows.append(dict(source=label,location=loc,entries=len(node['entries']),closed=valid and not invalid,invalid_entries=invalid,share_mode=node.get('share_mode')))
  if {'path','sha256','bytes'}<=set(node):
   ref={k:node[k] for k in ('path','sha256','bytes')};key=(ref['path'].casefold(),ref['sha256'].removeprefix('sha256:'),ref['bytes'])
   if key in seen:continue
   seen.add(key);p=Path(ref['path'])
   if key[0] in historical_canonical:
    state='HISTORICAL_CANONICAL_AT_SERVER_CLOSE_NOT_CURRENT_STATE';actual=None
   elif p.suffix.lower() in ('.sqlite','.db') or str(p).lower().endswith(('-wal','-shm')):
    state='HISTORICAL_DATABASE_RECEIPT_NOT_LIVE_PIN';actual=None
   elif not p.is_file():state='MISSING_AT_REVIEW';actual=None
   else:
    actual=pin(p);state='MATCH' if actual['sha256']==key[1] and actual['bytes']==key[2] else 'DRIFT'
   allrefs.append(dict(source=label,location=loc,expected=ref,actual=actual,state=state))
dump('final-input-pins.json',allrefs)
dump('guard-closure-checks.json',guardrows)
jobrows=[]
for name,result in [('backup-rehearsal',backup['Result']),('Root-harness',harness['result']),('Root-server',outerinv['result'])]:
 job=result['job_cleanup'];closed=job['active_processes_last_observed']==0 and not job['errors'] and all(job[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'))
 jobrows.append(dict(name=name,pid=result['owned_child_pid'],creation_time_100ns=result['creation_time_100ns'],actual_exit=result['actual_exit'],timed_out=result['timed_out'],error=result['error'],closed=closed))
db=Path(inspection['database_ref']['path'])
deleted=dict(database_exists=db.exists(),WAL_exists=Path(str(db)+'-wal').exists(),SHM_exists=Path(str(db)+'-shm').exists(),fixture_root_exists=db.parent.exists(),scope='existence only; no database contents read')
io=read(L/'original-tool-io.json')
events=[]
for event in io['events']:
 value=event['value']
 if isinstance(value,dict) and value.get('status')=='fulfilled':value=value['value']
 if isinstance(value,dict) and 'exit_code' in value:
  output=value.get('output','')
  if 'ROOT_PYTHON_EXIT=' in output:
   events.append(dict(key=event['store_key'],chunk_id=value.get('chunk_id'),outer_exit=value['exit_code'],Python_markers=[line for line in output.splitlines() if line.startswith('ROOT_PYTHON_EXIT=')]))
baseline=read(O/'initial-verification.json')
badrefs=[x for x in allrefs if x['state'] in ('MISSING_AT_REVIEW','DRIFT')]
bound=(approval['ConfigSHA256']=='sha256:'+pin(C/'controller.public.config.json')['sha256'] and approval['InspectionReceipt']==release['inspection_ref'] and approval['Snapshot']==inspection['snapshot_ref'] and release['published_ref']['sha256']=='sha256:'+pin(P/'facts/06-release-fixture.approval.json')['sha256'])
result=dict(authority='NONE',formal_acceptance=False,decision='FAILED_EXECUTION_WHOLE_SQL_INSPECTION_AND_CLEANUP_COMPONENTS_ACCEPTED',native_positive_accepted=False,Owner_accepted=False,original_business_accepted=False,nine_cases_accepted=False,independent_Go_native_SQL_model_execution=False,source_modified=False,canonical_modified=False,reference_counts=collections.Counter(x['state'] for x in allrefs),reference_count=len(allrefs),reference_failures=badrefs,guard_count=len(guardrows),guard_failures=[x for x in guardrows if not x['closed']],jobs=jobrows,controller_reported_closed=controller['job_and_guards_closed'],controller_reported_test_zero=controller['harness_test_exit_zero'],worker_still_alive=controller['worker_still_alive'],outer_reported_closed=outer['owned_outer_job_closed'],private_pipe=backup['Result']['private_stdin'],private_input_persisted=backup['PrivateInputPersisted'],release_specific_snapshot_inspection_binding_valid=bound,whole_SQL_read_receipt=baseline,postcleanup_existence=deleted,exact_Root_tool_completion_markers=events,Root_failure_ordinals_preserved=[835,836,837],new_mechanical_errors=0,prior_failure_prefix_and_FULL_not_reset=True)
dump('final-verification.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('whole_SQL_read_receipt','private_pipe','reference_failures')},ensure_ascii=False))

