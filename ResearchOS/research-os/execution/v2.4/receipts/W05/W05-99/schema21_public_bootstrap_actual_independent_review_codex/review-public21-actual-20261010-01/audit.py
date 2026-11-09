import json,hashlib,sqlite3,base64,re,types,stat,datetime
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
O=Path(__file__).parent
ROOT='codex:/root'
refs={}; checks=[]; details={}
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
def ref(path):
 p=Path(path); assert 'private' not in [x.lower() for x in p.parts], 'PRIVATE_READ_DENIED'
 b=p.read_bytes(); return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):
 p=Path(r['path']); assert 'private' not in [x.lower() for x in p.parts], 'PRIVATE_READ_DENIED'
 b=p.read_bytes(); assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'], 'REF_DRIFT:'+str(p)
 refs[str(p).lower()]={k:r[k] for k in ('path','sha256','bytes')}
 return b
def doc(r):return json.loads(read(r))
def save(name,d):
 p=O/name
 with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
returnref=dict(path=str(R/'execution/v2.4/receipts/W05/W05-99/integration_codex/public21-caller-9690cc6324834ded8781ce8a2233fa82/caller-return.root.json'),sha256='32bf8fa41ec9dc5e5af33ccf978a670540efb15d75cfa31e8b77f5ed67a697bf',bytes=278813)
ret=doc(returnref)
sref=dict(path=str(Path(returnref['path']).with_name('runner-returned-state.root.json')),sha256='a839fdff63ba5196762d63ebed08b77525ff1f43c435d82a41d96e4c5d65b717',bytes=58336)
s=doc(sref);c=doc(s['contract_ref']);ctx=s['root_context'];sc=doc(ctx['scope_ref']);reg=doc(ctx['registration_result_ref']);facts=doc(reg['facts_ref'])
req=doc(ctx['root_request_ref']);q=doc(ctx['resource_qualification_ref']);prog=doc(s['programme_binding']['qualification_ref']);bm=doc(s['baseline_manifest_ref'])
check('caller_return_state_exact',ret.get('runner_returned_state')==s)
check('caller_closed_no_error',ret.get('caller_error') is None and ret.get('source_guard_cleanup',{}).get('closed') is True and ret.get('source_guard_cleanup',{}).get('retained_handles_count')==0)
check('component_only',s['public_bootstrap_observed'] is True and s['first_failure'] is None and s['phase']=='complete' and all(s[k] is False for k in ('backup_restore_executed','formal_acceptance','parent_acceptance','original_data_touched','credential_bytes_read_or_emitted','automatic_retry')) and s['formal_case_accepted_delta']==0 and s['full20to24']=='OPEN')
for k in ('host_call_intent_ref','caller_source_review_ref','runner_source_review_ref','runtime_manifest_ref'):
 doc(ctx[k])
for k in ('review_hdf_ref','review_mf_ref','review_decision_ref','qualification_scope_ref','payload_ref'):
 doc(q[k])
