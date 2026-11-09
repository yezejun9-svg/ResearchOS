from pathlib import Path
import ast,copy,hashlib,json,types,sys
N=Path(__file__).parent;P=N.parent/'continue-20261010-01'
B=N.parents[1];Q=B/'public22_to_main23_continuation_independent_review_codex/review-20261010-01'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value,raw=False):
 with (N/name).open('xb') as f:f.write(value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
reviewpins=[dict(path=str(Q/'HDF.json'),sha256='a05ca327ebeafd2e4cf4aa4db6a7e4dc9b2eee0799e1e8e0c0dc9c77163df8bf',bytes=3946),
 dict(path=str(Q/'MF.json'),sha256='f0998ab1f5a8b322667f16ce963e5e5f0599584c620b05ca5e4bbaa130625239',bytes=8459),
 dict(path=str(Q/'decision.json'),sha256='3732ba65da6ff4749b09053fa028eabbe79cd4b23a68839e2026aeee44f18bae',bytes=14371)]
assert all(pin(r['path'])==r for r in reviewpins)
review=json.loads(Path(reviewpins[2]['path']).read_bytes())
assert review['decision']=='SOURCE_CHANGES_REQUIRED' and len(review['findings'])==1 and review['findings'][0]['id']=='P22C-OBSERVATION-CLOSE-001'
protected=[pin(p) for p in sorted(P.iterdir()) if p.is_file()]
before=(P/'public22_to23_root.source.py').read_bytes()
assert hashlib.sha256(before).hexdigest()=='f2ec57df742edda3ef8840df42384308813c616cb28ca4b83b6a48ea1151e430'
old1="""def record_observation(invocation,observed,ended,stdout_path,stderr_path,pinner):
    # Persist the returned native facts in memory before any fallible output hashing.
    invocation['observation']=observed
    invocation['actual_exit']=observed.get('actual_exit')
    invocation['ended_at_unix_ns']=ended
    invocation['creation_time_100ns_decimal']=str(observed['creation_time_100ns']) if type(observed.get('creation_time_100ns')) is int else None
    invocation['stdout_ref']=pinner(stdout_path)
    invocation['stderr_ref']=pinner(stderr_path)
"""
new1="""def retain_observation(invocation,observed,ended):
    # Retain returned native facts before either output stream can fail to close.
    invocation['observation']=observed
    invocation['actual_exit']=observed.get('actual_exit')
    invocation['ended_at_unix_ns']=ended
    invocation['creation_time_100ns_decimal']=str(observed['creation_time_100ns']) if type(observed.get('creation_time_100ns')) is int else None

def record_observation(invocation,observed,ended,stdout_path,stderr_path,pinner):
    retain_observation(invocation,observed,ended)
    invocation['stdout_ref']=pinner(stdout_path)
    invocation['stderr_ref']=pinner(stderr_path)

class ObservedOutput:
    def __init__(self,path,label,invocation,state):
        self.path=path;self.label=label;self.invocation=invocation;self.state=state
    def __enter__(self):
        self.stream=self.path.open('xb')
        return self.stream
    def __exit__(self,kind,primary,traceback):
        try:self.stream.close()
        except BaseException as close_error:
            detail=dict(phase=self.label+'-close',type=type(close_error).__name__,message=str(close_error))
            self.invocation.setdefault('output_close_errors',[]).append(detail)
            if primary is None:raise
            # A pre-existing child/body/inner-close error stays primary.
            self.state['secondary_errors'].append(detail)
        return False
"""
old2="""            with outpath.open('xb') as out,errpath.open('xb') as err:
                state['new_native_children_attempted']+=1
                observed=job.run_owned(phase['argv'],phase['cwd'],env,out,err,90,creation_flags=0x08000000)
            record_observation(invocation,observed,time.time_ns(),outpath,errpath,pin)
"""
new2="""            with ObservedOutput(outpath,'stdout',invocation,state) as out,ObservedOutput(errpath,'stderr',invocation,state) as err:
                state['new_native_children_attempted']+=1
                observed=job.run_owned(phase['argv'],phase['cwd'],env,out,err,90,creation_flags=0x08000000)
                retain_observation(invocation,observed,time.time_ns())
            record_observation(invocation,observed,invocation['ended_at_unix_ns'],outpath,errpath,pin)
"""
a,b=old1.encode(),new1.encode();c,d=old2.encode(),new2.encode()
assert before.count(a)==before.count(c)==1
after=before.replace(a,b,1).replace(c,d,1)
assert after.replace(d,c,1).replace(b,a,1)==before
tree0=ast.parse(before);tree1=ast.parse(after)
defs0={n.name:ast.dump(n,include_attributes=False) for n in tree0.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
defs1={n.name:ast.dump(n,include_attributes=False) for n in tree1.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert set(defs1)-set(defs0)=={'retain_observation','ObservedOutput'}
assert [k for k in defs0 if defs0[k]!=defs1[k]]==['record_observation','execute']
assert all(defs0[k]==defs1[k] for k in defs0 if k not in ('record_observation','execute'))
caller=save('public22_to23_root.source.py',after,True)
inputs=save('source-inputs.json',(P/'source-inputs.json').read_bytes(),True)
save('revision-inverse.json',dict(original_ref=pin(P/'public22_to23_root.source.py'),revised_ref=caller,
 replacement_blocks=[dict(before=old1,after=new1),dict(before=old2,after=new2)],
 exact_complete_inverse=True,changed_existing_functions=['record_observation','execute'],added=['retain_observation','ObservedOutput'],
 all_other_top_level_definitions_identical=True,prior_namespace_protected_refs=protected,
 review_hdf_ref=reviewpins[0],review_mf_ref=reviewpins[1],review_decision_ref=reviewpins[2]))
# Execute only the actual phase output block and observation helpers using inert fakes.
nodes=[n for n in tree1.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('retain_observation','record_observation','ObservedOutput')]
execute=next(n for n in tree1.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
block=next(n for n in ast.walk(execute) if isinstance(n,ast.With) and isinstance(n.items[0].context_expr,ast.Call)
 and isinstance(n.items[0].context_expr.func,ast.Name) and n.items[0].context_expr.func.id=='ObservedOutput')
record=next(n for n in ast.walk(execute) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
 and isinstance(n.value.func,ast.Name) and n.value.func.id=='record_observation')
blockcode=compile(ast.fix_missing_locations(ast.Module(body=[block,record],type_ignores=[])),str(N/'public22_to23_root.source.py'),'exec')
helpercode=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(N/'public22_to23_root.source.py'),'exec')
controls=[]
for case in ('normal-close','stdout-close','stderr-close'):
 ns={};exec(helpercode,ns)
 events=[];known={'actual_exit':0,'pid':1234,'creation_time_100ns':134360000000000001,
  'cleanup':{'closed':True,'job_closed':True,'process_closed':True,'thread_closed':True,'job_idle':True,'idle_active_processes':0,'errors':[]}}
 state=dict(new_native_children_attempted=0,secondary_errors=[]);invocation=dict(observation=None,actual_exit=None)
 class Stream:
  def __init__(self,label):self.label=label
  def close(self):
   # The entire returned observation must exist at both actual close boundaries.
   assert invocation['observation'] is known and invocation['actual_exit']==0
   assert invocation['creation_time_100ns_decimal']=='134360000000000001'
   events.append(self.label+'-close')
   if case==self.label+'-close':raise OSError(self.label+' CLOSE_FAULT')
 class FakePath:
  def __init__(self,label):self.label=label
  def open(self,mode):assert mode=='xb';events.append(self.label+'-open');return Stream(self.label)
 class Job:
  def run_owned(self,*args,**kwargs):
   assert args[2]=={'SYNTHETIC':'1'} and args[5]==90 and kwargs==dict(creation_flags=0x08000000)
   events.append('run_owned-return');return known
 def fakepin(path):
  assert events[-2:]==['stderr-close','stdout-close'] or 'pin-stdout' in events
  events.append('pin-'+path.label);return {'path':path.label,'sha256':'0'*64,'bytes':0}
 ns.update(state=state,invocation=invocation,phase=dict(argv=['SYNTHETIC_NO_PROCESS'],cwd='SYNTHETIC'),
  env={'SYNTHETIC':'1'},job=Job(),outpath=FakePath('stdout'),errpath=FakePath('stderr'),
  time=types.SimpleNamespace(time_ns=lambda:1791590380181760800),pin=fakepin)
 error=None
 try:exec(blockcode,ns)
 except OSError as exc:error=dict(type=type(exc).__name__,message=str(exc))
 assert invocation['observation'] is known and invocation['actual_exit']==0 and invocation['creation_time_100ns_decimal']=='134360000000000001'
 assert invocation['observation']['cleanup']==known['cleanup'] and state['new_native_children_attempted']==1
 assert [e for e in events if e.endswith('-close')]==['stderr-close','stdout-close']
 if case=='normal-close':
  assert error is None and 'stdout_ref' in invocation and 'stderr_ref' in invocation
 else:
  assert error==dict(type='OSError',message=case.removesuffix('-close')+' CLOSE_FAULT')
  assert invocation['output_close_errors']==[dict(phase=case,**error)]
  assert 'stdout_ref' not in invocation and 'stderr_ref' not in invocation and not any(e.startswith('pin-') for e in events)
 controls.append(dict(case=case,passed=True,synthetic_only=True,actual_product_processes=0,
  known_observation_retained=invocation,error=error,events=events,phase_may_continue=error is None,
  product_success_claimed=False,secondary_errors=state['secondary_errors']))
controlref=save('delta-source-controls.json',dict(schema='researchos.public22-continuation-close-fix-controls.v1',caller_ref=caller,
 controls=controls,count=3,old14_controls_rerun=False,old_four_native_children_replayed=False,resource781_guard_rerun=False,
 actual_Native_Go_SQL_TP_Rootstage_calls=0,formal_acceptance=False))
historyref=save('historical-review-prefix.json',dict(prior_source_hdf_ref=pin(P/'HDF.json'),prior_source_mf_ref=pin(P/'MF.json'),
 old14_controls_ref=pin(P/'delta-source-controls.json'),old14_success_preserved_not_rerun=True,
 independent_changes_required_refs=reviewpins,prior_counterexample_ref=review['new_source_controls_ref'],
 prior_781_resource_closure_ref=review['declared_public_resource_closure_ref'],
 prior_guard_closed_refs=review['actual_source_guard_cleanup_refs'],historical_only=True,
 prior_review_runtime_closure_reviewed=review['runtime_closure_reviewed'],future_Root_loaded_resource_gate_required=True,
 original1025='FAILED_RETAINED',old_four_native_children_replayed=False))
contract=json.loads((P/'root-calling-contract.source.json').read_bytes())
contract.update(caller_ref=caller,source_inputs_ref=inputs,source_only_controls=controlref,
 historical_review_prefix_ref=historyref,revision_reason='P22C-OBSERVATION-CLOSE-001',
 first_failure='Known Native observation, actual_exit, end time, exact decimal FILETIME and Job cleanup are retained immediately after run_owned returns, before either output stream closes. Stream close errors are recorded separately; pre-existing child/body/inner-close exceptions remain primary. Output hashes are attempted only after successful closes. NULL remains only when run_owned returned no observation. Close faults stop the phase and do not imply product success.',
 source_revision='continue-20261010-02',runtime_resource_qualification='Prior 781-resource review is historical only; new Source requires real non-author review and future Root runtime resource qualification before any execution.')
save('root-calling-contract.source.json',contract)
save('source-decision.json',dict(schema='researchos.public22-continuation-source-revision-declaration.v1',
 source_author='codex:/root/attach_restore_independent_review',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION',
 revision_reason='P22C-OBSERVATION-CLOSE-001',caller_ref=caller,source_inputs_ref=inputs,
 calling_contract_ref=pin(N/'root-calling-contract.source.json'),delta_controls_ref=controlref,
 historical_review_prefix_ref=historyref,complete_inverse_ref=pin(N/'revision-inverse.json'),
 source_author_acceptance=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False,
 Native_SQL_Go_TP_Rootstage_calls=0,STOP=True))
assert all(pin(ref['path'])==ref for ref in protected)
print(json.dumps(dict(caller_ref=caller,contract_ref=pin(N/'root-calling-contract.source.json'),
 delta_controls_ref=controlref,source_decision_ref=pin(N/'source-decision.json'),
 controls=3,prior_namespace_files_unchanged=len(protected),actual_Native_Go_SQL_TP_Rootstage_calls=0),ensure_ascii=False))

