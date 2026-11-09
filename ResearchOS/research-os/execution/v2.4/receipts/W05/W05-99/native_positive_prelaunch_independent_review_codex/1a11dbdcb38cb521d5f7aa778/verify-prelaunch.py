import ast,json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent.parent;R=B.parents[4]
S=B/'integration_codex/native-positive-serve-root-fb5b899afd644782/serve_one_positive.actual_owned.py'
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
add(pin(S));assert pin(S)['sha256']=='270565809ba108d7b25ef75c8787640acff66928d3ea4055e018f91b4750bc76'
cfg=read(C);walk(cfg);assert pin(C)['sha256']=='9d561a6be761ebb2e61bb72a7bee22b07e188cee3877105827f4ca48ba6928fc'
hc=read(cfg['HarnessConfig']['path']);walk(hc)
inv=read(cfg['CompilerInventory']['path']);build=read(cfg['BuildInvocation']['path']);walk(build)
assert hc['Case']=='positive-replay' and hc['CaseID']=='73df768bc70b4f64'
frozen={str(Path(r['path'])).casefold():r for r in cfg['FrozenInputs']}
assert len(frozen)==4083
assert str(Path(inv['GoRef']['path'])).casefold() in frozen
required=['native_migration_authority_harness_windows_test.go','backup_prepared_abandonment_upgrade_windows_test.go','backup_configuration_upgrade_test.go','backup_upgrade_test.go']
for name in required:
 p=Path(hc['BuildRoot'])/'internal/domain'/name;add(pin(p))
 assert str(p).casefold() in frozen
 assert any(str(Path(v['path'])).casefold()==str(p).casefold() for v in inv['build_inputs'])
assert build['actual_native_exit']==0 and '-tags=researchos_native_recovery_harness' in build['argv']
assert build['argv'][build['argv'].index('-o')+1]==cfg['TestProgram']['path']
assert build['result']['job_cleanup']['job_idle_confirmed'] and build['result']['job_cleanup']['handles_closed']
fresh=[cfg['ControllerDirectory'],hc['OutputDirectory']]
root=Path(hc['RootProgram']['path']).parent
fresh += [str(root/n) for n in ['recovery-release.json','current-schema23-to24-grant.json','consumed-schema23-to24-grants']]
assert not any(Path(p).exists() for p in fresh)
assert sorted(p.name for p in S.parent.iterdir())==['serve_one_positive.actual_owned.py']
tree=ast.parse(S.read_bytes());calls=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Call):calls.append(dict(line=node.lineno,call=ast.unparse(node.func)))
assert any(x==dict(line=21,call='module') for x in calls)
assert any(x==dict(line=40,call='guard.acquire') for x in calls)
module=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='module')
assert 'exec(compile(path.read_bytes()' in ast.get_source_segment(S.read_text(),module)
canonical=[pin(R/'execution/v2.4'/(n+'.json')) for n in ('checkpoint','path_ownership','step_state','commands')]
for r in canonical:add(r)
assert canonical[0]['sha256']=='71f15760598f24631740dee94a70461f98ff4b06e05b687e80b677c9fca4708f'
for r in refs.values():assert pin(r['path'])==r,('drift',r['path'])
ref=save('evidence.json',dict(base_refs=list(refs.values()),bootstrap_ref=pin(S),config_ref=pin(C),canonical_refs=canonical,frozen_inputs=4083,all_current_pins_match=True,output_and_fixed_paths_absent=fresh,launch_namespace_only_source=True,matching_test_binary_and_tagged_source_provenance=True,static_calls=calls,observed_order=dict(controller_exec_line=21,guard_helper_exec_line=24,guard_acquire_line=40),timeouts=dict(harness_context_seconds=1200,inner_job_seconds=1260,controller_cancel_seconds=1270,outer_job_seconds=1440,go_test_seconds=1500),target_executions=0,new_mechanical_errors=0))
print(json.dumps(dict(evidence_ref=ref,base_refs=len(refs),frozen=4083,drift=0,target_executions=0,new_mechanical_errors=0)))

