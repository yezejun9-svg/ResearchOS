from pathlib import Path
import subprocess,os,json,hashlib,time
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent;ROOT=PRIOR.parents[3];REV='65c66a4707c3fe714899d9819a50d26b5dcce853'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
replace={};sources=[]
for name in ['async_windows.go','async_windows_test.go','sandbox_windows.go']:
 p='ops/experiment_sandbox/'+name;dest=OUT/'source'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(git('show',REV+':'+p));replace[str(ROOT/p)]=str(dest);sources.append({'path':p,'sha256':sha(dest)})
for path in git('ls-tree','-r','--name-only','d3d6977','execution/receipts/W06/runtime-s2/sandbox-start-cancel').decode().splitlines():
 dest=OUT/'author-evidence'/Path(path).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(git('show','d3d6977:'+path))
replace[str(ROOT/'ops/experiment_sandbox/independent_s2_test.go')]=str(PRIOR/'independent_s2_test.go');replace[str(ROOT/'ops/experiment_sandbox/independent_cancel_fence_test.go')]=str(OUT/'start_cancel_test.go');put(OUT/'overlay.json',{'Replace':replace})
put(OUT/'source-audit.json',{'source_revision':REV,'main_head':git('rev-parse','HEAD').decode().strip(),'sources':sources,'diff':git('show',REV,'--','ops/experiment_sandbox/async_windows.go','ops/experiment_sandbox/async_windows_test.go').decode()})
lock=json.loads((ROOT/'execution/toolchains/go.json').read_text(encoding='utf-8-sig'));exe=Path(lock['executable']);assert sha(exe)==lock['executable_sha256'];native=OUT/'native';native.mkdir(exist_ok=True);env=dict(os.environ,GOTOOLCHAIN='local',GOENV='off',INDEPENDENT_S2_EVIDENCE=str(native))
args=[str(exe),'test','-json','-count=1','-timeout=25s','-overlay='+str(OUT/'overlay.json'),'./ops/experiment_sandbox','-run','^(TestRuntimeSandboxStartCancellationCleanup|TestIndependentStartCancellationFence)$'];start=time.monotonic()
with (OUT/'stdout.jsonl').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:r=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=40)
put(OUT/'command.json',{'argv':args,'cwd':str(ROOT),'exit_code':r.returncode,'seconds':time.monotonic()-start,'go_sha256':sha(exe)})
assertions=[]
for line in (OUT/'stdout.jsonl').read_text().splitlines():
 e=json.loads(line);o=e.get('Output','')
 if o.startswith('S2_INDEPENDENT_ASSERT '):assertions.append(json.loads(o.removeprefix('S2_INDEPENDENT_ASSERT ')))
put(OUT/'assertions.json',assertions);print(json.dumps({'exit_code':r.returncode,'assertions':len(assertions),'failures':[x for x in assertions if x['status']!='PASS'],'stderr':(OUT/'stderr.log').read_text()},indent=2))
