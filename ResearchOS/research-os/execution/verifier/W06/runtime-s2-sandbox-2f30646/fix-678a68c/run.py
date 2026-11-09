from pathlib import Path
import subprocess,os,json,hashlib,time
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent;ROOT=PRIOR.parents[3]
REV='678a68c3de3faa4b04b640efbeb651e379569594'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
old=json.loads((PRIOR/'index.json').read_text());assert sha(PRIOR/'index.json')=='ec5729b5bd65247383025e244a7351e43fa4d70f24e9bc93554006b1a64c0e14'
for row in old['files']:assert sha(PRIOR/row['path'])==row['sha256']
replace={};sources=[]
for name in ['async_windows.go','async_windows_test.go','sandbox_windows.go']:
 path='ops/experiment_sandbox/'+name;raw=git('show',REV+':'+path);dest=OUT/'source'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw);replace[str(ROOT/path)]=str(dest);sources.append({'path':path,'sha256':sha(dest)})
author=[]
for name in git('ls-tree','-r','--name-only','b087f8b','execution/receipts/W06/runtime-s2/sandbox-queued-write').decode().splitlines():
 dest=OUT/'author-evidence'/Path(name).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(git('show','b087f8b:'+name));author.append({'path':name,'sha256':sha(dest)})
replace[str(ROOT/'ops/experiment_sandbox/independent_s2_test.go')]=str(PRIOR/'independent_s2_test.go')
replace[str(ROOT/'ops/experiment_sandbox/independent_s2_queuefix_test.go')]=str(OUT/'queued_write_test.go')
put(OUT/'overlay.json',{'Replace':replace})
put(OUT/'source-audit.json',{'source_revision':REV,'main_head':git('rev-parse','HEAD').decode().strip(),'sources':sources,'author_evidence':author,'prior_index_sha256':sha(PRIOR/'index.json'),'prior_index_files_verified':len(old['files']),'source_diff':git('diff','2f30646',REV,'--','ops/experiment_sandbox').decode()})
lock=json.loads((ROOT/'execution/toolchains/go.json').read_text(encoding='utf-8-sig'));exe=Path(lock['executable']);assert sha(exe)==lock['executable_sha256']
raw=OUT/'native';raw.mkdir(exist_ok=True);env=dict(os.environ);env.update(GOTOOLCHAIN='local',GOENV='off',INDEPENDENT_S2_EVIDENCE=str(raw))
args=[str(exe),'test','-json','-count=1','-timeout=45s','-overlay='+str(OUT/'overlay.json'),'./ops/experiment_sandbox','-run','^(TestRuntimeSandbox(Async|QueuedWriteDeadline)|TestIndependentS2(QueuedWriteDeadlineFixed|AlreadyCancelledFrame|ConcurrentLifecycle|BlockedWriteCancel))$']
start=time.monotonic()
with (OUT/'stdout.jsonl').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:proc=subprocess.run(args,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=60)
put(OUT/'command.json',{'argv':args,'cwd':str(ROOT),'exit_code':proc.returncode,'elapsed_seconds':time.monotonic()-start,'go_executable_sha256':lock['executable_sha256'],'env_overrides':{k:env[k] for k in ['GOTOOLCHAIN','GOENV','INDEPENDENT_S2_EVIDENCE']}})
assertions=[];tests=[]
for line in (OUT/'stdout.jsonl').read_text().splitlines():
 event=json.loads(line);output=event.get('Output','')
 if output.startswith('S2_INDEPENDENT_ASSERT '):assertions.append(json.loads(output.removeprefix('S2_INDEPENDENT_ASSERT ')))
 if event.get('Action') in ['pass','fail'] and event.get('Test'):tests.append({'test':event['Test'],'verdict':event['Action']})
put(OUT/'assertions.json',assertions);put(OUT/'test-results.json',tests)
print(json.dumps({'exit_code':proc.returncode,'assertions':len(assertions),'failed':[r for r in assertions if r['status']!='PASS'],'tests':tests,'stderr':(OUT/'stderr.log').read_text()},indent=2))
