"""Actual Caller03 resource delta only; retain RT2 controls without rerunning them."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,hashlib,json,os,sys,types
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
N=Path(__file__).resolve().parent;PRIOR=N.parent/'runtime-s21root-20261010-02'
ACTOR='codex:/root/attach_fixture_source_review';THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
checks=[]
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def read(r):return json.loads(Path(r['path'] if isinstance(r,dict) else r).read_bytes())
def same(a,b):return os.path.normcase(os.path.abspath(a['path']))==os.path.normcase(os.path.abspath(b['path'])) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def check(n,x):checks.append(dict(name=n,passed=bool(x)))
def load(r,n):
 assert same(pin(r['path']),r);m=types.ModuleType(n);m.__file__=r['path'];sys.modules[n]=m
 exec(compile(Path(r['path']).read_bytes(),m.__file__,'exec'),m.__dict__);return m
def run():
 mr=pin(D/'old21.v3.runtime-manifest.actual.root.json');sr=pin(D/'old21.v3.runtime-qualification.scope.actual.root.json')
 assert (mr['sha256'],mr['bytes'])==('9b48f613fe80d894af146ae85ed6d8176845ef23a64bb825f4c36a5d48308d67',36056)
 assert (sr['sha256'],sr['bytes'])==('e7fa5f66c44934145184acf63204bf111b97709b3ee243d6648457a7be9cc693',1590)
 m,s=read(mr),read(sr);h=read(m['source_hdf_ref']);sm=read(m['source_mf_ref']);contract=read(m['builder_contract_ref'])
 ph,pf,pd=[pin(PRIOR/n) for n in ('HDF.json','MF.json','decision.json')];previous=read(pd);priorh=read(ph);priorchecks=read(previous['finitechecks_ref'])
 assert pd['sha256']=='31ae7b778282c4fad9f78d2825195021100ed9752ce7dbdd4c9dcea5df14174a' and previous['verdict']=='RUNTIME_CLOSURE_ACCEPTED' and priorchecks['passed']==428 and priorchecks['failed']==[]
 rr=pin(D/'original106029.actual-host.raw.jsonl');br=pin(D/'original106029.actual-host.binding.root.json')
 assert (rr['sha256'],rr['bytes'])==('9004bb75666e9fb5a2a0a87ef52d35f8536eb2fc21c8291412ba8575f5f98120',27679)
 assert (br['sha256'],br['bytes'])==('85cec17ff81339cc68b27dcdfd148e178c05a3d963eb649ad42a71ec6006e81a',1283)
 source_review_root=B/'schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-03'
 source_review_refs=[pin(source_review_root/n) for n in ('HDF.json','MF.json','decision.json')]
 g=load(contract['source_guard_ref'],'rt3_independent_guard')
 inputs=m['resource_refs']+[mr,sr,rr,br,m['probe_guard_ref'],m['source_hdf_ref'],m['source_mf_ref'],contract['toolchain_lock_ref'],ph,pf,pd,previous['finitechecks_ref'],previous['Source_guard_ref'],pin(__file__)]+sm['members']+source_review_refs
 unique={};canon={os.path.normcase(str(R/'execution/v2.4'/n)) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')}
 for r in inputs:
  k=os.path.normcase(os.path.abspath(r['path']));assert k not in canon and (k not in unique or same(unique[k],r));unique[k]=r
 guard=g.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=192*1024*1024);error=None
 try:
  guard.acquire(list(unique.values()))
  check('every finite input pinned and held',all(same(pin(r['path']),r) for r in unique.values()))
  caller=load(m['caller_ref'],'rt3_independent_caller');load(caller.TP_REF,'rt3_independent_tp')
  job=load(contract['owned_job_ref'],'rt3_independent_owned');load(contract['builder_ref'],'rt3_independent_builder');load(contract['base_helper_ref'],'rt3_independent_base')
  paths=list(job.runtime_resource_paths())
  for module in tuple(sys.modules.values()):
   for k in ('__file__','__cached__'):
    p=getattr(module,k,None)
    if p and Path(p).is_file():paths.append(p)
  paths += [sys.executable,contract['go_ref']['path'],m['caller_ref']['path'],caller.GUARD_REF['path'],caller.TP_REF['path'],contract['owned_job_ref']['path'],contract['builder_ref']['path'],contract['base_helper_ref']['path'],h['contract_ref']['path'],m['builder_contract_ref']['path'],contract['input_manifest_ref']['path']]
  observed={caller.canonical(p):pin(p) for p in paths};observer=observed.pop(caller.canonical(__file__))
  current={caller.canonical(r['path']):r for r in m['resource_refs']};old={caller.canonical(r['path']):r for r in previous['resource_refs']}
  unchanged=[r for k,r in current.items() if k in old and same(r,old[k])];removed=[r for k,r in old.items() if k not in current];added=[r for k,r in current.items() if k not in old]
  check('RT2 exact145 retained and exactly3 resource replacements',len(unchanged)==145 and len(removed)==len(added)==3)
  check('only Caller calling-contract and Root-probe resources replaced',{Path(r['path']).name for r in added}=={'old21_root.source.py','root-calling-contract.source.json','prepare_old21_v3_runtime_qualification.root.py'} and {Path(r['path']).name for r in removed}=={'old21_root.source.py','root-calling-contract.source.json','prepare_old21_v2_runtime_qualification.root.py'})
  check('complete original148 ordered unique resources preserved',len(current)==len(m['resource_refs'])==148 and list(current)==sorted(current))
  missing=[r for k,r in observed.items() if k not in current];drift=[r for k,r in observed.items() if k in current and not same(r,current[k])];extras=[r for k,r in current.items() if k not in observed]
  check('all147 actually observed resources covered',len(observed)==147 and not missing and not drift)
  check('only extra Root resource probe',len(extras)==1 and same(extras[0],pin(D/'prepare_old21_v3_runtime_qualification.root.py')))
  check('RT2 identity and original source resource decision retained',previous['review_author']==ACTOR and priorh['review_author']==ACTOR and previous['independent_non_author'] is True and same(priorh['decision_ref'],pd) and same(priorh['manifest_ref'],pf))
  previous_guard=read(previous['Source_guard_ref']);check('RT2 closed guard retained',previous_guard['verification']=='PASSED' and previous_guard['closed'] is True and previous_guard['retained_handles_count']==0 and previous_guard['errors']==[])
  sd=read(source_review_refs[2]);check('Task80 Source03 review binds new exact source',sd['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and sd['independent_non_author'] is True and same(sd['source_hdf_ref'],m['source_hdf_ref']) and same(sd['source_mf_ref'],m['source_mf_ref']) and same(sd['caller_ref'],m['caller_ref']) and same(sd['calling_contract_ref'],h['contract_ref']))
  check('Source03 HDF binds exact caller and MF',same(h['manifest_ref'],m['source_mf_ref']) and same(h['caller_ref'],m['caller_ref']))
  check('new Root manifest exact identity and no execution authority',m['schema']=='researchos.root-old21-runtime-manifest.v1' and m['issued_by']=='codex:/root' and m['root_thread_id']==THREAD and m['source_author']==previous['source_author'] and m['builder_source_author']==previous['builder_source_author'] and m['formal_acceptance'] is False and m['execution_grant'] is False)
  check('new Root scope exact identity purpose and no authority',s['schema']=='researchos.root-old21-runtime-qualification-scope.v2' and s['issued_by']=='codex:/root' and s['root_thread_id']==THREAD and s['slice_id']=='OLD21_RUNTIME_RESOURCE_QUALIFICATION' and s['formal_acceptance'] is False and s['execution_grant'] is False)
  check('new scope issued and currently live',datetime.fromisoformat(s['created_utc'])<=datetime.now(timezone.utc)<datetime.fromisoformat(s['lease_expires_at']))
  check('new manifest exact scope ref',same(m['qualification_scope_ref'],sr))
  for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref'):check('new scope exact '+k,same(s[k],m[k]))
  for k in ('builder_contract_ref','python_ref','go_ref'):check('unchanged qualified boundary '+k,same(m[k],previous[k]))
  check('actual interpreter exact locked unchanged Python',same(pin(sys.executable),m['python_ref']))
  rg=read(m['probe_guard_ref']);check('Root03 guard all148 closed verified',rg['verification']=='PASSED' and rg['closed'] is True and rg['retained_handles_count']==0 and rg['errors']==[] and rg['failure'] is None and len(rg['entries'])==148 and all(same(e,r) and e['verified'] is True and e['closed'] is True and e['final_path_match'] is True for e,r in zip(rg['entries'],m['resource_refs'])))
  binding=read(br);parts=[]
  with Path(binding['source_audit_path']).open('rb') as f:
   for offset,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
    f.seek(offset);v=f.read(size);check('Root03 exact original audit byte range',hashlib.sha256(v).hexdigest()==digest);parts.append(v)
  check('whole original Root03 hostpair preserved',b''.join(parts)==Path(rr['path']).read_bytes() and same(binding['original_capture_ref'],rr))
  rows=[json.loads(v) for v in parts];check('Root03 actual root identity and call pairing',rows[0]['payload']['id']==THREAD and rows[1]['payload']['call_id']==rows[2]['payload']['call_id']==binding['original_call_id'])
  actual_results=[json.loads(block['text']) for block in rows[2]['payload']['output'] if block.get('type')=='input_text' and block.get('text','').startswith('{')]
  check('both original sequential Root helpers retained successful',[x['chunk_id'] for x in actual_results]==['e0d6ff','b2e38a'] and all(x['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in x['output'] for x in actual_results))
  check('actual Root probe output binds exact new scope manifest and guard',all(digest in actual_results[1]['output'] for digest in (mr['sha256'],sr['sha256'],m['probe_guard_ref']['sha256'])))
  check('actual Root call uses new probe Source','prepare_old21_v3_runtime_qualification.root.py' in rows[1]['payload']['input'])
  check('all finite pins remain exact at close',all(same(pin(r['path']),r) for r in unique.values()))
 except BaseException as e:error=dict(type=type(e).__name__,message=str(e))
 finally:closed=guard.close()
 check('independent RT3 guard closed0',closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[])
 gr=save('Source-guard.closed.json',closed);failed=[x for x in checks if not x['passed']]
 if error:
  report=save('diagnostic.json',dict(error=error,checks=checks,guard_ref=gr));print(json.dumps(dict(error=error,report_ref=report),ensure_ascii=False),flush=True);raise SystemExit(1)
 closure=save('runtime-closure-delta-observation.json',dict(runtime_manifest_ref=mr,Root_actual_probe_raw_ref=rr,Root_actual_probe_binding_ref=br,inherited_RT2_review_refs=[ph,pf,pd],inherited_RT2_checks_ref=previous['finitechecks_ref'],inherited_checks_reexecuted=False,unchanged_resources=unchanged,removed_resources=removed,added_resources=added,observed_required_resources=list(observed.values()),observer_only_ref=observer,Root_observer_extra_refs=extras,missing_resources=missing,drifted_resources=drift,Task80_checks_reexecuted=False,author_controls_reexecuted=False,inventory_target_files_read=False,actual_Go_Native_SQL_TP_model_calls=0,live_Canon_handles=0,Canonical_written=False))
 fr=save('finite-delta-checks.json',dict(checks=checks,passed=len(checks)-len(failed),failed=failed))
 common=dict(review_author=ACTOR,source_author=m['source_author'],builder_source_author=m['builder_source_author'],root_thread_id=THREAD,**{k:m[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','python_ref','go_ref')},qualification_scope_ref=sr,runtime_manifest_ref=mr,formal_acceptance=False,execution_grant=False)
 dr=save('decision.json',dict(schema='researchos.old21-runtime-independent-review-decision.v2',**common,independent_non_author=True,verdict='RUNTIME_CLOSURE_ACCEPTED' if not failed else 'RUNTIME_CLOSURE_REJECTED',resource_refs=m['resource_refs'],finitechecks_ref=fr,Source_guard_ref=gr,closure_observation_ref=closure,programme_qualification=None))
 mf=save('MF.json',dict(schema='researchos.old21-runtime-independent-review-manifest.v2',members=list(unique.values())+[gr,closure,fr,dr]))
 hr=save('HDF.json',dict(schema='researchos.old21-runtime-independent-review-hdf.v2',**common,manifest_ref=mf,decision_ref=dr,reviewed_utc=datetime.now(timezone.utc).isoformat(),finitechecks_ref=fr,Source_guard_ref=gr,closure_observation_ref=closure,programme_qualification=None))
 print(json.dumps(dict(HDF=hr,MF=mf,decision=dr,checks=len(checks),failed=failed,held_refs=len(unique),resource_count=148,actual_observed_resources=len(observed),unchanged_RT2_resources=len(unchanged),verdict=read(dr)['verdict'],formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)
 if failed:raise SystemExit(1)
if __name__=='__main__':run()