check('runtime_prior_independent_qualification',q['status']=='QUALIFIED_FOR_PUBLIC21_BOOTSTRAP' and q['independent_non_author'] is True and q['formal_programme_qualification'] is False and q['review_author']!='codex:/root/attach_restore_independent_review')
check('qualification_exact_resources',q['runner_contract_ref']==s['contract_ref'] and q['runtime_manifest_ref']==ctx['runtime_manifest_ref'] and q['control_ref']==c['old21_control'])
for r in s['programme_binding']['program_refs'].values():read(r)
check('programme_qualified_old21',prog['status']=='QUALIFIED_OLD21_BUILD' and prog['source_schema_version']==21 and prog['programme_qualification'] is True and prog['source_commit']==c['source_commit'] and prog['source_tree']==c['source_tree'])
owner=doc(facts['owner_ref']);worker=doc(facts['worker_ref'])
check('fresh_scope_owner_worker',sc['scope_key']==ctx['scope_key']=='PUBLIC21_BOOTSTRAP_ONLY' and owner['owner_id']==worker['worker_id']==ctx['executor']==ROOT and owner['slice_id']==worker['slice_id']==sc['slice_id'] and owner['scope_ref']==worker['scope_ref']==ctx['scope_ref'])
check('execution_current4_binding',req['current_canonical_refs']==ctx['current_canonical_refs'] and reg['transaction']['checkpoint_ref']==ctx['current_canonical_refs'][0] and reg['transaction']['ownership_ref']==ctx['current_canonical_refs'][1] and reg['full_before_archive_refs'][2]['sha256']==ctx['current_canonical_refs'][2]['sha256'] and reg['full_before_archive_refs'][3]['sha256']==ctx['current_canonical_refs'][3]['sha256'])
for r in ctx['current_canonical_refs']:read(r)
for r in reg['full_before_archive_refs']:read(r)
doc(sc['registration_request_ref']);doc(s['request_ref']);read(sc['runner_ref'])
calls=s['calls'];check('one_public_bootstrap',len(calls)==1)
call=calls[0];obs=call['observation'];job=obs['job_cleanup']
check('public_argv',call['argv']==[c['old21_control']['path'],'--bootstrap-owner','--credential-file',s['private_owner_metadata']['path']] and call['cwd']==c['old21_root'] and call['timeout_seconds']==90)
check('env_minimal',set(call['env'])=={'SystemRoot','WINDIR','TEMP','TMP','RESEARCHOS_DATA_DIR'} and Path(call['env']['RESEARCHOS_DATA_DIR'])==Path(s['baseline_ref']['path']).parent)
check('native_exit_identity',call['actual_exit']==obs['actual_exit']==0 and type(obs['owned_child_pid']) is int and obs['owned_child_pid']==56236 and type(obs['creation_time_100ns']) is int and obs['creation_time_100ns']==134360613796799333 and obs['error'] is None and obs['timed_out'] is False)
check('owned_job_closed',all(job[k] is True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed')) and job['active_processes_last_observed']==0 and not job['errors'])
before=doc(call['before_ref']);result=doc(call['result_ref'])
check('raw_result_matches',result=={k:v for k,v in call.items() if k!='result_ref'})
for k in ('stdout_ref','stderr_ref'):read(call[k]);check('empty_'+k,call[k]['bytes']==0)
def dt(x):return datetime.datetime.fromisoformat(x.replace('Z','+00:00')).timestamp()
started=call['started_at_unix_ns']/1e9;ended=call['ended_at_unix_ns']/1e9
check('finite_execution_lease',started<ended<dt(sc['lease_expires_at']) and dt(req['created_utc'])<=started)
age=started-dt(q['created_utc']);check('qualification_older_than_180_with_fresh_scope',age>180 and dt(req['created_utc'])>dt(q['created_utc']),age)
details['qualification_age_seconds_at_entry']=age
details['identity']={'pid':obs['owned_child_pid'],'creation_time_100ns_decimal':str(obs['creation_time_100ns']),'actual_exit':0}
def host(r,label):
 b=doc(r); raw=read(b['original_capture_ref']); lines=raw.splitlines(keepends=True); originals=[]
 with Path(b['source_audit_path']).open('rb') as f:
  for off in b['source_line_offsets']:
   f.seek(off);originals.append(f.readline())
 check(label+'_original_lines',lines==originals and [hashlib.sha256(v).hexdigest() for v in originals]==b['original_line_sha256'])
 entries=[json.loads(v) for v in originals]
 check(label+'_root_session',entries[0]['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98')
 details[label]={'binding_ref':r,'capture_ref':b['original_capture_ref'],'timestamps':[x.get('timestamp') for x in entries],'payload_types':[x.get('payload',{}).get('type') for x in entries]}
 if 'original_call_id' in b:
  check(label+'_matching_callid',entries[1]['payload'].get('call_id')==entries[2]['payload'].get('call_id')==b['original_call_id'])
 return entries
host(ctx['pre_entry_host_binding_ref'],'pre_entry')
host(q['review_hostpair_binding_ref'],'runtime_peer')
host(q['root_issuance_binding_ref'],'runtime_root_issuance')
completed=dict(path=str(R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public21-bootstrap-completed.actual-audit.root.json'),sha256='bfa9a6a08269e3cc53afa9116220cbee350f558f47649c639b0fa7030c896c30',bytes=1095)
entries=host(completed,'actual_bootstrap')
p1,p2=entries[1]['payload'],entries[2]['payload']
check('actual_host_call_result_pair',p1.get('call_id')==p2.get('call_id') and p1.get('type')=='function_call' and p2.get('type')=='function_call_output')
check('actual_host_success', 'ROOT_PYTHON_EXIT=0' in str(p2) and '9340b0' in str(p2))
check('actual_host_bound_return',returnref['sha256'] in str(p2))
details['actual_host_call']=p1
details['actual_host_result']=p2
for name,a in s['guard_cleanup'].items():
 check('producer_guard_'+name,a['closed'] is True and a['retained_handles_count']==0 and not a['errors'] and a['verification']=='PASSED')
closed=doc(s['closed_receipt']['ref'])
check('closed_receipt_preserves_observation',closed['calls']==s['calls'] and closed['observations']==s['observations'] and closed['baseline_ref']==s['baseline_ref'])
sqlrefs=[]
for k,r in c['frozen_runtime_refs'].items():
 if k.startswith('migrations/'):read(r);sqlrefs.append(r)
check('numbered_source_inventory',sorted(int(Path(r['path']).name[:4]) for r in sqlrefs if re.match(r'^\d{4}_',Path(r['path']).name))==list(range(1,22)))
fence=Path(c['old21_root'])/'internal/domain/client_session_fence.go';fenceref=ref(fence);fencesrc=read(fenceref).decode()
dbref=s['baseline_ref'];read(dbref)
gm=types.ModuleType('independent_guard');exec(compile(read(c['source_guard']),c['source_guard']['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard()
guard.acquire(list(refs.values()))
try:
 db=Path(dbref['path'])
 check('baseline_readonly_attribute',bool(db.stat().st_file_attributes&stat.FILE_ATTRIBUTE_READONLY))
 check('sqlite_sidecars_empty',all(not Path(str(db)+suffix).exists() or Path(str(db)+suffix).stat().st_size==0 for suffix in ('-wal','-shm','-journal')))
 con=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
 try:
  con.execute('PRAGMA query_only=ON')
  schema=list(con.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))
  tables={}
  def encode(v):return {'blob_base64':base64.b64encode(v).decode('ascii')} if isinstance(v,bytes) else v
  for row in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
   name=row[0];quoted='"'+name.replace('"','""')+'"'
   serialized=sorted(json.dumps([encode(v) for v in row],ensure_ascii=False,separators=(',',':')) for row in con.execute('SELECT * FROM '+quoted))
   tables[name]={'count':len(serialized),'rows_sha256':hashlib.sha256('\n'.join(serialized).encode()).hexdigest()}
  actual=dict(database_ref=dbref,versions=[r[0] for r in con.execute('SELECT version FROM schema_migrations ORDER BY version')],schema_sha256=hashlib.sha256(json.dumps(schema,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),integrity=[r[0] for r in con.execute('PRAGMA integrity_check')],foreign_key_violations=len(con.execute('PRAGMA foreign_key_check').fetchall()),tables=tables,mode='ro,immutable,query_only',raw_rows_emitted=False)
  check('independent_full_database_oracle_matches',actual==s['observations']['created21'])
  check('ledger_1_to21_integrity_fk',actual['versions']==list(range(1,22)) and actual['integrity']==['ok'] and actual['foreign_key_violations']==0)
  details['nonempty_tables']={k:v['count'] for k,v in tables.items() if v['count']}
  check('business_empty',all(v['count']==0 for k,v in tables.items() if k not in {'auth_principals','auth_credentials','resource_write_lock','schema_migrations'} and not k.startswith('retrieval_fts_')))
  check('owner_credential_one',tables['auth_principals']['count']==tables['auth_credentials']['count']==1)
  normal=lambda v:re.sub(r'\s+',' ',v.replace('IF NOT EXISTS ','').strip().rstrip(';')).lower()
  addonsrc=read(c['frozen_runtime_refs']['migrations/sqlite/next_v24_sessions.sql']).decode()
  tableddl=addonsrc[addonsrc.index('CREATE TABLE'):addonsrc.index(');')+2]
  actualtable=next(row[3] for row in schema if row[0]=='table' and row[1]=='client_sessions')
  check('unnumbered_addon_exact_table_ddl',normal(tableddl)==normal(actualtable))
  for name in ('client_session_epoch_no_regression','client_session_require_fresh'):
   ddl=next(row[3] for row in schema if row[0]=='trigger' and row[1]==name)
   check('fence_ddl_'+name,normal(ddl) in normal(fencesrc))
  check('addon_unbumped_empty',tables['client_sessions']['count']==0 and max(actual['versions'])==21)
  details['ledger_columns']=[r[1] for r in con.execute('PRAGMA table_info(schema_migrations)')]
 finally:con.close()
 save('independent-database-observation.json',actual)
 read(dbref)
 check('private_owner_exists_only',Path(s['private_owner_metadata']['path']).is_file())
 details['private_owner_access']={'existence_checked':True,'bytes_read':False,'hash_computed':False,'copied':False}
finally:
 cleanup=guard.close();save('reviewer-source-guard-close.json',cleanup)
check('reviewer_guard_closed',cleanup['closed'] is True and cleanup['retained_handles_count']==0 and not cleanup['errors'])
save('source-pins.json',list(refs.values()))
save('audit-result.json',dict(checks=checks,failed=[x for x in checks if not x['passed']],details=details,numbered_and_addon_source_refs=sqlrefs,migration_ledger_checksum_column_exists=False,static_505_43_matrix_rerun=False))
print(json.dumps(dict(check_count=len(checks),failed=[x for x in checks if not x['passed']],pin_count=len(refs),nonempty=details['nonempty_tables'],guard_closed=cleanup['closed']),ensure_ascii=False))

