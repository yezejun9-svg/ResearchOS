import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
N=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/complete-public-graph-and-g2-r310'
RUNNER=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_continuation_preparation_codex/cli18-r310-67487c3a/runner.v5.py'
lanes={'remaining17':('cli17_scope.json','cli17_continuation_scope_ref','2a7433ca7802eb9e003642e2aa2de6b2e90d5289ea2e92316a997ce342ab1834'),'windows4':('cli_windows4_scope.json','cli_windows4_continuation_scope_ref','93eba52ff2b9190e63d6be713498ac7763a26b97028d485e6ea9731136032ccc')}
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def check(x,m):
 if not x:raise RuntimeError(m)
def save(p,v):
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
check(sys.flags.isolated and not sys.flags.optimize,'Python -I without optimization required')
check(len(sys.argv)==2 and sys.argv[1] in lanes,'EXACT_LANE')
lane=sys.argv[1];name,key,want=lanes[lane];scope=N/name;handoff=N/'handoff-r310-running.json'
check(ref(handoff)['sha256']=='c14d7fd45d2663067d2fbff8edfd093c7d0bd96d02117a4feab57fe9f1df6170','HANDOFF')
check(ref(RUNNER)['sha256']=='4082541964c610258b308c6439d5ea4b37167251729ef03653f1046e06807d9f','RUNNER')
check(ref(scope)['sha256']==want,'SCOPE')
cp=json.loads((ROOT/'execution/v2.4/checkpoint.json').read_bytes());pin=cp['work_in_progress'][key]
check(cp['revision']==310 and len(cp['failure_counters'])==384,'CP310')
check((ROOT/pin['path']).resolve()==scope.resolve() and pin['sha256']==want,'ACTUAL_SCOPE_PIN')
value=json.loads(scope.read_bytes());check(not Path(value['cli_bounded_continuation']['output']).exists(),'OUTPUT_EXISTS')
lock=json.loads((ROOT/'execution/toolchains/locked.json').read_bytes())['tools']
check(Path(sys.executable).resolve()==Path(lock['python']['path']).resolve() and ref(sys.executable)['sha256']==lock['python']['sha256'],'PYTHON')
OUT=HERE/lane;OUT.mkdir(exist_ok=False)
canon=[]
for name in ('checkpoint','path_ownership','step_state','commands'):
 p=ROOT/f'execution/v2.4/{name}.json';raw=p.read_bytes()
 expected=N/(name+('.desired.json' if name in ('checkpoint','path_ownership') else '.original.json'))
 check(raw==expected.read_bytes(),'CANONICAL:'+name)
 with (OUT/(name+'.before.json')).open('xb') as f:f.write(raw)
 canon.append(ref(p))
argv=[sys.executable,'-X','utf8','-I',str(RUNNER),'--lane',lane,'--scope',str(scope),'--scope-sha256',want]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(OUT/'preflight.json',dict(lane=lane,canonical=canon,scope=ref(scope),handoff=ref(handoff),runner=ref(RUNNER),launcher=ref(__file__),actual_tuple=[310,138,384],argv=argv,output_absent=True))
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','OS','PATHEXT','PATH','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE','PROCESSOR_IDENTIFIER','PROCESSOR_LEVEL','PROCESSOR_REVISION'}}
result=None;error=None
try:
 with (OUT/'stdout.raw').open('xb') as stdout,(OUT/'stderr.raw').open('xb') as stderr:
  result=subprocess.run(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
except BaseException as e:error=dict(type=type(e).__name__,message=str(e))
finally:
 save(OUT/'invocation.json',dict(argv=argv,cwd=str(ROOT),started_at=started,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_exit=result.returncode if result else None,wrapper_error=error,stdout=ref(OUT/'stdout.raw') if (OUT/'stdout.raw').is_file() else None,stderr=ref(OUT/'stderr.raw') if (OUT/'stderr.raw').is_file() else None,runner=ref(RUNNER),launcher=ref(__file__),automatic_retry=False))
print(json.dumps(dict(lane=lane,actual_exit=result.returncode if result else None,error=error,invocation=ref(OUT/'invocation.json')),ensure_ascii=False))
sys.exit(result.returncode if result else 1)
