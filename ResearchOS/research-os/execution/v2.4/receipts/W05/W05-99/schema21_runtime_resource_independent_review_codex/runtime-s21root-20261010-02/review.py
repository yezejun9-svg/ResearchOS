"""Finite independent Caller02 runtime review. No Root or programme issuance."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,hashlib,json,os,sys,types
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
D=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
N=Path(__file__).resolve().parent
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
def load(r,name):
 assert same(pin(r['path']),r)
 m=types.ModuleType(name);m.__file__=r['path'];sys.modules[name]=m
 exec(compile(Path(r['path']).read_bytes(),m.__file__,'exec'),m.__dict__);return m
def run():
 mr=pin(D/'old21.v2.runtime-manifest.actual.root.json');sr=pin(D/'old21.v2.runtime-qualification.scope.actual.root.json')
 assert (mr['sha256'],mr['bytes'])==('6835d161ef93c8fccc36bc0da4653d80146da29ba0c679baf5edf89d324ca247',36056)
 assert (sr['sha256'],sr['bytes'])==('bde316c3fa040b8941b9c0321da9db7e5264ecbf1c218f867808a3d8cf32da4c',1590)
 m,s=read(mr),read(sr);h=read(m['source_hdf_ref']);source_mf=read(m['source_mf_ref']);calling=read(h['contract_ref']);contract=read(m['builder_contract_ref'])
 priorqref=pin(D/'main23.v4.runtime-qualification-v2.issued.actual.root.json');priorq=read(priorqref);pdref=priorq['review_decision_ref'];pd=read(pdref)
 assert pdref['sha256']=='80a9e9e4031f65c1cb5a75d2c8eb7f5d9eea6aa9d3640ebf23feb13dc93b01d2'
 rr=pin(D/'original106028.actual-host.raw.jsonl');br=pin(D/'original106028.actual-host.binding.root.json')
 assert (rr['sha256'],rr['bytes'])==('99f90fdc541c2b9a2e1f1f123942b7cb8da20236bc5b8f06d8ac619451afd4d8',25931)
 assert (br['sha256'],br['bytes'])==('96ef77d88ad83246429a2f604d93e1187c427d4c7cad60c463808a6597dc0978',1283)
 guard=load(contract['source_guard_ref'],'old21_independent_runtime_guard')
 inputs=m['resource_refs']+[mr,sr,rr,br,m['probe_guard_ref'],m['source_hdf_ref'],m['source_mf_ref'],m['builder_contract_ref'],h['contract_ref'],contract['toolchain_lock_ref'],priorqref,pdref,pin(__file__)]+source_mf['members']
 canon={os.path.normcase(str(R/'execution/v2.4'/n)) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')}
 unique={}
 for r in inputs:
  key=os.path.normcase(os.path.abspath(r['path']));assert key not in canon
  assert key not in unique or same(unique[key],r);unique[key]=r
 refs=list(unique.values());held=guard.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=192*1024*1024);error=None
 try:
  held.acquire(refs)
  for r in refs:check('pin:'+r['path'],same(pin(r['path']),r))
  caller=load(m['caller_ref'],'old21_independent_resource_caller')
  load(caller.TP_REF,'old21_independent_resource_tp')
  job=load(contract['owned_job_ref'],'old21_independent_resource_owned')
  load(contract['builder_ref'],'old21_independent_resource_builder')
  load(contract['base_helper_ref'],'old21_independent_resource_base')
  paths=list(job.runtime_resource_paths())
  for module in tuple(sys.modules.values()):
   for k in ('__file__','__cached__'):
    p=getattr(module,k,None)
    if p and Path(p).is_file():paths.append(p)
  paths += [sys.executable,contract['go_ref']['path'],m['caller_ref']['path'],caller.GUARD_REF['path'],caller.TP_REF['path'],contract['owned_job_ref']['path'],contract['builder_ref']['path'],contract['base_helper_ref']['path'],h['contract_ref']['path'],m['builder_contract_ref']['path'],contract['input_manifest_ref']['path']]
  observed={caller.canonical(p):pin(p) for p in paths};observer_only=observed.pop(caller.canonical(__file__))
  proposed={caller.canonical(r['path']):r for r in m['resource_refs']};previous={caller.canonical(r['path']):r for r in pd['resource_refs']}
  unchanged=[r for k,r in proposed.items() if k in previous and same(r,previous[k])];added=[r for k,r in proposed.items() if k not in previous];removed=[r for k,r in previous.items() if k not in proposed]
  missing=[r for k,r in observed.items() if k not in proposed];drift=[r for k,r in observed.items() if k in proposed and not same(r,proposed[k])];extras=[r for k,r in proposed.items() if k not in observed]
  check('exact 148 ordered unique resources',len(m['resource_refs'])==len(proposed)==148 and list(proposed)==sorted(proposed))
  check('all independently observed modules caches native DLLs and required resources covered',not missing and not drift)
  check('only Root observer extra',len(extras)==1 and same(extras[0],pin(D/'prepare_old21_v2_runtime_qualification.root.py')))
  check('M4 inherited resources exact 142 unchanged with 3 removals and 6 additions',len(unchanged)==142 and len(removed)==3 and len(added)==6)
  check('only bounded expected additions',{Path(r['path']).name for r in added}=={'old21_root.source.py','old21_builder.py','prepare_old21_v2_runtime_qualification.root.py','root-calling-contract.source.json','contract.v2.json','input-manifest.json'})
  check('unchanged M4 qualification authentic bound accepted decision',priorq['review_author']==ACTOR and priorq['status']=='QUALIFIED_FOR_MAIN23_BUILD' and pd['verdict']=='RUNTIME_CLOSURE_ACCEPTED' and pd['resource_refs']==priorq['resource_refs'])
  locked=read(contract['toolchain_lock_ref'])
  check('running locked Python exact',same(pin(sys.executable),m['python_ref']) and m['python_ref']['sha256']==locked['tools']['python']['sha256'] and caller.canonical(m['python_ref']['path'])==caller.canonical(locked['tools']['python']['path']))
  check('Go exact locked builder pin',same(contract['go_ref'],m['go_ref']) and m['go_ref']['sha256']==locked['tools']['go']['sha256'] and caller.canonical(m['go_ref']['path'])==caller.canonical(locked['tools']['go']['path']))
  check('Root runtime manifest identity and no authority',m['schema']=='researchos.root-old21-runtime-manifest.v1' and m['issued_by']=='codex:/root' and m['root_thread_id']==THREAD and m['source_author']=='codex:/root/backup_regression_resources' and m['builder_source_author']=='codex:/root/native_temp_independent_review' and m['formal_acceptance'] is False and m['execution_grant'] is False)
  check('Root scope identity and purpose',s['schema']=='researchos.root-old21-runtime-qualification-scope.v2' and s['issued_by']=='codex:/root' and s['root_thread_id']==THREAD and s['slice_id']=='OLD21_RUNTIME_RESOURCE_QUALIFICATION' and s['formal_acceptance'] is False and s['execution_grant'] is False)
  check('Root scope issued and unexpired',datetime.fromisoformat(s['created_utc'])<=datetime.now(timezone.utc)<datetime.fromisoformat(s['lease_expires_at']))
  check('Root runtime manifest exact scope',same(m['qualification_scope_ref'],sr))
  for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref'):check('scope binds exact '+k,same(s[k],m[k]))
  check('Source02 HDF exact source MF caller',same(h['manifest_ref'],m['source_mf_ref']) and same(h['caller_ref'],m['caller_ref']) and h['source_author']==m['source_author'])
  check('Source02 calling contract runtime manifest required',calling['runtime_qualification']['review_hdf_schema']=='researchos.old21-runtime-independent-review-hdf.v2' and calling['runtime_qualification']['review_decision_schema']=='researchos.old21-runtime-independent-review-decision.v2' and calling['runtime_manifest_contract']['runtime_review_hdf_and_decision_extra_required_ref']=='runtime_manifest_ref')
  rg=read(m['probe_guard_ref']);check('Root guard closed0',rg['verification']=='PASSED' and rg['closed'] is True and rg['retained_handles_count']==0 and rg['errors']==[] and rg['failure'] is None)
  check('Root guard all original148 entries match',len(rg['entries'])==148 and all(same(e,r) and e['verified'] is True and e['closed'] is True and e['final_path_match'] is True for e,r in zip(rg['entries'],m['resource_refs'])))
  binding=read(br);parts=[]
  with Path(binding['source_audit_path']).open('rb') as f:
   for offset,size,digest in zip(binding['source_line_offsets'],binding['source_line_bytes'],binding['original_line_sha256']):
    f.seek(offset);v=f.read(size);check('Root actual original audit byte range',hashlib.sha256(v).hexdigest()==digest);parts.append(v)
  check('Root complete original hostpair bytes',b''.join(parts)==Path(rr['path']).read_bytes() and same(binding['original_capture_ref'],rr))
  rows=[json.loads(v) for v in parts]
  check('Root actual original actor and paired call',rows[0]['payload']['id']==THREAD and rows[1]['payload']['call_id']==rows[2]['payload']['call_id']==binding['original_call_id'])
  check('Root original call exact probe source', 'prepare_old21_v2_runtime_qualification.root.py' in str(rows[1]['payload']) and '9184b7' in str(rows[2]['payload']))
  check('Root actual output exact manifest and scope refs',mr['sha256'] in str(rows[2]['payload']) and sr['sha256'] in str(rows[2]['payload']) and m['probe_guard_ref']['sha256'] in str(rows[2]['payload']))
  # Small read-only negative controls use the same actual observed resource set.
  def covers(resources):
   mapping={caller.canonical(r['path']):r for r in resources}
   return len(mapping)==len(resources) and all(k in mapping and same(r,mapping[k]) for k,r in observed.items())
  check('control missing caller rejected',not covers([r for r in m['resource_refs'] if not same(r,m['caller_ref'])]))
  dll=next(r for r in observed.values() if r['path'].lower().endswith('.dll'))
  check('control missing actually loaded DLL rejected',not covers([r for r in m['resource_refs'] if not same(r,dll)]))
  changed=[dict(r) for r in m['resource_refs']]
  for r in changed:
   if same(r,m['python_ref']):r['sha256']='0'*64
  check('control Python content drift rejected',not covers(changed))
  check('control duplicate resource rejected',not covers(m['resource_refs']+[m['resource_refs'][0]]))
  for r in refs:check('final pin:'+r['path'],same(pin(r['path']),r))
 except BaseException as e:error=dict(type=type(e).__name__,message=str(e))
 finally:closed=held.close()
 check('independent guard closed0',closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[])
 gr=save('Source-guard.closed.json',closed)
 if error:
  save('diagnostic.json',dict(error=error,checks=checks,guard_ref=gr));print(json.dumps(dict(error=error,guard_ref=gr),ensure_ascii=False),flush=True);raise SystemExit(1)
 closure=save('runtime-closure-observation.json',dict(runtime_manifest_ref=mr,Root_actual_probe_raw_ref=rr,Root_actual_probe_binding_ref=br,inherited_M4_qualification_ref=priorqref,inherited_M4_decision_ref=pdref,unchanged_resources=unchanged,removed_resources=removed,added_resources=added,independently_observed_resources=list(observed.values()),observer_only_ref=observer_only,Root_observer_extra_refs=extras,missing_resources=missing,drifted_resources=drift,historical_Source_controls_rerun=False,inventory_target_files_read=False,Go_Native_SQL_TP_model_calls=0,live_Canon_handles=0,Canonical_written=False))
 failed=[c for c in checks if not c['passed']];fr=save('finitechecks.json',dict(checks=checks,passed=len(checks)-len(failed),failed=failed))
 common=dict(review_author=ACTOR,source_author=m['source_author'],builder_source_author=m['builder_source_author'],root_thread_id=THREAD,**{k:m[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','python_ref','go_ref')},qualification_scope_ref=sr,runtime_manifest_ref=mr,formal_acceptance=False,execution_grant=False)
 decision=save('decision.json',dict(schema='researchos.old21-runtime-independent-review-decision.v2',**common,independent_non_author=True,verdict='RUNTIME_CLOSURE_ACCEPTED' if not failed else 'RUNTIME_CLOSURE_REJECTED',resource_refs=m['resource_refs'],finitechecks_ref=fr,Source_guard_ref=gr,closure_observation_ref=closure,programme_qualification=None))
 mf=save('MF.json',dict(schema='researchos.old21-runtime-independent-review-manifest.v2',members=refs+[gr,closure,fr,decision]))
 hdf=save('HDF.json',dict(schema='researchos.old21-runtime-independent-review-hdf.v2',**common,manifest_ref=mf,decision_ref=decision,reviewed_utc=datetime.now(timezone.utc).isoformat(),finitechecks_ref=fr,Source_guard_ref=gr,closure_observation_ref=closure,programme_qualification=None))
 print(json.dumps(dict(HDF=hdf,MF=mf,decision=decision,checks=len(checks),failed=failed,held_refs=len(refs),resource_count=len(m['resource_refs']),observed_resources=len(observed),verdict=read(decision)['verdict'],formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)
 if failed:raise SystemExit(1)
if __name__=='__main__':run()
