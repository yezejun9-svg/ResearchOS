"""Retain failed audit origins; reuse actual nine-test success, run only bridge."""
from pathlib import Path
BASE=Path(__file__).resolve().parent
original=(BASE/'audit_candidate.py').read_text(encoding='utf-8')
exec(compile(original.split('# Execute only the unchanged test helpers')[0],str(BASE/'audit_candidate.py'),'exec'))
prior=read(OUT/'attempt2/test_collect.invocation.json')
require(prior['exit_code']==0,'actual collector exit')
for key in ('stdout_ref','stderr_ref'):require(sha(Path(prior[key]['path']))==prior[key]['sha256'],'original raw changed')
stderr=Path(prior['stderr_ref']['path']).read_text(encoding='utf-8')
require('OK' in stderr.splitlines() and 'Ran 9 tests' in stderr and ' ... ERROR' not in stderr and ' ... FAIL' not in stderr,'actual nine tests')
synthetic=OUT/'attempt2/SYNTHETIC_NOT_PRODUCT';new=synthetic/PREFIX
argv=[sys.executable,'-B','-X','utf8',str(new/'test_bridge.py'),'-v'];start=datetime.now(timezone.utc).isoformat()
result=subprocess.run(argv,cwd=synthetic,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True)
for kind,raw in [('stdout',result.stdout),('stderr',result.stderr)]:
    with (OUT/('test_bridge.'+kind)).open('xb') as f:f.write(raw)
record={'classification':'SYNTHETIC_NOT_PRODUCT','actual_argv':argv,'cwd':str(synthetic),'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,'stdout_ref':ref(OUT/'test_bridge.stdout'),'stderr_ref':ref(OUT/'test_bridge.stderr'),'expected_tests':4}
save('test_bridge.invocation.json',record)
require(result.returncode==0 and 'OK' in result.stderr.decode().splitlines() and 'Ran 4 tests' in result.stderr.decode(),'actual bridge controls')
unit_runs=[prior,record]
exec(compile(original[original.index("require(all(sha(WT/p['path'])"):],str(BASE/'audit_candidate.py'),'exec'))
