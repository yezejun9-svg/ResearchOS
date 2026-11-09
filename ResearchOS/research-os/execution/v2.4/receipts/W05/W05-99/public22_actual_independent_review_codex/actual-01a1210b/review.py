"""Independent existing-evidence review only. Never invokes a product entrypoint."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import types
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
P=B/'public22_root_caller_registration_source_codex/p22root-20261009-04'
D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
CASE=B/'integration_codex/schema22-public-89c0459006654891bf3c540af6b525aa'
C=CASE.parent/'schema22-public-caller-89c0459006654891bf3c540af6b525aa'
PR=B/'public22_root_caller_registration_independent_review_codex/review-v4-01a1210b'
ACTOR='codex:/root/attach_fixture_source_review'
checks=[];references={};archived=[]
def pin(p):
 p=Path(p).resolve(strict=True);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
 with (N/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('independent_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def check(name,ok,detail=None):checks.append(dict(name=name,passed=bool(ok),detail=detail))
def refs_in(v):
 if isinstance(v,dict):
  if set(('path','sha256','bytes'))<=v.keys():yield {k:v[k] for k in ('path','sha256','bytes')}
  else:
   for x in v.values():yield from refs_in(x)
 elif isinstance(v,list):
  for x in v:yield from refs_in(x)
def main():
 h=read(P/'HDF.json');g=mod(h['registrar_ref']['path']);c=mod(h['caller_ref']['path'])
 fact=read(P/'registration-facts.root.json');activation=read(P/'registration.activate.root.json');ar=read(D/'public22.v4.actual-request.root.json')
 caller=read(C/'caller-return.root.json');state=read(C/'runner-returned-state.root.json');closed=read(CASE/'case.closed.json')
 tx=Path(activation['transaction']['transaction_journal']);intent=read(tx/'intent.json');commit=read(tx/'committed.json')
 oldcp,oldow=(read(tx/(str(i)+'.before.json')) for i in range(2));cp,ow=(read(p) for p in g.CANON[:2])
 live=read(D/'pending-diagnostics.cp370.activation.live1024.root.json')
 oldmap={ (r['sha256'],r['bytes']):intent['before_refs'][i] for i,r in enumerate(fact['before_canonical_refs'][:2])}
 def add(ref):
  p=Path(ref['path']);assert 'private' not in p.parts,'PRIVATE_READ_FORBIDDEN'
  if p in g.CANON[:2] and (ref['sha256'],ref['bytes']) in oldmap:
   physical=oldmap[(ref['sha256'],ref['bytes'])];archived.append(dict(logical=ref,physical=physical));ref=physical;p=Path(ref['path'])
  actual=pin(p);check('ref '+str(p),actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'])
  references[str(p.resolve())]=actual
 paths=[Path(__file__),P/'HDF.json',P/'registration-facts.root.json',P/'registration.activate.root.json',P/'source-guard.cleanup.activate.root.json',*tx.glob('*.json'),D/'public22.v4.actual-request.root.json',D/'public22.v4.original1025.assignment.root.json',D/'RESUME.cp371-public22-stopped.live1026.root.json',D/'pending-diagnostics.cp370.activation.live1024.root.json',C/'caller-return.root.json',C/'runner-returned-state.root.json',CASE/'case.closed.json',N/'restore-delta-proof.json',N/'database-inspection.json',PR/'complete-hostpair-seal.with-identity.json',PR/'actual-actor-identity-chain.json',*g.CANON]
 for mode in ('build','check','activate','actual'):paths.extend([D/f'public22.v4.{mode}.actual-host.raw.jsonl',D/f'public22.v4.{mode}.actual-host.binding.root.json'])
 for p in paths:
  add(pin(p))
  if p.suffix=='.json' and p not in g.CANON and p.parent!=tx:
   for r in refs_in(read(p)):add(r)
 for obj in (h,read(h['manifest_ref']['path']),read(h['source_inputs_ref']['path'])):
  for r in refs_in(obj):add(r)
 guards=[caller['source_guard_cleanup'],*state['guard_cleanup'].values(),read(P/'source-guard.cleanup.activate.root.json')]
 for i,guard in enumerate(guards):
  check('original guard closed '+str(i),guard['closed'] and guard['retained_handles_count']==0 and guard['errors']==[] and guard['verification']=='PASSED')
  for e in guard['entries']:
   check('original guard verified '+str(i)+' '+e['path'],e['verified'] and e['final_path_match'] and e['closed']);add({k:e[k] for k in ('path','sha256','bytes')})
 guard=mod(g.GUARD).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 guard.acquire(list(references.values()))
 host=[]
 try:
  before=[pin(p) for p in g.CANON]
  check('TP exact historical pair',intent['expected_refs']==fact['before_canonical_refs'][:2] and all(intent['before_refs'][i]['sha256']==fact['before_canonical_refs'][i]['sha256'] for i in range(2)))
  check('TP exclusive complete commit',intent['mandatory_share_mode']==0 and intent['automatic_inverse'] is False and commit['written_indices']==[0,1] and commit['both_verified_while_exclusively_held'] and commit['after_refs']==before[:2]==activation['proposed_after_refs'])
  check('TP physical after exact current',all(Path(intent['after_refs'][i]['path']).read_bytes()==g.CANON[i].read_bytes() for i in range(2)))
  projected=g.transform(oldcp,oldow,fact,pin(P/'registration-facts.root.json'),live,fact['before_canonical_refs'],oldcp,oldow)
  check('pure transform exact current pair and inverse built-in',all(g.encoded(v)==p.read_bytes() for v,p in zip(projected,g.CANON[:2])))
  check('1002 historical rows plus19 originals preserved',len(oldcp['failure_counters'])==1002 and cp['failure_counters'][:1002]==oldcp['failure_counters'] and len(cp['failure_counters'])==1021 and [r['original_payload']['observed_ordinal'] for r in cp['failure_counters'][1002:]]==list(range(1005,1024)))
  check('SS CM unchanged',before[2:]==fact['before_canonical_refs'][2:])
  check('pending binding original1023 full prefix',g.pending(pin(D/'pending-diagnostics.cp370.activation.live1024.root.json'))==live)
  g.verify_source(read(fact['build_request_ref']['path']))
  check('Source nonauthor reviewed actual pinned chain',True)
  c.live_lease(ar['scope_ref'],ar['case_request_ref'],ar['owner_ref'],ar['worker_ref'],ar['current_canonical_vector_ref'],ar['output_root'],require_new=False)
  check('current scope owner worker exact live lease',True)
  for mode in ('build','check','activate','actual'):
   binding=read(D/f'public22.v4.{mode}.actual-host.binding.root.json');raw=Path(binding['original_capture_ref']['path']).read_bytes();lines=raw.splitlines(keepends=True)
   with Path(binding['source_audit_path']).open('rb') as f:
    source=[]
    for offset,size in zip(binding['source_line_offsets'],binding['source_line_bytes']):f.seek(offset);source.append(f.read(size))
   check('Root '+mode+' full raw bytes same original audit',len(lines)==3 and raw==b''.join(source) and [hashlib.sha256(x).hexdigest() for x in source]==binding['original_line_sha256'])
   header,call,result=map(json.loads,lines)
   check('Root '+mode+' actor identity',header['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98' and not isinstance(header['payload'].get('source'),dict))
   check('Root '+mode+' actual paired invocation',call['payload']['call_id']==result['payload']['call_id']==binding['original_call_id'] and call['payload']['name']=='functions.exec')
   text=call['payload']['input'];out=result['payload']['output'];serial=json.dumps(out,ensure_ascii=False) if not isinstance(out,str) else out
   check('Root '+mode+' intended producer selected',('public22_root_caller.source.py' if mode=='actual' else 'register_public22.source.py') in text and (mode=='actual' or ('--mode '+mode) in text or ('"'+mode+'"') in text))
   check('Root '+mode+' returned chunk known',binding['chunk_id'] in serial and binding['full_returned_tool_io_preserved'])
   host.append(dict(mode=mode,call_id=binding['original_call_id'],capture_ref=binding['original_capture_ref'],binding_ref=pin(D/f'public22.v4.{mode}.actual-host.binding.root.json'),console_complete=binding['console_output_complete']))
  check('caller complete state exact',caller['runner_returned_state']==state and caller['caller_error'] is None and caller['original_failure_assignment_required'])
  check('closed publication only field difference',{k:v for k,v in closed.items() if k!='closed_receipt'}=={k:v for k,v in state.items() if k!='closed_receipt'})
  check('stopped first failure retained',state['status']=='STOPPED_AT_FIRST_FAILURE' and state['phase']=='verify22' and state['first_failure']['message']=='PUBLIC_RESTORE_SCHEMA_MISMATCH' and state['first_failure']['last_child_exit']==0 and state['first_failure']['original_ordinal'] is None and state['baseline_retained'])
  phases=['bootstrap22','keygen22','backup22','verify22']
  check('four child calls only', [x['phase'] for x in state['calls']]==phases)
  for call in state['calls']:
   name=call['phase'];o=call['observation'];j=o['job_cleanup'];result=read(call['result_ref']['path']);br=read(call['before_ref']['path'])
   check(name+' exact persisted native result',result=={k:v for k,v in call.items() if k!='result_ref'})
   check(name+' before command projection',all(br[k]==call[k] for k in ('phase','argv','cwd','env','timeout_seconds','started_at_unix_ns')) and br['observation'] is None and br['actual_exit'] is None)
   check(name+' clean actual process exit',call['actual_exit']==o['actual_exit']==0 and o['error'] is None and not o['timed_out'] and o['resumed'] and o['stage']=='WAIT_PRIMARY_AND_JOB_IDLE')
   check(name+' actual PID FILETIME precision',type(o['owned_child_pid']) is int and o['owned_child_pid']>0 and type(o['creation_time_100ns']) is int and call['started_at_unix_ns']<=o['creation_time_100ns']*100-11644473600000000000<=call['ended_at_unix_ns'])
   check(name+' Job idle handles closed',all(j[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed')) and j['active_processes_last_observed']==0 and j['errors']==[] and j['termination_requested'] is False and j['termination_succeeded'] is None)
   check(name+' isolated old binary environment',Path(call['argv'][0]).name in ('old22-control.exe','old22-backup.exe') and '--spec' not in call['argv'] and call['env']['RESEARCHOS_DATA_DIR']==str(CASE/'source22') and call['timeout_seconds']==90 and call['stderr_ref']['bytes']==0)
  assign=read(D/'public22.v4.original1025.assignment.root.json')
  check('original1025 explicit Root assignment without history edit',assign['ordinal']==1025 and assign['first_failure']==state['first_failure'] and assign['caller_record_ref']==pin(C/'caller-return.root.json') and assign['returned_state_ref']==pin(C/'runner-returned-state.root.json') and assign['automatic_retry'] is False and assign['counter_reset'] is False)
  proof=read(N/'restore-delta-proof.json');check('all11 independent immutable SQL rootcause checks',len(proof['checks'])==11 and all(proof['checks'].values()))
  lr=read(h['runner_review_ref']['path']);leaf=mod(lr['runner_ref']['path'])
  try:leaf.validate_restore22(state['observations']['verify22'],state['observations']['sealed22'])
  except Exception as exc:check('pure oracle reproduces exact original schema stop',type(exc).__name__=='BoundaryError' and str(exc)=='PUBLIC_RESTORE_SCHEMA_MISMATCH')
  else:check('pure oracle reproduces exact original schema stop',False)
  synthetic=copy.deepcopy(state['observations']['verify22']);synthetic['schema_sha256']=state['observations']['sealed22']['schema_sha256']
  try:leaf.validate_restore22(synthetic,state['observations']['sealed22'])
  except Exception as exc:check('synthetic schema-only relaxation still rejects table change',type(exc).__name__=='BoundaryError' and 'TABLE' in str(exc),str(exc))
  else:check('synthetic schema-only relaxation still rejects table change',False)
  check('formal remains false no23or24 product',not state['formal_acceptance'] and not state['full20to24'] and not state['schema21'] and not state['next23to24'] and all(not state['publication'][k] for k in ('snapshot23','candidate23','backup23','verify23')))
  check('Canon unchanged during independent review',before==[pin(p) for p in g.CANON])
  for ref in references.values():check('post-held '+ref['path'],pin(ref['path'])==ref)
 finally:cleanup=guard.close()
 check('independent read guard clean',cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
 gr=save('review.source-guard.closed.json',cleanup)
 failed=[x for x in checks if not x['passed']]
 report=save('review.json',dict(actor=ACTOR,checks=checks,failed=failed,held_refs=len(references),historical_logical_refs_resolved_to_actual_TP_archives=archived,root_hosts=host,source_guard_ref=gr,product_executions=0,SQL_writes=0,Canon_writes=0,synthetic_counterexample_labeled=True,review_read_diagnostics=[dict(chunk_id='209e27',outer_exit=0,diagnostic='rg wrong registration.source.py path missing; Source/product not invoked'),dict(chunk_id='3fd207',outer_exit=0,diagnostic='Get-Content wrong caller.closed.json path missing; Source/product not invoked')]))
 decision=save('decision.json',dict(actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',decision='QUALIFIED_REGISTRATION_AND_PUBLIC22_STOPPED_SOURCE_ORACLE_MISMATCH' if not failed else 'REVIEW_CHECKS_REQUIRE_RESOLUTION',registration_qualified=not failed,actual_public22_status='STOPPED_AT_FIRST_FAILURE',first_failure_original=1025,actual_native_exits=[0,0,0,0],root_cause='Source oracle incorrectly requires raw restored schema and all table rows to equal sealed baseline; public restore intentionally adds exact backup_require_fresh_observation trigger and revokes the existing credential.',required_source_fix='For bootstrap22 scope, validate exact frozen restore trigger, all other sqlite_master objects, all83 table counts, all82 other table row hashes, auth_credentials non-revoked columns and exact revoked=1, owner1 and ledger1..22. Preserve original1025 and baseline. New Source review and Root scope before retry.',report_ref=report,root_cause_ref=pin(N/'restore-delta-proof.json'),baseline_manifest_ref=state['baseline_manifest_ref'],formal_acceptance=False,parent_acceptance=False,execution_grant=False,full20to24=False))
 mf=save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(__file__),report,decision,gr,pin(N/'restore-delta-proof.json'),pin(N/'database-inspection.json')],input_refs=list(references.values())))
 hdf=save('HDF.json',dict(schema='researchos.public22-actual-independent-review.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',reviewed_utc=datetime.now(timezone.utc).isoformat(),decision_ref=decision,manifest_ref=mf,source_hdf_ref=pin(P/'HDF.json'),review_ref=report,registration_ref=pin(P/'registration.activate.root.json'),caller_ref=pin(C/'caller-return.root.json'),returned_state_ref=pin(C/'runner-returned-state.root.json'),original_assignment_ref=pin(D/'public22.v4.original1025.assignment.root.json'),root_cause_ref=pin(N/'restore-delta-proof.json'),source_guard_ref=gr,checks=len(checks),failed=len(failed),formal_acceptance=False,parent_acceptance=False,execution_grant=False))
 print(json.dumps(dict(HDF=hdf,MF=mf,decision=decision,checks=len(checks),held_refs=len(references),failed=failed),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
