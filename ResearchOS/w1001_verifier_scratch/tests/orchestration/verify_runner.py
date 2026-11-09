"""Adversarial runner-protocol checks, explicitly not domain acceptance evidence."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('orchestration_runner',ROOT/'ops/ci/orchestration.py')
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
real_run=subprocess.run
expected=runner.EXPECTED['TestW06ContextContinuation']
base=[{'assertion_id':id,'expected':True,'actual':True,'status':'PASS','evidence':{'fixture':'runner protocol only'}} for id in expected]
cases={'zero':b'PASS\n','duplicate':b'\n'.join(('W06_ASSERTION '+json.dumps(x)).encode() for x in base+[base[0]]),'malformed':b'W06_ASSERTION not-json\n','missing':b'\n'.join(('W06_ASSERTION '+json.dumps(x)).encode() for x in base[:-1])}
rows=[]
for name,raw in cases.items():
 def fake_run(cmd,*args,**kwargs):
  if isinstance(cmd,list) and len(cmd)>1 and cmd[1]=='test':return subprocess.CompletedProcess(cmd,0,raw,b'')
  return real_run(cmd,*args,**kwargs)
 with patch.dict(os.environ,{'RESEARCHOS_TASK_ID':'W06','RESEARCHOS_CHECK_ID':'W06-G02','RESEARCHOS_CASE_ID':''}),patch.object(runner.sys,'argv',['orchestration.py','--mode','fixture']),patch.object(subprocess,'run',fake_run),contextlib.redirect_stdout(io.StringIO()) as output:
  result=runner.main()
 observed=json.loads(output.getvalue())
 report_path=Path(observed['receipt'])
 report=json.loads(report_path.read_text(encoding='utf-8'))
 report.update(scope='RUNNER_PROTOCOL_FAULT_INJECTION_ONLY',subprocess_execution='MOCKED_NOT_EXECUTED',injected_stdout_case=name)
 report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 row={'assertion_id':'RUNNER-'+name.upper(),'expected':1,'actual':result,'status':'PASS' if result==1 else 'FAIL','evidence':json.loads(output.getvalue())}
 rows.append(row)
print(json.dumps({'scope':'RUNNER_PROTOCOL_FAULT_INJECTION_ONLY','status':'PASS' if all(x['status']=='PASS' for x in rows) else 'FAIL','assertions':rows}))
raise SystemExit(0 if all(x['status']=='PASS' for x in rows) else 1)
