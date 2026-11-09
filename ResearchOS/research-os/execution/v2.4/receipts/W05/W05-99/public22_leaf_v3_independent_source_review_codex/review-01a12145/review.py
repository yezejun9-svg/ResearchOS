"""Independent leaf v3 Source review. No product or registration entrypoint."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import stat
import types
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
S=B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v3'
PR=B/'public22_actual_independent_review_codex/actual-01a1210b'
ACTOR='codex:/root/attach_fixture_source_review'
checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
 with (N/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('review_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def same(a,b):return Path(a['path'])==Path(b['path']) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
def reject(name,fn,expected=None):
 try:fn()
 except Exception as e:check(name,type(e).__name__=='BoundaryError' and (expected is None or str(e)==expected),dict(exception=type(e).__name__,message=str(e)))
 else:check(name,False,'Unexpected acceptance')
def main():
 h=read(S/'HDF.json');mf=read(h['manifest_ref']['path']);contract=read(h['contract_ref']['path']);source=Path(h['runner_ref']['path']).read_bytes()
 old=read(PR/'HDF.resolved.json');oldmf=read(PR/'MF.resolved.json');state=read(old['returned_state_ref']['path']);assignment=read(old['original_assignment_ref']['path']);case=read(state['request_ref']['path'])
 root=Path(case['output_root']);original_request=state['request_ref'];original_canon=[pin(R/'execution/v2.4'/(n+'.json')) for n in ('checkpoint','path_ownership','step_state','commands')]
 references=[pin(__file__),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],*read(h['source_inputs_ref']['path'])['references'],pin(PR/'HDF.resolved.json'),old['returned_state_ref'],old['original_assignment_ref'],original_request,*original_canon]
 references.extend(oldmf['input_refs']);references.extend(oldmf['members'])
 references.extend([contract['old22_recovery_source'],contract['old22_backup_source'],contract['old22_canonical_source']])
 references=list({str(Path(r['path']).resolve()):r for r in references}.values())
 for r in references:
  assert 'private' not in Path(r['path']).parts
  check('exact pin '+r['path'],same(pin(r['path']),r))
 guard=mod(contract['source_guard']['path']).SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(references)
 try:
  leaf=mod(h['runner_ref']['path']);tree=ast.parse(source)
  check('handoff exact Source triple',pin(S/'HDF.json')['sha256']=='986c86da716c5be2c26922f0aa64200a4f925037bc6a84aa7135383a985346f5' and h['manifest_ref']['sha256']=='e791329078879c06624741ef81d3b26726f94820c8b83f6eedd9e083f39c3afe' and h['runner_ref']['sha256']=='ed27d2d7ebac26f3adfb10b2d199d196d92c6638be1edc3a12081025c53d6fde')
  check('contract exact current runner',same(contract['source_runner_ref'],h['runner_ref']) and same(contract['source_inputs_ref'],h['source_inputs_ref']))
  check('distinct Source author',leaf.AUTHOR==h['source_author']==contract['source_author']=='codex:/root/w09_formal_profile_source_impl' and leaf.AUTHOR!=ACTOR)
  check('frozen Go source held in Source closure',all(r in read(h['source_inputs_ref']['path'])['references'] for r in [contract['old22_recovery_source'],contract['old22_backup_source'],contract['old22_canonical_source']]))
  # Execute exactly the author's finite controls through result construction,
  # excluding only its final old-namespace publication statements.
  controls_path=next(Path(r['path']) for r in mf['members'] if Path(r['path']).name=='source_controls.py')
  ctl=ast.parse(controls_path.read_bytes());stop=next(i for i,n in enumerate(ctl.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets))
  env={'__file__':str(controls_path),'__name__':'independent_controls_no_publication'}
  exec(compile(ast.Module(body=ctl.body[:stop+1],type_ignores=[]),str(controls_path),'exec'),env)
  check('100 finite controls independently reproduced',env['result']['count']==100 and env['result']['pass']==100 and env['result']['fail']==0 and env['result']==read(h['controls_ref']['path']))
  trigger=leaf.expected_restore_trigger_sql(Path(contract['old22_recovery_source']['path']).read_text(encoding='utf-8'))
  observed_source=leaf.readonly_database_observation(root/'source22/researchos.sqlite');observed_restore=leaf.readonly_database_observation(root/'verified22/state.sqlite');manifest=read(root/'backup22/manifest.json')
  priorproof=read(old['root_cause_ref']['path'])
  check('exact trigger equals independent original proof',trigger==priorproof['exact_trigger_sql'])
  check('full schema Go manifest equivalence',observed_source['schema_sha256']==priorproof['source_full_schema_hash'].removeprefix('sha256:') and observed_restore['schema_sha256']==priorproof['restored_full_schema_hash'].removeprefix('sha256:') and manifest['schema_hash']=='sha256:'+observed_source['schema_sha256'])
  check('actual original database refs unchanged',observed_source['database_ref']==state['observations']['sealed22']['database_ref'] and observed_restore['database_ref']==state['observations']['verify22']['database_ref'])
  check('actual strengthened oracle accepts original artifacts',leaf.validate_restore22(observed_restore,observed_source,manifest,trigger))
  check('full auth columns and PK authenticated',observed_source['credentials']['columns']==['token_hash','principal','expires_at','revoked'] and observed_source['credentials']['pk_columns']==['token_hash'] and observed_source['credentials']['count']==observed_restore['credentials']['count']==1 and observed_source['credentials']['expected_revoked_rows_sha256']==observed_restore['tables']['auth_credentials']['rows_sha256'])
  check('all83 tables and82 others exactly preserved',len(observed_source['tables'])==len(observed_restore['tables'])==83 and [n for n in observed_source['tables'] if observed_source['tables'][n]!=observed_restore['tables'][n]]==['auth_credentials'])
  # Counterexamples use copied observations only: never mutate either database.
  for table in observed_source['tables']:
   if table=='auth_credentials':continue
   bad=copy.deepcopy(observed_restore);bad['tables'][table]['rows_sha256']='f'*64
   reject('changed real table row digest '+table,lambda bad=bad:leaf.validate_restore22(bad,observed_source,manifest,trigger))
  for field in ('token_hash','principal','expires_at'):
   # A changed non-revoked value changes the full-row hash even when the
   # observation's self-consistency hash is changed alongside it.
   bad=copy.deepcopy(observed_restore);bad['tables']['auth_credentials']['rows_sha256']='f'*64;bad['credentials']['source_rows_sha256']='f'*64
   reject('full-row digest changed '+field,lambda bad=bad:leaf.validate_restore22(bad,observed_source,manifest,trigger),'PUBLIC_RESTORE_CREDENTIAL_ROWS_MISMATCH')
  bad=copy.deepcopy(observed_restore);bad['credentials']['columns'].append('extra')
  reject('extra credential column rejected',lambda:leaf.validate_restore22(bad,observed_source,manifest,trigger),'PUBLIC_RESTORE_CREDENTIAL_LAYOUT_MISMATCH')
  bad=copy.deepcopy(observed_restore);bad['schema_rows'].append(['view','injected','injected','CREATE VIEW injected AS SELECT 1']);bad['schema_rows'].sort(key=lambda r:(r[0],r[1]));bad['schema_sha256']=leaf.schema_digest(bad['schema_rows'])
  reject('extra view with recomputed digest rejected',lambda:leaf.validate_restore22(bad,observed_source,manifest,trigger),'PUBLIC_RESTORE_SCHEMA_MISMATCH')
  projection=leaf.compile_case(contract,case)
  for actual,phase in zip(state['calls'],projection['phases']):
   check('original exact argv cwd '+phase['id'],actual['argv']==phase['argv'] and Path(actual['cwd'])==Path(phase['cwd']))
   check('original closed OwnedJob '+phase['id'],leaf.closed_job(actual['observation']))
   check('original PID FILETIME integer retained '+phase['id'],type(actual['observation']['creation_time_100ns']) is int and actual['started_at_unix_ns']<=actual['observation']['creation_time_100ns']*100-11644473600000000000<=actual['ended_at_unix_ns'])
  evidence=dict(prior_review_hdf_ref=pin(PR/'HDF.resolved.json'),original_assignment_ref=old['original_assignment_ref'],returned_state_ref=old['returned_state_ref'],source_db_ref=observed_source['database_ref'],restored_db_ref=observed_restore['database_ref'],backup_manifest_ref=pin(root/'backup22/manifest.json'),restore_report_ref=pin(root/'verified22/restore-report.json'),backup_stdout_ref=pin(root/'raw/backup22.stdout'),verify_stdout_ref=pin(root/'raw/verify22.stdout'))
  # The real operational Scope is absent by design. A finite test double is
  # used only to validate the Source interface under our independent guard.
  called=[]
  class ReviewOnlyScope:
   def require_existing_observation(self,cref,qref,ev,source_author):
    assert cref==h['contract_ref'] and qref==original_request and ev==evidence and source_author==h['source_author'];called.append('SYNTHETIC_SOURCE_INTERFACE_NOT_ROOT_AUTHORITY')
  result=leaf.recheck_existing_public22(h['contract_ref'],original_request,evidence,ReviewOnlyScope())
  check('finite existing recheck exact real artifacts',len(called)==1 and result['status']=='SOURCE_RECHECK_VALIDATED_EXISTING_ARTIFACTS_ONLY' and result['original_ordinal']==1025 and result['new_native_children']==0 and result['formal_acceptance'] is False and result['execution_grant'] is False)
  recheck=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='recheck_existing_public22')
  calls={ast.unparse(n.func) for n in ast.walk(recheck) if isinstance(n,ast.Call)}
  check('recheck no write process or native entry',not calls.intersection({'save_new','os.chmod','job_module.run_owned','run_registered_case','subprocess.run','Path.mkdir'}))
  forbidden=[];original_read=leaf.read_exact
  def no_read(ref):forbidden.append(ref);raise AssertionError('Unexpected IO before Scope gate')
  class Denied:
   def require_existing_observation(self,*a,**kw):raise leaf.BoundaryError('REVIEW_TEST_ROOT_LEASE_REVOKED')
  try:
   leaf.read_exact=no_read
   reject('no Root Scope rejected before IO',lambda:leaf.recheck_existing_public22(h['contract_ref'],original_request,evidence,None),'LIVE_ROOT_EXISTING_OBSERVATION_SCOPE_REQUIRED')
   reject('JSON Scope rejected before IO',lambda:leaf.recheck_existing_public22(h['contract_ref'],original_request,evidence,{'approved':True}),'LIVE_ROOT_EXISTING_OBSERVATION_SCOPE_REQUIRED')
   reject('Root denial stops before IO',lambda:leaf.recheck_existing_public22(h['contract_ref'],original_request,evidence,Denied()),'REVIEW_TEST_ROOT_LEASE_REVOKED')
   check('no IO reached on denied scopes',forbidden==[])
  finally:leaf.read_exact=original_read
  # Compare all frozen author host captures to exact original audit lines once.
  bindings=[read(r['path']) for r in mf['members'] if Path(r['path']).name.endswith('.binding.json')]
  bylog={}
  for bind in bindings:bylog.setdefault(bind['source_log'],set()).update(bind['source_ordinals'])
  saved={}
  for logfile,ordinals in bylog.items():
   with Path(logfile).open('rb') as f:
    for i,line in enumerate(f):
     if i in ordinals:saved[(logfile,i)]=line
     if i>=max(ordinals):break
  for bind in bindings:
   raw=Path(bind['capture_ref']['path']).read_bytes();lines=[saved[(bind['source_log'],i)] for i in bind['source_ordinals']]
   check('author real audit capture '+Path(bind['capture_ref']['path']).name,raw==b''.join(lines) and [hashlib.sha256(v).hexdigest() for v in lines]==bind['original_line_sha256'])
   header=json.loads(lines[0])['payload'];check('author distinct actual header '+Path(bind['capture_ref']['path']).name,header['id']=='01a12011-7d41-7991-a01c-de2d71701ff7' and header['source']['subagent']['thread_spawn']['agent_path']=='/root/w09_formal_profile_source_impl')
  baseline=read(state['baseline_manifest_ref']['path'])
  check('baseline readonly file attributes retained',all(Path(r['path']).stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY for r in baseline['references']))
  check('no Canon writes',original_canon==[pin(r['path']) for r in original_canon])
  check('original1025 and actual state remain failed',read(old['returned_state_ref']['path'])==state and read(old['original_assignment_ref']['path'])==assignment and state['status']=='STOPPED_AT_FIRST_FAILURE')
  for r in references:check('held unchanged '+r['path'],same(pin(r['path']),r))
 finally:closed=guard.close()
 check('review Guard closed all handles',closed['verification']=='PASSED' and closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[])
 gr=save('source-guard.closed.json',closed)
 controls=save('independent-controls.json',dict(checks=checks,failed=[x for x in checks if not x['passed']],author_controls_count=100,real_databases_readonly=True,synthetic_scope_only=True,no_Root_scope_granted=True,recheck_interface_result=result,source_guard_ref=gr))
 req=save('next-root-recheck-contract.json',dict(status='REVIEWER_REQUIREMENTS_ONLY_NOT_ROOT_REQUEST_OR_REGISTRATION',leaf_entry='recheck_existing_public22(contract_ref, request_ref, evidence, root_scope)',contract_ref=h['contract_ref'],request_ref=original_request,request_value=case,evidence=evidence,caller_scope_method='require_existing_observation(contract_ref, request_ref, evidence, source_author=...)',source_author=h['source_author'],required_new_Root_scope_fields=['issued_by=codex:/root','mode=READONLY_EXISTING_PUBLIC22_ORIGINAL1025','exact leaf Source HDF/MF/runner/contract/source-inputs refs','exact independent leaf v3 decision and HDF/MF plus actual reviewer hostpair and identity','exact original case_id/output_root/request_ref','all nine evidence refs above','original1025 Root assignment, original actual Root hostpair/binding, caller returned record, case.closed ref','all four native before/result/stdout/stderr and integer PID/FILETIME observations','baseline manifest+encrypted files+readonly attributes; do not read private key/owner file','new Root caller Source+independent review, current canonical vector, registered owner and worker documents, readonly lease and fresh Root activation witness','complete held Source/Python/SQLite loaded runtime and existing artifact resource refs','new separate review-receipt namespace; zero product child and zero original-case writes','formal_acceptance=false,parent_acceptance=false,original1025_result=FAILED_RETAINED'],original_actual_capture_ref=assignment['original_capture_ref'],original_actual_capture_binding_ref=assignment['capture_binding_ref'],original_caller_record_ref=assignment['caller_record_ref'],original_case_closed_ref=state['closed_receipt']['ref'],actual_argv_cwd_projection_required=True,original_host_audit_validation='Compare saved header/call/result raw bytes at binding source offsets; bind real Root actor, exact v4 runner caller request and its ref, original native raw bytes and complete persisted records. Original console was truncated: preserve complete returned tool IO, do not claim full console.',holding_requirement='Root caller owns SourceReadGuard and pins complete closure before invoking leaf; hold through both read-only observations, final pin recheck and new receipt publication. Leaf Scope callback must reject wrong or revoked registration, stale lease, author self-review, missing/mismatched original evidence, or absence of held resources before first file read.',original_case_request_must_not_be_replaced=True,new_Root_envelope_separate_from_original_case_request=True,old_caller_v4_not_compatible=True,old_caller_reason='No require_existing_observation method; old AUTHOR/contract/scope are v2 and permit product phases. A separately reviewed readonly-only caller is required.',new_scope_granted=False,formal_acceptance=False,execution_grant=False))
 failed=[v for v in checks if not v['passed']]
 dr=save('decision.json',dict(schema='researchos.public22-leaf-v3-independent-source-decision.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=h['source_author'],decision='ACCEPTED_SOURCE_ONLY' if not failed else 'CHANGES_REQUIRED',source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],runner_ref=h['runner_ref'],contract_ref=h['contract_ref'],source_inputs_ref=h['source_inputs_ref'],independent_controls_ref=controls,next_root_recheck_contract_ref=req,blocking_findings=failed,existing_artifacts_oracle='VALIDATED_READONLY_IN_FINITE_REVIEW_SCOPE_ONLY',original1025_status='FAILED_RETAINED',actual_native_children_replayed=0,Root_operational_scope_registered=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,current_main23_qualified=False,full20to24=False))
 mr=save('MF.json',dict(schema='researchos.independent-source-review-manifest.v1',members=[pin(__file__),dr,controls,req,gr],input_refs=references))
 hr=save('HDF.json',dict(schema='researchos.public22-leaf-v3-independent-source-review.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',reviewed_utc=datetime.now(timezone.utc).isoformat(),source_author_id=h['source_author'],source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],runner_ref=h['runner_ref'],contract_ref=h['contract_ref'],source_inputs_ref=h['source_inputs_ref'],manifest_ref=mr,source_decision_ref=dr,independent_controls_ref=controls,next_root_recheck_contract_ref=req,source_guard_ref=gr,checks=len(checks),held_refs=len(references),blocking_findings=len(failed),execution_grant=False,formal_acceptance=False,parent_acceptance=False))
 print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,next_root_recheck_contract=req,checks=len(checks),held_refs=len(references),failed=failed),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
