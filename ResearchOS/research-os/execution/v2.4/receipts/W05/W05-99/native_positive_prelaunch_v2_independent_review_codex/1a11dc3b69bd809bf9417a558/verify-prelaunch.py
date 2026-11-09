import ast,json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent;R=B.parents[4]
S=B/'integration_codex/native-positive-serve-v2-root-75dc3afca9b34a99/serve_one_positive.actual_owned.py'
OLD=B/'integration_codex/native-positive-serve-root-fb5b899afd644782/serve_one_positive.actual_owned.py'
PREV=B/'native_positive_prelaunch_independent_review_codex/1a11dbdcb38cb521d5f7aa778'
C=B/'integration_codex/native-positive-controller-config-v2-root-0da7b5a0b3f84a13/controller.public.config.json'
refs={}
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def add(r):
 r=dict(path=str(Path(r['path'])),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes']);k=r['path'].casefold()
 assert k not in refs or refs[k]==r
 refs[k]=r
def walk(v):
 if isinstance(v,dict):
  if all(k in v for k in ('path','sha256','bytes')):add(v)
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
def read(p):
 add(pin(p));return json.loads(Path(p).read_bytes())
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
assert pin(S)['sha256']=='e686e3c523829f959f091fcdeee0ee9e1f8fdf0ac42638bd83c7a306f29db084'
assert pin(OLD)['sha256']=='270565809ba108d7b25ef75c8787640acff66928d3ea4055e018f91b4750bc76'
for p in (S,OLD,PREV/'HDF.json',PREV/'MF.json'):add(pin(p))
cfg=read(C);walk(cfg);assert pin(C)['sha256']=='9d561a6be761ebb2e61bb72a7bee22b07e188cee3877105827f4ca48ba6928fc' and pin(C)['bytes']==1098985
hc=read(cfg['HarnessConfig']['path']);walk(hc)
inv=read(cfg['CompilerInventory']['path']);build=read(cfg['BuildInvocation']['path']);walk(build)
assert hc['Case']=='positive-replay' and hc['CaseID']=='73df768bc70b4f64'
frozen={str(Path(r['path'])).casefold():r for r in cfg['FrozenInputs']};assert len(frozen)==4083
assert str(Path(inv['GoRef']['path'])).casefold() in frozen
assert build['actual_native_exit']==0 and '-tags=researchos_native_recovery_harness' in build['argv']
assert build['argv'][build['argv'].index('-o')+1]==cfg['TestProgram']['path']
assert build['result']['job_cleanup']['job_idle_confirmed'] and build['result']['job_cleanup']['handles_closed']
fresh=[cfg['ControllerDirectory'],hc['OutputDirectory']]
root=Path(hc['RootProgram']['path']).parent
fresh += [str(root/n) for n in ['recovery-release.json','current-schema23-to24-grant.json','consumed-schema23-to24-grants']]
assert not any(Path(p).exists() for p in fresh)
assert sorted(p.name for p in S.parent.iterdir())==['serve_one_positive.actual_owned.py']
raw=S.read_bytes();tree=ast.parse(raw);calls=[]
for n in ast.walk(tree):
 if isinstance(n,ast.Call):calls.append(dict(line=n.lineno,call=ast.unparse(n)))
config_reads=[c for c in calls if c['call']=='C.read_bytes()'];assert len(config_reads)==1 and config_reads[0]['line']==38
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
m=functions['module_raw'];ms=ast.unparse(m)
assert 'raw = checked(ref, raw)' in ms and "exec(compile(raw, str(path), 'exec'), m.__dict__)" in ms
main_try=next(n for n in tree.body if isinstance(n,ast.Try));assert main_try.lineno==53 and main_try.finalbody
assert any(c['line']==50 and c['call']=='guard.acquire(refs)' for c in calls)
assert any(c['line']==56 and c['call']=="module_raw(cfg['ControllerSource'], guard.get_buffer(cfg['ControllerSource']['path']))" for c in calls)
assert any(c['line']==57 and c['call']=="module_raw(cfg['OriginalOwnedHelper'], guard.get_buffer(cfg['OriginalOwnedHelper']['path']))" for c in calls)
assert any(c['line']==47 and c['call']=="module_raw(guard_ref, checked(guard_ref, Path(guard_ref['path']).read_bytes()))" for c in calls)
assert any(c['line']==66 and c['call']=='runtime_guard.acquire(additional)' for c in calls)
assert any(c['line']==68 and c['call']=='controller.serve(config_ref)' for c in calls)
assert any(c['line']==78 and 'helper.run_owned(argv, str(R), env, stdout, stderr, 1440' in c['call'] for c in calls)
assert not any('controller.approve' in c['call'] or 'controller.sign' in c['call'] for c in calls)
final_text='\n'.join(ast.unparse(n) for n in main_try.finalbody)
assert 'runtime_guard.close()' in final_text and 'guard.close()' in final_text
assert 'serve-child-source-guard.cleanup.actual.json' in final_text and 'serve-outer-source-guard.cleanup.actual.json' in final_text
assert "'-I', '-S', '-B', '-X', 'utf8'" in ast.unparse(tree)
canonical=[pin(R/'execution/v2.4'/(n+'.json')) for n in ('checkpoint','path_ownership','step_state','commands')]
for r in canonical:add(r)
assert canonical[0]['sha256']=='71f15760598f24631740dee94a70461f98ff4b06e05b687e80b677c9fca4708f'
for r in refs.values():assert pin(r['path'])==r,('drift',r['path'])
ref=save('evidence.json',dict(base_refs=list(refs.values()),bootstrap_ref=pin(S),previous_bootstrap_ref=pin(OLD),config_ref=pin(C),canonical_refs=canonical,frozen_inputs=4083,all_current_pins_match=True,output_and_fixed_paths_absent=fresh,launch_namespace_only_source=True,matching_test_binary_and_tagged_source_provenance=True,static_calls=calls,ordering=dict(config_single_read_line=38,config_fixed_pin_line=40,config_same_buffer_decode_line=41,guard_verified_same_buffer_module_line=47,main_guard_acquire_line=50,controller_held_buffer_module_line=56,helper_held_buffer_module_line=57,additional_runtime_guard_line=66,child_serve_line=68,parent_owned_job_line=78,finally_line=88),bootstrap_source_finding_fixed=True,target_executions=0,new_mechanical_errors=0))
print(json.dumps(dict(evidence_ref=ref,base_refs=len(refs),frozen=4083,drift=0,source_finding_fixed=True,target_executions=0,new_mechanical_errors=0)))

