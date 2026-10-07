from pathlib import Path
import subprocess,os,json,hashlib,datetime,time
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
lock=json.loads((ROOT/'execution/toolchains/go.json').read_text(encoding='utf-8-sig'));exe=Path(lock['executable']);assert hashlib.sha256(exe.read_bytes()).hexdigest()==lock['executable_sha256']
raw=OUT/'native';raw.mkdir(exist_ok=True)
env=dict(os.environ);env.update(GOTOOLCHAIN='local',GOENV='off',INDEPENDENT_S2_EVIDENCE=str(raw))
args=[str(exe),'test','-json','-count=1','-timeout=90s','-overlay='+str(OUT/'overlay.json'),'./ops/experiment_sandbox','-run','^(TestRuntimeSandbox(Async|BeforeResumeVeto|StreamLimit)|TestSandboxRootOverlap|TestIndependentS2(PersistBeforeResume|Veto|ConcurrentLifecycle|BlockedWriteCancel|StreamError|RunCompatibility))$']
begin=datetime.datetime.now(datetime.timezone.utc).isoformat();start=time.monotonic()
with (OUT/'stdout.jsonl').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:
 proc=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=105)
receipt={'argv':args,'cwd':str(ROOT),'started_at':begin,'elapsed_seconds':time.monotonic()-start,'exit_code':proc.returncode,'go_executable_sha256':lock['executable_sha256'],'env_overrides':{k:env[k] for k in ['GOTOOLCHAIN','GOENV','INDEPENDENT_S2_EVIDENCE']}}
(OUT/'command.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
events=[];assertions=[]
for line in (OUT/'stdout.jsonl').read_text(encoding='utf-8').splitlines():
 try:event=json.loads(line)
 except ValueError:continue
 events.append(event)
 output=event.get('Output','')
 if output.startswith('S2_INDEPENDENT_ASSERT '):assertions.append(json.loads(output.removeprefix('S2_INDEPENDENT_ASSERT ')))
(OUT/'assertions.json').write_text(json.dumps(assertions,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'exit_code':proc.returncode,'elapsed_seconds':receipt['elapsed_seconds'],'assertion_count':len(assertions),'failed_assertions':[r for r in assertions if r['status']!='PASS'],'test_results':[{'test':e.get('Test'),'action':e['Action']} for e in events if e.get('Action') in ['pass','fail']],'stderr':(OUT/'stderr.log').read_text(encoding='utf-8')},indent=2))
