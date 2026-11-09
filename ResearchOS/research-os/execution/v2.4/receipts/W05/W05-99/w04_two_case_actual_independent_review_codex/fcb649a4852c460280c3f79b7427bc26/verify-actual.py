import json,hashlib,ast
from pathlib import Path
D=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
O=B/'integration_codex/w04-two-resource-repaired-cases-root-86149090aa0241f8'
refs={}
def j(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def key(p):return str(Path(p)).casefold()
def ck(r):
 a=pin(r['path']);assert (a['sha256'],a['bytes'])==(r['sha256'].removeprefix('sha256:'),r['bytes']),r['path']
 refs[key(a['path'])]=a;return a
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
expected=dict(path=str(O/'validation.closed.json'),sha256='930c553793e8e85acc046d45921840387d98aa90fb807a4848ec311ec16119b6',bytes=1139220)
ck(expected);c=j(expected['path']);assert len(list(O.iterdir()))==7
for p in O.iterdir():assert p.is_file();ck(pin(p))
frozen={key(r['path']):ck(r) for r in c['frozen_source_refs']}
assert len(frozen)==len(c['frozen_source_refs'])==4337
g=j(O/'input-source-guard.cleanup.actual.json')
assert g['closed'] and not g['errors'] and g['failure'] is None and g['retained_handles_count']==0 and len(g['entries'])==4337
guarded={}
for r in g['entries']:
 assert r['verified'] and r['final_path_match'] and r['closed']
 a=ck(r);guarded[key(a['path'])]=a
assert guarded==frozen
ci=j(ck(c['compiler_input_ref'])['path']);test=ck(c['test_binary_ref'])
assert test['sha256']=='3412a2b3fbf86c69584ad71503fffa0fd64b435d66ca203e1939e3cc7b9c53c1' and test['bytes']==42258944
assert ci['package_count']==364 and ci['build_input_count']==3793 and ci['product_inventory_count']==599
for r in ci['build_inputs']+ci['product_inventory']+ci['compiler_tool_refs']+[ci['GoRef']]:
 assert key(r['path']) in frozen
 a=pin(r['path']);assert a['sha256']==r['sha256'].removeprefix('sha256:') and a['bytes']==r['bytes']
res=j(ck(c['exact_resource_ref'])['path'])
for r in res['source_refs']:assert key(r['path']) in frozen
ind=j(ck(c['resource_independent_ref'])['path'])
assert ind['decision']=='W04_FROZEN_RESOURCE_COMPONENT_ACCEPTED_STOP'
inv=j(ck(c['invocation_ref'])['path']);argv=inv['argv']
assert argv==[ci['GoRef']['path'],'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',test['path'],'-test.v=test2json','-test.run=^(TestW04A01|TestW04CurrentA01)$','-test.count=1','-test.timeout=3m']
env=inv['public_environment'];T=Path(inv['cwd']).parent.parent
assert env['RESEARCHOS_W04_PACKAGE_INPUT']==res['package_input']
assert env['PATH'].split(';')[0]==str(Path(res['python_ref']['path']).parent)
assert env['PYTHONUTF8']==env['PYTHONDONTWRITEBYTECODE']=='1'
assert 'RESEARCHOS_NATIVE_MIGRATION_HARNESS_CONFIG' not in env
legacy=[p for p in (T/'spec/v2.0').rglob('*') if p.is_file()]
snapshot=[p for p in Path(res['package_input']).rglob('*') if p.is_file()]
assert len(legacy)==34 and len(snapshot)==148
for p in legacy+snapshot:assert key(p) in frozen
tool2=Path(env['GOROOT'])/'pkg/tool/windows_amd64/test2json.exe'
assert not tool2.exists() and key(tool2) not in frozen
wrapper_missing=[]
for rel in ('src/cmd/test2json/main.go','src/cmd/internal/test2json/test2json.go'):
 p=Path(env['GOROOT'])/rel
 assert p.is_file() and key(p) not in frozen
 wrapper_missing.append(ck(pin(p)))
dispatch_ref=ck(pin(Path(env['GOROOT'])/'src/cmd/go/internal/tool/tool.go'))
result=inv['result'];jc=result['job_cleanup']
assert result['actual_exit']==inv['actual_native_exit']==0 and not result['timed_out'] and result['error'] is None and result['resumed']
assert not jc['errors'] and jc['active_processes_last_observed']==0 and not jc['termination_requested']
assert all(jc[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'))
for k in ('stdout_ref','stderr_ref'):ck(inv[k])
assert inv['stdout_ref']['bytes']==188894 and inv['stderr_ref']['bytes']==0
events=[json.loads(x) for x in Path(inv['stdout_ref']['path']).read_bytes().splitlines()]
assert len(events)==165 and all(e['Package']=='researchos.local/research-os/internal/domain' for e in events)
expected_tests=['TestW04A01','TestW04CurrentA01']
runs=[e['Test'] for e in events if e['Action']=='run'];assert runs==expected_tests
term=[e for e in events if e['Action'] in ('pass','fail','skip') and e.get('Test')]
assert len(term)==2 and [e['Test'] for e in term]==expected_tests and all(e['Action']=='pass' for e in term)
package_terminal=[e for e in events if e['Action'] in ('pass','fail','skip') and not e.get('Test')]
assert len(package_terminal)==1 and package_terminal[0]['Action']=='pass'
assert c['terminal_actions']==dict.fromkeys(expected_tests,'pass') and c['counts']=={'pass':2,'fail':0,'skip':0}
assertions=[]
for t in expected_tests:
 joined=''.join(e.get('Output','') for e in events if e.get('Test')==t and e['Action']=='output')
 assertions_t=[json.loads(s[len('W04_ASSERTION '):]) for s in joined.splitlines() if s.startswith('W04_ASSERTION ')]
 assert len(assertions_t)==(3 if t=='TestW04A01' else 2)
 for a in assertions_t:
  assert a['actual']==a['expected']
  assertions.append(dict(test=t,assertion_id=a['assertion_id'],status=a['status'],expected=a['expected'],actual=a['actual']))
io=j(O/'original-tool-io.json')
assert io['launch']['result']['chunk_id']=='918fd1' and io['launch']['result']['session_id']==io['completion']['input']['session_id']==25121
r=io['completion']['result'];assert r['chunk_id']=='ad1a3d' and r['exit_code']==0
lines=r['output'].splitlines();assert lines[-1]=='ROOT_PYTHON_EXIT=0'
assert json.loads(lines[0])['closed_ref']==expected
for r in c['canonical_unchanged_refs']:ck(r)
assert j(R/'execution/v2.4/checkpoint.json')['revision']==356
for k in ('native_migration_cases_executed','private_key_reads','issuer_signatures','original_trial_DB_writes','external_provider_requests'):assert c[k]==0
assert not c['formal_acceptance']
ast.parse((O/'validate_w04_two_cases.actual_owned.py').read_bytes())
python=Path(res['python_ref']['path']).parent
missing=[]
for rel in ('Lib/argparse.py','Lib/datetime.py','Lib/urllib/parse.py','Lib/site.py'):
 p=python/rel;assert p.is_file() and key(p) not in frozen
 missing.append(ck(pin(p)))
e=dict(closed_ref=expected,original_root_IO=io,case_terminal=term,package_terminal=package_terminal,assertions=assertions,events=165,owned_job=result,guards_4337_all_closed_current_pins_match=True,tagged_test_compiler_inputs_3793_product599_tools_all_present=True,legacy_spec_files_guarded=34,frozen_snapshot_files_guarded=148,tagged_test_ref=test,resource_scope='Two exact observed test results only; complete event-wrapper and descendant Python dependency closure NOT established',legacy_python_gap=dict(importer_ref=ck(pin(T/'spec/v2.0/tools/validate_package.py')),import_lines=[8,10,16],legacy_invocation_source=ck(pin(T/'internal/domain/context_test.go')),legacy_invocation_line=313,missing_from_actual_guard_current_refs=missing,refs_are_current_supplemental_not_retroactive_guards=True,affects='TestW04A01 only'),common_wrapper_gap=dict(expected_tool_path=str(tool2),tool_binary_exists_now=False,tool_binary_guarded=False,tool_source_missing_refs=wrapper_missing,dispatch_source_ref=dispatch_ref,dispatch_lines=[100,120,123,268,334,349],actual_compile_or_cache_hit_not_observed=True,affects='both cases event wrapper',future_prebuilt_exact_tool_or_complete_tool_build_closure_required=True),formal_owner_labels_not_consumed_as_authority=True,reviewer_target_execution=0,review_diagnostic_ordinal=816,base_refs=list(refs.values()))
r=save('evidence.json',e)
print(json.dumps(dict(directory=str(D),evidence=r,base_refs=len(refs),pass_count=2,assertions=5,guards=4337,legacy=34,snapshot=148,unguarded_child_python_dependencies=len(missing),new_errors_excluding816=0),ensure_ascii=True))
