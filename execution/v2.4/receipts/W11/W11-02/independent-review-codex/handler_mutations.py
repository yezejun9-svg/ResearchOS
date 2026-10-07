import contextlib, copy, importlib.util, io, json, os, pathlib, sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os'); OUT=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('w1102_under_review',ROOT/'tests/jev/w1102_check.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=json.loads((OUT/'audit40-rows.json').read_text())
actual=json.loads((ROOT/'execution/v2.4/receipts/W11/W11-02/dispatched/03ca6c36-4bfd-4814-982a-d6b506d9dd10/report.json').read_text())
checks=[]
for variant in ['valid-blocked','zero','duplicate','missing','unknown','mismatched','malformed-json','failed-exit','source-drift','tool-hash']:
 root=OUT/'handler-synthetic'/variant;root.mkdir(parents=True)
 for f in ['tests/jev/w1102_check.py','tests/jev/w1102_probe/main.go','go.mod','go.sum','execution/verifier/W11/frozen-live-ac9d6153/aggregate.stdout.json']:
  target=root/f;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/f).read_bytes())
 changed=copy.deepcopy(rows)
 if variant=='zero':changed=[]
 if variant=='duplicate':changed[-1]=changed[0]
 if variant=='missing':changed=changed[:-1]
 if variant=='unknown':changed[-1]['assertion_id']='UNEXPECTED'
 if variant=='mismatched':changed[0]['actual']='FORGED_DIFFERENT_VALUE'
 raw=''.join('W11_ASSERTION '+json.dumps(x)+'\n' for x in changed).encode()
 if variant=='malformed-json':raw+=b'W11_ASSERTION {broken\n'
 calls=[]
 def fake_run(argv,**kwargs):
  calls.append(argv)
  if argv[1]=='version':return SimpleNamespace(returncode=0,stdout=b'go version go1.27.1 windows/amd64\n',stderr=b'')
  if argv[1]=='test':
   if variant=='source-drift':(root/'go.mod').write_text('synthetic source drift')
   return SimpleNamespace(returncode=1 if variant=='failed-exit' else 0,stdout=raw,stderr=b'')
  if argv[1]=='run':return SimpleNamespace(returncode=0,stdout=json.dumps(actual['resource_probe']).encode(),stderr=b'')
  raise AssertionError(argv)
 stdout=io.StringIO();stderr=io.StringIO()
 env={'RESEARCHOS_TASK_ID':'W11','RESEARCHOS_CHECK_ID':'W11-02','RESEARCHOS_CASE_ID':'','RESEARCHOS_GO':str(ROOT/'.local/tools/go1.27.1/go/bin/go.exe')}
 with patch.object(m,'ROOT',root),patch.object(m,'__file__',str(root/'tests/jev/w1102_check.py')),patch.dict(os.environ,env,clear=True),patch.object(m.sys,'argv',['w1102_check.py']),patch.object(m.subprocess,'run',fake_run),patch.object(m.subprocess,'check_output',return_value='SYNTHETIC_NOT_GIT\n'),patch.object(m,'GO_SHA256','sha256:wrong' if variant=='tool-hash' else m.GO_SHA256),contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
  code=m.main()
 want=2 if variant=='valid-blocked' else 1
 assert code==want,(variant,code)
 if stdout.getvalue():
  summary=json.loads(stdout.getvalue());assert summary['status']==('BLOCKED' if variant=='valid-blocked' else 'FAIL')
  if variant=='valid-blocked':assert len(summary['assertion_ids'])==len(set(summary['assertion_ids']))==40
 if variant not in ('valid-blocked','source-drift'):assert not any(c[1]=='run' for c in calls)
 for name,body in [('stdout.txt',stdout.getvalue()),('stderr.txt',stderr.getvalue())]:
  with (root/name).open('x',encoding='utf-8') as f:f.write(body)
 checks.append({'id':'HANDLER-'+variant,'status':'PASS','actual_exit_code':code,'expected_exit_code':want,'real_subprocesses':0,'mode':'SYNTHETIC_HANDLER_MUTATION_ONLY'})
with (OUT/'handler-mutation-results.json').open('x',encoding='utf-8') as f:json.dump({'checks':checks,'status':'PASS_IN_SCOPE','real_subprocesses':0},f,indent=2)
print(json.dumps({'status':'PASS_IN_SCOPE','synthetic_mutations':len(checks),'real_subprocesses':0}))
