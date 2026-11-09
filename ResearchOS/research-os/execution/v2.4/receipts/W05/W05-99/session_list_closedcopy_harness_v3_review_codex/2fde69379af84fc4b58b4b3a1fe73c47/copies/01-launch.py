import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,os,datetime,types
P=Path(__file__).resolve().parent;W=P.parents[6]
# Exact task paths; no computed deletion or cleanup.
W=Path(r'D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-session-list-proof-r312')
H=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py')
raw=H.read_bytes()
if hashlib.sha256(raw).hexdigest()!='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad':raise RuntimeError('Helper mismatch')
m=types.ModuleType('owned');m.__file__=str(H);exec(compile(raw,str(H),'exec'),m.__dict__)
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
env.update(PATH='C:/Windows/System32;C:/Windows',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
argv=[sys.executable,'-I',str(P/'execute.py')];started=datetime.datetime.now(datetime.timezone.utc).isoformat();result=None
try:
 with (P/'driver.stdout.raw').open('xb') as so,(P/'driver.stderr.raw').open('xb') as se:result=m.run_owned(argv,str(W),env,so,se,1800)
finally:
 with (P/'driver.invocation.json').open('x',encoding='utf-8') as f:json.dump({'argv':argv,'cwd':str(W),'environment':env,'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':result,'actual_exit':result.get('actual_exit') if result else None},f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=True))
c=result.get('job_cleanup') or {}
sys.exit(0 if result.get('actual_exit')==0 and result.get('error') is None and result.get('timed_out') is False and result.get('resumed') is True and all(c.get(k) is True for k in ['kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and c.get('errors')==[] else 1)
