import json,hashlib,ast
from pathlib import Path
D=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
O=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/observed-owned-three-public-root-c2269931d64a48d7'
refs={}
def j(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def ck(r):
 a=pin(r['path']);assert (a['sha256'],a['bytes'])==(r['sha256'],r['bytes']),r['path']
 refs[a['path']]=a;return a
def save(n,d):
 with (D/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
expected=dict(path=str(O/'validation.closed.json'),sha256='5a00cfb4a7afa46690c9fb7630a887e738a3294903a78a9ddb2363abdbf1375f',bytes=21168)
ck(expected);closed=j(expected['path'])
for p in O.iterdir():
 assert p.is_file()
 ck(pin(p))
assert len(list(O.iterdir()))==20
assert closed['all_four_jobs_closed'] and closed['main_canonical_unchanged']
assert not closed['Owner_private_input_used'] and not closed['native_migration_executed'] and not closed['formal_acceptance']
assert closed['provider_requests']==closed['production_db_writes']==0
frozen=closed['frozen_runtime_refs'];assert len(frozen)==94 and len({x['path'] for x in frozen})==94
for r in frozen:ck(r)
guards={}
for kind in ('inner','outer'):
 g=j(O/(kind+'-source-guard.cleanup.actual.json'));es=g['entries']
 if isinstance(es,dict):es=list(es.values())
 assert len(es)==94 and g['closed'] and g['retained_handles_count']==0 and not g['errors'] and g['failure'] is None
 assert {x['path'] for x in es}=={x['path'] for x in frozen}
 for x in es:
  assert x['verified'] and x['final_path_match'] and x['closed'];ck(x)
 guards[kind]=dict(entries=len(es),closed=True,retained_handles=0,live_drift=0)
def good(r):
 c=r['job_cleanup']
 assert r['resumed'] and isinstance(r['owned_child_pid'],int) and isinstance(r['creation_time_100ns'],int)
 assert not c['errors'] and c['active_processes_last_observed']==0
 assert all(c[k] for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'))
outer=j(ck(closed['outer_invocation_ref'])['path']);good(outer['result'])
assert outer['actual_native_exit']==outer['result']['actual_exit']==0 and not outer['result']['timed_out'] and outer['result']['error'] is None
for k in ('stdout_ref','stderr_ref'):ck(outer[k])
inner=j(ck(closed['inner_ref'])['path'])
assert inner['cases_passed']==['normal','cancel','timeout'] and inner['all_three_jobs_closed'] and not inner['Main_or_native_authority_claim']
summary={}
for name,r in zip(inner['cases_passed'],inner['case_refs']):
 d=j(ck(r)['path']);result=d['result'];good(result);events=d['events']
 assert events[0]['event']=='assigned-before-resume' and not events[0]['observation']['resumed']
 assert events[1]['event']=='resumed' and events[1]['observation']['resumed']
 assert sum(e['event']=='assigned-before-resume' for e in events)==1 and sum(e['event']=='resumed' for e in events)==1
 for e in events:
  s=e['observation']
  assert s['owned_child_pid']==result['owned_child_pid'] and s['creation_time_100ns']==result['creation_time_100ns']
  assert s['job_cleanup']['assigned_before_resume'] and not s['job_cleanup']['handles_closed']
 counts=[e['observation']['job_cleanup']['active_processes_last_observed'] for e in events if e['observation']['job_cleanup']['active_processes_last_observed'] is not None]
 assert max(counts)>=2 and d['descendant_observed'] and d['actual_held_job_observation'] and d['component_only']
 ready=j(ck(d['public_ready_ref'])['path']);assert ready['mode']==name and ready['public_dummy']
 for k in ('stdout_ref','stderr_ref'):ck(d[k])
 assert d['stderr_ref']['bytes']==0
 if name=='normal':
  assert result['actual_exit']==0 and not result['timed_out'] and result['error'] is None and ready['child_pid'] is None
  assert j(d['stdout_ref']['path'])==dict(mode='normal',public_dummy=True)
 else:
  assert result['actual_exit']==3758097160 and result['job_cleanup']['termination_requested'] and result['job_cleanup']['termination_succeeded'] and result['job_cleanup']['termination_code_requested']==3758097160
  assert isinstance(ready['child_pid'],int) and ready['child_pid']!=result['owned_child_pid'] and max(counts)>=3
  assert d['stdout_ref']['bytes']==0
  if name=='cancel':assert not result['timed_out'] and result['error']=='RuntimeError: Root requested owned case cancellation'
  else:assert result['timed_out'] and result['error'] is None and 2<=result['elapsed_seconds']<7
 summary[name]=dict(actual_exit=result['actual_exit'],timed_out=result['timed_out'],error=result['error'],events=len(events),observed_counts=sorted(set(counts)),public_ready=ready,grandchild_created_by_probe=name!='normal',descendant_field_means_count_threshold_only=True,job_cleanup=result['job_cleanup'])
io=j(O/'original-tool-io.json');assert len(io['pairs'])==1
result=io['pairs'][0]['result']
assert result['chunk_id']=='0a0dfe' and result['exit_code']==0
lines=result['output'].splitlines();assert lines[-1]=='ROOT_PYTHON_EXIT=0'
assert json.loads(lines[0])['closed_ref']==expected
assert io['actualPythonExit']==io['actualOuterExit']==0 and io['controllerSourceFindingOpen'] and io['nativeMigrationExecutions']==0 and not io['formalAcceptance']
assert json.loads(Path(outer['stdout_ref']['path']).read_bytes())['inner_closed_ref']==closed['inner_ref']
assert outer['stderr_ref']['bytes']==0
for n in ('validate_observed_three_public.actual_owned.py','public_probe.py'):ast.parse((O/n).read_bytes())
canonical_expected={
'checkpoint':('9476bb385b95f5ed992d20b23171270d0c0525f22d2afaf5137f79ee00bc3f52',4054756),
'path_ownership':('48c5641956b5f22bb48f7775e46d90494bd95944027f55070e430e207a506452',192861),
'step_state':('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
'commands':('b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129',68156)}
for n,(sha,size) in canonical_expected.items():
 r=pin(R/'execution/v2.4'/(n+'.json'));assert (r['sha256'],r['bytes'])==(sha,size);ck(r)
e=dict(closed_ref=expected,source_scripts_AST_only=True,case_summary=summary,guard_summary=guards,original_actual_tool_IO=io,outer_result=outer['result'],frozen_runtime_refs=94,canonical_CP356_all4_current_exact=True,base_refs=list(refs.values()),new_mechanical_errors=0)
r=save('evidence.json',e)
print(json.dumps(dict(directory=str(D),evidence=r,refs=len(refs),cases=summary,guards=guards),ensure_ascii=True))
